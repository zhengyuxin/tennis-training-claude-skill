"""
generate_pdf_mobile.py — Mobile-optimized version of the tennis training report.

Key differences from generate_pdf_cn.py (desktop):
  - Single-column layout throughout (no side-by-side cards or tables)
  - Narrower margins (10mm) so content fills more of the phone screen
  - Larger fonts (body 12pt, headings scaled up proportionally)
  - Taller chart aspect ratios — easier to read on a small display
  - Summary cards and training plan stacked vertically (XT first, then YZ)

Everything else — data, analysis text, chart types, section order — is identical
to the desktop version. Keep DATA in sync with generate_pdf_cn.py.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table,
    TableStyle, HRFlowable
)
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# ── Register fonts ─────────────────────────────────────────────────────────────
FONT_PATH  = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
LATIN_PATH = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
pdfmetrics.registerFont(TTFont('CN',  FONT_PATH))
pdfmetrics.registerFont(TTFont('LAT', LATIN_PATH))

CN  = 'CN'
LAT = 'LAT'

# ── Mixed-text helper ──────────────────────────────────────────────────────────
def is_cjk(ch):
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or
            0x3400 <= cp <= 0x4DBF or
            0x20000 <= cp <= 0x2A6DF or
            0x3000 <= cp <= 0x303F or
            0x2E80 <= cp <= 0x2EFF or
            0xFF00 <= cp <= 0xFFEF or
            0xFE30 <= cp <= 0xFE4F)

def mix(text):
    if not text:
        return text
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    parts = []
    seg = ''
    cur_cjk = is_cjk(text[0]) if text else False
    for ch in text:
        ck = is_cjk(ch)
        if ck != cur_cjk:
            font = CN if cur_cjk else LAT
            parts.append(f'<font name="{font}">{seg}</font>')
            seg = ch
            cur_cjk = ck
        else:
            seg += ch
    if seg:
        font = CN if cur_cjk else LAT
        parts.append(f'<font name="{font}">{seg}</font>')
    return ''.join(parts)

# ── matplotlib font setup ──────────────────────────────────────────────────────
fm.fontManager.addfont(FONT_PATH)
prop = fm.FontProperties(fname=FONT_PATH)

plt.rcParams.update({
    'font.family': ['DejaVu Sans', 'Droid Sans Fallback'],
    'axes.unicode_minus': False,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'axes.facecolor': '#fafafa',
    'figure.facecolor': 'white',
    'axes.labelsize': 11,   # slightly larger for mobile
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
})

# ── Date helpers (keep in sync with generate_pdf_cn.py) ──────────────────────
def _parse_date(d):
    m, day = int(d.split('/')[0]), int(d.split('/')[1])
    yr = 2025 if m == 12 else 2026
    return yr, m, day

def date_to_filestr(d):
    yr, m, day = _parse_date(d)
    return f"{yr}{m:02d}{day:02d}"

def date_to_cn(d):
    yr, m, day = _parse_date(d)
    return f"{yr}年{m}月{day}日"

# ── DATA — keep in sync with generate_pdf_cn.py ───────────────────────────────
DATES = ["12/30", "2/10", "3/3"]
XT = dict(
    整体      = [89, 87, 85],
    正手      = [90, 87, 87],
    反手      = [84, 86, 71],
    正手速度  = [68, 68, 69],
    反手速度  = [65, 64, 67],
    最长回合  = [118, 79, 58],
    超过5回合 = [72, 71, 61],
    落点左    = [11, 14, 17],
    落点中    = [64, 67, 59],
    落点右    = [24, 18, 23],
    落点深    = [59, 64, 64],
    落点浅    = [40, 35, 35],
)
YZ = dict(
    整体      = [91, 90, 90],
    正手      = [93, 91, 93],
    反手      = [87, 88, 85],
    正手速度  = [66, 68, 72],
    反手速度  = [64, 66, 67],
    最长回合  = [118, 79, 58],
    超过5回合 = [72, 71, 61],
    落点左    = [8,  11, 13],
    落点中    = [70, 74, 71],
    落点右    = [19, 13, 14],
    落点深    = [53, 56, 56],
    落点浅    = [46, 43, 43],
)

BLUE   = "#3b82f6"; GREEN  = "#10b981"; RED    = "#ef4444"
AMBER  = "#f59e0b"; PURPLE = "#8b5cf6"; ORANGE = "#f97316"

import re as _re
_SESSION = _re.search(r'(/sessions/[^/]+)', __file__)
_SESSION_ROOT = _SESSION.group(1) if _SESSION else '/sessions/current'
IMG_DIR = f"{_SESSION_ROOT}/img_mobile"
os.makedirs(IMG_DIR, exist_ok=True)

# ── Charts (taller aspect ratio for mobile) ────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))  # taller than desktop
ax.plot(DATES, XT['正手'], 'o-',  color=BLUE,  lw=2.5, ms=8)
ax.plot(DATES, XT['反手'], 'o--', color=BLUE,  lw=2.5, ms=8)
ax.plot(DATES, YZ['正手'], 's-',  color=GREEN, lw=2.5, ms=8)
ax.plot(DATES, YZ['反手'], 's--', color=GREEN, lw=2.5, ms=8)
ax.axhline(90, color=BLUE,  lw=1.2, linestyle=':', alpha=0.7)
ax.axhline(85, color=AMBER, lw=1.2, linestyle=':', alpha=0.7)
n = len(DATES) - 1
ax.text(n + 0.05, 90.5, '正手目标 90%', fontsize=9, color=BLUE)
ax.text(n + 0.05, 85.5, '反手目标 85%', fontsize=9, color=AMBER)
for label, val, col, dy in [
    (f'XT 正手 {XT["正手"][-1]}%', XT['正手'][-1], BLUE,   1.5),
    (f'XT 反手 {XT["反手"][-1]}%', XT['反手'][-1], RED,   -4.0),
    (f'YZ 正手 {YZ["正手"][-1]}%', YZ['正手'][-1], GREEN,  2.8),
    (f'YZ 反手 {YZ["反手"][-1]}%', YZ['反手'][-1], "#059669",-1.5),
]:
    ax.annotate(label, xy=(n, val), xytext=(n + 0.05, val + dy),
                fontsize=9, color=col, fontweight='bold')
ax.set_ylim(62, 100)
ax.set_ylabel('成功率 (%)')
ax.set_title('正手 & 反手成功率趋势', fontsize=13, fontweight='bold', pad=12)
ax.legend(['XT 正手', 'XT 反手', 'YZ 正手', 'YZ 反手'],
          loc='lower left', framealpha=0.8, ncol=2)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_stroke.png", dpi=150, bbox_inches='tight')
plt.close()

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(DATES, XT['正手速度'], 'o-',  color=BLUE,  lw=2.5, ms=8)
ax.plot(DATES, XT['反手速度'], 'o--', color=BLUE,  lw=2.5, ms=8)
ax.plot(DATES, YZ['正手速度'], 's-',  color=GREEN, lw=2.5, ms=8)
ax.plot(DATES, YZ['反手速度'], 's--', color=GREEN, lw=2.5, ms=8)
ax.set_ylim(58, max(max(YZ['正手速度']), max(XT['正手速度'])) + 6)
ax.set_ylabel('速度 (km/h)')
ax.set_title('击球速度趋势', fontsize=13, fontweight='bold', pad=12)
ax.legend(['XT 正手速度', 'XT 反手速度', 'YZ 正手速度', 'YZ 反手速度'],
          loc='upper left', framealpha=0.8, ncol=2)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_speed.png", dpi=150, bbox_inches='tight')
plt.close()

fig, ax1 = plt.subplots(figsize=(8, 4.5))
ax2 = ax1.twinx()
ln1 = ax1.plot(DATES, XT['超过5回合'], 'D-', color=PURPLE, lw=2.5, ms=8, label='超过5回合 (%)')
ax1.axhline(70, color=PURPLE, lw=1, linestyle=':', alpha=0.6)
ax1.text(0.02, 71, '目标 70%', fontsize=9, color=PURPLE)
ln2 = ax2.plot(DATES, XT['最长回合'], 'P--', color=ORANGE, lw=2.5, ms=9, label='最长回合')
ax1.set_ylabel('超过5回合 (%)', color=PURPLE)
ax2.set_ylabel('最长回合 (球数)', color=ORANGE)
ax1.set_ylim(50, 85); ax2.set_ylim(40, 135)
ax1.tick_params(axis='y', labelcolor=PURPLE)
ax2.tick_params(axis='y', labelcolor=ORANGE)
ax1.legend(ln1 + ln2, ['超过5回合 (%)', '最长回合'], loc='upper right', framealpha=0.8)
ax1.set_title('回合稳定性趋势（双方共用）', fontsize=13, fontweight='bold', pad=12)
ax1.spines['top'].set_visible(False); ax2.spines['top'].set_visible(False)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_rally.png", dpi=150, bbox_inches='tight')
plt.close()

def landing_chart(data, name, color_set, fname):
    fig, (ax_lr, ax_ds) = plt.subplots(2, 1, figsize=(8, 8))  # stacked vertically for mobile
    bw = 0.25; xi = np.arange(len(DATES))
    c1, c2, c3 = color_set
    b1 = ax_lr.bar(xi-bw, data['落点左'], bw, label='左区', color=c1, alpha=0.85)
    b2 = ax_lr.bar(xi,    data['落点中'], bw, label='中区', color=c2, alpha=0.85)
    b3 = ax_lr.bar(xi+bw, data['落点右'], bw, label='右区', color=c3, alpha=0.85)
    for b in (b1, b2, b3):
        ax_lr.bar_label(b, fmt='%d', fontsize=8, padding=2)
    ax_lr.set_xticks(xi); ax_lr.set_xticklabels(DATES)
    ax_lr.set_ylabel('%'); ax_lr.set_ylim(0, 100)
    ax_lr.set_title(f'{name} – 左/中/右区', fontsize=12, fontweight='bold')
    ax_lr.legend(fontsize=10)
    b4 = ax_ds.bar(xi-bw/2, data['落点深'], bw*1.2, label='深区', color=c2, alpha=0.85)
    b5 = ax_ds.bar(xi+bw/2, data['落点浅'], bw*1.2, label='浅区', color=c1, alpha=0.5)
    for b in (b4, b5):
        ax_ds.bar_label(b, fmt='%d', fontsize=8, padding=2)
    ax_ds.set_xticks(xi); ax_ds.set_xticklabels(DATES)
    ax_ds.set_ylabel('%'); ax_ds.set_ylim(0, 95)
    ax_ds.set_title(f'{name} – 深/浅区', fontsize=12, fontweight='bold')
    ax_ds.legend(fontsize=10)
    plt.tight_layout(pad=2.5)
    plt.savefig(f"{IMG_DIR}/{fname}", dpi=150, bbox_inches='tight')
    plt.close()

landing_chart(XT, 'XT', ['#93c5fd','#2563eb','#1e3a8a'], 'chart_xt_land.png')
landing_chart(YZ, 'YZ', ['#6ee7b7','#059669','#064e3b'], 'chart_yz_land.png')

categories = ['正手稳定', '反手稳定', '整体成功', '回合稳定', '落点深区', '中区精准']
xt_vals = [XT['正手'][-1], XT['反手'][-1], XT['整体'][-1],
           XT['超过5回合'][-1], XT['落点深'][-1], XT['落点中'][-1]]
yz_vals = [YZ['正手'][-1], YZ['反手'][-1], YZ['整体'][-1],
           YZ['超过5回合'][-1], YZ['落点深'][-1], YZ['落点中'][-1]]
N = len(categories)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist(); angles += angles[:1]
def pad(v): return v + v[:1]

fig, (ra, rb) = plt.subplots(1, 2, figsize=(9, 5), subplot_kw=dict(polar=True))
for ax, vals, col, nm in [(ra, xt_vals, BLUE, 'XT'), (rb, yz_vals, GREEN, 'YZ')]:
    ax.plot(angles, pad(vals), 'o-', color=col, lw=2)
    ax.fill(angles, pad(vals), color=col, alpha=0.2)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(categories, size=10)
    ax.set_ylim(0, 100); ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25','50','75','100'], size=8, color='gray')
    ax.set_title(nm, fontsize=14, fontweight='bold', pad=22, color=col)
    ax.grid(color='gray', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_radar.png", dpi=150, bbox_inches='tight')
plt.close()

print("手机版图表生成完成。")

# ══════════════════════════════════════════════════════════════════════════════
# PDF Assembly — Mobile layout (single column, larger fonts)
# ══════════════════════════════════════════════════════════════════════════════
_PLAYERS = "YZ_XT"  # update if player pair changes
_DATE_STR = date_to_filestr(DATES[-1])
OUT = f"{_SESSION_ROOT}/mnt/outputs/{_PLAYERS}_网球训练报告_手机版_{_DATE_STR}.pdf"
os.makedirs(f"{_SESSION_ROOT}/mnt/outputs", exist_ok=True)

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=10*mm, rightMargin=10*mm,   # narrower margins → more content width
    topMargin=15*mm, bottomMargin=15*mm,
    title=f"YZ & XT 网球训练报告（手机版）· {date_to_cn(DATES[-1])}",
)

W = A4[0] - 20*mm   # wider content area than desktop (190mm vs 170mm)

def H(c): return HexColor(c)

def sty(name, **kw):
    # Base font size 12pt (vs 10pt desktop) for comfortable phone reading
    defaults = dict(fontName=CN, fontSize=12, leading=19, textColor=H('#374151'))
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

title_sty = sty('t1', fontSize=22, textColor=H('#111827'), spaceAfter=5)
sub_sty   = sty('t2', fontSize=10, textColor=H('#9ca3af'), spaceAfter=16)
h2_sty    = sty('h2', fontSize=16, textColor=H('#1f2937'), spaceBefore=18, spaceAfter=8)
h3_sty    = sty('h3', fontSize=13, textColor=H('#374151'), spaceBefore=12, spaceAfter=5)
cap_sty   = sty('cap', fontSize=9, textColor=H('#9ca3af'), spaceAfter=10, alignment=TA_CENTER)
body_sty  = sty('body', fontSize=12, leading=20, spaceAfter=7)
foot_sty  = sty('ft',   fontSize=8,  textColor=H('#9ca3af'), alignment=TA_CENTER)

def rule(color='#e5e7eb', t=0.5):
    return HRFlowable(width='100%', thickness=t, color=H(color), spaceAfter=7, spaceBefore=7)

def img(path, h_ratio=0.55):
    # Taller ratio than desktop (0.55 vs 0.38) — charts fill more vertical space
    return Image(path, width=W, height=W * h_ratio)

def P(text, style, **kw):
    return Paragraph(mix(text), style)

def Pcap(text):
    return P(text, cap_sty)

# ── Single-column summary card ────────────────────────────────────────────────
def summary_card_single(metrics, bg_h, title, tc):
    """Full-width summary card for one player."""
    rows = [[P(title, sty('ct', fontSize=13, textColor=H(tc), alignment=TA_CENTER)), '', '', '']]
    for m in metrics:
        rows.append([
            P(m[0], sty('ml', fontSize=10, textColor=H('#6b7280'), alignment=TA_CENTER)),
            P(m[1], sty('mv', fontSize=17, textColor=H(m[4]),      alignment=TA_CENTER)),
            P(m[2], sty('ms', fontSize=9,  textColor=H('#9ca3af'), alignment=TA_CENTER)),
            '',
        ])
    cw = [W/4] * 4
    t = Table(rows, colWidths=cw)
    t.setStyle(TableStyle([
        ('SPAN',          (0,0),(3,0)),
        ('BACKGROUND',    (0,0),(3,0), H(bg_h)),
        ('ROWBACKGROUNDS',(0,1),(3,-1), [H('#fafafa'), H('#ffffff')] * 4),
        ('BOX',           (0,0),(-1,-1), 0.5, H('#e5e7eb')),
        ('INNERGRID',     (0,0),(-1,-1), 0.25, H('#e5e7eb')),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    return t

def summary_section(xt_latest, yz_latest):
    xt_m = [
        ('正手成功率', f'{xt_latest["正手"]}%',    f'↕ vs 首次 {XT["正手"][0]}%',   '#eff6ff', '#1d4ed8'),
        ('反手成功率', f'{xt_latest["反手"]}%',    '⚠ 注意稳定性',                  '#fef2f2', '#dc2626'),
        ('正手速度',   f'{xt_latest["正手速度"]} km/h', f'首次 {XT["正手速度"][0]} km/h', '#f0fdf4', '#15803d'),
        ('反手速度',   f'{xt_latest["反手速度"]} km/h', f'首次 {XT["反手速度"][0]} km/h', '#f0fdf4', '#15803d'),
    ]
    yz_m = [
        ('正手成功率', f'{yz_latest["正手"]}%',    '保持高位 ✓',                    '#f0fdf4', '#15803d'),
        ('反手成功率', f'{yz_latest["反手"]}%',    f'↕ vs 首次 {YZ["反手"][0]}%',   '#fffbeb', '#b45309'),
        ('正手速度',   f'{yz_latest["正手速度"]} km/h', f'首次 {YZ["正手速度"][0]} km/h', '#f0fdf4', '#15803d'),
        ('反手速度',   f'{yz_latest["反手速度"]} km/h', f'首次 {YZ["反手速度"][0]} km/h', '#f0fdf4', '#15803d'),
    ]
    date_label = DATES[-1]
    xt_card = summary_card_single(xt_m, '#dbeafe', f'XT · 最新数据 {date_label}', '#1d4ed8')
    yz_card = summary_card_single(yz_m, '#d1fae5', f'YZ · 最新数据 {date_label}', '#065f46')
    # Return as a list so caller can use extend() — cards stacked vertically
    return [xt_card, Spacer(1, 8), yz_card]

# ── Data tables (single column, slightly larger font) ─────────────────────────
def data_tables():
    hdr = ['日期','整体','最长\n回合','超5\n回合','正手','正手\n速度','反手','反手\n速度']
    cw  = [24*mm, 18*mm, 20*mm, 18*mm, 16*mm, 22*mm, 16*mm, 22*mm]

    def build(src, bg):
        rows = []
        for i, d in enumerate(DATES):
            rows.append([d,
                f"{src['整体'][i]}%",
                str(src['最长回合'][i]),
                f"{src['超过5回合'][i]}%",
                f"{src['正手'][i]}%",
                f"{src['正手速度'][i]} km/h",
                f"{src['反手'][i]}%",
                f"{src['反手速度'][i]} km/h"])
        data = [hdr] + rows
        p = []
        for ri, row in enumerate(data):
            pr = []
            for ci, cell in enumerate(row):
                is_bad = (ri > 0 and ci == 6 and
                          int(cell.replace('%','').replace(' km/h','')) < 82)
                tc = H('#dc2626') if is_bad else (white if ri == 0 else H('#374151'))
                s = sty('td', fontSize=10, alignment=TA_CENTER, textColor=tc)
                pr.append(P(cell, s))
            p.append(pr)
        t = Table(p, colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,0), H(bg)),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[H('#f9fafb'), white]),
            ('BOX',           (0,0),(-1,-1), 0.5, H('#d1d5db')),
            ('INNERGRID',     (0,0),(-1,-1), 0.25, H('#e5e7eb')),
            ('TOPPADDING',    (0,0),(-1,-1), 7),
            ('BOTTOMPADDING', (0,0),(-1,-1), 7),
            ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ]))
        return t

    return build(XT, '#2563eb'), build(YZ, '#059669')

# ── Training plan (stacked vertically) ────────────────────────────────────────
def training_plan_card(items, bg, title, tc):
    cw = [10*mm, 45*mm, W - 60*mm]
    data = [[P(title, sty('pt', fontSize=12, textColor=H(tc))), '', '']]
    for icon, ttl, desc in items:
        data.append([
            P(icon, sty('pi', fontSize=12, alignment=TA_CENTER)),
            P(ttl,  sty('ptl', fontSize=11, textColor=H(tc))),
            P(desc, sty('pd',  fontSize=10, textColor=H('#4b5563'), leading=16)),
        ])
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ('SPAN',          (0,0),(2,0)),
        ('BACKGROUND',    (0,0),(2,0), H(bg)),
        ('ROWBACKGROUNDS',(0,1),(2,-1),[H('#f9fafb'), white]*4),
        ('BOX',           (0,0),(-1,-1), 0.5, H('#e5e7eb')),
        ('INNERGRID',     (0,0),(-1,-1), 0.25, H('#e5e7eb')),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    return t

def training_plan():
    xt_items = [
        ('🔴', '反手专项（最优先）', '将速度降至 60 km/h 以下，先求稳定再提速，目标恢复到 84%+'),
        ('🟡', '中区定点训练',       '有意识击打中区和右区，纠正落点偏漂习惯'),
        ('🟢', '多拍稳定对打',       '目标：超过5回合比例重新达到 70%+'),
        ('🔵', '正手节奏维稳',       '保持现有水平，反手恢复前不追速度'),
    ]
    yz_items = [
        ('🟡', '反手稳定性监控',     '密切关注，保持 87%+ 以上，防止重蹈 XT 覆辙'),
        ('🟢', '大角度变线训练',     '增加左区落点练习，减少落点过于集中被预判'),
        ('🔵', '正手速度可继续',     '但设置质量底线：成功率低于 90% 则降速'),
        ('🟠', '长回合共同训练',     '两人进行多拍专项练习，共同提升稳定性'),
    ]
    xt_card = training_plan_card(xt_items, '#dbeafe', 'XT · 训练重点', '#1d4ed8')
    yz_card = training_plan_card(yz_items, '#d1fae5', 'YZ · 训练重点', '#065f46')
    return [xt_card, Spacer(1, 8), yz_card]

# ── Insight helper ─────────────────────────────────────────────────────────────
def insight(icon, title, text, tc):
    full_text = f'<font color="{tc}"><b>{mix(title)}</b></font>  {mix(text)}'
    t = Table([[
        Paragraph(icon, sty('ic', fontSize=14, alignment=TA_CENTER)),
        Paragraph(full_text, sty('it', fontSize=12, leading=19)),
    ]], colWidths=[12*mm, W - 14*mm])
    t.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),3),  ('BOTTOMPADDING',(0,0),(-1,-1),3),
    ]))
    return t

def tip_box(text, bg='#fffbeb', border='#fde68a', tc='#92400e'):
    inner = Table(
        [[Paragraph(mix(text), sty('tb', fontSize=11, textColor=H(tc), leading=17))]],
        colWidths=[W - 10*mm])
    inner.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), H(bg)),
        ('BOX',(0,0),(-1,-1), 0.8, H(border)),
        ('TOPPADDING',(0,0),(-1,-1),10),
        ('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('LEFTPADDING',(0,0),(-1,-1),12),
        ('RIGHTPADDING',(0,0),(-1,-1),12),
    ]))
    return inner

# ── Build story ────────────────────────────────────────────────────────────────
xt_latest = {k: v[-1] for k, v in XT.items()}
yz_latest = {k: v[-1] for k, v in YZ.items()}
xt_tbl, yz_tbl = data_tables()
story = []

# Header
n_sessions = len(DATES)
story.append(P(f'🎾  YZ & XT  网球训练报告  ·  {date_to_cn(DATES[-1])}', title_sty))
story.append(P(
    f'训练周期：{date_to_cn(DATES[0])} — {date_to_cn(DATES[-1])}  ·  共{n_sessions}次训练  ·  目标：提升正手与反手稳定性',
    sub_sty))
story.append(rule('#3b82f6', 1.5))
story.append(Spacer(1, 6))

# Summary — stacked vertically
story.extend(summary_section(xt_latest, yz_latest))
story.append(Spacer(1, 12))

# Charts — taller h_ratio for mobile
story.append(rule())
story.append(P('一、正手 & 反手成功率趋势', h2_sty))
story.append(img(f"{IMG_DIR}/chart_stroke.png", 0.58))
story.append(Pcap('实线 = 正手  |  虚线 = 反手  |  点线 = 目标参考线'))
story.append(Spacer(1, 6))

story.append(P('二、击球速度趋势', h2_sty))
story.append(img(f"{IMG_DIR}/chart_speed.png", 0.52))
story.append(Pcap('实线 = 正手速度  |  虚线 = 反手速度'))
story.append(Spacer(1, 6))

story.append(P('三、回合稳定性趋势', h2_sty))
story.append(img(f"{IMG_DIR}/chart_rally.png", 0.52))
story.append(Pcap('紫色（左轴）= 超过5回合  |  橙色（右轴）= 最长回合'))
story.append(Spacer(1, 6))

story.append(P('四、击球落地分布', h2_sty))
story.append(img(f"{IMG_DIR}/chart_xt_land.png", 0.88))   # stacked subplot is taller
story.append(Pcap('XT 落点分布（上：左/中/右  下：深/浅）'))
story.append(img(f"{IMG_DIR}/chart_yz_land.png", 0.88))
story.append(Pcap('YZ 落点分布（上：左/中/右  下：深/浅）'))
story.append(Spacer(1, 6))

story.append(P(f'五、综合雷达图（最新 {DATES[-1]}）', h2_sty))
story.append(img(f"{IMG_DIR}/chart_radar.png", 0.52))
story.append(Pcap('基于最新一次训练数据的六维能力评估'))

# Data tables
story.append(rule())
story.append(P('六、完整训练数据', h2_sty))
story.append(P('XT', h3_sty))
story.append(xt_tbl)
story.append(Spacer(1, 10))
story.append(P('YZ', h3_sty))
story.append(yz_tbl)

# Insights
story.append(rule())
story.append(P('七、数据分析 & Insights', h2_sty))

story.append(P('XT', h3_sty))
story.append(insight('⚠️', '反手危机（最紧急）：',
    '反手成功率出现明显下滑。速度同期提升，典型的"追速牺牲稳定"现象。'
    '建议立即将反手速度降至 60 km/h 以下，重建稳定性后再提速。', '#dc2626'))
story.append(Spacer(1,5))
story.append(insight('📍', '落点分布监控：',
    '关注左区/右区偏漂趋势，如果某侧区域超过 20% 则需要专项定点练习，有意识打向中区。',
    '#d97706'))
story.append(Spacer(1,5))
story.append(insight('✅', '深区控制持续改善：',
    '深区落点比例持续提升，底线球质量在提高，继续保持。', '#15803d'))
story.append(Spacer(1,5))
story.append(insight('📉', '正手监控：',
    '正手成功率需维持在 87% 以上。在反手问题未解决期间不宜追求速度提升。', '#6b7280'))

story.append(Spacer(1, 10))
story.append(P('YZ', h3_sty))
story.append(insight('⭐', '正手堪称教科书级稳定：',
    f'正手保持 {YZ["正手"][0]}%/{YZ["正手"][1]}%/{YZ["正手"][-1]}% 高位稳定，'
    f'速度从 {YZ["正手速度"][0]} → {YZ["正手速度"][-1]} km/h 大幅提升，速度与稳定性兼顾，是两人中表现最优的指标。',
    '#15803d'))
story.append(Spacer(1,5))
story.append(insight('⚠️', '反手小幅下滑，需关注：',
    f'反手成功率从 {YZ["反手"][0]}% → {YZ["反手"][-1]}%，'
    '反手速度同步提升，趋势与 XT 早期相似，若继续追速可能触发稳定性下降，需密切观察。',
    '#b45309'))
story.append(Spacer(1,5))
story.append(insight('📍', '落点趋向中间化：',
    '中区比例持续偏高，落点过于集中容易被对手预判。建议适当加入大角度球和变线训练。',
    '#6b7280'))
story.append(Spacer(1,5))
story.append(insight('📈', '深区控制稳步提升：',
    f'深区比例 {YZ["落点深"][0]}% → {YZ["落点深"][-1]}%，底线球质量在提高。', '#2563eb'))

story.append(Spacer(1, 10))
story.append(P('共同趋势', h3_sty))
story.append(insight('📉', '长回合能力持续下降：',
    f'最长回合 {XT["最长回合"][0]} → {XT["最长回合"][-1]}；超5回合比例 {XT["超过5回合"][0]}% → {XT["超过5回合"][-1]}%。'
    '建议每次训练安排 20–30 分钟定点多拍对打专项练习。', '#dc2626'))
story.append(Spacer(1,5))
story.append(insight('⚡', '速度提升正在压迫稳定性：',
    '两人击球速度均有提升趋势，但伴随成功率下降。建议原则：先达到正手 ≥90%、反手 ≥85% 的硬指标，再逐步追求速度提升。',
    '#d97706'))
story.append(Spacer(1, 8))
story.append(tip_box(
    f'⚡ 速度与稳定性权衡参考：YZ 正手是最佳范例——{YZ["正手速度"][-1]} km/h 速度配合 {YZ["正手"][-1]}% 成功率。'
    '建议以此为标准：若速度提升但成功率低于目标值，立即降速恢复稳定性后再尝试提速。'
))

# Training plan — stacked vertically
story.append(rule())
story.append(P('八、针对稳定性目标的训练建议', h2_sty))
story.extend(training_plan())

# Footer
story.append(Spacer(1, 18))
story.append(rule('#e5e7eb', 0.5))
story.append(P(
    f'手机版报告由 Claude 生成  ·  训练周期：{date_to_cn(DATES[0])} — {date_to_cn(DATES[-1])}（共{n_sessions}次训练）',
    foot_sty))

doc.build(story)
print(f"手机版PDF已生成：{OUT}")
