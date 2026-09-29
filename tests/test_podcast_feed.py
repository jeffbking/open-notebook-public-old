"""
Tests for the token-gated public podcast feed (api/routers/podcast_feed.py).

The feed token is the only gate on /public/podcasts/, so every miss (feed off,
wrong token, unknown episode, missing audio) must be the same 404, and the
routes must bypass password auth because podcast apps cannot send a bearer.
"""

from unittest.mock import AsyncMock, patch
from xml.etree import ElementTree

import pytest
from fastapi.testclient import TestClient

from open_notebook.podcasts.models import PodcastEpisode

TOKEN = "t" * 40
ORIGIN = "https://podcasts.example.test"
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"


def make_episode(key, audio_file, **overrides):
    defaults = dict(
        id=f"episode:{key}",
        name=f"Episode {key}",
        episode_profile={"name": "default"},
        speaker_profile={"name": "default"},
        briefing="internal briefing",
        content="source content",
        audio_file=audio_file,
        outline={"segments": [{"name": "Intro", "description": "Sets the scene"}]},
        command=None,
    )
    defaults.update(overrides)
    return PodcastEpisode(**defaults)


@pytest.fixture
def client():
    from api.main import app

    return TestClient(app)


@pytest.fixture
def feed_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OPEN_NOTEBOOK_PODCAST_FEED_TOKEN", TOKEN)
    monkeypatch.setenv("OPEN_NOTEBOOK_PODCAST_FEED_ORIGIN", ORIGIN)
    monkeypatch.setattr(
        "open_notebook.podcasts.audio_paths.PODCASTS_FOLDER", str(tmp_path)
    )
    (tmp_path / "episodes" / "a").mkdir(parents=True)
    (tmp_path / "episodes" / "a" / "a.mp3").write_bytes(b"0123456789" * 10)
    return tmp_path


class TestFeedGate:
    def test_feed_disabled_without_token(self, client, monkeypatch):
        monkeypatch.delenv("OPEN_NOTEBOOK_PODCAST_FEED_TOKEN", raising=False)
        monkeypatch.setenv("OPEN_NOTEBOOK_PODCAST_FEED_ORIGIN", ORIGIN)
        assert client.get(f"/public/podcasts/{TOKEN}/feed.xml").status_code == 404
        assert client.get("/api/podcasts/feed-info").json() == {
            "enabled": False,
            "feed_url": None,
        }

    def test_short_token_disables_feed(self, client, monkeypatch):
        monkeypatch.setenv("OPEN_NOTEBOOK_PODCAST_FEED_TOKEN", "short")
        monkeypatch.setenv("OPEN_NOTEBOOK_PODCAST_FEED_ORIGIN", ORIGIN)
        assert client.get("/public/podcasts/short/feed.xml").status_code == 404

    def test_wrong_token_is_404(self, client, feed_env):
        for path in ("feed.xml", "cover.png", "audio/a.mp3"):
            assert client.get(f"/public/podcasts/{'x' * 40}/{path}").status_code == 404

    def test_feed_info_reports_url(self, client, feed_env):
        assert client.get("/api/podcasts/feed-info").json() == {
            "enabled": True,
            "feed_url": f"{ORIGIN}/public/podcasts/{TOKEN}/feed.xml",
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("path", "expected"),
        [(f"/public/podcasts/{TOKEN}/feed.xml", 200), ("/api/podcasts/feed-info", 401)],
    )
    async def test_public_prefix_bypasses_password_auth(
        self, monkeypatch, path, expected
    ):
        from fastapi import Request
        from starlette.responses import Response

        from api.auth import PasswordAuthMiddleware

        monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "secret-password")

        async def allow(_: Request) -> Response:
            return Response(status_code=200)

        middleware = PasswordAuthMiddleware(AsyncMock())
        scope = {"type": "http", "method": "GET", "path": path, "headers": []}
        response = await middleware.dispatch(Request(scope), allow)
        assert response.status_code == expected


class TestFeedCover:
    def test_cover_art_is_served(self, client, feed_env):
        response = client.get(f"/public/podcasts/{TOKEN}/cover.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content.startswith(b"\x89PNG")


class TestFeedContent:
    def test_lists_only_episodes_with_audio_on_disk(self, client, feed_env):
        episodes = [
            make_episode("a", "episodes/a/a.mp3"),
            make_episode("pending", None),
            make_episode("gone", "episodes/gone/gone.mp3"),
            make_episode("escape", "../outside.mp3"),
        ]
        with patch.object(
            PodcastEpisode, "get_all", new=AsyncMock(return_value=episodes)
        ):
            response = client.get(f"/public/podcasts/{TOKEN}/feed.xml")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/rss+xml")
        channel = ElementTree.fromstring(response.content).find("channel")
        assert channel is not None
        items = channel.findall("item")
        assert [item.findtext("title") for item in items] == ["Episode a"]
        enclosure = items[0].find("enclosure")
        assert enclosure is not None
        assert enclosure.get("url") == f"{ORIGIN}/public/podcasts/{TOKEN}/audio/a.mp3"
        assert enclosure.get("length") == "100"
        assert enclosure.get("type") == "audio/mpeg"
        assert items[0].findtext("description") == "Intro: Sets the scene"
        image = channel.find(f"{ITUNES}image")
        assert image is not None
        assert image.get("href") == f"{ORIGIN}/public/podcasts/{TOKEN}/cover.png"
        assert channel.findtext(f"{ITUNES}block") == "yes"
        # Internal generation inputs never leak into the public feed.
        assert b"internal briefing" not in response.content
        assert b"source content" not in response.content


class TestFeedAudio:
    def test_audio_supports_range_requests(self, client, feed_env):
        episode = make_episode("a", "episodes/a/a.mp3")
        with patch.object(PodcastEpisode, "get", new=AsyncMock(return_value=episode)):
            response = client.get(
                f"/public/podcasts/{TOKEN}/audio/a.mp3", headers={"Range": "bytes=0-9"}
            )
        assert response.status_code == 206
        assert response.content == b"0123456789"
        assert response.headers["content-type"] == "audio/mpeg"

    def test_invalid_episode_key_is_404(self, client, feed_env):
        response = client.get(f"/public/podcasts/{TOKEN}/audio/a%3Ab.mp3")
        assert response.status_code == 404

    def test_unknown_episode_is_404(self, client, feed_env):
        with patch.object(
            PodcastEpisode, "get", new=AsyncMock(side_effect=Exception("missing"))
        ):
            response = client.get(f"/public/podcasts/{TOKEN}/audio/nope.mp3")
        assert response.status_code == 404
