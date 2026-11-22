---
version: 1
slug: "frontend-index-html"
primary_target: "frontend/index.html"
related_targets: []
---

# Surface brief: live scores app (frontend/index.html)

Scope: the whole front, list (`/`) and match page (`#/match/<id>`). Visitor mode: Operate.
Audience and job: esports fans checking live series mid-match, phone or second screen, evening. Task: see who leads every live series, what is next, then drill into one match.
Constraints: real API data only (games, rosters, stream; no maps, no player stats), English UI, no emoji, static single file, polls every 30 s.
Memorable moment: the VS axis, with each side's series growing outward from the centre.

## Direction contract

THESIS: Every match is billed like a fight night: two teams squared off across a central VS axis, games won stacking outward from the centre like rounds. It refuses the category default of a left-aligned team list with a score column on the right.

OWN-WORLD: Black ground #0c0c0c, poster yellow #ffd400 owning the full-bleed game bar (the shell's only rule), off-white #f5f5f0 type, one red reserved strictly for the game being played now. No greys as decoration, no gradients, shadows or glow. Anton stacked condensed caps for team names and scores, Archivo for labels in tracked uppercase. Square tape blocks at one fixed scale.

STORY: The fan sees every live series at a glance (who leads, toward what target, which game is in play), switches game or tab, opens a match to read it round by round with rosters facing off, and taps through to the stream.

FIRST VIEWPORT: Header with logo, Live/Upcoming/Finished tabs and data status; full-width yellow game bar; then event headers (tournament left, game and format right in yellow) over billing rows: team left right-aligned, tape growing left from the centre, score and status on the axis, tape growing right, team right. Primary action: the billing row itself opens the match.

FORM: Fight Night Billing, position 4 of my ordered grounded list, assigned by the roll after one re-roll. seed:ad67455271a527a6. Raises kept: one fixed tape scale (botanical folio), red only for the game in play (orienteering), one cell grid (Crouwel), only the live game lifts (streaming wall). Signature interaction: on the match page, each game is a bar leaving the VS axis toward its winner, its length the game's real duration. Motion grammar: one authored move, a new game won fills its block with a wipe outward from the centre; nothing loops; reduced motion makes it instant.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
