"""
View-pair human confirmation (CHANGE-017).

Presents detector candidates for confirmation and records confirmed pairs
with a view_pair_id and direction labels to data/pipeline/confirmed_pairs.json.
Synthetic pairs (pure reflections) can be auto-registered with
`--auto-synthetic`; they are labeled synthetic and receive lower training
weight in the dataset loader.

Human confirmation is interactive by design — pairs teach the model view
rotation geometry, and a false pair teaches it wrong geometry.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from data.pipeline.view_pair_detector import PairCandidate, detect_pairs  # noqa: E402
from tools._common import IndexedSprite  # noqa: E402

CONFIRMED_PATH = _AM_PIXEL / "data" / "pipeline" / "confirmed_pairs.json"


def load_confirmed(path: Path | None = None) -> list[dict]:
    p = path or CONFIRMED_PATH
    if not p.is_file():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def save_confirmed(pairs: list[dict], path: Path | None = None) -> None:
    p = path or CONFIRMED_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(pairs, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def register_pair(
    candidate: PairCandidate,
    *,
    direction_a: str,
    direction_b: str,
    synthetic: bool = False,
    path: Path | None = None,
) -> dict:
    pairs = load_confirmed(path)
    entry = {
        "view_pair_id": f"vp_{uuid.uuid4().hex[:12]}",
        "sprite_a": candidate.sprite_a,
        "sprite_b": candidate.sprite_b,
        "direction_a": direction_a,
        "direction_b": direction_b,
        "kind": candidate.kind,
        "silhouette_iou": candidate.silhouette_iou,
        "synthetic": synthetic,
    }
    pairs.append(entry)
    save_confirmed(pairs, path)
    return entry


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Confirm view-pair candidates")
    p.add_argument("corpus_dir", help="directory of indexed .npz sprites")
    p.add_argument("--auto-synthetic", action="store_true",
                   help="register mirror candidates as synthetic pairs without prompting")
    args = p.parse_args()

    sprites = {
        f.stem: IndexedSprite.load_npz(f) for f in sorted(Path(args.corpus_dir).glob("*.npz"))
    }
    candidates = detect_pairs(sprites)
    print(f"{len(candidates)} candidates from {len(sprites)} sprites")
    for c in candidates:
        if args.auto_synthetic and c.kind == "mirror":
            e = register_pair(c, direction_a="left", direction_b="right", synthetic=True)
            print(f"  auto-registered synthetic {e['view_pair_id']}: {c.sprite_a} <-> {c.sprite_b}")
            continue
        ans = input(f"  {c.sprite_a} <-> {c.sprite_b} ({c.kind}, IoU {c.silhouette_iou}) — confirm? [y/N/dirs a,b] ")
        if ans.lower().startswith("y"):
            register_pair(c, direction_a="front", direction_b="side")
        elif "," in ans:
            da, db = (s.strip() for s in ans.split(",", 1))
            register_pair(c, direction_a=da, direction_b=db)


if __name__ == "__main__":
    main()
