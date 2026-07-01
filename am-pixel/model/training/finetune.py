"""Stage 2 fine-tuning: resume from a checkpoint at lower LR on the curated
set (Golden Dataset / approved production assets). Same gates as train.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from model.training import train as train_mod  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="AM Pixel fine-tuning (Stage 2)")
    p.add_argument("--corpus", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--steps", type=int, default=300)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--lr", type=float, default=5e-5)  # lower than initial training
    p.add_argument("--log-every", type=int, default=50)
    p.add_argument("--validation-run", action="store_true")
    args = p.parse_args()

    import torch

    from model.architecture.transformer import load_checkpoint, save_checkpoint
    from model.hardware.detector import get_device
    from model.training.dataset import SpriteDataset, collate
    from model.training.loss import next_token_loss
    from torch.utils.data import DataLoader

    corpus_dir = Path(args.corpus)
    train_mod.check_gates(corpus_dir, args.validation_run)
    device = get_device()
    model, ckpt = load_checkpoint(args.checkpoint, device)
    model.train()

    dl = DataLoader(SpriteDataset(corpus_dir, "train"), batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    val_dl = DataLoader(SpriteDataset(corpus_dir, "validation"), batch_size=args.batch_size, collate_fn=collate)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    step, best = 0, float("inf")
    out = Path(args.checkpoint).with_name("finetuned.pt")
    while step < args.steps:
        for batch in dl:
            batch = {k: v.to(device) for k, v in batch.items()}
            logits = model(batch["values"], batch["xs"], batch["ys"], batch["phases"],
                           batch["channels"], batch["pad_mask"])
            loss = next_token_loss(logits, batch["targets"])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            step += 1
            if step % args.log_every == 0 or step >= args.steps:
                vl, _ = train_mod.evaluate(model, val_dl, device)
                print(f"finetune step {step}: train {loss.item():.4f} val {vl:.4f}")
                if vl < best:
                    best = vl
                    save_checkpoint(model, out, step, {"val_loss": vl, "finetuned_from": args.checkpoint})
                model.train()
            if step >= args.steps:
                break
    print(f"finetuned checkpoint: {out}")


if __name__ == "__main__":
    main()
