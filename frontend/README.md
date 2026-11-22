# Frontend (planned)

Next.js + TypeScript, mobile-first.

Pages:
- `/` today's matches grouped by game (live / upcoming / finished)
- `/match/[id]` match detail
- `/game/[slug]` per-game view

Talks to the FastAPI backend (`/matches`, `/videogames`). Live updates via polling first, SSE later.
