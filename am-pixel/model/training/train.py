"""
Main training loop.

GATES (Constitution Rules 5/6, CHANGE-028):
- Production runs call compliance.training_run_gate(): IMPLEMENTATION_NOTES.md
  present, PHASE4_ARCHITECTURE_REVIEW: APPROVED in phase_gates.md, non-empty
  provenance manifest. Refuses tier 0 data.
- Validation runs (--validation-run, CHANGE-037) are pipeline smoke tests:
  they REQUIRE that every sprite in the corpus dir is tier 0 in the manifest,
  and that IMPLEMENTATION_NOTES.md exists. They never touch production
  checkpoints (saved under model/checkpoints/validation/).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from data.pipeline import provenance  # noqa: E402
from model.architecture import config as cfg_mod  # noqa: E402
from model.architecture.transformer import PixelTransformer, save_checkpoint  # noqa: E402
from model.hardware.detector import get_device  # noqa: E402
from model.training.dataset import SpriteDataset, collate  # noqa: E402
from model.training.loss import next_token_loss, token_accuracy  # noqa: E402
from model.training.scheduler import warmup_cosine  # noqa: E402

TRAINING_LOG = _AM_PIXEL / "logs" / "training_log.md"


def _log(line: str) -> None:
    TRAINING_LOG.parent.mkdir(parents=True, exist_ok=True)
    with TRAINING_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def check_gates(corpus_dir: Path, validation_run: bool) -> None:
    impl = _AM_PIXEL / "model" / "architecture" / "IMPLEMENTATION_NOTES.md"
    if not impl.is_file():
        raise SystemExit("GATE: IMPLEMENTATION_NOTES.md missing (CHANGE-020) — refusing to train")
    manifest = {e["sprite_id"]: e for e in provenance.load()}
    sprite_ids = [f.stem for f in corpus_dir.glob("*.npz")]
    if not sprite_ids:
        raise SystemExit(f"GATE: no sprites in {corpus_dir}")
    missing = [s for s in sprite_ids if s not in manifest]
    if missing:
        raise SystemExit(
            f"GATE: {len(missing)} corpus sprites lack provenance entries (Constitution Rule 5): {missing[:5]}"
        )
    tiers = {manifest[s]["tier"] for s in sprite_ids}
    if validation_run:
        if tiers != {0}:
            raise SystemExit(f"GATE: --validation-run requires ALL tier-0 data, found tiers {tiers} (CHANGE-037)")
    else:
        if 0 in tiers:
            raise SystemExit("GATE: tier-0 synthetic data in a production run (CHANGE-037) — refusing")
        from tools import compliance

        if not compliance.training_run_gate():
            raise SystemExit(
                "GATE: training_run_gate failed — needs PHASE4_ARCHITECTURE_REVIEW: APPROVED "
                "in logs/phase_gates.md and a non-empty manifest (CHANGE-028)"
            )


def train(args: argparse.Namespace) -> Path:
    corpus_dir = Path(args.corpus)
    check_gates(corpus_dir, args.validation_run)

    device = get_device()
    cfg = cfg_mod.small() if args.size == "small" else cfg_mod.base()
    model = PixelTransformer(cfg).to(device)

    train_ds = SpriteDataset(corpus_dir, "train")
    val_ds = SpriteDataset(corpus_dir, "validation")
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    val_dl = DataLoader(val_ds, batch_size=args.batch_size, collate_fn=collate)

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = warmup_cosine(opt, warmup_steps=min(100, args.steps // 10), total_steps=args.steps)

    run_kind = "VALIDATION RUN (tier 0)" if args.validation_run else "PRODUCTION RUN"
    ckpt_dir = _AM_PIXEL / "model" / "checkpoints" / ("validation" if args.validation_run else "production")
    _log(
        f"\n## Training run {_dt.datetime.now().isoformat(timespec='seconds')} — {run_kind}\n"
        f"- corpus: {corpus_dir} ({len(train_ds)} train / {len(val_ds)} val)\n"
        f"- model: {args.size} ({model.n_parameters():,} params), device {device}\n"
        f"- steps {args.steps}, batch {args.batch_size}, lr {args.lr}"
    )

    step, t0, best_val = 0, time.time(), float("inf")
    ckpt_path = ckpt_dir / "latest.pt"
    model.train()
    while step < args.steps:
        for batch in train_dl:
            batch = {k: v.to(device) for k, v in batch.items()}
            logits = model(batch["values"], batch["xs"], batch["ys"], batch["phases"],
                           batch["channels"], batch["pad_mask"])
            loss = next_token_loss(logits, batch["targets"], label_smoothing=0.05)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            step += 1
            if step % args.log_every == 0 or step == args.steps:
                val_loss, val_acc = evaluate(model, val_dl, device)
                _log(f"- step {step}: train_loss {loss.item():.4f} | val_loss {val_loss:.4f} "
                     f"| val_token_acc {val_acc:.1%} | {time.time() - t0:.0f}s")
                print(f"step {step}/{args.steps} train {loss.item():.4f} val {val_loss:.4f} acc {val_acc:.1%}")
                if val_loss < best_val:
                    best_val = val_loss
                    save_checkpoint(model, ckpt_path, step, {"val_loss": val_loss, "validation_run": args.validation_run})
                model.train()
            if step >= args.steps:
                break
    _log(f"- finished: best val_loss {best_val:.4f}; checkpoint {ckpt_path}")
    return ckpt_path


@torch.no_grad()
def evaluate(model: PixelTransformer, dl: DataLoader, device) -> tuple[float, float]:
    model.eval()
    losses, accs = [], []
    for batch in dl:
        batch = {k: v.to(device) for k, v in batch.items()}
        logits = model(batch["values"], batch["xs"], batch["ys"], batch["phases"],
                       batch["channels"], batch["pad_mask"])
        losses.append(next_token_loss(logits, batch["targets"]).item())
        accs.append(token_accuracy(logits, batch["targets"]))
    return float(sum(losses) / len(losses)), float(sum(accs) / len(accs))


def main() -> None:
    p = argparse.ArgumentParser(description="AM Pixel training")
    p.add_argument("--corpus", required=True, help="directory of indexed .npz sprites")
    p.add_argument("--steps", type=int, default=600)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--size", choices=["small", "base"], default="small")
    p.add_argument("--log-every", type=int, default=50)
    p.add_argument("--validation-run", action="store_true",
                   help="tier-0 pipeline smoke test (CHANGE-037) — never production")
    args = p.parse_args()
    ckpt = train(args)
    print(f"checkpoint: {ckpt}")


if __name__ == "__main__":
    main()
