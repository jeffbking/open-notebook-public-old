"""Token-gated public podcast feed routes (see api/podcast_feed_service.py).

Public routes live under ``/public/podcasts/{token}/`` and are meant to be
exposed through a path-scoped tunnel; every miss is the same 404.
"""

from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from api.podcast_feed_service import (
    build_feed_xml,
    cover_path,
    episode_audio_path,
    feed_url,
    load_feed_settings,
    require_feed_token,
)

router = APIRouter()
public_router = APIRouter(prefix="/public/podcasts")


class PodcastFeedInfo(BaseModel):
    enabled: bool
    feed_url: Optional[str] = None


@router.get("/podcasts/feed-info", response_model=PodcastFeedInfo)
async def podcast_feed_info() -> PodcastFeedInfo:
    """Feed URL for the UI (behind the normal API auth, never public)."""
    settings = load_feed_settings()
    if settings is None:
        return PodcastFeedInfo(enabled=False)
    return PodcastFeedInfo(enabled=True, feed_url=feed_url(settings))


@public_router.api_route("/{token}/feed.xml", methods=["GET", "HEAD"])
async def podcast_feed(token: str) -> Response:
    settings = require_feed_token(token)
    return Response(
        content=await build_feed_xml(settings),
        media_type="application/rss+xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=300"},
    )


@public_router.api_route("/{token}/audio/{episode_key}.mp3", methods=["GET", "HEAD"])
async def podcast_feed_audio(token: str, episode_key: str) -> FileResponse:
    require_feed_token(token)
    # FileResponse answers HEAD and Range requests, which podcast apps use to
    # size downloads and to seek.
    return FileResponse(
        await episode_audio_path(episode_key),
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@public_router.api_route("/{token}/cover.png", methods=["GET", "HEAD"])
async def podcast_feed_cover(token: str) -> FileResponse:
    require_feed_token(token)
    return FileResponse(
        cover_path(),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
