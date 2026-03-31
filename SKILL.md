---
name: tennis-report
description: >
  Use this skill whenever the user wants to: (1) extract tennis training data
  from app screenshots and save it to Apple Notes, (2) update existing training
  records, or (3) generate a Chinese PDF training report with charts and analysis.

  Trigger on any of these cues: tennis training / 网球训练, screenshots from a
  swing sensor app (Swing Vision, SwingVision, 挥拍), "提取数据", "更新note",
  "生成报告", "训练报告", "网球PDF", landing distribution / 落点分布, forehand /
  backhand success rate / 正反手成功率. Trigger even when only one part of the
  workflow is requested (e.g. "just extract the data" or "only generate the PDF").
---

# Tennis Training Report Skill

## Overview

This skill handles a three-phase workflow. Each phase can be run independently or all together:

1. **Extract** – read numerical data from tennis app screenshots
2. **Update Apple Notes** – persist the data in a structured HTML table note
3. **Generate PDF** – produce two Chinese-language PDF reports (desktop + mobile)

---

## Phase 1 – Data Extraction from Screenshots

### What data to look for

The screenshots come from a swing-sensor tennis app (e.g. Swing Vision). Each session screen typically shows two views, toggled by a player button. Key metrics:

| Field | Chinese label | Notes |
|---|---|---|
| 整体成功率 | 整体 | Overall success % |
| 正手成功率 | 正手 | Forehand success % |
| 反手成功率 | 反手 | Backhand success % |
| 正手速度 | 正手速度 | Forehand avg speed km/h |
| 反手速度 | 反手速度 | Backhand avg speed km/h |
| 最长回合 | 最长回合 | Longest rally (strokes) |
| 超过5回合 | 超过5回合 | % rallies > 5 strokes |
| 落点左/中/右 | 落点分布 | Landing zone: left / center / right % |
| 落点深/浅 | 落点深浅 | Landing zone: deep / shallow % |

### ⚠️ Critical rule: reading deep vs shallow from the court diagram

The landing distribution screen shows a top-down court diagram. Three horizontal percentage numbers (left / center / right) appear clustered at **one end** of the court — this marks where that player's shots land (their **opponent's** side). Two vertical numbers (deep % and shallow %) appear on the **left side** of the diagram.

**The position of the three horizontal numbers tells you which vertical number is 深区:**

| Where horizontal numbers appear | Upper vertical % | Lower vertical % |
|---|---|---|
| **At the TOP** of the court diagram | 深区 (deep) | 浅区 (shallow) |
| **At the BOTTOM** of the court diagram | 浅区 (shallow) | 深区 (deep) |

**Why:** The court diagram is oriented from the highlighted player's perspective. When their shots land near the top of the diagram, that's the far (deep) end of the opponent's court.

**Do NOT rely on the player's name to infer deep vs shallow.** Always use the visual position of the horizontal numbers as the ground truth. The same player may appear at the top in one screenshot and the bottom in another depending on app orientation.

**Verified example (2026-03-20 session):**
- YZ screenshot: horizontal numbers at TOP → upper vertical % = 深区
- LW screenshot: horizontal numbers at BOTTOM → lower vertical % = 深区

### ✅ Validation checks — run before writing to note or PDF

After extracting landing distribution data for each player, verify:

1. **左/中/右 sum check:** 落点左 + 落点中 + 落点右 must equal **98, 99, or 100**.
2. **深/浅 sum check:** 落点深 + 落点浅 must equal **98, 99, or 100**.

The app rounds each percentage independently, so a sum of 98 is a normal rounding artifact — accept it as-is without asking the user to correct it. Only flag sums outside the 98–100 range.

If either check falls **outside** 98–100, **stop and alert the user before proceeding:**

> ⚠️ 数据校验失败：[玩家名] 的落点数据加和异常
> - 落点左 + 落点中 + 落点右 = [实际加和]（期望 98–100）
> - 落点深 + 落点浅 = [实际加和]（期望 98–100）
>
> 可能是图像识别错误，请人工核查截图后再继续。

Do **not** write the row to Apple Notes or generate the PDF until the user confirms the data is correct.

### Extraction approach

1. For each player's landing distribution screenshot, identify which player is highlighted (the button UI shows which is active)
2. Locate the three horizontal numbers (left/center/right) and note whether they are at the **TOP** or **BOTTOM** of the court diagram
3. Use the visual position rule above to determine which vertical number is 深区 and which is 浅区
4. Note the date of the session (shown on the screenshot or provided by the user)
5. Extract all numeric values; record as integers (drop the % symbol)
6. Run the validation checks on 左+中+右 and 深+浅 sums — alert user and stop if either fails (98 is acceptable, do not flag it)

---

## Phase 2 – Update Apple Notes

### Step 1: Identify the players and find the right note

Each session involves exactly two players. Their codes appear as toggle buttons in the app screenshots (e.g. "YZ", "XT", "JM", "LW").

**How to identify the note to update:**

1. From the screenshots, read the two player codes shown in the session (the player toggle UI).
2. Call `list_notes` to get all notes.
3. Find the note whose name contains **both** player codes (case-insensitive). Note names use no spaces around `&`. Examples:
   - Players YZ + XT → note **"YZ&XT 🎾"**
   - Players YZ + JM → note **"YZ&JM 🎾"**
   - Players YZ + LW → note **"YZ&LW 🎾"**
4. If no note matches, alert the user before proceeding.

### Step 2: Read and update the note

Use `get_note_content` to read the current note before updating.

### Note structure

Every tennis note contains three HTML tables:
- **综合** — one row per session, overall stats for both players combined
- **[Player A code]** — per-session detailed stats for player A
- **[Player B code]** — per-session detailed stats for player B

The table heading text matches the player code exactly (e.g. `XT`, `YZ`, `JM`, `LW`). Use this to locate the right table.

**Column order (all three tables):**

综合: `日期 | 整体 | 最长回合 | 超过5回合 | 正手 | 正手速度 | 反手 | 反手速度`

Per-player tables: same columns plus `落点左 | 落点中 | 落点右 | 落点深 | 落点浅`

### Step 3: Insert the new row

1. Find the correct table for each section (综合 + two player tables)
2. Insert a **new `<tr>` row** for the new session — do **not** overwrite existing rows
3. Preserve all existing cell styles exactly: `valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"`
4. Use `update_note_content` with the full updated HTML

---

## Phase 3 – Generate Chinese PDF Reports (Desktop + Mobile)

Always generate **two PDF files** — one optimized for desktop/print and one for mobile reading. Use the bundled scripts as starting templates; do not start from scratch.

### Quick start

```bash
# Install dependencies if needed
pip install reportlab matplotlib --break-system-packages -q

# Edit the DATA section at the top of each script, then run both:
python scripts/generate_pdf_cn.py       # desktop version
python scripts/generate_pdf_mobile.py  # mobile version
```

### Data section to update (same for both scripts)

At the top of each script, update the `DATES`, `XT`, and `YZ` dicts with all historical session data:

```python
DATES = ["12/30", "2/10", "3/3"]   # add new dates here
XT = dict(
    整体      = [89, 87, 85],      # one value per session
    正手      = [90, 87, 87],
    # ... etc
)
```

### Font setup (do not change)

Both scripts use a **dual-font approach** that fixes the "numbers don't render" problem:

- **ReportLab** – registers `LiberationSans` (Latin/digits) as `LAT` and `DroidSansFallbackFull` (CJK) as `CN`. The `mix()` helper function automatically wraps each run of text in the correct `<font name="...">` tag.
- **Matplotlib** – sets `font.family = ['DejaVu Sans', 'Droid Sans Fallback']` as a fallback chain; DejaVu handles ASCII/numbers, Droid handles CJK. Do **not** pass `fontproperties=prop` to mixed-content labels — let the fallback chain work automatically.

Font paths (Ubuntu/Debian VM):
- `/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf`
- `/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf`

### Output file naming

Both filenames include the **date of the latest training session** (`YYYYMMDD`):

- Desktop: `<playerA>_<playerB>_网球训练报告_<YYYYMMDD>.pdf`
- Mobile:  `<playerA>_<playerB>_网球训练报告_手机版_<YYYYMMDD>.pdf`

Example for a 3/24 session: `YZ_XT_网球训练报告_20260324.pdf` and `YZ_XT_网球训练报告_手机版_20260324.pdf`

The scripts derive the date string automatically from `DATES[-1]` using the bundled `date_to_filestr()` helper. The session root and output directory are also auto-detected from `__file__`, so no manual path editing is needed. The **PDF title** (the large headline at the top of the report) also includes the Chinese date: `🎾  YZ & XT  网球训练报告  ·  2026年3月24日`.

### Desktop vs Mobile layout differences

The mobile version (`generate_pdf_mobile.py`) is adapted from the desktop script with these changes:

| Aspect | Desktop | Mobile |
|---|---|---|
| Margins | 20mm left/right | 10mm left/right |
| Layout | Two-column (side-by-side) | **Single column throughout** |
| Body font size | 10pt | 12pt |
| Chart height ratio | ~0.38 | ~0.55 (taller = easier to read on phone) |
| Summary cards | XT and YZ side-by-side | Stacked vertically |
| Training plan | XT and YZ side-by-side | Stacked vertically |
| Data table font | 8.5pt | 10pt |

The analysis text, insights, and recommendations are the same in both versions.

**When adapting the mobile script**, the main changes are:
- Set `leftMargin=rightMargin=10*mm`
- Replace all `Table([[xt_card, yz_card]], colWidths=[half, half])` with `[xt_card, Spacer(1,8), yz_card]` (vertical stack in the story)
- Increase `h_ratio` in `img()` calls from 0.38/0.34/0.44 to 0.55/0.50/0.60
- Increase base font sizes in `sty()` defaults and specific styles

### Step 4: Present both files

After generating both PDFs, use `present_files` to share both with the user:

```python
# present_files([
#   {"file_path": ".../YZ_XT_网球训练报告.pdf"},
#   {"file_path": ".../YZ_XT_网球训练报告_手机版.pdf"},
# ])
```

### Report sections (in order, same for both versions)

1. Header + subtitle (training period, session count, goal)
2. Summary cards (latest metrics for each player)
3. Charts:
   - 正手 & 反手成功率趋势 (line chart, with target reference lines: forehand 90%, backhand 85%)
   - 击球速度趋势
   - 回合稳定性趋势 (dual Y-axis: 超过5回合 % and 最长回合)
   - 落点分布 XT (bar charts: left/center/right and deep/shallow; numeric label on top of every bar)
   - 落点分布 YZ
   - 综合雷达图 (radar, latest session only)
4. 完整训练数据 (tables for XT and YZ; highlight backhand < 82% in red)
5. 数据分析 & Insights (per-player observations + shared trends)
6. 训练建议 (prioritized training recommendations per player)
7. Footer

### Analysis guidelines

When writing insights, focus on the user's stated goal: **增强正手和反手的稳定性** (improve forehand and backhand stability). Key patterns to surface:

- Speed vs stability tradeoff: if success rate drops while speed rises, flag it immediately
- Backhand is typically the weaker stroke — watch for rates below 82–85%
- Landing distribution drift (e.g. left-zone creep for XT) = actionable drill suggestion
- Rally decline (超过5回合 %, 最长回合) is a shared indicator worth noting together
- YZ forehand is the gold standard example: high speed + high stability

Always use **XT** and **YZ** (not inferred Chinese names) throughout the report.

---

## Player context

- **XT** – tends to sacrifice backhand stability when chasing speed. Landing distribution drifts left over time. Deep zone control has been improving.
- **YZ** – very stable forehand (consistent ~90%+). Backhand slightly more volatile. Landing tends to cluster in center — could use more angle variation.
- **Shared** – longest rally and 5+ rally % are both declining across sessions, suggesting a need for dedicated multi-ball stability drills.

---

## Error checklist

| Symptom | Fix |
|---|---|
| Numbers missing in PDF | Ensure `mix()` is applied to all `Paragraph()` calls; check LAT font is registered |
| `got multiple values for keyword argument 'fontSize'` | Use defaults-dict pattern in `sty()`: `defaults = dict(...); defaults.update(kw); return ParagraphStyle(name, **defaults)` |
| CJK missing from matplotlib charts | Use `font.family = ['DejaVu Sans', 'Droid Sans Fallback']` in rcParams; do not use `fontproperties=prop` on mixed labels |
| 深/浅 looks reversed | Re-read the critical rule: check whether horizontal numbers are at TOP or BOTTOM of court diagram |
| Validation sum outside 98–100 | Stop and flag to user — sums of 98 are normal rounding and should be accepted automatically |
| PDF filename missing date | `date_to_filestr(DATES[-1])` derives the date from the last entry in `DATES`. Ensure `DATES` is updated with the current session date before running the script |
