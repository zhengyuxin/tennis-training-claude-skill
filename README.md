# 🎾 SwingVision Tennis Training — Claude Cowork Skill

A [Claude Cowork](https://claude.ai) skill that turns **SwingVision** screenshots into structured training records, trend charts, and PDF coaching reports — entirely through conversation, no code required.

---

## What it does

| Phase | Description |
|---|---|
| **1. Extract** | Read SwingVision session screenshots → pull out all metrics (FH/BH success rate, swing speed, rally stats, landing zones, Apple Watch heart rate) |
| **2. Store** | Write data into a structured Apple Notes table, one row per session, one note per player pair. Auto-creates the note if it doesn't exist yet. |
| **3. Report** | Generate a Chinese PDF training report (desktop + mobile) with trend charts, landing zone distribution, radar chart, and written coaching analysis |

---

## Example output

### PDF Report (desktop)

> Trend charts · Landing zone distribution · Per-player insights · Training recommendations

### Data stored in Apple Notes

Each player pair gets a persistent note (e.g. `YZ&XT 🎾`) with one row per session:

| 日期 | 整体 | 最长回合 | 超过5回合 | 正手 | 正手速度 | 反手 | 反手速度 | 落点左区 | 落点中区 | 落点右区 | 落点深区 | 落点浅区 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3/24 | 89% | 39 | 74% | 92% | 76 | 81% | 73 | 11% | 75% | 13% | 61% | 38% |

---

## Install

```bash
# Clone the repo
git clone https://github.com/zhengyuxin86/tennis-training-claude-skill.git

# Copy the skill folder into Claude's skills directory (Mac)
mkdir -p ~/.claude/skills
cp -r tennis-training-claude-skill ~/.claude/skills/tennis-training-claude-skill
```

Restart Claude Cowork — the skill loads automatically.

---

## Usage

Just talk to Claude in Cowork mode:

```
"Extract data from these SwingVision screenshots and update the note"
"Generate a training report for YZ and XT"
"Generate both desktop and mobile PDF reports based on the data in notes"
```

Claude will handle extraction, storage, and report generation end-to-end.

---

## Requirements

| Requirement | Notes |
|---|---|
| Claude desktop (Cowork mode) | Required |
| SwingVision app (iOS) | Required for data capture |
| Apple Notes MCP | Required for persistent storage |
| Python 3 | Required for PDF generation |
| `pip install reportlab matplotlib` | Auto-installed on first run |

---

## How the data extraction works

SwingVision shows a top-down court diagram with landing zone percentages. Reading deep vs. shallow correctly requires knowing the diagram orientation:

| Horizontal numbers position | Upper vertical % | Lower vertical % |
|---|---|---|
| At the **top** of court | Deep zone | Shallow zone |
| At the **bottom** of court | Shallow zone | Deep zone |

The skill encodes this rule explicitly and runs three validation checks on every extraction:
1. Left + Center + Right must sum to 98–100
2. Deep + Shallow must sum to 98–100
3. Deep zone should be **greater than** Shallow zone (sanity check for normal baseline play)

---

## Report contents

Both PDF versions (desktop A4 + mobile-optimised) include:

1. **Summary cards** — latest session metrics for each player with trend vs. first session
2. **Forehand & backhand success rate trends** (line chart, with target reference lines)
3. **Shot speed trends** (km/h)
4. **Rally stability trends** (dual-axis: Rallies 5+% and longest rally)
5. **Landing zone distribution** per player (left/center/right bars + deep/shallow bars)
6. **Performance radar chart** (latest session)
7. **Full data table** (all sessions, backhand < 82% highlighted in red)
8. **Written analysis** — per-player observations + shared trends
9. **Training recommendations** — prioritised by urgency

---

## Apple Notes structure

The skill creates one note per player pair, named `[PlayerA]&[PlayerB] 🎾` (e.g. `YZ&XT 🎾`). Each note contains three HTML tables:

- **综合** (combined) — overall stats for both players
- **[Player A]** — per-session detailed stats for Player A
- **[Player B]** — per-session detailed stats for Player B

If YZ is one of the players, YZ's table includes an extra **心率 (heart rate)** column for Apple Watch data.

---

## Player context (customise for your own use)

The skill is designed for any two-player pairing. The bundled scripts use `XT` and `YZ` as player codes — replace with your own initials.

Player-specific notes in the default configuration:
- **XT** — tends to trade backhand stability for swing speed; landing distribution drifts left over time
- **YZ** — very stable forehand (~90%+); backhand more volatile; landing clusters in center-deep

---

## Files

```
tennis-training-claude-skill/
├── SKILL.md                     ← Core skill instructions (Claude reads this)
├── README.md                    ← This file
└── scripts/
    ├── generate_pdf_cn.py       ← Chinese desktop PDF generator (A4)
    └── generate_pdf_mobile.py   ← Chinese mobile PDF generator (single-column)
```

---

## Background

This skill was built to solve a real problem: SwingVision generates great per-session data, but it's locked inside the app with no export. By combining SwingVision (Generation 1 AI — computer vision, ball tracking) with Claude (Generation 2 AI — LLM reasoning and analysis), you get a complete pipeline:

**SwingVision captures → Claude extracts, stores, and analyses → PDF report ready to share**

Read the full write-up: [Medium article link]

---

## License

MIT — use freely, adapt to your own players and training goals.
