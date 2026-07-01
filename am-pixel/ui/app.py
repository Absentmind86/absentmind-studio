"""
AM Pixel local web UI (SPEC §13) — FastAPI serving the inference API and the
single-page interface. Localhost only in local mode; the EMERGENCY_HALT file
gates generation (checked per request via compliance.is_halted, never
SystemExit in server context).
"""

from __future__ import annotations

import datetime as _dt
import json
import shutil
import sys
from pathlib import Path

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from model.inference.api import router as inference_router  # noqa: E402

UI_DIR = Path(__file__).resolve().parent
app = FastAPI(title="AM Pixel", version="0.1")
app.include_router(inference_router, prefix="/api")
app.mount("/static", StaticFiles(directory=UI_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    return FileResponse(UI_DIR / "templates" / "index.html")


@app.get("/fragment/{name}", response_class=HTMLResponse)
def fragment(name: str) -> FileResponse:
    safe = {"project_tabs": "project_tabs.html", "freeform": "freeform.html"}
    if name not in safe:
        raise HTTPException(404)
    return FileResponse(UI_DIR / "templates" / safe[name])


@app.get("/api/status")
def status() -> dict:
    from model.hardware.detector import detect
    from tools import compliance

    info = detect()
    ckpt = _AM_PIXEL / "model" / "checkpoints" / "validation" / "latest.pt"
    disk = shutil.disk_usage(str(_AM_PIXEL))
    return {
        "halted": compliance.is_halted(),
        "backend": info.backend,
        "device_name": info.name,
        "vram_gb": info.vram_gb,
        "disk_free_gb": round(disk.free / 1e9, 1),
        "checkpoint": str(ckpt) if ckpt.is_file() else None,
        "phase": _current_phase(),
    }


def _current_phase() -> str:
    """First phase section whose 'Date completed:' line is still blank."""
    pg = _AM_PIXEL / "logs" / "phase_gates.md"
    if not pg.is_file():
        return "Phase 0"
    name, completed = None, True
    for line in pg.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Phase"):
            if name is not None and not completed:
                return name
            name = line.lstrip("# ").split("—")[0].strip()
            completed = False
        elif line.strip().startswith("Date completed:") and line.split(":", 1)[1].strip():
            completed = True
    return name if (name and not completed) else "Phase 0"


@app.get("/api/continuity")
def continuity() -> dict:
    manifest = _AM_PIXEL / "dna" / "CONTINUITY_MANIFEST.md"
    return {"markdown": manifest.read_text(encoding="utf-8") if manifest.is_file() else ""}


class DecisionRequest(BaseModel):
    action: str  # approve | reject | adjust
    mode: str = "freeform"  # freeform | project
    png_base64: str
    width: int
    height: int
    note: str = ""
    name: str = "untitled"


@app.post("/api/decision")
def decision(req: DecisionRequest) -> dict:
    """Approve/reject/adjust from the UI. Freeform approvals land in freeform/
    only and are logged to logs/freeform_log.md (SPEC §5.7) — never project state."""
    import base64

    ts = _dt.datetime.now().isoformat(timespec="seconds")
    if req.action == "approve" and req.mode == "freeform":
        out_dir = _AM_PIXEL / "freeform"
        out_dir.mkdir(exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in req.name) or "untitled"
        path = out_dir / f"{safe}_{ts.replace(':', '')}.png"
        path.write_bytes(base64.b64decode(req.png_base64))
        log = _AM_PIXEL / "logs" / "freeform_log.md"
        with log.open("a", encoding="utf-8") as f:
            f.write(f"- {ts} approved {path.name} ({req.width}x{req.height}) — {req.note or 'no note'}\n")
        return {"saved": str(path)}
    if req.action in ("reject", "adjust"):
        log = _AM_PIXEL / "logs" / "generation_log.md"
        with log.open("a", encoding="utf-8") as f:
            f.write(f"- {ts} {req.action} ({req.mode}, {req.width}x{req.height}) — {req.note or 'no note'}\n")
        return {"logged": True}
    raise HTTPException(422, f"unsupported action/mode: {req.action}/{req.mode} (project approvals arrive with Mode 1 pipeline)")


def main() -> None:
    import uvicorn

    # localhost only — never exposed to external network in local mode (SPEC §13.2)
    uvicorn.run(app, host="127.0.0.1", port=8177)


if __name__ == "__main__":
    main()
