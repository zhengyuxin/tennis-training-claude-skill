# 🎾 Tennis Training Claude Skill — SwingVision × Claude Cowork

**[English](#english) | [中文](#中文)**

---

<a name="english"></a>
## English

A [Claude Cowork](https://claude.ai) skill that turns **SwingVision** screenshots into structured training records, trend charts, and PDF coaching reports — entirely through conversation, no code required.

### What it does

| Phase | Description |
|---|---|
| **1. Extract** | Read SwingVision session screenshots → pull out all metrics (FH/BH success rate, swing speed, rally stats, landing zones, Apple Watch heart rate) |
| **2. Store** | Write data into a structured Apple Notes table, one row per session, one note per player pair. Auto-creates the note if it doesn't exist yet. |
| **3. Report** | Generate a Chinese PDF training report (desktop + mobile) with trend charts, landing zone distribution, radar chart, and written coaching analysis |

### Install

```bash
# Clone the repo
git clone https://github.com/zhengyuxin/tennis-training-claude-skill.git

# Copy the skill folder into Claude's skills directory (Mac)
mkdir -p ~/.claude/skills
cp -r tennis-training-claude-skill ~/.claude/skills/tennis-training-claude-skill
```

Restart Claude Cowork — the skill loads automatically.

### Usage

Just talk to Claude in Cowork mode:

```
"Extract data from these SwingVision screenshots and update the note"
"Generate a training report for YZ and XT"
"Generate both desktop and mobile PDF reports based on the data in notes"
```

### Requirements

| Requirement | Notes |
|---|---|
| Claude desktop (Cowork mode) | Required |
| SwingVision app (iOS) | Required for data capture |
| Apple Notes MCP | Required for persistent storage |
| Python 3 | Required for PDF generation |
| `pip install reportlab matplotlib` | Auto-installed on first run |

### How the data extraction works

SwingVision shows a top-down court diagram with landing zone percentages. Reading deep vs. shallow correctly requires knowing the diagram orientation:

| Horizontal numbers position | Upper vertical % | Lower vertical % |
|---|---|---|
| At the **top** of court | Deep zone | Shallow zone |
| At the **bottom** of court | Shallow zone | Deep zone |

The skill encodes this rule explicitly and runs three validation checks on every extraction:
1. Left + Center + Right must sum to 98–100
2. Deep + Shallow must sum to 98–100
3. Deep zone should be **greater than** Shallow zone (sanity check for normal baseline play)

### Report contents

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

### Apple Notes structure

The skill creates one note per player pair, named `[PlayerA]&[PlayerB] 🎾` (e.g. `YZ&XT 🎾`). Each note contains three HTML tables:

- **综合** (combined) — overall stats for both players
- **[Player A]** — per-session detailed stats
- **[Player B]** — per-session detailed stats

If YZ is one of the players, YZ's table includes an extra **心率 (heart rate)** column for Apple Watch data.

### Files

```
tennis-training-claude-skill/
├── SKILL.md                     ← Core skill instructions (Claude reads this)
├── README.md                    ← This file
└── scripts/
    ├── generate_pdf_cn.py       ← Chinese desktop PDF generator (A4)
    └── generate_pdf_mobile.py   ← Chinese mobile PDF generator (single-column)
```

### Background

This skill bridges two generations of AI:

- **Generation 1 (Computer Vision)** — SwingVision tracks ball trajectories, counts strokes, measures speed, and maps landing zones from live video
- **Generation 2 (LLM)** — Claude reads those numbers, reasons across sessions, writes coaching analysis, and generates structured reports

Read the full write-up: *[Medium article — coming soon]*

### License

MIT — use freely, adapt to your own players and training goals.

---

<a name="中文"></a>
## 中文

一个 [Claude Cowork](https://claude.ai) skill，将 **SwingVision** 的训练截图自动转化为结构化训练记录、趋势图表和 PDF 训练报告——全程对话驱动，无需写任何代码。

### 功能概览

| 阶段 | 说明 |
|---|---|
| **1. 提取** | 读取 SwingVision 截图 → 提取全部数据（正反手成功率、击球速度、回合数据、落点分布、Apple Watch 心率） |
| **2. 存储** | 写入结构化 Apple Notes 表格，每次训练一行，每对球员一个 Note。如 Note 不存在则自动新建。 |
| **3. 报告** | 生成中文 PDF 训练报告（桌面版 + 手机版），包含趋势图、落点分布图、雷达图及文字分析 |

### 安装

```bash
# 克隆仓库
git clone https://github.com/zhengyuxin/tennis-training-claude-skill.git

# 将 skill 文件夹复制到 Claude skills 目录（Mac）
mkdir -p ~/.claude/skills
cp -r tennis-training-claude-skill ~/.claude/skills/tennis-training-claude-skill
```

重启 Claude Cowork，skill 会自动加载。

### 使用方式

在 Cowork 模式下直接告诉 Claude：

```
"从这些 SwingVision 截图中提取数据并更新 Notes"
"基于 Notes 里的数据生成 YZ 和 XT 的训练报告"
"生成桌面版和手机版 PDF 报告"
```

### 环境要求

| 依赖 | 说明 |
|---|---|
| Claude 桌面版（Cowork 模式） | 必须 |
| SwingVision（iOS） | 用于训练数据采集 |
| Apple Notes MCP | 用于持久化存储数据 |
| Python 3 | 用于 PDF 生成 |
| `pip install reportlab matplotlib` | 首次运行自动安装 |

### 落点数据读取规则

SwingVision 的落点图方向根据球员视角而变化，深/浅区的判断规则如下：

| 横向数字位置 | 上方纵向 % | 下方纵向 % |
|---|---|---|
| 图表**上方** | 深区 | 浅区 |
| 图表**下方** | 浅区 | 深区 |

Skill 内置三重校验：
1. 左 + 中 + 右 加和必须为 98–100
2. 深 + 浅 加和必须为 98–100
3. 深区必须大于浅区（底线训练的正常规律）

### 报告内容

桌面版（A4）和手机版均包含：

1. **数据卡片** — 最新一场各项指标及与首次训练的对比
2. **正反手成功率趋势折线图**（含目标参考线）
3. **击球速度趋势图**（km/h）
4. **回合稳定性趋势图**（双轴：超过5回合% 和最长回合）
5. **落点分布图**（左/中/右区 + 深/浅区柱状图）
6. **综合雷达图**（最新一场）
7. **完整数据表格**（反手 < 82% 标红）
8. **文字分析**——逐球员洞察 + 共同趋势
9. **训练建议**——按优先级排序

### Apple Notes 结构

每对球员对应一个 Note，命名为 `[球员A]&[球员B] 🎾`（如 `YZ&XT 🎾`），每个 Note 包含三张 HTML 表格：

- **综合** — 两人的整体数据汇总
- **[球员A]** — 球员 A 的逐场详细数据
- **[球员B]** — 球员 B 的逐场详细数据

若球员之一为 YZ，YZ 的表格额外包含**心率**列（来自 Apple Watch）。

### 文件结构

```
tennis-training-claude-skill/
├── SKILL.md                     ← Skill 核心指令文件（Claude 读取）
├── README.md                    ← 本文件
└── scripts/
    ├── generate_pdf_cn.py       ← 中文桌面版 PDF 生成脚本（A4）
    └── generate_pdf_mobile.py   ← 中文手机版 PDF 生成脚本（单栏）
```

### 背景

这个 Skill 融合了两代 AI 技术：

- **第一代 AI（计算机视觉）** — SwingVision 从实时视频中追踪球轨迹、统计击球次数、测量速度、标记落点区域
- **第二代 AI（大语言模型）** — Claude 读取这些数字，跨 session 推理分析，用自然语言写出教练级别的训练报告

完整技术文章：*[Medium 文章——即将发布]*

### 许可

MIT 开源协议，可自由使用并根据自己的球员和训练目标进行定制。
