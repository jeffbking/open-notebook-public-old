# ADR-010: Public podcast feed behind a token and a path-scoped tunnel

- **Status**: Accepted
- **Date**: 2026-09
- **Related**: [ADR-009](ADR-009-mobile-shell-and-pwa.md) (mobile/PWA)

## Context

Podcast apps (Apple Podcasts, Overcast, Pocket Casts) subscribe to an RSS URL. Overcast and Pocket Casts fetch feeds from their own servers, so a tailnet-only or password-protected URL doesn't work for them, and podcast apps can't send the app's bearer password. The rest of Open Notebook must stay private.

## Decision

**Serve a token-gated RSS feed, its episode audio and its cover under `/public/podcasts/<token>/` on the API, and expose only that path publicly through a Cloudflare Tunnel whose ingress forwards `/public/podcasts/` and answers 404 for everything else at the edge.**

- The token (`OPEN_NOTEBOOK_PODCAST_FEED_TOKEN`, ≥32 URL-safe characters) is the only gate. A missing, short or wrong token, a disabled feed, and an unknown episode all return the same 404. Password auth skips the `/public/podcasts/` prefix, and these routes check the token themselves.
- The feed lists only episodes whose audio exists inside the podcasts folder, via `resolve_contained_audio_path`. Episode descriptions come from the outline; briefings and source content are never published.
- The RSS comes from `feedgen` (podcast extension). Durations come from `ffprobe`, which is already in the image. `mutagen` was rejected because its GPL license doesn't fit this MIT project.
- The channel sets `itunes:block` so directories don't list the feed.
- This mirrors the separate Newslop app's feed pattern rather than importing episodes into Newslop, which has no way to accept externally made audio.

## Consequences

- Anyone with the feed URL can list and download every generated episode. Rotating the token (edit `.env`, restart) invalidates old subscriptions.
- Cloudflare caches `.png` and `.mp3` responses at the edge, including 404s. Purge by URL after fixing a broken asset.
