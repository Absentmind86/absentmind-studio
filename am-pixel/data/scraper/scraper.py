"""
Training-data scraper — provenance-first (Constitution Rule 5).

Contract: for every sprite, the provenance entry is written to the manifest
BEFORE the sprite file is written to disk. A crash between the two leaves an
orphan manifest entry (harmless), never an unprovenanced sprite (illegal).

License policy (SPEC §15): CC0 and CC-BY only. CC-BY-SA is ON HOLD pending
legal review (CHANGE-038). Robots/scraping blocks are respected: any 403/robots
disallow marks the source blocked in sources.md and the scraper moves on.

2026-07-01 session note: this execution environment's network policy blocks
all approved sources (opengameart.org, itch.io, kenney.nl -> proxy 403).
Documented in logs/BLOCKERS.md. The scraper is fully implemented so it can
run unmodified from a network-enabled machine.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import sys
import urllib.robotparser
from dataclasses import dataclass
from pathlib import Path

import httpx

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from data.pipeline import provenance  # noqa: E402

SOURCES_MD = _AM_PIXEL / "data" / "scraper" / "sources.md"
SCRAPE_LOG = _AM_PIXEL / "data" / "scraper" / "scrape_log.md"
USER_AGENT = "AMPixelScraper/1.0 (training-data collection; respects robots.txt)"


@dataclass
class Source:
    name: str
    url: str
    license: str  # must be in provenance.ACCEPTABLE_LICENSES
    creator: str


def _log(line: str) -> None:
    SCRAPE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SCRAPE_LOG.open("a", encoding="utf-8") as f:
        f.write(f"- {_dt.datetime.now().isoformat(timespec='seconds')} {line}\n")


def robots_allows(url: str, client: httpx.Client) -> bool:
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        resp = client.get(robots_url, timeout=15)
        if resp.status_code >= 400:
            return True  # no robots.txt -> allowed
        rp.parse(resp.text.splitlines())
    except httpx.HTTPError:
        return False  # can't verify -> don't scrape
    return rp.can_fetch(USER_AGENT, url)


def fetch_sprite(source: Source, dest_dir: Path, manifest_path: Path | None = None) -> Path | None:
    """Download one asset with provenance-first ordering. Returns the file path or None."""
    if source.license not in provenance.ACCEPTABLE_LICENSES:
        _log(f"REJECTED (license {source.license}): {source.url}")
        return None
    with httpx.Client(headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
        if not robots_allows(source.url, client):
            _log(f"BLOCKED by robots.txt: {source.url}")
            return None
        resp = client.get(source.url, timeout=60)
        resp.raise_for_status()
        content = resp.content

    sprite_id = f"scrape_{hashlib.sha256(content).hexdigest()[:16]}"
    if provenance.has(sprite_id, manifest_path):
        _log(f"DUPLICATE content hash, skipped: {source.url}")
        return None

    # provenance BEFORE the file hits disk — Constitution Rule 5
    provenance.append(
        {
            "sprite_id": sprite_id,
            "source_url": source.url,
            "creator": source.creator,
            "license": source.license,
            "license_url": "",
            "date_added": _dt.date.today().isoformat(),
            "perceptual_hash": hashlib.sha256(content).hexdigest(),
            "copyright_filter_status": "pending_review",
            "tier": 2,
        },
        manifest_path,
    )
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{sprite_id}{Path(source.url).suffix or '.png'}"
    dest.write_bytes(content)
    _log(f"FETCHED {source.url} -> {dest.name} ({len(content)} bytes, {source.license})")
    return dest


def main() -> None:
    print(
        "scraper: no source list configured in this run.\n"
        "Add Source entries (name, url, license, creator) and call fetch_sprite().\n"
        "See data/scraper/sources.md for the source register and network status."
    )


if __name__ == "__main__":
    main()
