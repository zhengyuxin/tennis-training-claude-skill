---
name: tennis-report
description: >
  Use this skill whenever the user wants to: (1) extract tennis training data
  from SwingVision screenshots and save it to Apple Notes, (2) update existing
  training records, or (3) generate a PDF training report with charts and analysis.

  Trigger on any of these cues: tennis training / 网球训练, screenshots from a
  swing sensor app (SwingVision, Swing Vision, 挥拍), "extract data" / "提取数据",
  "update note" / "更新note", "generate report" / "生成报告", "training report" /
  "训练报告", "tennis PDF" / "网球PDF", landing distribution / 落点分布, forehand /
  backhand success rate / 正反手成功率.

  Trigger even when only one part of the workflow is requested
  (e.g. "just extract the data" or "only generate the PDF").
---

# SwingVision Tennis Training Skill

## Overview

This skill handles a three-phase workflow. Each phase can be run independently or all together:

1. **Extract** – read numerical data from SwingVision screenshots
2. **Store** – persist the data in a structured Apple Notes HTML table
3. **Generate PDF** – produce two PDF reports (desktop A4 + mobile), in the appropriate language

---

## Language selection — automatic (screenshot-first)

**Determine the output language from the SwingVision app UI visible in the screenshots — not from the user's message language.** This is the first thing to do before any extraction or processing step.

### Step 1 — Inspect the screenshot UI language

Look at the metric labels shown in the uploaded screenshots:

| If the app displays | Set `LANG` |
|---|---|
| Chinese labels: 正手, 反手, 整体, 落点, 超过5回合, 最长回合, 速度 … | `'cn'` |
| English labels: Forehand, Backhand, Overall, Landing, Rallies, Longest Rally, Speed … | `'en'` |

The screenshot language is ground truth — it reflects the user's chosen app locale and is the most reliable signal.

### Step 2 — Fallback when no screenshots are provided

If the user hasn't uploaded screenshots yet (e.g. "just generate the PDF" with data already stored), fall back to the user's message language:

| User's message contains | Set `LANG` |
|---|---|
| Any Chinese characters | `'cn'` |
| Only English | `'en'` |

### Step 3 — Apply consistently across ALL outputs

Once `LANG` is set, use it everywhere without exception:

| Output surface | Language rule |
|---|---|
| **Claude's own Cowork replies** | Write in the detected language (Chinese if `cn`, English if `en`) |
| **Apple Notes — note title** | Use the language-appropriate format (see Phase 2 below) |
| **Apple Notes — table headers** | Use the correct header set for the detected language (see Phase 2 below) |
| **Apple Notes — confirmation messages** | Write in detected language |
| **PDF — all section headings, chart labels, axis titles** | Controlled by `LANG` variable in both scripts |
| **PDF — Analysis & Insights (section 7)** | Write all prose in detected language |
| **PDF — Training Recommendations (section 8)** | Write all plan items in detected language |

Do not ask the user to choose a language. Do not mix languages within a single output.

---

## Phase 1 – Data Extraction from Screenshots

### Metrics to extract

| Field | App label (EN) | App label (CN) | Description |
|---|---|---|---|
| Overall | Overall | 整体 | Overall success rate % |
| Forehand | Forehand | 正手 | Forehand success rate % |
| Backhand | Backhand | 反手 | Backhand success rate % |
| FH Speed | Forehand Speed | 正手速度 | Forehand average speed km/h |
| BH Speed | Backhand Speed | 反手速度 | Backhand average speed km/h |
| Longest Rally | Longest Rally | 最长回合 | Longest rally in strokes |
| Rallies 5+ | Rallies 5+ | 超过5回合 | % of rallies lasting more than 5 strokes |
| L / C / R | Left / Center / Right | 落点分布 | Landing zone: left / center / right % |
| Deep / Shallow | Deep / Shallow | 落点深浅 | Landing zone: deep / shallow % |

### ⚠️ Critical rule: reading Deep vs Shallow from the court diagram

The landing distribution screen shows a top-down court diagram. Three horizontal percentages (left / center / right) are clustered at **one end** of the court — that end marks where the highlighted player's shots land (the opponent's side). Two vertical percentages (deep % and shallow %) appear on the **left edge** of the diagram.

**The position of the three horizontal numbers determines which vertical number is Deep:**

| Where horizontal numbers appear | Upper vertical % | Lower vertical % |
|---|---|---|
| **At the TOP** of the court diagram | Deep | Shallow |
| **At the BOTTOM** of the court diagram | Shallow | Deep |

**Why:** The diagram is oriented from the highlighted player's perspective. Shots landing near the top of the diagram go to the far (deep) end of the opponent's court.

**Do NOT infer deep/shallow from the player's name.** Always use the visual position of the horizontal numbers as ground truth. The same player may appear at the top in one screenshot and the bottom in another depending on app orientation.

**Verified example (2026-03-20 session):**
- YZ screenshot: horizontal numbers at TOP → upper vertical % = Deep
- LW screenshot: horizontal numbers at BOTTOM → lower vertical % = Deep

### ✅ Validation checks — run before writing to Notes or PDF

After extracting landing distribution for each player, verify:

1. **L + C + R sum:** Left + Center + Right must equal **98, 99, or 100**
2. **Deep + Shallow sum:** Deep + Shallow must equal **98, 99, or 100**

The app rounds each percentage independently. A sum of 98 is a normal rounding artifact — accept it without flagging. Only alert for sums **outside** the 98–100 range.

If either check fails, **stop and alert the user:**

> ⚠️ Validation failed: [Player]'s landing zone data does not sum correctly.
> - Left + Center + Right = [actual sum] (expected 98–100)
> - Deep + Shallow = [actual sum] (expected 98–100)
>
> This may be a misread. Please check the screenshot manually before continuing.

Do **not** write the row to Apple Notes or generate the PDF until the user confirms the data is correct.

### Extraction steps

1. For each player's landing distribution screenshot, identify which player is highlighted (the toggle button UI shows which is active)
2. Locate the three horizontal numbers (L/C/R) and note whether they are at the **TOP** or **BOTTOM** of the court diagram
3. Apply the visual position rule to determine which vertical number is Deep and which is Shallow
4. Note the session date (from the screenshot or user-provided)
5. Extract all values as integers (strip the % symbol)
6. Run the L+C+R and Deep+Shallow validation checks before proceeding

---

## Phase 2 – Store in Apple Notes

### Step 1: Identify players and find the right note

Each session involves exactly two players. Their codes appear as toggle buttons in the screenshots (e.g. "YZ", "XT", "JM", "LW").

1. Read the two player codes from the screenshots
2. Call `list_notes` to get all notes
3. Find the note whose name contains **both** player codes (case-insensitive). Note names follow the pattern `YZ&XT 🎾` — no spaces around `&`. Examples:
   - Players YZ + XT → **"YZ&XT 🎾"**
   - Players YZ + JM → **"YZ&JM 🎾"**
   - Players YZ + LW → **"YZ&LW 🎾"**

### Step 2: Auto-create the note if it does not exist

If no matching note is found, **automatically create a new one** — do not stop to ask the user.

**Naming rule:**
- If YZ is one of the players: `YZ&[other] 🎾` (YZ always first)
- Otherwise: alphabetical order, e.g. `AB&CD 🎾`

**Note template to use when creating — choose the header set that matches `LANG`:**

**If `LANG='cn'` (Chinese headers):**

```html
<table>
  <tr>
    <th colspan="8" style="background:#e0f0ff;">综合汇总</th>
  </tr>
  <tr>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>日期</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>整体</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>最长回合</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>5+回合%</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>正手%</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>正手速度</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>反手%</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>反手速度</b></td>
  </tr>
</table>

<table>
  <tr>
    <th colspan="13" style="background:#e0f0ff;">PLAYER_A</th>
  </tr>
  <tr>
    <td ...><b>日期</b></td>
    <td ...><b>整体</b></td>
    <td ...><b>最长回合</b></td>
    <td ...><b>5+回合%</b></td>
    <td ...><b>正手%</b></td>
    <td ...><b>正手速度</b></td>
    <td ...><b>反手%</b></td>
    <td ...><b>反手速度</b></td>
    <td ...><b>左</b></td>
    <td ...><b>中</b></td>
    <td ...><b>右</b></td>
    <td ...><b>深</b></td>
    <td ...><b>浅</b></td>
  </tr>
</table>

<table>
  <tr>
    <th colspan="13" style="background:#e0f0ff;">PLAYER_B</th>
  </tr>
  <!-- same header row as PLAYER_A -->
</table>
```

**If `LANG='en'` (English headers):**

```html
<table>
  <tr>
    <th colspan="8" style="background:#e0f0ff;">Summary</th>
  </tr>
  <tr>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>Date</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>Overall</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>Longest</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>Rallies 5+</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>FH%</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>FH Spd</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>BH%</b></td>
    <td style="valign:top;border:1px solid #ccc;padding:3px 5px;min-width:70px"><b>BH Spd</b></td>
  </tr>
</table>

<table>
  <tr>
    <th colspan="13" style="background:#e0f0ff;">PLAYER_A</th>
  </tr>
  <tr>
    <td ...><b>Date</b></td>
    <td ...><b>Overall</b></td>
    <td ...><b>Longest</b></td>
    <td ...><b>Rallies 5+</b></td>
    <td ...><b>FH%</b></td>
    <td ...><b>FH Spd</b></td>
    <td ...><b>BH%</b></td>
    <td ...><b>BH Spd</b></td>
    <td ...><b>L</b></td>
    <td ...><b>C</b></td>
    <td ...><b>R</b></td>
    <td ...><b>Deep</b></td>
    <td ...><b>Shallow</b></td>
  </tr>
</table>

<table>
  <tr>
    <th colspan="13" style="background:#e0f0ff;">PLAYER_B</th>
  </tr>
  <!-- same header row as PLAYER_A -->
</table>
```

Replace `PLAYER_A` and `PLAYER_B` with the actual player codes. If YZ is a player, add a **Heart Rate** column (`心率` for `cn` / `HR` for `en`) after the speed columns in all three tables (YZ wears an Apple Watch during training).

Create the note with `add_note`, then proceed to insert the session row.

### Step 3: Read and update the note

Call `get_note_content` to read the current note before updating.

### Note structure

Every tennis note contains three HTML tables:
- **Summary** — one row per session, overall combined stats
- **[Player A]** — per-session detailed stats for player A
- **[Player B]** — per-session detailed stats for player B

The table heading matches the player code exactly (e.g. `XT`, `YZ`, `JM`, `LW`).

**Column order (use the header text that matches `LANG`):**

| Column | `LANG='cn'` | `LANG='en'` |
|---|---|---|
| Session date | 日期 | Date |
| Overall success rate | 整体 | Overall |
| Longest rally | 最长回合 | Longest |
| Rallies 5+ pct | 5+回合% | Rallies 5+ |
| Forehand % | 正手% | FH% |
| Forehand speed | 正手速度 | FH Spd |
| Backhand % | 反手% | BH% |
| Backhand speed | 反手速度 | BH Spd |
| Heart rate (YZ only) | 心率 | HR |
| Landing left | 左 | L |
| Landing center | 中 | C |
| Landing right | 右 | R |
| Landing deep | 深 | Deep |
| Landing shallow | 浅 | Shallow |

Summary columns: date → overall → longest → rallies5+ → FH% → FH speed → BH% → BH speed (+ HR if YZ)

Per-player columns: same as summary + left → center → right → deep → shallow

### Step 4: Insert the new row

1. Locate the correct table for each section (Summary + two player tables)
2. Insert a **new `<tr>` row** — do **not** overwrite existing rows
3. Preserve all existing cell styles exactly:
   `valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"`
4. Call `update_note_content` with the full updated HTML

---

## Phase 3 – Generate PDF Reports (Desktop + Mobile)

Always generate **two PDF files** — desktop A4 and mobile. Use the bundled scripts as templates; do not rewrite from scratch.

### Quick start

```bash
# Install dependencies if needed
pip install reportlab matplotlib --break-system-packages -q

# Set LANG at the top of each script, then run:
python scripts/generate_pdf.py          # desktop A4
python scripts/generate_pdf_mobile.py  # mobile (single-column, larger fonts)
```

### Step 1: Set the language

At the top of **both** scripts, set the `LANG` variable based on the user's language (see Language selection section above):

```python
LANG = 'cn'   # or 'en'
```

This single switch controls all chart labels, axis titles, section headings, table headers, insight text, training plan items, and the output filename.

### Step 2: Update the data section

Update `DATES`, `P1_CODE`, `P1`, and `YZ` dicts with the full session history:

```python
DATES   = ["12/30", "2/10", "3/3", "3/24"]  # all session dates (MM/DD)
P1_CODE = "XT"                                # partner player code

P1 = dict(
    整体      = [89, 87, 85, 88],   # one value per session
    正手      = [90, 87, 87, 90],
    反手      = [84, 86, 71, 79],
    正手速度  = [68, 68, 69, 72],
    反手速度  = [65, 64, 67, 65],
    最长回合  = [118, 79, 58, 48],
    超过5回合 = [72, 71, 61, 63],
    落点左    = [11, 14, 17, 18],
    落点中    = [64, 67, 59, 60],
    落点右    = [24, 18, 23, 21],
    落点深    = [59, 64, 64, 62],
    落点浅    = [40, 35, 35, 37],
)
YZ = dict(
    # same structure
)
```

> Note: the dict keys remain in Chinese (they are internal field names used by both scripts). Only the output text — chart labels, section headers, insight text — changes with `LANG`.

### Font setup (do not change)

Both scripts use a **dual-font system** that ensures correct rendering for both Chinese and Latin/digit characters:

- **ReportLab** registers `DroidSansFallbackFull` as `CN` and `LiberationSans` as `LAT`/`LATB`. The `mix()` helper wraps each text run in the correct font tag automatically.
- **Matplotlib** uses `font.family = ['Liberation Sans', 'Droid Sans Fallback']` for English, `['DejaVu Sans', 'Droid Sans Fallback']` for Chinese. Do **not** pass `fontproperties=` to mixed-content labels.

Font paths (Ubuntu/Debian sandbox):
- `/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf`
- `/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf`
- `/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf`

### Output filenames

Both scripts auto-derive the date string from `DATES[-1]`. The `LANG` switch also controls the filename suffix:

| Version | LANG='cn' | LANG='en' |
|---|---|---|
| Desktop | `YZ_XT_Tennis_Report_20260324.pdf` | `YZ_XT_Tennis_Report_EN_20260324.pdf` |
| Mobile  | `YZ_XT_Tennis_Report_Mobile_20260324.pdf` | `YZ_XT_Tennis_Report_Mobile_EN_20260324.pdf` |

### Desktop vs Mobile layout

| Aspect | Desktop (`generate_pdf.py`) | Mobile (`generate_pdf_mobile.py`) |
|---|---|---|
| Margins | 20mm left/right | 10mm left/right |
| Layout | Two-column (side-by-side cards) | **Single column throughout** |
| Body font | 10pt | 12pt |
| Chart height ratio | ~0.38 | ~0.55 (taller for phone screens) |
| Summary cards | P1 and YZ side-by-side | Stacked vertically |
| Training plan | P1 and YZ side-by-side | Stacked vertically |

### Report sections (same order for both versions)

1. Header + subtitle (training period, session count, goal)
2. Latest session summary cards (one per player)
3. Charts:
   - Forehand & Backhand success rate trends (line chart; reference lines at FH 90%, BH 85%)
   - Shot speed trends
   - Rally stability trends (dual Y-axis: Rallies 5+% and Longest Rally)
   - Landing zone distribution — P1 (bar charts: L/C/R and Deep/Shallow; values labelled on bars)
   - Landing zone distribution — YZ
   - Performance radar chart (latest session only)
4. Full training data tables (P1 and YZ; backhand < 82% highlighted in red)
5. Analysis & Insights (per-player observations + shared trends)
6. Training recommendations (prioritised, per player)
7. Footer

### Analysis guidelines

Focus on the training goal: **improve forehand and backhand stability**. Key patterns to surface:

- **Speed vs stability tradeoff:** if success rate drops while speed rises, flag it immediately
- **Backhand threshold:** rates below 82–85% warrant a warning
- **Landing drift:** if one zone exceeds ~20% consistently, suggest targeted drills
- **Rally decline:** drop in Rallies 5+% or Longest Rally is a shared signal — note together
- **YZ forehand** is the benchmark: high speed + high stability maintained simultaneously

Always refer to players by their codes (e.g. `XT`, `YZ`) — never infer or use Chinese names.

### Step 3: Present both files

After generating, share both PDFs with the user:

```python
present_files([
    {"file_path": ".../YZ_XT_Tennis_Report_20260324.pdf"},
    {"file_path": ".../YZ_XT_Tennis_Report_Mobile_20260324.pdf"},
])
```

---

## Error checklist

| Symptom | Fix |
|---|---|
| Numbers missing or garbled in PDF | Ensure `mix()` wraps all `Paragraph()` text; confirm `LAT` font is registered |
| `got multiple values for keyword argument 'fontSize'` | Use defaults-dict pattern in `sty()`: `defaults = dict(...); defaults.update(kw); return ParagraphStyle(name, **defaults)` |
| CJK characters missing from charts | Use `font.family = ['DejaVu Sans', 'Droid Sans Fallback']` in rcParams; do not use `fontproperties=prop` on mixed-content labels |
| Deep/Shallow values look reversed | Re-check the critical rule: are the horizontal L/C/R numbers at TOP or BOTTOM of the court diagram? |
| Validation sum outside 98–100 | Stop and alert the user with the actual sum values; a sum of exactly 98 is normal and should be accepted silently |
| PDF filename missing date | Confirm `DATES` includes the current session date; `date_to_filestr(DATES[-1])` auto-derives the filename suffix |

---

## Player context (for insight generation)

- **P1 / partner** – typically sacrifices backhand stability when chasing speed. Landing distribution may drift left over time. Deep zone control has been improving.
- **YZ** – very stable forehand (consistently ~90%+). Backhand slightly more volatile. Landing tends to cluster in the center zone — angle variation is a useful drill focus.
- **Shared** – Longest Rally and Rallies 5+% often decline together across sessions, signalling a need for dedicated multi-shot rally drills.
