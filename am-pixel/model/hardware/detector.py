"""
Universal hardware/backend detection (Constitution Rule 3, CHANGE-003/036).

ALL device references in the codebase route through get_device(). There are
zero hardcoded "cuda" strings anywhere else. Detection hierarchy:
CUDA (NVIDIA, and AMD via ROCm builds) -> MPS (Apple Silicon) ->
XPU (Intel, torch.xpu) -> CPU. Never halts on missing accelerators.
"""

from __future__ import annotations

import datetime as _dt
import time
from dataclasses import dataclass
from pathlib import Path

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
HARDWARE_LOG = _AM_PIXEL / "logs" / "hardware.log"


@dataclass
class HardwareInfo:
    backend: str  # "cuda" | "rocm" | "mps" | "xpu" | "cpu"
    device: str  # torch device string
    name: str
    vram_gb: float | None
    tokens_per_sec: float | None = None


def detect() -> HardwareInfo:
    import torch

    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        # ROCm builds surface AMD GPUs through the torch.cuda API
        backend = "rocm" if getattr(torch.version, "hip", None) else "cuda"
        return HardwareInfo(backend, "cuda:0", name, round(vram, 1))
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return HardwareInfo("mps", "mps", "Apple Silicon (MPS)", None)
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return HardwareInfo("xpu", "xpu", torch.xpu.get_device_name(0), None)
    import platform

    return HardwareInfo("cpu", "cpu", platform.processor() or platform.machine(), None)


def get_device() -> "torch.device":  # noqa: F821
    import torch

    return torch.device(detect().device)


def baseline_tokens_per_sec(seq_len: int = 256, iters: int = 8) -> float:
    """Rough autoregressive throughput estimate on a tiny model — the Phase 0
    'baseline inference speed on a 16x16 test sprite' number for hardware.log."""
    import torch
    import torch.nn as nn

    device = get_device()
    d, layer = 128, nn.TransformerEncoderLayer(128, 4, 256, batch_first=True)
    model = nn.Sequential().to(device)
    enc = nn.TransformerEncoder(layer, 2).to(device).eval()
    emb = nn.Embedding(300, d).to(device)
    mask = torch.triu(torch.ones(seq_len, seq_len, device=device, dtype=torch.bool), 1)
    tok = torch.randint(0, 300, (1, seq_len), device=device)
    with torch.no_grad():
        enc(emb(tok), mask=mask)  # warmup
        t0 = time.perf_counter()
        for _ in range(iters):
            enc(emb(tok), mask=mask)
        dt = time.perf_counter() - t0
    del model
    # AR generation runs one full forward per generated token (no KV cache in
    # this probe), so tokens/sec ~= forwards/sec
    return round(iters / dt, 2) if dt else 0.0


def log_detection(info: HardwareInfo, log_path: Path | None = None) -> None:
    path = log_path or HARDWARE_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(
            f"{_dt.datetime.now().isoformat(timespec='seconds')} "
            f"backend={info.backend} device={info.device} name={info.name!r} "
            f"vram_gb={info.vram_gb} baseline_tok_per_sec={info.tokens_per_sec}\n"
        )


def main() -> None:
    info = detect()
    info.tokens_per_sec = baseline_tokens_per_sec()
    log_detection(info)
    print(f"backend: {info.backend}\ndevice:  {info.device}\nname:    {info.name}")
    print(f"vram:    {info.vram_gb} GB\nbaseline: ~{info.tokens_per_sec} tok/s (tiny model)")
    if info.tokens_per_sec and info.tokens_per_sec < 20:
        print("NOTE: baseline under 20 tok/s — plan cloud GPU before Phase 4 (ROADMAP).")


if __name__ == "__main__":
    main()
