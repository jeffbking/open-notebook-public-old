"""Token-gated public podcast feed: settings, token check and RSS generation.

Everything under ``/public/podcasts/{token}/`` is meant to be reachable from the
public internet (through a path-scoped tunnel) so podcast apps can subscribe.
The token is the only gate, so every public route answers a missing, short or
wrong token -- and a disabled feed -- with the same 404 as an unknown path.

Configuration (environment):
- ``OPEN_NOTEBOOK_PODCAST_FEED_TOKEN`` (or ``..._FILE``): enables the feed.
  At least 32 URL-safe characters, e.g. ``python -c "import secrets;
  print(secrets.token_urlsafe(32))"``.
- ``OPEN_NOTEBOOK_PODCAST_FEED_ORIGIN``: public origin that serves
  ``/public/podcasts/`` (e.g. ``https://podcasts.example.com``).
- ``OPEN_NOTEBOOK_PODCAST_FEED_TITLE`` / ``..._DESCRIPTION``: channel text.
"""

import asyncio
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from feedgen.feed import FeedGenerator
from loguru import logger

from open_notebook.exceptions import NotFoundError
from open_notebook.podcasts.audio_paths import resolve_contained_audio_path
from open_notebook.podcasts.models import PodcastEpisode
from open_notebook.utils.encryption import get_secret_from_env

MIN_TOKEN_LENGTH = 32
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_EPISODE_KEY_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")
COVER_PATH = (
    Path(__file__).resolve().parents[1]
    / "open_notebook"
    / "podcasts"
    / "assets"
    / "feed-cover.png"
)


@dataclass(frozen=True)
class FeedSettings:
    token: str
    origin: str
    title: str
    description: str

    @property
    def base_url(self) -> str:
        return f"{self.origin}/public/podcasts/{self.token}"


def load_feed_settings() -> Optional[FeedSettings]:
    """Read feed settings from the environment; None when the feed is off."""
    token = (get_secret_from_env("OPEN_NOTEBOOK_PODCAST_FEED_TOKEN") or "").strip()
    origin = os.environ.get("OPEN_NOTEBOOK_PODCAST_FEED_ORIGIN", "").strip().rstrip("/")
    if not token or not origin:
        return None
    if len(token) < MIN_TOKEN_LENGTH or not _TOKEN_RE.fullmatch(token):
        logger.warning(
            "Podcast feed disabled: OPEN_NOTEBOOK_PODCAST_FEED_TOKEN must be at "
            f"least {MIN_TOKEN_LENGTH} URL-safe characters"
        )
        return None
    if not origin.startswith(("https://", "http://")):
        logger.warning("Podcast feed disabled: OPEN_NOTEBOOK_PODCAST_FEED_ORIGIN is not a URL")
        return None
    return FeedSettings(
        token=token,
        origin=origin,
        title=os.environ.get("OPEN_NOTEBOOK_PODCAST_FEED_TITLE", "").strip() or "Open Notebook",
        description=os.environ.get("OPEN_NOTEBOOK_PODCAST_FEED_DESCRIPTION", "").strip()
        or "Podcasts generated from your Open Notebook research.",
    )


def require_feed_token(token: str) -> FeedSettings:
    """Settings for a matching token; the same NotFoundError for anything else."""
    settings = load_feed_settings()
    if settings is None or not hmac.compare_digest(
        token.encode("utf-8"), settings.token.encode("utf-8")
    ):
        raise NotFoundError("Not Found")
    return settings


def _episode_key(episode: PodcastEpisode) -> str:
    return str(episode.id).split(":", 1)[-1]


def _episode_description(episode: PodcastEpisode) -> str:
    segments = (episode.outline or {}).get("segments") or []
    lines = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        name = str(segment.get("name") or "").strip()
        detail = str(segment.get("description") or "").strip()
        if name and detail:
            lines.append(f"{name}: {detail}")
        elif name or detail:
            lines.append(name or detail)
    return "\n\n".join(lines) or episode.name


def _published_at(episode: PodcastEpisode) -> datetime:
    created = episode.created
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created)
        except ValueError:
            created = None
    if not isinstance(created, datetime):
        return datetime.now(timezone.utc)
    return created if created.tzinfo else created.replace(tzinfo=timezone.utc)


# (path, mtime_ns) -> seconds; ffprobe once per file version.
_duration_cache: dict[tuple[str, int], Optional[int]] = {}


async def _audio_duration_seconds(path: Path) -> Optional[int]:
    key = (str(path), path.stat().st_mtime_ns)
    if key in _duration_cache:
        return _duration_cache[key]
    seconds: Optional[int] = None
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        seconds = round(float(stdout.decode().strip()))
    except Exception as e:  # missing ffprobe, timeout, unparsable output
        logger.debug(f"Could not read duration of {path.name}: {e}")
    _duration_cache[key] = seconds
    return seconds


def feed_url(settings: FeedSettings) -> str:
    return f"{settings.base_url}/feed.xml"


async def build_feed_xml(settings: FeedSettings) -> bytes:
    """RSS 2.0 + iTunes feed of every episode whose audio exists on disk."""
    episodes = await PodcastEpisode.get_all(order_by="created desc")
    cover_url = f"{settings.base_url}/cover.png"
    url = feed_url(settings)

    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title(settings.title)
    fg.description(settings.description)
    fg.link(href=url, rel="alternate")
    fg.link(href=url, rel="self")
    fg.language("en")
    fg.image(url=cover_url, title=settings.title, link=url)
    fg.podcast.itunes_image(cover_url)
    fg.podcast.itunes_author(settings.title)
    fg.podcast.itunes_summary(settings.description)
    fg.podcast.itunes_category("Technology")
    fg.podcast.itunes_explicit("no")
    fg.podcast.itunes_block(True)  # private feed: keep it out of directories

    for episode in episodes:
        audio_path = resolve_contained_audio_path(episode.audio_file)
        if audio_path is None or not audio_path.is_file():
            continue  # still generating, failed, or missing on disk
        entry = fg.add_entry(order="append")
        entry.guid(f"open-notebook:{episode.id}", permalink=False)
        entry.title(episode.name)
        entry.description(_episode_description(episode))
        entry.published(_published_at(episode))
        entry.enclosure(
            f"{settings.base_url}/audio/{_episode_key(episode)}.mp3",
            str(audio_path.stat().st_size),
            "audio/mpeg",
        )
        duration = await _audio_duration_seconds(audio_path)
        if duration:
            entry.podcast.itunes_duration(duration)

    return fg.rss_str(pretty=True)


async def episode_audio_path(episode_key: str) -> Path:
    """Audio file for a feed episode key, or NotFoundError."""
    if not _EPISODE_KEY_RE.fullmatch(episode_key):
        raise NotFoundError("Not Found")
    try:
        episode = await PodcastEpisode.get(f"episode:{episode_key}")
    except Exception as e:
        raise NotFoundError("Not Found") from e
    audio_path = resolve_contained_audio_path(episode.audio_file if episode else None)
    if audio_path is None or not audio_path.is_file():
        raise NotFoundError("Not Found")
    return audio_path


def cover_path() -> Path:
    if not COVER_PATH.is_file():
        raise NotFoundError("Not Found")
    return COVER_PATH
