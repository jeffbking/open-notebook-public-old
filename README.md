# Open Notebook (personal hard fork)

A self-hosted, privacy-focused research notebook (an alternative to Google's NotebookLM): collect sources into notebooks, chat and search over them, and turn them into podcasts.

This repository, `jeffbking/open-notebook`, is a **personal hard fork** of [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook). It runs on one host for one user.

- **Upstream is never merged.** There is no `upstream` git remote, and `gh` defaults to this repository. Changes are made directly here, with no PRs or reviews.
- **Nothing is published.** There are no registry images, releases or GitHub Actions (Actions are disabled on the repo), and no issues, PRs or Discussions go to the original project.
- **Nothing updates itself.** The app has no "update available" check, and every image is pinned or built from this checkout.

## What's different from upstream

| Area | Change |
|---|---|
| Deploy | Compose builds the app image from this checkout (`open_notebook:local`) instead of pulling `lfnovo/open_notebook`. SurrealDB is pinned to `v2.7.0` (no floating tag, no pull on `up`). |
| Mobile | Phone layout with a top bar and a slide-in navigation drawer. Dialogs fit the screen and scroll. Touch-friendly controls, and no iOS zoom on inputs. ([ADR-009](docs/7-DEVELOPMENT/decisions/ADR-009-mobile-shell-and-pwa.md)) |
| PWA | Installable app with a manifest and icons. A Serwist service worker precaches static assets, never caches `/api`, and serves an offline page. |
| Podcast feed | Token-gated public RSS feed of generated episodes for podcast apps, served through a path-scoped Cloudflare Tunnel. ([ADR-010](docs/7-DEVELOPMENT/decisions/ADR-010-public-podcast-feed.md)) |
| Podcast prompts | The prompts ask for the final JSON only. Asking for visible `<think>` reasoning made Anthropic models refuse (`reasoning_extraction`). |
| Models | OpenAI-compatible providers always use chat completions: langchain-openai would otherwise force the Responses API for model names containing `codex`. The patch is in `open_notebook/__init__.py`. |
| Gemini STT | Handles the `audioTranscription` response shape of dedicated transcription models (same file). |
| Removed | Upstream update check, release process and scripts, Docker publish workflows, Dependabot, issue/discussion/PR templates, Cubic review config, and the maintainers' `release` / `process-discussions` agent skills. |

## Running it

Three tiers: Next.js UI (8502) → FastAPI (5055) → SurrealDB (8000), plus a background worker in the app container. All ports are bound to `127.0.0.1`.

```bash
make deploy                 # rebuild the image from this checkout and restart the app
docker compose up -d        # start everything (surrealdb, open_notebook, cloudflared)
docker compose logs -f open_notebook
```

Database migrations run automatically when the API starts. Before a deploy that brings new migrations, export the database first (see [Backups](#backups)).

### Access

- **UI (tailnet only):** `https://open-notebook.walrus-bebop.ts.net/`, through a Tailscale VIP service (`svc:open-notebook`). Tailscale Serve proxies it to `127.0.0.1:8502`, and Next.js forwards `/api/*` to the API.
- **Public podcast feed:** `https://notebook-podcasts.ezhost.ing/public/podcasts/<token>/feed.xml`, through the `cloudflared` sidecar (tunnel `open-notebook-podcasts`). Cloudflare forwards only `/public/podcasts/` to the API; every other path is a 404 at its edge. Copy the full URL from the **Podcast feed** card on the Podcasts page.

### Configuration (`.env`, gitignored, mode 0600)

| Variable | Purpose |
|---|---|
| `OPEN_NOTEBOOK_ENCRYPTION_KEY` | Encrypts provider credentials stored in the database. Required. |
| `SURREAL_USER` / `SURREAL_PASSWORD` | Database credentials, shared by both services. |
| `OPEN_NOTEBOOK_PODCAST_FEED_TOKEN` | Enables the public feed. At least 32 URL-safe characters. Rotating it breaks existing subscriptions. |
| `OPEN_NOTEBOOK_TUNNEL_TOKEN` | Token for the `cloudflared` tunnel. |

Compose also sets `API_URL`, the feed origin and title, and podcast TTS pacing: `TTS_BATCH_SIZE=3` (Breezeblue's free plan allows 3 concurrent generations), `PODCAST_RETRY_MAX_ATTEMPTS=6` and `PODCAST_RETRY_WAIT_MAX=60`.

### AI providers (configured in the UI under Models; keys are stored encrypted in the database)

- **Language models:** the Oneshot gateway, as an OpenAI-compatible credential (`https://oneshot.walrus-bebop.ts.net/v1`). Models include `claude/sonnet`, `claude/opus`, `codex/gpt-6-luna` and `agy/gemini-3.8-flash`.
- **Text to speech:** Breezeblue, which has an ElevenLabs-compatible API. It is set up as an **ElevenLabs** credential with base URL `https://api.breeze.blue`, using the `breeze-tts-2` model. Speaker profiles use Breezeblue voice IDs (`voc_…`). Voice IDs are specific to each provider, so changing a profile's TTS model means remapping its voices too.
- **Speech to text and embeddings:** Google AI. Gemini TTS is still configured but isn't the default, because its quota on this key (10 requests/minute, 100/day) can't cover a full episode.

## Backups

```bash
set -a; . ./.env; set +a
docker exec open-notebook-surrealdb-1 /surreal export --conn http://localhost:8000 \
  --user "$SURREAL_USER" --pass "$SURREAL_PASSWORD" --ns open_notebook --db open_notebook - \
  > ~/backups/open-notebook/$(date +%Y%m%d-%H%M).surql
```

Generated podcast audio lives in `./notebook_data/podcasts/`, and database files in `./surreal_data/`.

## Development

The host has no `uv`, `ruff` or Python toolchain, so backend checks run in the uv container:

```bash
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e UV_CACHE_DIR=/uvcache -e UV_PROJECT_ENVIRONMENT=/venv \
  -v ~/.cache/uv-on:/uvcache -v ~/.cache/uv-on-venv:/venv -v "$PWD":/w -w /w \
  ghcr.io/astral-sh/uv:python3.12-bookworm-slim \
  sh -c 'uv sync --frozen && uv run ruff check . && uv run python -m mypy . && uv run pytest tests/'
```

Use the same image for `uv lock` after changing dependencies.

Frontend (inside `frontend/`):

```bash
npm ci --replace-registry-host=always   # npm 12 rejects the lockfile's npmmirror URLs otherwise
npx tsc --noEmit && npm run lint && npm run test
```

`next dev` appends a block to `frontend/AGENTS.md`. Run `git checkout -- frontend/AGENTS.md` before committing.

Coding-agent rules are in [AGENTS.md](AGENTS.md). Architecture, recipes and design decisions are in [docs/7-DEVELOPMENT/](docs/7-DEVELOPMENT/index.md). The user guides under [docs/](docs/index.md) come from upstream and still describe the general product.

## License and attribution

MIT, like the original project. See [LICENSE](LICENSE). Open Notebook was created by Luis Novo and contributors at [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook). This fork keeps that license and copyright notice.
