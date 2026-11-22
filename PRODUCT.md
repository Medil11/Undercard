# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Esports fans who follow several games and check scores while matches are being played, often on a phone or as a second screen next to a stream. Their job: see what is live right now, how each series stands, and what is coming up, in a few seconds.

## Product Purpose

Undercard shows live, upcoming and finished esports matches across games in one place, FlashScore style. Success means a fan opens it mid-match and understands every live series at a glance, then drills into one match for its games, rosters and stream.

It is also a personal portfolio project of a data/software engineer, so the build quality is part of what it shows, but the fan comes first.

## Positioning

Reading a series at a glance. Where score sites show a bare number, Undercard makes the series state legible: the format (best of N, or first to N for Overwatch), maps/games won toward the target, who leads, which game is being played, and how each game ended.

## Operating Context

- Live use during matches: short visits, frequent refreshes (the front polls the API every 30 s), mobile and desktop.
- Data comes from the PandaScore free plan through the backend. The token never reaches the browser.
- Match page per match: games with winner and duration, current team rosters, main stream link.

## Capabilities and Constraints

- Statuses: running, not_started, finished, canceled, postponed. Tabs: Live, Upcoming, Finished. Filter by game.
- Series format: `match_type` is `best_of` or `first_to`; `number_of_games` means series length or wins needed accordingly.
- Available per match: league, tournament, scheduled time, games (position, status, winner, length), team logos (`image_url`, may be missing or dark), rosters (player handle, real name, role, nationality, photo), stream URL.
- Not available on the free plan: per-player or per-game detailed stats (403), map names (null). Do not design for data that is not there.
- Rosters are current team rosters, not necessarily the lineup of a given match; the UI must say so.
- Player vs player games (StarCraft 2) are skipped by ingestion.
- Everything stays free and local: no paid service, no account other than the PandaScore token.
- Current front: one static file, `frontend/index.html`, vanilla JS, served by FastAPI at `/`. A Next.js + TypeScript port is planned (`/`, `/match/[id]`, `/game/[slug]`).
- Interface language: English (switching from the current French UI).
- Open decision: optional tournament tier filter (S/A/B/C) if the payload exposes tiers.

## Brand Commitments

- Name: Undercard (renamed from Esport Live on 2026-11-22). The undercard is every bout of a fight night, not just the headliner: every match across every game.
- Logo: `frontend/icon.svg` (mark: a triangle broken into its three corners, a dot at its centre) and `frontend/logo.svg` (mark + Unbounded 600 wordmark, all white on black).
- No emoji in the interface.
- Team logos come from the API, with a neutral initials fallback.
- Reference for information density and structure: Liquipedia (Upcoming / Completed tabs, explicit series format).

## Evidence on Hand

- Real live data through the local API (`GET /matches`, `GET /matches/{id}`, `GET /videogames`).
- Fictional demo data when the API is unreachable (`frontend/index.html`) and a demo seed (`backend/ingestion/seed_demo.py`).
- No testimonials, users, or metrics exist; do not invent any.

## Product Principles

1. Series state first: every match row answers "who leads, toward what target, which game now" without a click.
2. Live is the loudest thing on screen; everything else stays quiet.
3. Density over decoration: many matches visible at once, scannable in seconds.
4. Truthful data: show only what the API provides, label caveats plainly, never fake numbers.
5. Fast and light: one page, no build step today, instant on a phone.
