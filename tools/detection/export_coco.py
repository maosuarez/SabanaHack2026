"""Exporta train/test en formato COCO + imágenes a outputs/colab_bundle(.zip) para Colab."""

from __future__ import annotations

import json
import shutil
import zipfile
from typing import Any

from common import FLOWERS_CSV, OUT_DIR, ROOT, load_gt, md5_to_file
from PIL import Image

BUNDLE = ROOT / "outputs/colab_bundle"
ZIP_PATH = ROOT / "outputs/colab_bundle.zip"
EXPECTED = {"train": 154, "test": 24}


def build_coco(
    md5s: list[str], gt: dict[str, list[tuple[float, float, float, float]]]
) -> dict[str, Any]:
    """COCO con una categoría 'rose'; bbox = [x, y, w, h] en píxeles (esquina sup. izq.)."""
    files = md5_to_file()
    images: list[dict[str, Any]] = []
    anns: list[dict[str, Any]] = []
    for i, m in enumerate(md5s, start=1):
        with Image.open(files[m]) as im:
            w, h = im.size
        images.append(
            {"id": i, "file_name": files[m].name, "width": w, "height": h, "md5": m}
        )
        for x1, y1, x2, y2 in gt.get(m, []):
            bw, bh = (x2 - x1) * w, (y2 - y1) * h
            anns.append(
                {
                    "id": len(anns) + 1,
                    "image_id": i,
                    "category_id": 1,
                    "bbox": [x1 * w, y1 * h, bw, bh],
                    "area": bw * bh,
                    "iscrowd": 0,
                }
            )
    return {
        "images": images,
        "annotations": anns,
        "categories": [{"id": 1, "name": "rose"}],
    }


def main() -> None:
    split = json.loads((OUT_DIR / "split.json").read_text())
    gt = load_gt()
    files = md5_to_file()
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    (BUNDLE / "images").mkdir(parents=True)
    cocos = {part: build_coco(split[part], gt) for part in ("train", "test")}
    for part, coco in cocos.items():
        (BUNDLE / f"{part}.json").write_text(json.dumps(coco))
    for m in split["train"] + split["test"]:
        shutil.copy2(files[m], BUNDLE / "images" / files[m].name)  # copia, no mueve

    # Verificaciones: sin fuga de test en train y conteos esperados
    train_md5 = {im["md5"] for im in cocos["train"]["images"]}
    test_md5 = {im["md5"] for im in cocos["test"]["images"]}
    assert not train_md5 & test_md5, "md5 de test presente en train.json"
    for part, n in EXPECTED.items():
        got = len(cocos[part]["annotations"])
        assert got == n, f"{part}: {got} cajas != {n}"
    assert FLOWERS_CSV.exists()

    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(BUNDLE.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(ROOT / "outputs"))
    print(
        "ok",
        {p: (len(c["images"]), len(c["annotations"])) for p, c in cocos.items()},
        "zip MB",
        round(ZIP_PATH.stat().st_size / 1e6, 1),
    )


if __name__ == "__main__":
    main()
