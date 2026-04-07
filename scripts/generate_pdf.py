import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os, re as _re

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable,
    KeepTogether
)
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# ══════════════════════════════════════════════════════════════════════════════
# ① LANGUAGE  —  set to 'cn' (Chinese) or 'en' (English)
# ══════════════════════════════════════════════════════════════════════════════
LANG = 'cn'

# ══════════════════════════════════════════════════════════════════════════════
# ② DATA  —  update this section for each new session
# ══════════════════════════════════════════════════════════════════════════════
DATES = ["3/21", "3/28"]   # session dates  (MM/DD, Dec treated as 2025)
P1_CODE = "JM"             # partner player code

P1 = dict(
    整体      = [87, 90],
    正手      = [90, 90],
    反手      = [80, 87],
    正手速度  = [68, 71],
    反手速度  = [68, 68],
    最长回合  = [39, 54],
    超过5回合 = [72, 72],
    落点左    = [8,  8],
    落点中    = [61, 68],
    落点右    = [30, 23],
    落点深    = [68, 68],
    落点浅    = [31, 31],
)
YZ = dict(
    整体      = [86, 85],
    正手      = [87, 90],
    反手      = [79, 74],
    正手速度  = [76, 74],
    反手速度  = [71, 70],
    最长回合  = [39, 54],
    超过5回合 = [72, 72],
    落点左    = [13, 18],
    落点中    = [66, 61],
    落点右    = [19, 20],
    落点深    = [67, 68],
    落点浅    = [32, 31],
)

# ══════════════════════════════════════════════════════════════════════════════
# ③ STRINGS  —  all UI text in both languages
# ══════════════════════════════════════════════════════════════════════════════
STRINGS = {
    'cn': dict(
        report_title    = 'YZ & {p1} 网球训练报告',
        report_subtitle = '训练周期：{start} — {end}  |  共 {n} 次训练  |  目标：增强正手和反手的稳定性',
        latest_label    = '最新数据',
        s1 = '一、正手 & 反手成功率趋势',
        s2 = '二、击球速度趋势',
        s3 = '三、回合稳定性趋势',
        s4 = '四、击球落点分布',
        s5 = '五、综合雷达图（最新训练）',
        s6 = '六、完整训练数据',
        s7 = '七、数据分析 & 洞察',
        s8 = '八、针对稳定性目标的训练建议',
        chart_stroke  = '正手 & 反手成功率趋势',
        chart_speed   = '击球速度趋势',
        chart_rally   = '回合稳定性趋势（双方共用）',
        fh='正手', bh='反手',
        fh_spd='正手速度', bh_spd='反手速度',
        fh_target='正手目标 90%', bh_target='反手目标 85%',
        success_rate='成功率 (%)', speed_unit='速度 (km/h)',
        over5='超过5回合 (%)', longest='最长回合',
        longest_unit='最长回合 (球数)', target_70='目标 70%',
        left='左区', center='中区', right='右区',
        deep='深区', shallow='浅区',
        land_lr='{name} – 左/中/右区', land_ds='{name} – 深/浅区',
        fh_rate='正手成功率', bh_rate='反手成功率',
        radar_cats=['正手稳定','反手稳定','整体成功','回合稳定','落点深区','中区精准'],
        th=['日期','整体','最长回合','超5回合','正手','正手速度','反手','反手速度'],
        p1_focus='{p1} · 训练重点', yz_focus='YZ · 训练重点',
        p1_card='{p1} · {label}', yz_card='YZ · {label}',
        footer='数据来源：SwingVision  |  分析：Claude (Anthropic)  |  共 {n} 次训练记录',
        cap_stroke='实线 = 正手；虚线 = 反手；{p1} 目标 90%；反手目标 85%',
        cap_speed='实线 = 正手速度；虚线 = 反手速度',
        cap_rally='左轴：超过5回合 (%)；右轴：最长回合 (球数)',
        cap_land_p1='{p1} 落点数据（每次训练）',
        cap_land_yz='YZ 落点数据（每次训练）',
        cap_radar='最新一次训练综合雷达图',
        cap_table='反手成功率低于 82% 标红',
        date_title='{yr}年{m}月{d}日',
    ),
    'en': dict(
        report_title    = 'YZ & {p1} Tennis Training Report',
        report_subtitle = 'Period: {start} – {end}  |  Sessions: {n}  |  Goal: Forehand & Backhand Stability',
        latest_label    = 'Latest',
        s1 = '1. Forehand & Backhand Success Rate Trends',
        s2 = '2. Shot Speed Trends',
        s3 = '3. Rally Stability Trends',
        s4 = '4. Landing Zone Distribution',
        s5 = '5. Performance Radar (Latest Session)',
        s6 = '6. Full Training Data',
        s7 = '7. Analysis & Insights',
        s8 = '8. Training Recommendations',
        chart_stroke  = 'Forehand & Backhand Success Rate Trends',
        chart_speed   = 'Shot Speed Trends',
        chart_rally   = 'Rally Stability Trends (Both Players)',
        fh='FH', bh='BH',
        fh_spd='FH Speed', bh_spd='BH Speed',
        fh_target='FH target 90%', bh_target='BH target 85%',
        success_rate='Success Rate (%)', speed_unit='Speed (km/h)',
        over5='Rallies 5+ (%)', longest='Longest Rally',
        longest_unit='Longest Rally (shots)', target_70='Target 70%',
        left='Left', center='Center', right='Right',
        deep='Deep', shallow='Shallow',
        land_lr='{name} – L / C / R', land_ds='{name} – Deep / Shallow',
        fh_rate='Forehand %', bh_rate='Backhand %',
        radar_cats=['FH Stability','BH Stability','Overall','Rally Depth','Deep Zone','Center Acc.'],
        th=['Date','Overall','Longest','Rallies 5+','FH%','FH Spd','BH%','BH Spd'],
        p1_focus='{p1} — Training Focus', yz_focus='YZ — Training Focus',
        p1_card='{p1} | {label}', yz_card='YZ | {label}',
        footer='Data: SwingVision  |  Analysis: Claude (Anthropic)  |  {n} sessions recorded',
        cap_stroke='Solid = forehand, dashed = backhand  |  FH target 90%, BH target 85%',
        cap_speed='Solid = forehand speed, dashed = backhand speed',
        cap_rally='Left axis: Rallies 5+ (%)  |  Right axis: Longest rally (shots)',
        cap_land_p1='{p1} landing zone distribution per session',
        cap_land_yz='YZ landing zone distribution per session',
        cap_radar='Performance radar — most recent session',
        cap_table='Backhand % values below 82% highlighted in red',
        date_title='{m}/{d}/{yr}',
    ),
}

T = STRINGS[LANG]

# ══════════════════════════════════════════════════════════════════════════════
# ④ FONTS
# ══════════════════════════════════════════════════════════════════════════════
CJK_PATH   = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
LATIN_PATH = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
LATIN_BOLD = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'

pdfmetrics.registerFont(TTFont('CN',   CJK_PATH))
pdfmetrics.registerFont(TTFont('LAT',  LATIN_PATH))
pdfmetrics.registerFont(TTFont('LATB', LATIN_BOLD))

BODY_FONT = 'CN' if LANG == 'cn' else 'LAT'
HEAD_FONT = 'CN' if LANG == 'cn' else 'LATB'

def is_cjk(ch):
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0x20000 <= cp <= 0x2A6DF or 0x3000 <= cp <= 0x303F or
            0x2E80 <= cp <= 0x2EFF or 0xFF00 <= cp <= 0xFFEF or
            0xFE30 <= cp <= 0xFE4F)

def mix(text):
    """Wrap CJK runs in CN font, Latin/digit runs in LAT font."""
    if not text:
        return text
    if LANG == 'en':
        # Pure Latin — skip CJK detection for speed
        safe = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        return f'<font name="LAT">{safe}</font>'
    text = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    parts, seg = [], ''
    cur_cjk = is_cjk(text[0])
    for ch in text:
        ck = is_cjk(ch)
        if ck != cur_cjk:
            parts.append(f'<font name="{"CN" if cur_cjk else "LAT"}">{seg}</font>')
            seg, cur_cjk = ch, ck
        else:
            seg += ch
    if seg:
        parts.append(f'<font name="{"CN" if cur_cjk else "LAT"}">{seg}</font>')
    return ''.join(parts)

# ── matplotlib font ───────────────────────────────────────────────────────────
if LANG == 'cn':
    fm.fontManager.addfont(CJK_PATH)
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Droid Sans Fallback']
else:
    plt.rcParams['font.family'] = ['Liberation Sans', 'DejaVu Sans']

plt.rcParams.update({
    'axes.unicode_minus': False,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.3, 'grid.linestyle': '--',
    'axes.facecolor': '#fafafa', 'figure.facecolor': 'white',
    'axes.labelsize': 10, 'xtick.labelsize': 9,
    'ytick.labelsize': 9, 'legend.fontsize': 9,
})

# ══════════════════════════════════════════════════════════════════════════════
# ⑤ DATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _parse(d):
    m, day = int(d.split('/')[0]), int(d.split('/')[1])
    yr = 2025 if m == 12 else 2026
    return yr, m, day

def date_to_filestr(d):
    yr, m, day = _parse(d)
    return f"{yr}{m:02d}{day:02d}"

def date_to_label(d):
    yr, m, day = _parse(d)
    if LANG == 'cn':
        return T['date_title'].format(yr=yr, m=m, d=day)
    return T['date_title'].format(yr=yr, m=m, d=day)

def date_to_xlbl(d):
    months = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    yr, m, day = _parse(d)
    return f"{months[m]} {day}" if LANG == 'en' else d

XLABELS = [date_to_xlbl(d) for d in DATES]

# ══════════════════════════════════════════════════════════════════════════════
# ⑥ CHARTS
# ══════════════════════════════════════════════════════════════════════════════
_SESSION = _re.search(r'(/sessions/[^/]+)', __file__)
_SESSION_ROOT = _SESSION.group(1) if _SESSION else '/sessions/current'
IMG_DIR = f"{_SESSION_ROOT}/img_{LANG}"
os.makedirs(IMG_DIR, exist_ok=True)

BLUE   = "#3b82f6"; BLUE2  = "#2563eb"
GREEN  = "#10b981"; RED    = "#ef4444"
AMBER  = "#f59e0b"; PURPLE = "#8b5cf6"; ORANGE = "#f97316"
n = len(XLABELS) - 1

# Chart 1: Success rates (line trend chart for multi-session data)
# FIX: ax.text(n+0.05, ...) extends x-axis so target labels float far right.
#      Use axhline(label=...) + legend instead; set explicit xlim so the axis
#      stays snug around the actual data range.
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.plot(XLABELS, P1['正手'], 'o-',  color=BLUE,  lw=2.5, ms=7, label=f"{P1_CODE} {T['fh']}")
ax.plot(XLABELS, P1['反手'], 'o--', color=BLUE,  lw=2.5, ms=7, label=f"{P1_CODE} {T['bh']}")
ax.plot(XLABELS, YZ['正手'], 's-',  color=GREEN, lw=2.5, ms=7, label=f"YZ {T['fh']}")
ax.plot(XLABELS, YZ['反手'], 's--', color=GREEN, lw=2.5, ms=7, label=f"YZ {T['bh']}")
ax.axhline(90, color=BLUE,  lw=1.3, linestyle=':', alpha=0.7, label=T['fh_target'])
ax.axhline(85, color=AMBER, lw=1.3, linestyle=':', alpha=0.7, label=T['bh_target'])
ax.set_ylim(62, 102)
ax.set_ylabel(T['success_rate'], fontsize=10)
ax.set_title(T['chart_stroke'], fontsize=12, fontweight='bold', pad=10)
ax.legend(loc='upper right', framealpha=0.85, fontsize=9, ncol=2)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_stroke.png", dpi=150, bbox_inches='tight')
plt.close()

# Chart 2: Speed
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.plot(XLABELS, P1['正手速度'], 'o-',  color=BLUE,  lw=2.5, ms=7)
ax.plot(XLABELS, P1['反手速度'], 'o--', color=BLUE,  lw=2.5, ms=7)
ax.plot(XLABELS, YZ['正手速度'], 's-',  color=GREEN, lw=2.5, ms=7)
ax.plot(XLABELS, YZ['反手速度'], 's--', color=GREEN, lw=2.5, ms=7)
ax.set_ylim(60, 82)
ax.set_ylabel(T['speed_unit'], fontsize=10)
ax.set_title(T['chart_speed'], fontsize=12, fontweight='bold', pad=10)
ax.legend([f"{P1_CODE} {T['fh_spd']}", f"{P1_CODE} {T['bh_spd']}", f"YZ {T['fh_spd']}", f"YZ {T['bh_spd']}"],
          loc='upper left', framealpha=0.8, fontsize=9, ncol=2)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_speed.png", dpi=150, bbox_inches='tight')
plt.close()

# Chart 3: Rally stability
fig, ax1 = plt.subplots(figsize=(8, 3.2))
ax2 = ax1.twinx()
ln1 = ax1.plot(XLABELS, P1['超过5回合'], 'D-', color=PURPLE, lw=2.5, ms=7, label=T['over5'])
ax1.axhline(70, color=PURPLE, lw=1, linestyle=':', alpha=0.6)
ax1.text(0.02, 71, T['target_70'], fontsize=8, color=PURPLE)
ln2 = ax2.plot(XLABELS, P1['最长回合'], 'P--', color=ORANGE, lw=2.5, ms=8, label=T['longest'])
ax1.set_ylabel(T['over5'],       fontsize=10, color=PURPLE)
ax2.set_ylabel(T['longest_unit'], fontsize=10, color=ORANGE)
ax1.set_ylim(50, 85); ax2.set_ylim(20, 70)
ax1.tick_params(axis='y', labelcolor=PURPLE)
ax2.tick_params(axis='y', labelcolor=ORANGE)
ax1.legend(ln1+ln2, [T['over5'], T['longest']], loc='upper right', framealpha=0.8, fontsize=9)
ax1.set_title(T['chart_rally'], fontsize=12, fontweight='bold', pad=10)
ax1.spines['top'].set_visible(False); ax2.spines['top'].set_visible(False)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_rally.png", dpi=150, bbox_inches='tight')
plt.close()

# Charts 4 & 5: Landing distribution
def landing_chart(data, name, color_set, fname):
    fig, (ax_lr, ax_ds) = plt.subplots(1, 2, figsize=(8, 3.2))
    bw = 0.3; xi = np.arange(len(XLABELS))
    c1, c2, c3 = color_set
    b1 = ax_lr.bar(xi-bw, data['落点左'], bw, label=T['left'],   color=c1, alpha=0.85)
    b2 = ax_lr.bar(xi,    data['落点中'], bw, label=T['center'], color=c2, alpha=0.85)
    b3 = ax_lr.bar(xi+bw, data['落点右'], bw, label=T['right'],  color=c3, alpha=0.85)
    for b in (b1,b2,b3): ax_lr.bar_label(b, fmt='%d', fontsize=8, padding=2)
    ax_lr.set_xticks(xi); ax_lr.set_xticklabels(XLABELS)
    ax_lr.set_ylabel('%', fontsize=10)
    ax_lr.set_title(T['land_lr'].format(name=name), fontsize=10, fontweight='bold')
    ax_lr.legend(fontsize=8); ax_lr.set_ylim(0, 90)

    b4 = ax_ds.bar(xi-bw/2, data['落点深'], bw*1.2, label=T['deep'],    color=c2, alpha=0.85)
    b5 = ax_ds.bar(xi+bw/2, data['落点浅'], bw*1.2, label=T['shallow'], color=c1, alpha=0.5)
    for b in (b4,b5): ax_ds.bar_label(b, fmt='%d', fontsize=8, padding=2)
    ax_ds.set_xticks(xi); ax_ds.set_xticklabels(XLABELS)
    ax_ds.set_ylabel('%', fontsize=10)
    ax_ds.set_title(T['land_ds'].format(name=name), fontsize=10, fontweight='bold')
    ax_ds.legend(fontsize=8); ax_ds.set_ylim(0, 90)
    plt.tight_layout()
    plt.savefig(f"{IMG_DIR}/{fname}", dpi=150, bbox_inches='tight')
    plt.close()

landing_chart(P1, P1_CODE, ['#93c5fd','#2563eb','#1e3a8a'], 'chart_p1_land.png')
landing_chart(YZ, 'YZ',    ['#6ee7b7','#059669','#064e3b'], 'chart_yz_land.png')

# Chart 6: Radar
categories = T['radar_cats']
p1_vals = [P1['正手'][-1], P1['反手'][-1], P1['整体'][-1], P1['超过5回合'][-1], P1['落点深'][-1], P1['落点中'][-1]]
yz_vals = [YZ['正手'][-1], YZ['反手'][-1], YZ['整体'][-1], YZ['超过5回合'][-1], YZ['落点深'][-1], YZ['落点中'][-1]]
N = len(categories)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist(); angles += angles[:1]
def pad(v): return v + v[:1]
# FIX: figsize=(8, 4) → each polar subplot gets 4×4 → true circle.
# FIX: no bbox_inches='tight' — it trims to label bounding box and adds
#      unequal padding that distorts circles into ovals.
#      Use subplots_adjust() for spacing and save at the exact figsize.
BLUE2_R = "#1d4ed8"
fig, (ra, rb) = plt.subplots(1, 2, figsize=(8, 4), subplot_kw=dict(polar=True))
for ax, vals, col, nm in [(ra, p1_vals, BLUE2_R, P1_CODE), (rb, yz_vals, GREEN, 'YZ')]:
    ax.plot(angles, pad(vals), 'o-', color=col, lw=2.2, ms=6)
    ax.fill(angles, pad(vals), color=col, alpha=0.18)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(categories, size=9)
    ax.set_ylim(0, 100); ax.set_yticks([25,50,75,100])
    ax.set_yticklabels(['25','50','75','100'], size=7, color='#94a3b8')
    ax.set_title(nm, fontsize=13, fontweight='bold', pad=22, color=col)
    ax.grid(color='#cbd5e1', alpha=0.5)
    ax.spines['polar'].set_color('#e2e8f0')
plt.subplots_adjust(left=0.06, right=0.94, top=0.88, bottom=0.08, wspace=0.45)
plt.savefig(f"{IMG_DIR}/chart_radar.png", dpi=150)   # no bbox_inches='tight'
plt.close()

print(f"[{LANG.upper()}] All charts generated.")

# ══════════════════════════════════════════════════════════════════════════════
# ⑦ PDF ASSEMBLY
# ══════════════════════════════════════════════════════════════════════════════
_DATE_STR = date_to_filestr(DATES[-1])
_LANG_SUF = '' if LANG == 'cn' else '_EN'
OUT = f"{_SESSION_ROOT}/mnt/outputs/YZ_{P1_CODE}_Tennis_Report{_LANG_SUF}_{_DATE_STR}.pdf"
os.makedirs(f"{_SESSION_ROOT}/mnt/outputs", exist_ok=True)

_title_date = date_to_label(DATES[-1])
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm,
    title=T['report_title'].format(p1=P1_CODE),
)
W = A4[0] - 40*mm

def H(c): return HexColor(c)

def sty(name, **kw):
    defaults = dict(fontName=BODY_FONT, fontSize=10, leading=16, textColor=H('#374151'))
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

title_sty = sty('t1', fontName=HEAD_FONT, fontSize=20, textColor=H('#111827'), spaceAfter=4)
sub_sty   = sty('t2', fontSize=9,  textColor=H('#9ca3af'), spaceAfter=14)
h2_sty    = sty('h2', fontName=HEAD_FONT, fontSize=14, textColor=H('#1f2937'), spaceBefore=16, spaceAfter=6)
h3_sty    = sty('h3', fontName=HEAD_FONT, fontSize=11, textColor=H('#374151'), spaceBefore=10, spaceAfter=4)
cap_sty   = sty('cap', fontSize=8, textColor=H('#9ca3af'), spaceAfter=8, alignment=TA_CENTER)
foot_sty  = sty('ft',  fontSize=7.5, textColor=H('#9ca3af'), alignment=TA_CENTER)

def rule(color='#e5e7eb', t=0.5):
    return HRFlowable(width='100%', thickness=t, color=H(color), spaceAfter=6, spaceBefore=6)

# ── Colored section-header bar ─────────────────────────────────────────────────
SECTION_BLUE  = '#1e3a5f'
SECTION_GREEN = '#14532d'

def section_header(title, bg=SECTION_BLUE):
    """Full-width coloured title bar. Always use inside KeepTogether with
    first content so the header cannot be stranded at the bottom of a page."""
    row = [[Paragraph(mix(title),
             sty('sh', fontName=HEAD_FONT, fontSize=12, textColor=white, leading=17))]]
    t = Table(row, colWidths=[W])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), H(bg)),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
    ]))
    return t

def img(path, h_ratio=0.38):
    return Image(path, width=W, height=W*h_ratio)

def P(text, style):
    return Paragraph(mix(text), style)

def Pcap(text):
    return P(text, cap_sty)

# ── Summary cards ─────────────────────────────────────────────────────────────
def summary_cards():
    half = W/2 - 3*mm; cw = [half/4]*4
    def card(metrics, bg_h, title, tc):
        rows = [[P(title, sty('ct', fontName=HEAD_FONT, fontSize=11, textColor=H(tc), alignment=TA_CENTER)),'','','']]
        for m in metrics:
            val_fs = 11 if '\u00a0km' in m[1] else 15
            rows.append([
                P(m[0], sty('ml', fontSize=8,   textColor=H('#6b7280'), alignment=TA_CENTER)),
                P(m[1], sty('mv', fontName=HEAD_FONT, fontSize=val_fs, textColor=H(m[4]),
                             alignment=TA_CENTER, leading=val_fs*1.3)),
                P(m[2], sty('ms', fontSize=7.5, textColor=H('#9ca3af'), alignment=TA_CENTER)),
                '',
            ])
        t = Table(rows, colWidths=cw)
        t.setStyle(TableStyle([
            ('SPAN',(0,0),(3,0)), ('BACKGROUND',(0,0),(3,0),H(bg_h)),
            ('ROWBACKGROUNDS',(0,1),(3,-1),[H('#fafafa'),H('#ffffff')]*4),
            ('BOX',(0,0),(-1,-1),0.5,H('#e5e7eb')), ('INNERGRID',(0,0),(-1,-1),0.25,H('#e5e7eb')),
            ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('ALIGN',(0,0),(-1,-1),'CENTER'), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ]))
        return t

    yr, m, day = _parse(DATES[-1])
    label = f"{m}/{day}" if LANG == 'en' else f"{m}月{day}日"
    p1_m = [
        (T['fh_rate'], f"{P1['正手'][-1]}%",   '✓' if P1['正手'][-1]>=90 else '↑',   '#f0fdf4','#15803d'),
        (T['bh_rate'], f"{P1['反手'][-1]}%",   '✓' if P1['反手'][-1]>=85 else '↑',   '#f0fdf4' if P1['反手'][-1]>=82 else '#fef2f2','#15803d' if P1['反手'][-1]>=82 else '#dc2626'),
        (T['fh_spd'],  f"{P1['正手速度'][-1]}\u00a0km/h", '—', '#fffbeb','#b45309'),
        (T['bh_spd'],  f"{P1['反手速度'][-1]}\u00a0km/h", '—', '#fffbeb','#b45309'),
    ]
    yz_m = [
        (T['fh_rate'], f"{YZ['正手'][-1]}%",   '✓' if YZ['正手'][-1]>=90 else '↑',   '#f0fdf4','#15803d'),
        (T['bh_rate'], f"{YZ['反手'][-1]}%",   '✓' if YZ['反手'][-1]>=85 else '↑',   '#f0fdf4' if YZ['反手'][-1]>=82 else '#fef2f2','#15803d' if YZ['反手'][-1]>=82 else '#dc2626'),
        (T['fh_spd'],  f"{YZ['正手速度'][-1]}\u00a0km/h", '—', '#fffbeb','#b45309'),
        (T['bh_spd'],  f"{YZ['反手速度'][-1]}\u00a0km/h", '—', '#fffbeb','#b45309'),
    ]
    p1_card = card(p1_m, '#dbeafe', T['p1_card'].format(p1=P1_CODE, label=f"{T['latest_label']} {label}"), '#1d4ed8')
    yz_card = card(yz_m, '#d1fae5', T['yz_card'].format(label=f"{T['latest_label']} {label}"),              '#065f46')
    outer = Table([[p1_card, yz_card]], colWidths=[half, half])
    outer.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),  ('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('COLPADDING',(0,0),(-1,-1),4),
    ]))
    return outer

# ── Data tables ───────────────────────────────────────────────────────────────
def data_tables():
    hdr = T['th']
    cw  = [22*mm,17*mm,22*mm,18*mm,16*mm,20*mm,16*mm,20*mm]
    def build(src, bg):
        rows = []
        for i, d in enumerate(DATES):
            yr, m, day = _parse(d)
            dlbl = f"{m}/{day}" if LANG == 'en' else d
            rows.append([dlbl, f"{src['整体'][i]}%", str(src['最长回合'][i]),
                         f"{src['超过5回合'][i]}%", f"{src['正手'][i]}%",
                         f"{src['正手速度'][i]} km/h", f"{src['反手'][i]}%",
                         f"{src['反手速度'][i]} km/h"])
        data = [hdr] + rows
        p = []
        for ri, row in enumerate(data):
            pr = []
            for ci, cell in enumerate(row):
                is_bad = (ri>0 and ci==6 and int(cell.replace('%','').replace(' km/h','')) < 82)
                tc = H('#dc2626') if is_bad else (white if ri==0 else H('#374151'))
                pr.append(P(cell, sty('td', fontSize=8.5, alignment=TA_CENTER, textColor=tc)))
            p.append(pr)
        t = Table(p, colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),H(bg)),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[H('#f9fafb'),white]),
            ('BOX',(0,0),(-1,-1),0.5,H('#d1d5db')), ('INNERGRID',(0,0),(-1,-1),0.25,H('#e5e7eb')),
            ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('ALIGN',(0,0),(-1,-1),'CENTER'), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ]))
        return t
    return build(P1,'#2563eb'), build(YZ,'#059669')

# ── Training plan ─────────────────────────────────────────────────────────────
def training_plan(p1_items, yz_items):
    half = W/2 - 3*mm; cw = [8*mm, 36*mm, half-46*mm]
    def card(items, bg, title, tc):
        data = [[P(title, sty('pt', fontName=HEAD_FONT, fontSize=10, textColor=H(tc))),'','']]
        for icon, ttl, desc in items:
            data.append([
                P(icon, sty('pi', fontSize=10, alignment=TA_CENTER)),
                P(ttl,  sty('ptl', fontName=HEAD_FONT, fontSize=9,   textColor=H(tc))),
                P(desc, sty('pd',  fontSize=8.5, textColor=H('#4b5563'), leading=14)),
            ])
        t = Table(data, colWidths=cw)
        t.setStyle(TableStyle([
            ('SPAN',(0,0),(2,0)), ('BACKGROUND',(0,0),(2,0),H(bg)),
            ('ROWBACKGROUNDS',(0,1),(2,-1),[H('#f9fafb'),white]*4),
            ('BOX',(0,0),(-1,-1),0.5,H('#e5e7eb')), ('INNERGRID',(0,0),(-1,-1),0.25,H('#e5e7eb')),
            ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LEFTPADDING',(0,0),(-1,-1),6), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ]))
        return t
    p1_c = card(p1_items, '#dbeafe', T['p1_focus'].format(p1=P1_CODE), '#1d4ed8')
    yz_c = card(yz_items, '#d1fae5', T['yz_focus'], '#065f46')
    outer = Table([[p1_c, yz_c]], colWidths=[half, half])
    outer.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),  ('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('COLPADDING',(0,0),(-1,-1),4),
    ]))
    return outer

# FIX: mix() HTML-escapes < and >, so NEVER pass markup through it.
# Apply mix() to plain-text segments only, then assemble the XML string.
def insight(icon, bold_text, body_text, color):
    mb  = mix(f'{icon}  {bold_text}')   # plain text → safe XML
    mbd = mix(body_text)
    xml = f'<b>{mb}</b>  {mbd}'
    # Left-border accent card
    accent = Table([['']], colWidths=[4])
    accent.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), H(color)),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    text_cell = Paragraph(xml, sty('ins', fontSize=9.5, leading=15, textColor=H('#1e293b')))
    t = Table([[accent, text_cell]], colWidths=[5, W-5])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (1,0), (1,0), H('#f8fafc')),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (1,0), (1,0), 8),
        ('RIGHTPADDING',  (1,0), (1,0), 6),
        ('TOPPADDING',    (0,0), (0,0), 0),
        ('BOTTOMPADDING', (0,0), (0,0), 0),
        ('LEFTPADDING',   (0,0), (0,0), 0),
        ('RIGHTPADDING',  (0,0), (0,0), 0),
        ('BOX',           (0,0), (-1,-1), 0.5, H('#e2e8f0')),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return t

# ── Localised insight/plan text ───────────────────────────────────────────────
if LANG == 'cn':
    p1_plan = [
        ('🟢', '维持反手上升势头', '继续保持 87% 高位，速度可适度提升，但以稳定优先'),
        ('🔵', '正手稳定维持',     '两次训练均保持 90%，需防止追速导致下滑'),
        ('🟢', '落点深区稳定保持', '深区持续维持在 68%，底线控制能力突出'),
        ('🟠', '右区比例回归',     '落点右区从 30%→23%，加入斜线球练习增加变化'),
    ]
    yz_plan = [
        ('🔴', '反手专项（最优先）', '反手 79%→74%，持续下滑，降速优先，目标恢复至 82%+'),
        ('🟢', '落点深区稳中微升', '深区从 67%→68%，保持稳定，底线控制质量良好'),
        ('🟢', '正手成功维持',     '正手提升至 90%，保持这一水平，勿以速度换稳定'),
        ('🟠', '长回合共同训练',   '超过5回合保持 72% 但最长回合还有提升空间'),
    ]
    p1_insights = [
        ('✅', '落点深区保持稳定：',
         f'深区比例维持在 {P1["落点深"][-1]}%，浅区 {P1["落点浅"][-1]}% 不变，底线控制质量高度一致。',
         '#15803d'),
        ('✅', '正手持续稳定：',
         f'正手 {P1["正手"][0]}%→{P1["正手"][-1]}%，两场训练高度一致，基础扎实。',
         '#2563eb'),
    ]
    yz_insights = [
        ('⚠️', '反手需要关注：',
         f'反手从 {YZ["反手"][0]}% 降至 {YZ["反手"][-1]}%，建议下次训练降速优先恢复稳定。',
         '#dc2626'),
        ('✅', '正手成功维持：',
         f'正手 {YZ["正手"][0]}%→{YZ["正手"][-1]}%，保持高位稳定。',
         '#2563eb'),
    ]
    shared_insight = ('✅', '双方落点深区同步稳定：',
        f'{P1_CODE} 深区 {P1["落点深"][0]}%→{P1["落点深"][-1]}%，'
        f'YZ 深区 {YZ["落点深"][0]}%→{YZ["落点深"][-1]}%，'
        '两人底线控制水平高度一致且稳定，建议继续维持这一落点深度优势。',
        '#15803d')
else:
    p1_plan = [
        ('[+]', 'Sustain backhand momentum',   f'BH at {P1["反手"][-1]}% — maintain speed-stability balance.'),
        ('[+]', 'Protect forehand at 90%',     'Two sessions at 90%. Avoid letting speed creep compromise it.'),
        ('[+]', 'Landing depth control solid', f'Deep zone held at {P1["落点深"][-1]}% — outstanding baseline control.'),
        ('[~]', 'Restore right-zone variety',  f'Right zone dropped {P1["落点右"][0]}%→{P1["落点右"][-1]}%. Add cross-court drills.'),
    ]
    yz_plan = [
        ('[!]', 'Backhand: top priority',      f'BH dropped {YZ["反手"][0]}%→{YZ["反手"][-1]}%. Reduce swing speed; target 82%+.'),
        ('[+]', 'Deep zone stable and rising', f'Deep zone {YZ["落点深"][0]}%→{YZ["落点深"][-1]}% — controlled baseline play.'),
        ('[+]', 'Forehand reached peak',       f'FH at {YZ["正手"][-1]}%. Do not sacrifice consistency for speed.'),
        ('[~]', 'Long-rally joint drills',     'Rallies 5+ stable but longest rally still has room to grow.'),
    ]
    p1_insights = [
        ('[OK]', 'Landing depth locked in:',
         f'Deep zone held at {P1["落点深"][-1]}%, shallow at {P1["落点浅"][-1]}%. Consistent baseline depth control.',
         '#15803d'),
        ('[OK]', 'Forehand rock-solid:',
         f'FH {P1["正手"][0]}%→{P1["正手"][-1]}% — two-session consistency is the benchmark.',
         '#2563eb'),
    ]
    yz_insights = [
        ('[Watch]', 'Backhand needs attention:',
         f'BH dropped {YZ["反手"][0]}%→{YZ["反手"][-1]}%. Next session: reduce speed, rebuild control.',
         '#dc2626'),
        ('[OK]', 'Forehand at peak:',
         f'FH {YZ["正手"][0]}%→{YZ["正手"][-1]}% — protect this level.',
         '#2563eb'),
    ]
    shared_insight = ('[OK]', 'Landing depth in sync for both:',
        f'{P1_CODE} deep zone {P1["落点深"][0]}%→{P1["落点深"][-1]}%, '
        f'YZ deep zone {YZ["落点深"][0]}%→{YZ["落点深"][-1]}%. '
        'Both players maintaining strong baseline depth — continue this advantage.',
        '#15803d')

# ── Build story ───────────────────────────────────────────────────────────────
story = []
story.append(P(f"🎾  {T['report_title'].format(p1=P1_CODE)}  ·  {_title_date}", title_sty))
story.append(P(T['report_subtitle'].format(
    start=date_to_xlbl(DATES[0]), end=date_to_xlbl(DATES[-1]), n=len(DATES)), sub_sty))
story.append(rule('#3b82f6', 1.5))
story.append(Spacer(1, 6))
story.append(summary_cards())
story.append(Spacer(1, 10))

# FIX: every section_header() lives inside a KeepTogether with its first
# content element so it can never be stranded alone at the bottom of a page.
story.append(KeepTogether([
    section_header(T['s1']),
    Spacer(1, 4),
    img(f"{IMG_DIR}/chart_stroke.png", 0.40),
]))
story.append(Pcap(T['cap_stroke'].format(p1=P1_CODE)))
story.append(Spacer(1, 8))

story.append(KeepTogether([
    section_header(T['s2']),
    Spacer(1, 4),
    img(f"{IMG_DIR}/chart_speed.png", 0.34),
]))
story.append(Pcap(T['cap_speed']))
story.append(Spacer(1, 8))

story.append(KeepTogether([
    section_header(T['s3']),
    Spacer(1, 4),
    img(f"{IMG_DIR}/chart_rally.png", 0.34),
]))
story.append(Pcap(T['cap_rally']))
story.append(Spacer(1, 8))

# FIX: Section 4 — header must be in the SAME KeepTogether as the first chart.
story.append(KeepTogether([
    section_header(T['s4']),
    Spacer(1, 4),
    P(P1_CODE, h3_sty),
    img(f"{IMG_DIR}/chart_p1_land.png", 0.34),
]))
story.append(Pcap(T['cap_land_p1'].format(p1=P1_CODE)))
story.append(KeepTogether([
    P('YZ', h3_sty),
    img(f"{IMG_DIR}/chart_yz_land.png", 0.34),
]))
story.append(Pcap(T['cap_land_yz']))
story.append(Spacer(1, 8))

# FIX: radar h_ratio = 4/8 = 0.50 to match the exact figsize aspect ratio
story.append(KeepTogether([
    section_header(T['s5']),
    Spacer(1, 4),
    img(f"{IMG_DIR}/chart_radar.png", 0.50),
    Pcap(T['cap_radar']),
]))
story.append(Spacer(1, 10))

p1_tbl, yz_tbl = data_tables()
story.append(KeepTogether([
    section_header(T['s6']),
    Spacer(1, 4),
    P(P1_CODE, h3_sty),
    p1_tbl,
]))
story.append(Spacer(1, 8))
story.append(KeepTogether([P('YZ', h3_sty), yz_tbl]))
story.append(Spacer(1, 4)); story.append(Pcap(T['cap_table']))
story.append(Spacer(1, 10))

story.append(section_header(T['s7']))
story.append(Spacer(1, 6))
story.append(P(P1_CODE, h3_sty))
for args in p1_insights:
    story.append(insight(*args)); story.append(Spacer(1, 4))
story.append(Spacer(1, 4))
story.append(P('YZ', h3_sty))
for args in yz_insights:
    story.append(insight(*args)); story.append(Spacer(1, 4))
story.append(Spacer(1, 4))
story.append(insight(*shared_insight))
story.append(Spacer(1, 10))

story.append(section_header(T['s8'], bg=SECTION_GREEN))
story.append(Spacer(1, 6))
story.append(training_plan(p1_plan, yz_plan))
story.append(Spacer(1, 14))

story.append(rule())
story.append(P(T['footer'].format(n=len(DATES)), foot_sty))

doc.build(story)
print(f"[{LANG.upper()}] PDF saved: {OUT}")
