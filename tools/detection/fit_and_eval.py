"""2.3: fija umbral por modelo SOLO con train (max F1) y evalúa en test."""

from __future__ import annotations

import json
import random

from common import OUT_DIR, ROOT, load_gt
from evaluate import best_f1_threshold, by_condition, load_conditions, load_preds

BUNDLE_TRAIN = ROOT / "outputs/colab_bundle/train.json"
RTDETR_SEED = 2026
RTDETR_VAL_FRAC = 0.2


def rtdetr_val_md5s() -> list[str]:
    """Reproduce la validación interna de finetune_rtdetr.py (mismo shuffle y semilla)."""
    imgs = json.loads(BUNDLE_TRAIN.read_text())["images"]
    idx = list(range(len(imgs)))
    random.Random(RTDETR_SEED).shuffle(idx)
    n_val = max(1, round(len(idx) * RTDETR_VAL_FRAC))
    return [imgs[i]["md5"] for i in idx[:n_val]]


def main() -> None:
    gt = load_gt()
    split = json.loads((OUT_DIR / "split.json").read_text())
    conds = load_conditions()
    thr_out: dict[str, dict] = {}
    res: dict[str, dict] = {}
    models = ["owlv2", "gdino"]
    if (OUT_DIR / "preds_rtdetr_test.json").exists():
        models.append("rtdetr")
    for model in models:
        tr = load_preds(OUT_DIR / f"preds_{model}_train.json")
        te = load_preds(OUT_DIR / f"preds_{model}_test.json")
        if model == "rtdetr":
            # Las 36 imágenes de entrenamiento están sobreajustadas: solo la validación interna
            fit_md5s = rtdetr_val_md5s()
            criterion = (
                "max F1 @IoU0.5 sobre la validacion interna (no vista en entrenamiento)"
            )
        else:
            fit_md5s = split["train"]
            criterion = "max F1 @IoU0.5 sobre imagenes de train"
        thr, f1 = best_f1_threshold(gt, tr, fit_md5s)
        thr_out[model] = {
            "threshold": thr,
            "criterion": criterion,
            "train_f1": f1,
            "n_train_images": len(fit_md5s),
        }
        meta = json.loads((OUT_DIR / f"preds_{model}_test.json").read_text())["meta"]
        res[model] = {
            "by_condition_test": by_condition(gt, te, split["test"], conds, thr),
            "train": by_condition(gt, tr, split["train"], {}, thr)["todas"],
            "ms_per_image_mean": meta["ms_per_image_mean"],
            "ms_per_image_median": meta["ms_per_image_median"],
        }
    (OUT_DIR / "thresholds.json").write_text(json.dumps(thr_out, indent=1))
    (OUT_DIR / "results_test.json").write_text(json.dumps(res, indent=1))
    for m, r in res.items():
        print(
            m,
            "thr={:.3f} trainF1={:.2f} ms={:.0f}".format(
                thr_out[m]["threshold"], thr_out[m]["train_f1"], r["ms_per_image_mean"]
            ),
        )
        tr = r["train"]
        print(
            "  train recall {:.2f} fp/img {:.2f} AP {:.2f}".format(
                tr["recall"], tr["fp_per_image"], tr["ap"]
            )
        )
        for c, v in r["by_condition_test"].items():
            print(
                f"  {c:<13} n={v['images']:2d} gt={v['gt']:2d} recall={v['recall']:.2f} "
                f"fp/img={v['fp_per_image']:.2f} AP={v['ap']:.2f}"
            )


if __name__ == "__main__":
    main()
