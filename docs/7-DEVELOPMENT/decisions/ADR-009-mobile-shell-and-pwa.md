# ADR-009: Phone layout via a drawer shell; PWA via the Next.js manifest and Serwist

- **Status**: Accepted
- **Date**: 2026-09
- **Related**: [ADR-003](ADR-003-streamlit-to-nextjs.md) (the Next.js UI this extends)

## Context

On a phone the fixed 256px sidebar took two thirds of the screen, and dialogs had `overflow-hidden` with no height cap, so tall ones (Generate Podcast, episode/speaker profiles, Add Source) clipped their footers and could not be scrolled. The app also could not be installed to a home screen.

## Decision

**Below `md` the `AppShell` swaps the sidebar for a top bar plus a left drawer (shadcn `Sheet` on the existing `@radix-ui/react-dialog`). `DialogContent` caps its height at `100dvh - 2rem` and scrolls by default. The PWA uses Next's built-in `app/manifest.ts` and `@serwist/turbopack` for the service worker.**

- The drawer renders the same `AppSidebar` in a `mobile` mode (always expanded, closes on navigation) — one nav definition, no second menu.
- Dialogs that manage their own inner scroll keep working: an explicit `overflow-hidden`/`max-h-*` in `className` still wins via `tailwind-merge`.
- On coarse pointers dialogs focus themselves instead of the first input, so opening a form does not pop the keyboard over it; inputs are 16px on phones so iOS does not zoom.
- Hover-only affordances (`opacity-0 group-hover:opacity-100`) also get `[@media(hover:none)]:opacity-100`; Tailwind v4 gates `hover:` behind `(hover: hover)`, so they were unreachable on touch.
- The service worker never caches `/api/*` or `/config` (`NetworkOnly`): that is live, authenticated data. Static assets use Serwist's `defaultCache`; failed document navigations fall back to a precached `/~offline` page. `reloadOnOnline` is off so a flaky connection does not wipe a half-typed chat. Registration is disabled in `next dev`.

## Alternatives considered

- **`next-pwa` / `@ducanh2912/next-pwa`** — rejected: webpack plugins, and Next 16 builds with Turbopack. Serwist is their maintained successor and the option the Next.js PWA guide points to for Turbopack.
- **Hand-written service worker in `public/`** — rejected: precache manifests, revisioning and route strategies are what Serwist exists for.
- **Manifest only, no service worker** — rejected: installability works, but there is no offline fallback and no asset caching for slow mobile links.
- **Separate mobile navigation (bottom tab bar)** — rejected for now: nine destinations do not fit a tab bar, and a second nav definition would drift from the sidebar.

## Consequences

- `esbuild` (dev dependency) bundles `src/app/sw.ts` at build time via the `/serwist/[path]` route handler; `tsconfig` includes the `webworker` lib for that file.
- Any new API-like route outside `/api/` that must not be cached needs a matcher in `sw.ts`.
- New dialogs get scroll-on-overflow for free; a dialog that needs a fixed inner scroller must pass `overflow-hidden` explicitly.
