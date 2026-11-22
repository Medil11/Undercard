---
name: Undercard
description: Live esports series billed like a fight night, two teams squared off across a central VS axis.
colors:
  ground-black: "#0c0c0c"
  hover-black: "#171715"
  empty-slot: "#262624"
  rule-line: "#242422"
  poster-white: "#f5f5f0"
  muted-ash: "#b3b3ad"
  dim-ash: "#8a8a84"
  logo-plate: "#55554f"
  light-plate: "#e4e4de"
  poster-yellow: "#ffd400"
  poster-yellow-hover: "#ffe04d"
  yellow-ink: "#4d4300"
  in-play-red: "#ff3326"
typography:
  display:
    fontFamily: "Anton, Impact, Arial Narrow, sans-serif"
    fontSize: "128px"
    fontWeight: 400
    lineHeight: "112px"
    letterSpacing: "0em"
    fontFeature: "tnum"
  headline:
    fontFamily: "Anton, Impact, Arial Narrow, sans-serif"
    fontSize: "92px"
    fontWeight: 400
    lineHeight: "84px"
    letterSpacing: "0em"
  score:
    fontFamily: "Anton, Impact, Arial Narrow, sans-serif"
    fontSize: "32px"
    fontWeight: 400
    lineHeight: "34px"
    letterSpacing: "0.02em"
    fontFeature: "tnum"
  title:
    fontFamily: "Anton, Impact, Arial Narrow, sans-serif"
    fontSize: "28px"
    fontWeight: 400
    lineHeight: "32px"
    letterSpacing: "0.01em"
  subtitle:
    fontFamily: "Anton, Impact, Arial Narrow, sans-serif"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: "24px"
  body:
    fontFamily: "Archivo, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: "20px"
  body-strong:
    fontFamily: "Archivo, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 700
    lineHeight: "20px"
  note:
    fontFamily: "Archivo, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: "18px"
  label:
    fontFamily: "Archivo, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: "16px"
    letterSpacing: "0.08em"
rounded:
  square: "0px"
spacing:
  tape-gap: "4px"
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
  axis: "120px"
components:
  tape-block-empty:
    backgroundColor: "{colors.empty-slot}"
    rounded: "{rounded.square}"
    size: "22px"
  tape-block-won:
    backgroundColor: "{colors.poster-white}"
    rounded: "{rounded.square}"
    size: "22px"
  tape-block-in-play:
    backgroundColor: "{colors.in-play-red}"
    rounded: "{rounded.square}"
    size: "22px"
  billing-row:
    backgroundColor: "{colors.ground-black}"
    textColor: "{colors.poster-white}"
    typography: "{typography.title}"
    height: "76px"
  billing-row-hover:
    backgroundColor: "{colors.hover-black}"
  game-bar:
    backgroundColor: "{colors.poster-yellow}"
    textColor: "{colors.ground-black}"
  game-chip:
    textColor: "{colors.ground-black}"
    typography: "{typography.label}"
    padding: "10px 14px"
  game-chip-empty:
    textColor: "{colors.yellow-ink}"
  game-chip-active:
    backgroundColor: "{colors.ground-black}"
    textColor: "{colors.poster-yellow}"
  tab:
    textColor: "{colors.muted-ash}"
    typography: "{typography.label}"
    height: "64px"
  tab-active:
    textColor: "{colors.poster-white}"
  button-primary:
    backgroundColor: "{colors.poster-yellow}"
    textColor: "{colors.ground-black}"
    typography: "{typography.label}"
    rounded: "{rounded.square}"
    padding: "10px 16px"
  button-primary-hover:
    backgroundColor: "{colors.poster-yellow-hover}"
  avatar:
    backgroundColor: "{colors.empty-slot}"
    textColor: "{colors.muted-ash}"
    rounded: "{rounded.square}"
    size: "32px"
  avatar-logo:
    backgroundColor: "{colors.logo-plate}"
  avatar-logo-dark-mark:
    backgroundColor: "{colors.light-plate}"
  avatar-logo-light-mark:
    backgroundColor: "{colors.empty-slot}"
---

# Design System: Undercard

## Overview

**Creative North Star: "Fight Night Billing"**

Every match is billed like a boxing card. Two teams square off across a central VS axis; the left team is set flush right against the centre, the right team flush left, and the games each side has won stack outward from the axis as square tape blocks, like rounds on a scorecard. The page is a black poster with off-white condensed caps on it and one full-bleed band of poster yellow carrying the game filter. Nothing floats, nothing glows, nothing is rounded.

Density is high and calm: the list is a stack of hairline-separated billing rows under event headers, many visible at once. Loudness is rationed. Off-white marks what has happened (games won, the score), red marks only the game being played right now, and yellow is the poster's single colour field plus the few marks that act on it (the logo's "Live", the format in event headers, the primary button, focus). The match page is the same billing row blown up to poster scale, followed by a game-by-game ledger where each won game is a bar leaving the axis toward its winner, and two rosters facing each other across the same axis.

**Key Characteristics:**
- Symmetric VS axis: every match row mirrors around a fixed centre column.
- Square tape blocks at one fixed size per breakpoint, one block per game needed to win.
- Black ground, off-white type, one yellow field, one red state.
- Anton condensed caps for names and numbers; Archivo tracked uppercase for every label.
- Flat and square: zero radius, no elevation, hairline rules for structure.

## Colors

A poster palette: black ground, off-white ink, one yellow field, one signal red, and a ladder of warm greys that only ever carry hierarchy or empty state.

### Primary
- **Poster Yellow** (poster-yellow): the full-bleed game filter bar, the format/game text on the right of event headers, the "Live" in the logo, the primary button, text selection, and the focus ring. **Poster Yellow Hover** (poster-yellow-hover) is the button's hover only.
- **Yellow Ink** (yellow-ink): text on the yellow bar for games with zero matches in the current tab; readable but receded.

### Secondary
- **In-Play Red** (in-play-red): the game currently being played and nothing else. The next tape block of a running series, the "Live · G3" axis label, the "In play" game lane on the match page.

### Neutral
- **Ground Black** (ground-black): page, header and billing-row background; text on yellow.
- **Hover Black** (hover-black): billing-row hover fill, one step up from ground.
- **Empty Slot** (empty-slot): unfilled tape blocks and initials-avatar plates; the shape of what is still to be won.
- **Rule Line** (rule-line): the 1px hairline under every event header, billing row, game lane, section heading and roster line.
- **Poster White** (poster-white): primary type, won tape blocks, game-duration bars, the active tab underline and the tab's live square.
- **Muted Ash** (muted-ash): secondary text: inactive tabs, tournament names, axis status ("Final", "In 12 min"), durations, real names, notes, footer.
- **Dim Ash** (dim-ash): the losing team's name on a finished row, TBD teams, tab counts, unplayed game labels.
- **Logo Plate** (logo-plate): the mid-grey plate behind an API logo before its brightness is measured, and the fallback when it cannot be measured.
- **Light Plate** (light-plate): the pale plate behind a logo measured as dark, so dark marks stay readable on the black ground. A logo measured as light sits on Empty Slot instead.

### Named Rules
**The One Red Rule.** In-Play Red marks the game being played now and nothing else. Not errors, not "live" badges, not hover. The tab's live indicator is an off-white square, not red.

**The One Field Rule.** Poster Yellow fills exactly one surface edge to edge: the game bar. Everywhere else it is a text colour or a single small control (the primary button). No yellow cards, panels or row fills.

**The Functional Grey Rule.** Greys carry hierarchy (muted, dim), empty state (empty slot), structure (rule line) or logo legibility (logo plate, light plate). Never decoration, never gradients.

**The Measured Plate Rule.** A logo's plate is chosen by the logo's measured brightness, never by hand: average luminance of opaque pixels under 0.45 gets Light Plate, otherwise Empty Slot.

## Typography

**Display Font:** Anton (with Impact, Arial Narrow), self-hosted
**Body Font:** Archivo variable (with system-ui, Segoe UI), self-hosted
**Label Font:** Archivo 700, tracked uppercase

**Character:** Anton is the fight poster: tall condensed caps for team names and scores, always uppercase. Archivo is the small print on the bill: labels in tracked uppercase, body in plain sentence case.

### Hierarchy
- **Display** (Anton 400, 128px/112px; 52px/48px under 700px): the series score on the match page poster, tabular figures.
- **Headline** (Anton 400, 92px/84px, up to three lines; 34px/32px under 700px): team names on the match page poster.
- **Score** (Anton 400, 32px/34px, +0.02em, tabular; 24px/26px under 700px): the score or start time on a billing row's axis. The logo uses the same size at 32px/32px.
- **Title** (Anton 400, 28px/32px, +0.01em, up to two lines; 19px/21px under 700px): team names on billing rows and the empty-state message.
- **Subtitle** (Anton 400, 22px/24px): roster team headings. Game-lane winner names use Anton 18px/20px.
- **Body** (Archivo 400, 15px/20px): default running text. **Body Strong** (Archivo 700, 16px/20px) is the player handle.
- **Note** (Archivo 400, 13px/18px): data caveats, real names, footer.
- **Label** (Archivo 700, 12px/16px, +0.08em, uppercase): tabs, chips, event headers, axis status, section headings, durations, nationality, buttons. Counts inside tabs and chips drop to weight 500 and zero tracking.

### Named Rules
**The Caps Billing Rule.** Team names and numbers are Anton uppercase; labels are Archivo tracked uppercase; only notes and body run in sentence case.

**The Tabular Score Rule.** Scores and times use tabular figures so the axis never jitters between refreshes.

## Layout

One centred column, max 1344px, with 24px gutters (16px under 700px). Header is 64px and sticky, with the yellow game bar riding inside it so the filter never scrolls away.

The billing row is a five-column grid: team, tape, axis, tape, team. The axis is a fixed 120px; each tape column is sized from the tape math (five blocks of `--b` plus four `--gap` plus 32px padding), so every row's axis lands on the same vertical line regardless of series length. Under 700px the row restacks to three columns (team, 76px axis, team) with each tape tucked under its team name, still mirrored.

The match page reuses the billing row with a 280px axis (104px on phone), names and avatars stacked vertically toward the axis. Its grid has a second row: tape, button cell, tape, so the stream button sits under the score between the two tapes. Under 700px the axis spans both rows and the button moves to a third, full-width row below the tapes. The game-by-game ledger keeps the axis at 120px (64px on phone) with each half split into a track and a 200px meta lane (48px on phone, winner name hidden). Rosters are two columns separated by the same 120px gap, the left roster right-aligned; on phone they collapse to one left-aligned column.

Spacing steps observed: 4 (tape gap), 8, 12, 16, 24, 32, 48, 64px. Breakpoints: 899px (header wraps to logo + status over tabs) and 699px (billing row restacks, tape shrinks to 14px blocks with 3px gaps).

### Named Rules
**The Fixed Axis Rule.** The centre column has one width per context and every row honours it; content arranges itself around the axis, never the reverse.

## Elevation & Depth

Flat. No drop shadows, no glow, no blur, no gradients. Depth is conveyed by tone and line only: a one-step lift to Hover Black on row hover, hairline Rule Lines between rows, and the yellow game bar as the only colour field. The one box-shadow in the build is a 4px inset underline on the active tab, used as a rule, not as elevation.

### Named Rules
**The Flat Poster Rule.** Surfaces never lift. If something needs emphasis, it changes tone (white, yellow, red), not height.

## Shapes

Everything is square: zero radius on tape blocks, avatars, chips, buttons, the live square and duration bars. Avatars are square plates with initials, or the API logo contained with 3px padding. The tape block is the system's atom; the game-duration bar is the same block stretched horizontally, same 22px height.

### Named Rules
**The One Scale Rule.** Tape blocks are one fixed size per breakpoint (22px, 14px on phone). A best-of-five and a best-of-three use the same block; the series length shows as block count, never as resized blocks.

## Components

### Billing Row (signature)
The core unit. Team left (right-aligned toward the axis) with its avatar nearest the centre, left tape growing leftward from the axis, the axis (score or start time in Anton, status label below), right tape growing rightward, team right.
- **Tape:** one block per game needed to win (best of N: ceil(N/2); first to N: N). Won blocks Poster White, the next block of a running series In-Play Red, the rest Empty Slot.
- **Axis states:** live shows score plus "Live · G n" in red; finished shows score plus "Final" in muted; upcoming shows time plus "In n min" or the day; canceled/postponed show an en dash plus the status.
- **Loser:** on a finished row the losing team's name drops to Dim Ash.
- **Hover / Focus:** background to Hover Black (0.15s); focus is the 2px yellow outline pulled inside the row (offset -2px).
- **Motion:** a newly won block wipes outward from the axis (clip-path, 0.42s, ease cubic-bezier(.16,1,.3,1)). Nothing loops. Reduced motion removes it.

### Event Header
League left in label style with tournament in Muted Ash, game and format right in Poster Yellow, a hairline below. Groups billing rows.

### Game Bar (navigation)
Full-bleed Poster Yellow band under the header. Chips are label-style text on yellow with a count; zero-count games in Yellow Ink; hover is an 8% black tint; the active chip inverts to black with yellow text. Horizontally scrollable, scrollbar hidden. Focus ring is black, inset.

### Tabs
Live / Upcoming / Finished in label style, Muted Ash at rest, Poster White on hover and when selected; selected gets a 4px off-white underline at the header's bottom edge. Counts sit inside each tab in Dim Ash; the Live tab adds an 8px off-white square when anything is running.

### Buttons
- **Shape:** square (0px).
- **Primary:** Poster Yellow fill, black label text, 10px 16px padding, optional 16px stroked SVG icon after the label.
- **Hover / Focus:** Poster Yellow Hover; focus ring switches to off-white so it reads against the yellow.
- **Back link:** label-style text in Muted Ash with a 16px chevron, Poster White on hover.

### Avatar
Square plate with up to three initials in Archivo 700 on Empty Slot. When the API provides a logo it sits contained (3px inset) on the Logo Plate until it loads, then its brightness is measured (24x24 sample, mean luminance of opaque pixels): dark marks (under 0.45) move to Light Plate, light marks to Empty Slot. If the image fails, the initials return on Empty Slot. Team logos and player photos follow the same rule. 32px in rows, 72px on the match poster, 36px in rosters, 24px / 44px on phone.

### Match Poster
The billing row at poster scale: Headline team names stacked over their avatars, Display score on a 280px axis, tape under each name, and, when a stream exists, the "Watch stream" primary button in its own cell under the score between the tapes (on phone, a full-width button row below the tapes).

### Game-by-Game Ledger
One 44px lane per game across the axis. The axis cell names the game; the winner's half carries an off-white bar whose length is the game's real duration relative to the longest game, plus the winner name and duration. If any duration is missing, every winner gets a single tape block instead of a bar, so no length is ever implied. A running game fills both sides with a red block and a red "In play" label; unplayed games show a dim label and empty lanes.

### Roster
Two columns mirrored across the axis: Anton team heading, then player lines (36px avatar, handle in Body Strong, real name and role in Note, nationality code in label style), hairline below each. Always followed by the note that these are current rosters, not necessarily the match lineup.

### Empty and Loading States
Centred Anton message at title size ("No live matches right now", "Loading matches"), with a primary button to the next useful tab when Live is empty.

## Do's and Don'ts

### Do:
- **Do** keep every match symmetric around a fixed-width axis: left team right-aligned, right team left-aligned, tapes growing outward.
- **Do** express series length as a count of same-size square blocks (22px, 14px on phone).
- **Do** reserve In-Play Red (#ff3326) for the game being played now.
- **Do** set team names and scores in Anton uppercase and every label in Archivo 700, 12px, +0.08em, uppercase.
- **Do** separate rows with 1px Rule Line hairlines and show hover as a tone step to Hover Black.
- **Do** derive any bar length from real data (game duration) and fall back to a plain block when the data is missing.
- **Do** keep motion to the outward wipe of a newly won block, and make it instant under reduced motion.

### Don't:
- **Don't** use red for anything other than the game in play: not errors, not badges, not hover, not the tab's live indicator.
- **Don't** fill any surface with yellow other than the game bar; elsewhere yellow is text, focus, or the primary button.
- **Don't** add rounded corners, drop shadows, glow, blur or gradients.
- **Don't** resize tape blocks to fit a longer series.
- **Don't** use greys decoratively; each grey has a hierarchy, empty-slot, rule or logo-plate role.
- **Don't** fall back to a left-aligned team list with a score column on the right.
