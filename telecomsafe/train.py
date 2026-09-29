"""Train the phase 1 detector.

    python -m telecomsafe.train --exp e2                          # baseline = configs/baseline.yaml
    python -m telecomsafe.train --exp e1                          # same, all built-in augmentation off
    python -m telecomsafe.train --exp e1 --epochs 1 --fraction 0.05   # smoke test
    python -m telecomsafe.train --exp teacher --data data/processed/teacher/dataset.yaml --epochs 50

Runs land in runs/phase1/<name>/ (Ultralytics saves args.yaml there — check it to
confirm E1 really trained with augmentation off). Only the command-line overrides
below are allowed; anything else belongs in configs/baseline.yaml.
"""

from __future__ import annotations

import argparse

from telecomsafe.paths import CONFIGS, PROCESSED, RUNS, load_yaml

# Every built-in train-time augmentation in Ultralytics' detect task.
NO_AUGMENTATION = {
    "mosaic": 0.0, "mixup": 0.0, "cutmix": 0.0, "copy_paste": 0.0,
    "fliplr": 0.0, "flipud": 0.0,
    "hsv_h": 0.0, "hsv_s": 0.0, "hsv_v": 0.0,
    "degrees": 0.0, "translate": 0.0, "scale": 0.0, "shear": 0.0, "perspective": 0.0,
}


def train_args(exp: str, data: str, overrides: dict) -> dict:
    cfg = dict(load_yaml(CONFIGS / "baseline.yaml"))
    if exp == "e1":
        cfg.update(NO_AUGMENTATION)
    cfg.update({k: v for k, v in overrides.items() if v is not None})
    model = cfg.pop("model")
    cfg.update(data=data, project=str(RUNS), name=overrides.get("name") or exp, exist_ok=True)
    return {"model": model, **cfg}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exp", required=True, choices=["e1", "e2", "teacher"])
    ap.add_argument("--data", default=str(PROCESSED / "yolo" / "dataset.yaml"))
    ap.add_argument("--name", help="run name (default: the experiment id)")
    ap.add_argument("--model", help="e.g. yolo11m.pt for the s-vs-m comparison")
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--batch", type=int)
    ap.add_argument("--fraction", type=float, help="train on a fraction of the data (smoke tests)")
    args = ap.parse_args(argv)

    from ultralytics import YOLO
    from ultralytics.cfg import DEFAULT_CFG_DICT

    cfg = train_args(args.exp, args.data, {
        "name": args.name, "model": args.model, "epochs": args.epochs,
        "batch": args.batch, "fraction": args.fraction,
    })
    # Older Ultralytics releases lack some augmentation keys (e.g. cutmix); passing them is an error.
    cfg = {k: v for k, v in cfg.items() if k == "model" or k in DEFAULT_CFG_DICT}
    model = YOLO(cfg.pop("model"))
    model.train(**cfg)


if __name__ == "__main__":  # required on Windows: dataloader workers re-import this module
    main()
