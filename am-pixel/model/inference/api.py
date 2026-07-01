"""Inference API endpoints (mounted by ui/app.py and model/inference/server.py)."""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

router = APIRouter()

_MODEL_CACHE: dict = {}
DEFAULT_CHECKPOINT = _AM_PIXEL / "model" / "checkpoints" / "validation" / "latest.pt"


class GenerateRequest(BaseModel):
    width: int = Field(16, ge=8, le=64)
    height: int = Field(24, ge=8, le=64)
    palette: list[str] | None = None  # hex colors; None -> default sample palette
    temperature: float = Field(0.9, gt=0, le=2.0)
    seed: int | None = None
    checkpoint: str | None = None


class GenerateResponse(BaseModel):
    png_base64: str
    png_base64_4x: str
    width: int
    height: int
    palette: list[str]
    automated_score: int
    gate_passed: bool
    score_breakdown: dict


def _load_model(checkpoint: str | None):
    from model.architecture.transformer import load_checkpoint
    from model.hardware.detector import get_device

    path = Path(checkpoint) if checkpoint else DEFAULT_CHECKPOINT
    if not path.is_file():
        raise HTTPException(503, f"no checkpoint at {path} — train a model first (model/training/train.py)")
    key = str(path)
    if key not in _MODEL_CACHE:
        device = get_device()
        model, _ = load_checkpoint(path, device)
        _MODEL_CACHE[key] = (model, device)
    return _MODEL_CACHE[key]


def _png_b64(rgba, scale: int = 1) -> str:
    import numpy as np
    from PIL import Image

    arr = np.kron(rgba, np.ones((scale, scale, 1), dtype=rgba.dtype)) if scale > 1 else rgba
    buf = io.BytesIO()
    Image.fromarray(arr, "RGBA").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    from tools import compliance

    if compliance.is_halted():
        raise HTTPException(423, "EMERGENCY_HALT is set — all generation gated (human removes the file)")

    from model.inference.generate import generate_sprite
    from tools.rubric_scorer import score_rubric_a

    model, device = _load_model(req.checkpoint)
    if req.palette:
        palette = [tuple(int(h.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)) for h in req.palette]
    else:
        palette = [(48, 32, 32), (136, 88, 64), (200, 136, 88), (32, 48, 88), (72, 96, 152), (136, 160, 208)]
    if len(palette) > 15:
        raise HTTPException(422, "max 15 colors + transparent (SNES)")

    sprite = generate_sprite(
        model, palette, req.width, req.height,
        temperature=req.temperature, seed=req.seed, device=device,
    )
    rgba = sprite.to_rgba()
    score = score_rubric_a(rgba)
    return GenerateResponse(
        png_base64=_png_b64(rgba),
        png_base64_4x=_png_b64(rgba, 4),
        width=req.width,
        height=req.height,
        palette=["#{:02X}{:02X}{:02X}".format(*c) for c in palette],
        automated_score=score["automated_score"],
        gate_passed=bool(score["passed_gate"]),
        score_breakdown={k: f"{v['score']}/{v['max']}" for k, v in score["categories"].items()},
    )


@router.get("/health")
def health() -> dict:
    from tools import compliance

    return {
        "status": "halted" if compliance.is_halted() else "ok",
        "checkpoint_available": DEFAULT_CHECKPOINT.is_file(),
    }


@router.get("/hardware")
def hardware() -> dict:
    from model.hardware.detector import detect

    info = detect()
    return {"backend": info.backend, "device": info.device, "name": info.name, "vram_gb": info.vram_gb}
