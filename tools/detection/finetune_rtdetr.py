"""Afina PekingU/rtdetr_r50vd en train.json (COCO) y predice sobre train y test.

Pensado para Colab (T4). Uso: python finetune_rtdetr.py --bundle colab_bundle --out outputs/rtdetr
Salida de predicciones: mismo formato que preds_*_test.json (por md5, cajas x1y1x2y2 normalizadas).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageEnhance
from transformers import RTDetrForObjectDetection

MODEL_ID = "PekingU/rtdetr_r50vd"
SCORE_FLOOR = 0.001  # piso técnico; el umbral operativo se fija con fit_and_eval.py


def load_coco(path: Path) -> list[dict[str, Any]]:
    """Lista de {md5, file, w, h, boxes} con cajas [x1, y1, x2, y2] en píxeles."""
    coco = json.loads(path.read_text())
    by_img: dict[int, list[list[float]]] = {im["id"]: [] for im in coco["images"]}
    for a in coco["annotations"]:
        x, y, w, h = a["bbox"]
        by_img[a["image_id"]].append([x, y, x + w, y + h])
    return [
        {
            "md5": im["md5"],
            "file": path.parent / "images" / im["file_name"],
            "w": im["width"],
            "h": im["height"],
            "boxes": by_img[im["id"]],
        }
        for im in coco["images"]
    ]


def augment(
    img: Image.Image, boxes: list[list[float]], rng: random.Random
) -> tuple[Image.Image, list[list[float]]]:
    """Rotación ±30°, zoom, brillo/contraste leves y flip horizontal (solo entrenamiento)."""
    w, h = img.size
    ang = math.radians(rng.uniform(-30, 30))
    s = rng.uniform(0.8, 1.3)
    cx, cy = w / 2, h / 2
    c, sn = math.cos(ang) * s, math.sin(ang) * s
    # Matriz directa M (entrada -> salida) alrededor del centro; PIL pide la inversa
    m = np.array(
        [[c, -sn, cx - c * cx + sn * cy], [sn, c, cy - sn * cx - c * cy], [0, 0, 1]]
    )
    inv = np.linalg.inv(m)
    img = img.transform(
        (w, h),
        Image.Transform.AFFINE,
        tuple(inv[:2].flatten().tolist()),
        resample=Image.Resampling.BILINEAR,
        fillcolor=(114, 114, 114),
    )
    out: list[list[float]] = []
    for x1, y1, x2, y2 in boxes:
        pts = np.array([[x1, y1, 1], [x2, y1, 1], [x2, y2, 1], [x1, y2, 1]]) @ m.T
        nx1, ny1 = pts[:, 0].min(), pts[:, 1].min()
        nx2, ny2 = pts[:, 0].max(), pts[:, 1].max()
        area0 = (nx2 - nx1) * (ny2 - ny1)
        cx1, cy1, cx2, cy2 = max(nx1, 0), max(ny1, 0), min(nx2, w), min(ny2, h)
        area1 = max(cx2 - cx1, 0) * max(cy2 - cy1, 0)
        if area0 > 0 and area1 / area0 >= 0.5 and cx2 - cx1 > 4 and cy2 - cy1 > 4:
            out.append([cx1, cy1, cx2, cy2])
    img = ImageEnhance.Brightness(img).enhance(rng.uniform(0.8, 1.2))
    img = ImageEnhance.Contrast(img).enhance(rng.uniform(0.8, 1.2))
    if rng.random() < 0.5:
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        out = [[w - x2, y1, w - x1, y2] for x1, y1, x2, y2 in out]
    return img, out


def to_tensor(img: Image.Image, size: int) -> torch.Tensor:
    """Resize cuadrado (cajas normalizadas no cambian) y escala a [0,1]; RT-DETR no usa mean/std."""
    arr = np.asarray(
        img.resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32
    )
    return torch.from_numpy(arr / 255.0).permute(2, 0, 1)


def make_batch(
    items: list[dict[str, Any]],
    size: int,
    train: bool,
    rng: random.Random,
    device: torch.device,
) -> tuple[torch.Tensor, list[dict[str, torch.Tensor]]]:
    xs: list[torch.Tensor] = []
    labels: list[dict[str, torch.Tensor]] = []
    for it in items:
        img = Image.open(it["file"]).convert("RGB")
        boxes = it["boxes"]
        if train:
            img, boxes = augment(img, boxes, rng)
        w, h = img.size
        cxcywh = [
            [(x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h]
            for x1, y1, x2, y2 in boxes
        ]
        xs.append(to_tensor(img, size))
        labels.append(
            {
                "class_labels": torch.zeros(
                    len(cxcywh), dtype=torch.long, device=device
                ),
                "boxes": torch.tensor(
                    cxcywh, dtype=torch.float32, device=device
                ).reshape(-1, 4),
            }
        )
    return torch.stack(xs).to(device), labels


@torch.no_grad()
def predict(
    model: RTDetrForObjectDetection,
    items: list[dict[str, Any]],
    size: int,
    device: torch.device,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, float]]:
    """Scores crudos (sigmoide) por query; cajas x1y1x2y2 normalizadas respecto a la imagen original."""
    model.eval()
    preds: dict[str, list[dict[str, Any]]] = {}
    times: dict[str, float] = {}
    for it in items:
        img = Image.open(it["file"]).convert("RGB")
        x = to_tensor(img, size)[None].to(device)
        t0 = time.perf_counter()
        out = model(pixel_values=x)
        if device.type == "cuda":
            torch.cuda.synchronize()
        times[it["md5"]] = (time.perf_counter() - t0) * 1000
        scores = out.logits[0].sigmoid().max(-1).values.cpu()
        bx = out.pred_boxes[0].cpu()
        keep = scores >= SCORE_FLOOR
        preds[it["md5"]] = [
            {
                "box": [
                    max(0.0, cx - bw / 2),
                    max(0.0, cy - bh / 2),
                    min(1.0, cx + bw / 2),
                    min(1.0, cy + bh / 2),
                ],
                "score": float(s),
            }
            for (cx, cy, bw, bh), s in zip(bx[keep].tolist(), scores[keep].tolist())
        ]
    return preds, times


def save_preds(
    path: Path,
    preds: dict,
    times: dict[str, float],
    device: torch.device,
    args: argparse.Namespace,
) -> None:
    ms = sorted(times.values())
    meta = {
        "model": MODEL_ID,
        "finetuned": True,
        "score_floor": SCORE_FLOOR,
        "device": device.type,
        "img_size": args.img_size,
        "epochs": args.epochs,
        "seed": args.seed,
        "ms_per_image_mean": sum(ms) / len(ms),
        "ms_per_image_median": ms[len(ms) // 2],
        "ms_first_image_cold": next(iter(times.values())),
    }
    path.write_text(json.dumps({"meta": meta, "times_ms": times, "predictions": preds}))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=Path("colab_bundle"))
    ap.add_argument("--out", type=Path, default=Path("outputs/rtdetr"))
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument(
        "--lr", type=float, default=1e-4, help="lr de cabeza; backbone usa lr/10"
    )
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--img-size", type=int, default=640)
    ap.add_argument(
        "--val-frac", type=float, default=0.2, help="fracción de train para validar"
    )
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--smoke", action="store_true", help="1 paso en CPU con 2 imágenes")
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    device = torch.device(
        "cpu" if args.smoke or not torch.cuda.is_available() else "cuda"
    )
    args.out.mkdir(parents=True, exist_ok=True)

    train_all = load_coco(args.bundle / "train.json")
    test = load_coco(args.bundle / "test.json")
    # Validación interna salida del train (nunca del test)
    idx = list(range(len(train_all)))
    random.Random(args.seed).shuffle(idx)
    n_val = max(1, round(len(idx) * args.val_frac))
    val = [train_all[i] for i in idx[:n_val]]
    train = [train_all[i] for i in idx[n_val:]]
    if args.smoke:
        args.epochs, args.img_size, args.batch = 1, 320, 2
        train, val, test = train[:2], train[:1], test[:2]
        train_all = train
    print(
        f"device={device} train={len(train)} val={len(val)} test={len(test)}",
        flush=True,
    )

    model = RTDetrForObjectDetection.from_pretrained(
        MODEL_ID,
        num_labels=1,
        id2label={0: "rose"},
        label2id={"rose": 0},
        ignore_mismatched_sizes=True,
    ).to(device)
    backbone = [p for n, p in model.named_parameters() if "backbone" in n]
    rest = [p for n, p in model.named_parameters() if "backbone" not in n]
    opt = torch.optim.AdamW(
        [{"params": backbone, "lr": args.lr / 10}, {"params": rest, "lr": args.lr}],
        weight_decay=1e-4,
    )
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, args.epochs))
    use_amp = device.type == "cuda"
    scaler = torch.amp.GradScaler(enabled=use_amp)

    history: list[dict[str, float]] = []
    best = float("inf")
    ckpt = args.out / "checkpoint"
    for ep in range(1, args.epochs + 1):
        model.train()
        order = train[:]
        rng.shuffle(order)
        tl, nb = 0.0, 0
        for i in range(0, len(order), args.batch):
            x, lab = make_batch(
                order[i : i + args.batch], args.img_size, True, rng, device
            )
            with torch.autocast(device.type, dtype=torch.float16, enabled=use_amp):
                loss = model(pixel_values=x, labels=lab).loss
            opt.zero_grad()
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 0.1)
            scaler.step(opt)
            scaler.update()
            tl += float(loss.detach())
            nb += 1
            if args.smoke:
                break
        sched.step()
        # Pérdida de validación (sin aumentación)
        model.eval()
        vl, vn = 0.0, 0
        with torch.no_grad():
            for i in range(0, len(val), args.batch):
                x, lab = make_batch(
                    val[i : i + args.batch], args.img_size, False, rng, device
                )
                with torch.autocast(device.type, dtype=torch.float16, enabled=use_amp):
                    vl += float(model(pixel_values=x, labels=lab).loss)
                vn += 1
        rec = {"epoch": ep, "train_loss": tl / nb, "val_loss": vl / vn}
        history.append(rec)
        print(rec, flush=True)
        if rec["val_loss"] < best:
            best = rec["val_loss"]
            model.save_pretrained(ckpt)
        (args.out / "loss.json").write_text(json.dumps(history, indent=1))

    # Mejor checkpoint por pérdida de validación interna
    model = RTDetrForObjectDetection.from_pretrained(ckpt).to(device)
    for name, items in (("test", test), ("train", train_all)):
        preds, times = predict(model, items, args.img_size, device)
        save_preds(args.out / f"preds_rtdetr_{name}.json", preds, times, device, args)
        print(
            name,
            "imgs",
            len(preds),
            "ms_mean",
            sum(times.values()) / len(times),
            flush=True,
        )
    print("best_val_loss", best)


if __name__ == "__main__":
    main()
