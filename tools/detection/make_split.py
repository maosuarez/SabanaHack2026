"""Split por md5 (1.1): test ~20%, estratificado, semilla fija."""

from __future__ import annotations

import json
import random

from common import OUT_DIR, load_gt, load_stages

SEED = 2026
N_TEST = 11  # decisión provisional del usuario (~20% de 56)


def main() -> None:
    gt, st = load_gt(), load_stages()
    md5s = sorted(gt)
    multi = [m for m in md5s if len(set(st[m])) > 1]
    over = [m for m in md5s if "sobreabierto" in st[m]]
    rng = random.Random(SEED)
    # Semilla fija: reintenta hasta cubrir ambas condiciones con una imagen que sea multiclase y otra sobreabierto
    pool = md5s[:]
    for _ in range(1000):
        test = rng.sample(pool, N_TEST)
        if any(m in multi for m in test) and any(m in over for m in test):
            n_over = sum(m in over for m in test)
            n_multi = sum(m in multi for m in test)
            # proporciones cercanas a las globales (aprox 20%)
            if 1 <= n_over <= 3 and 2 <= n_multi <= 4:
                break
    train = [m for m in md5s if m not in test]
    assert not set(train) & set(test)
    out = {
        "seed": SEED,
        "n_test_provisional": N_TEST,
        "train": sorted(train),
        "test": sorted(test),
    }
    (OUT_DIR / "split.json").write_text(json.dumps(out, indent=1))
    for k in ("train", "test"):
        ms = out[k]
        print(
            k,
            len(ms),
            "imagenes",
            sum(len(gt[m]) for m in ms),
            "flores",
            "multiclase",
            sum(m in multi for m in ms),
            "sobreabierto",
            sum(m in over for m in ms),
        )


if __name__ == "__main__":
    main()
