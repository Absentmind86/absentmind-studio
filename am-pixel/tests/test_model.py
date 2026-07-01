"""Model stack: tokenizer phases, forward/loss shapes, tiny overfit, masked sampling."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from data.pipeline.indexer import index_sprite
from model.architecture import config as cfg_mod
from model.architecture.config import OPQ_ID, PHASE_COND, PHASE_MASK, TRANSPARENT_ID
from model.architecture.tokenizer import conditioning_length, tokenize
from model.architecture.transformer import PixelTransformer, load_checkpoint, save_checkpoint
from model.inference.generate import generate_sprite
from model.training.dataset import collate
from model.training.loss import next_token_loss


@pytest.fixture()
def tokenized(good_character):
    return tokenize(index_sprite(good_character))


def test_tokenizer_layout(tokenized, good_character):
    h, w = good_character.shape[:2]
    n_pal = len(tokenized.palette)
    cond = conditioning_length(n_pal)
    assert not tokenized.target_mask[:cond].any()  # conditioning never a target
    assert (tokenized.phases[:cond] == PHASE_COND).all()
    mask_slice = slice(cond, cond + h * w)
    assert (tokenized.phases[mask_slice] == PHASE_MASK).all()
    mask_vals = set(np.unique(tokenized.values[mask_slice]))
    assert mask_vals <= {TRANSPARENT_ID, OPQ_ID}
    n_visible = int((tokenized.values[mask_slice] == OPQ_ID).sum())
    assert len(tokenized.values) == cond + h * w + n_visible


def test_forward_and_loss_shapes(tokenized):
    cfg = cfg_mod.ModelConfig(d_model=32, n_head=2, n_layer=1, d_ff=64)
    model = PixelTransformer(cfg)
    batch = collate([tokenized, tokenized])
    logits = model(batch["values"], batch["xs"], batch["ys"], batch["phases"],
                   batch["channels"], batch["pad_mask"])
    assert logits.shape == (*batch["values"].shape, cfg_mod.VOCAB_SIZE)
    loss = next_token_loss(logits, batch["targets"])
    assert loss.isfinite()


def test_tiny_overfit_and_masked_generation(good_character, tmp_path):
    """One sprite, tiny model, a few hundred steps — loss must fall hard and
    generation must respect the palette mask exactly."""
    torch.manual_seed(0)
    sprite = index_sprite(good_character)
    tok = tokenize(sprite)
    cfg = cfg_mod.ModelConfig(d_model=64, n_head=2, n_layer=2, d_ff=128, dropout=0.0)
    model = PixelTransformer(cfg)
    batch = collate([tok])
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
    first = last = None
    for step in range(220):
        logits = model(batch["values"], batch["xs"], batch["ys"], batch["phases"],
                       batch["channels"], batch["pad_mask"])
        loss = next_token_loss(logits, batch["targets"])
        if first is None:
            first = loss.item()
        last = loss.item()
        opt.zero_grad()
        loss.backward()
        opt.step()
    assert last < first * 0.25, f"overfit failed: {first:.3f} -> {last:.3f}"

    gen = generate_sprite(model, sprite.palette, sprite.width, sprite.height, temperature=0.5, seed=1)
    assert gen.grid.shape == sprite.grid.shape
    assert gen.grid.max() <= len(sprite.palette)  # palette mask held
    assert gen.grid.min() >= 0

    p = tmp_path / "ckpt.pt"
    save_checkpoint(model, p, 220)
    model2, ckpt = load_checkpoint(p)
    assert ckpt["step"] == 220
    assert model2.n_parameters() == model.n_parameters()
