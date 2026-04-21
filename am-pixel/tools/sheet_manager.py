"""
Sprite sheet operations — layout manifests, frame records.

Frame records MAY include `"status": "superseded_by_rollback_v2"` after a DNA rollback (CHANGE-029);
PNG files remain in git history — manifests mark non-authoritative frames.

See am-pixel/SPEC.md §4.3 DNA Rollback Procedure. Phase 0 stub.
"""
# Implementation pending — structure only.


def main() -> None:
    raise NotImplementedError("Sprite sheet operations")


if __name__ == "__main__":
    main()
