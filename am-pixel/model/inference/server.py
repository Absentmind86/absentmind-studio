"""Standalone local inference server (SPEC §13.2/§14) — localhost only."""

from __future__ import annotations

import sys
from pathlib import Path

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from fastapi import FastAPI  # noqa: E402

from model.inference.api import router  # noqa: E402

app = FastAPI(title="AM Pixel Inference", version="0.1")
app.include_router(router, prefix="/api")


def main() -> None:
    import uvicorn

    # localhost only — never exposed to external network in local mode (SPEC §13.2)
    uvicorn.run(app, host="127.0.0.1", port=8181)


if __name__ == "__main__":
    main()
