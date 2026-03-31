"""
generate_pdf_mobile.py — Mobile-optimized multilingual tennis training report.

Key differences from the desktop version:
  - Single-column layout (no side-by-side cards or tables)
  - Narrower margins (10mm) for more content width
  - Larger fonts (body 12pt) for comfortable phone reading
  - Taller chart aspect ratios
  - Summary cards and training plan stacked vertically

Change LANG at the top to switch between Chinese (cn) and English (en).
"""

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
    SimpleDocTemplate, Paragraph, Spacer, Image, Table,
    TableStyle, HRFlowable
)
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# ══════════════════════════════════════════════════════════════════════════════
# ① LANGUAGE  —  set to 'cn' (Chinese) or 'en' (English)
# ══════════════════════════════════════════════════════════════════════════════
LANG = 'cn'

# ══════════════════════════════════════════════════════════════════════════════
# ② DATA  —  update this section for each new training period
# ══════════════════════════════════════════════════════════════════════════════
DATES   = ["12/30", "2/10", "3/3", "3/24"]
P1_CODE = "XT"           # partner player code

P1 = dict(
    整体      = [89, 87, 85, 88],
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
    整体      = [91, 90, 90, 89],
    正手      = [93, 91, 93, 92],
    反手      = [87, 88, 85, 81],
    正手速度  = [66, 68, 72, 74],
    反手速度  = [64, 66, 67, 71],
    最长回合  = [118, 79, 58, 48],
    超过5回合 = [72, 71, 61, 63],
    落点左    = [8,  11, 13, 11],
    落点中    = [70, 74, 71, 75],
    落点右    = [19, 13, 14, 13],
    落点深    = [53, 56, 56, 61],
    落点浅    = [46, 43, 43, 38],
)

# ══════════════════════════════════════════════════════════════════════════════
# ③ STRINGS  —  all UI text in both languages
# ══════════════════════════════════════════════════════════════════════════════
STRINGS = {
    'cn': dict(
        report_title    = '🎾  YZ & {p1}  网球训练报告',
        report_subtitle = '训练周期：{start} — {end}  ·  共{n}次训练  ·  目标：提升正手与反手稳定性',
        s1 = '一、正手 & 反手成功率趋势',
        s2 = '二、击球速度趋势',
        s3 = '三、回合稳定性趋势',
        s4 = '四、击球落点分布',
        s5 = '五、综合雷达图（最新训练）',
        s6 = '六、完整训练数据',
        s7 = '七、数据分析 & 洞察',
        s8 = '八、针对稳定性目标的训练建议',
        latest_label    = '最新数据',
        fh='正手', bh='反手',
        fh_spd='正手速度', bh_spd='反手速度',
        fh_target='正手目标 90%', bh_target='反手目标 85%',
        success_rate='成功率 (%)', speed_unit='速度 (km/h)',
        over5='超过5回合 (%)', longest='最长回合',
        longest_unit='最长回合 (球数)', target_70='目标 70%',
        left='左区', center='中区', right='右区',
        deep='深区', shallow='浅区',
        fh_rate='正手成功率', bh_rate='反手成功率',
        radar_cats=['正手稳定','反手稳定','整体成功','回合稳定','落点深区','中区精准'],
        th=['日期','整体','最长\n回合','超5\n回合','正手','正手\n速度','反手','反手\n速度'],
        p1_focus='{p1} · 训练重点', yz_focus='YZ · 训练重点',
        p1_card='{p1} · {label}', yz_card='YZ · {label}',
        shared_trends='共同趋势',
        cap_stroke='实线 = 正手  |  虚线 = 反手  |  点线 = 目标参考线',
        cap_speed='实线 = 正手速度  |  虚线 = 反手速度',
        cap_rally='紫色（左轴）= 超过5回合  |  橙色（右轴）= 最长回合',
        cap_land_p1='{p1} 落点分布（上：左/中/右  下：深/浅）',
        cap_land_yz='YZ 落点分布（上：左/中/右  下：深/浅）',
        cap_radar='基于最新一次训练数据的六维能力评估',
        cap_table='反手成功率低于 82% 标红',
        land_lr='{name} – 左/中/右区', land_ds='{name} – 深/浅区',
        chart_stroke='正手 & 反手成功率趋势',
        chart_speed='击球速度趋势',
        chart_rally='回合稳定性趋势（双方共用）',
        footer='手机版报告由 Claude 生成  ·  训练周期：{start} — {end}（共{n}次训练）',
        date_title='{yr}年{m}月{d}日',
        warn_keep_it='⚠ 注意稳定性', good_holding='保持高位 ✓',
        # Summary card metric labels
        card_fh='正手成功率', card_bh='反手成功率',
        card_fh_spd='正手速度', card_bh_spd='反手速度',
        vs_first='↕ vs 首次 {val}%',
        speed_suffix=' km/h',
        first_val='首次 {val} km/h',
        # Insights
        ins_p1_1_title='反手危机（最紧急）：',
        ins_p1_1_body='反手成功率出现明显下滑。速度同期提升，典型的"追速牺牲稳定"现象。建议立即将反手速度降至 60 km/h 以下，重建稳定性后再提速。',
        ins_p1_2_title='落点分布监控：',
        ins_p1_2_body='关注左区/右区偏漂趋势，如果某侧区域超过 20% 则需要专项定点练习，有意识打向中区。',
        ins_p1_3_title='深区控制持续改善：',
        ins_p1_3_body='深区落点比例持续提升，底线球质量在提高，继续保持。',
        ins_p1_4_title='正手监控：',
        ins_p1_4_body='正手成功率需维持在 87% 以上。在反手问题未解决期间不宜追求速度提升。',
        ins_yz_1_title='正手堪称教科书级稳定：',
        ins_yz_2_title='反手小幅下滑，需关注：',
        ins_yz_2_body='反手速度同步提升，趋势与 {p1} 早期相似，若继续追速可能触发稳定性下降，需密切观察。',
        ins_yz_3_title='落点趋向中间化：',
        ins_yz_3_body='中区比例持续偏高，落点过于集中容易被对手预判。建议适当加入大角度球和变线训练。',
        ins_yz_4_title='深区控制稳步提升：',
        ins_shared_1_title='长回合能力持续下降：',
        ins_shared_2_title='速度提升正在压迫稳定性：',
        ins_shared_2_body='两人击球速度均有提升趋势，但伴随成功率下降。建议原则：先达到正手 ≥90%、反手 ≥85% 的硬指标，再逐步追求速度提升。',
        tip_template='⚡ 速度与稳定性权衡参考：YZ 正手是最佳范例——{spd} km/h 速度配合 {pct}% 成功率。建议以此为标准：若速度提升但成功率低于目标值，立即降速恢复稳定性后再尝试提速。',
        # Training plan
        plan_p1_items=[
            ('🔴', '反手专项（最优先）', '将速度降至 60 km/h 以下，先求稳定再提速，目标恢复到 84%+'),
            ('🟡', '中区定点训练',       '有意识击打中区和右区，纠正落点偏漂习惯'),
            ('🟢', '多拍稳定对打',       '目标：超过5回合比例重新达到 70%+'),
            ('🔵', '正手节奏维稳',       '保持现有水平，反手恢复前不追速度'),
        ],
        plan_yz_items=[
            ('🟡', '反手稳定性监控',     '密切关注，保持 87%+ 以上，防止重蹈 {p1} 覆辙'),
            ('🟢', '大角度变线训练',     '增加左区落点练习，减少落点过于集中被预判'),
            ('🔵', '正手速度可继续',     '但设置质量底线：成功率低于 90% 则降速'),
            ('🟠', '长回合共同训练',     '两人进行多拍专项练习，共同提升稳定性'),
        ],
    ),
    'en': dict(
        report_title    = '🎾  YZ & {p1}  Tennis Training Report',
        report_subtitle = 'Period: {start} – {end}  ·  Sessions: {n}  ·  Goal: Forehand & Backhand Stability',
        s1 = '1. Forehand & Backhand Success Rate Trends',
        s2 = '2. Shot Speed Trends',
        s3 = '3. Rally Stability Trends',
        s4 = '4. Landing Zone Distribution',
        s5 = '5. Performance Radar (Latest Session)',
        s6 = '6. Full Training Data',
        s7 = '7. Analysis & Insights',
        s8 = '8. Training Recommendations',
        latest_label    = 'Latest',
        fh='FH', bh='BH',
        fh_spd='FH Speed', bh_spd='BH Speed',
        fh_target='FH target 90%', bh_target='BH target 85%',
        success_rate='Success Rate (%)', speed_unit='Speed (km/h)',
        over5='Rallies 5+ (%)', longest='Longest Rally',
        longest_unit='Longest Rally (shots)', target_70='Target 70%',
        left='Left', center='Center', right='Right',
        deep='Deep', shallow='Shallow',
        fh_rate='Forehand %', bh_rate='Backhand %',
        radar_cats=['FH Stability','BH Stability','Overall','Rally Depth','Deep Zone','Center Acc.'],
        th=['Date','Overall','Longest','Rallies 5+','FH%','FH Spd','BH%','BH Spd'],
        p1_focus='{p1} — Training Focus', yz_focus='YZ — Training Focus',
        p1_card='{p1} | {label}', yz_card='YZ | {label}',
        shared_trends='Shared Trends',
        cap_stroke='Solid = forehand, dashed = backhand  |  dotted = target lines',
        cap_speed='Solid = forehand speed, dashed = backhand speed',
        cap_rally='Purple (left axis): Rallies 5+%  |  Orange (right axis): Longest rally (shots)',
        cap_land_p1='{p1} landing zone distribution (top: L/C/R  bottom: Deep/Shallow)',
        cap_land_yz='YZ landing zone distribution (top: L/C/R  bottom: Deep/Shallow)',
        cap_radar='Six-dimension performance radar — most recent session',
        cap_table='Backhand % values below 82% highlighted in red',
        land_lr='{name} – L / C / R', land_ds='{name} – Deep / Shallow',
        chart_stroke='Forehand & Backhand Success Rate Trends',
        chart_speed='Shot Speed Trends',
        chart_rally='Rally Stability Trends (Both Players)',
        footer='Mobile report generated by Claude  ·  Period: {start} – {end}  ({n} sessions)',
        date_title='{m}/{d}/{yr}',
        warn_keep_it='⚠ Watch stability', good_holding='Holding high ✓',
        card_fh='Forehand %', card_bh='Backhand %',
        card_fh_spd='FH Speed', card_bh_spd='BH Speed',
        vs_first='↕ vs first {val}%',
        speed_suffix=' km/h',
        first_val='First: {val} km/h',
        ins_p1_1_title='Backhand Crisis (Most Urgent):',
        ins_p1_1_body='Backhand success rate has dropped significantly while speed increased — a classic "chasing speed at the cost of stability" pattern. Reduce backhand speed to below 60 km/h immediately to rebuild consistency.',
        ins_p1_2_title='Landing Zone Drift:',
        ins_p1_2_body='Watch for left/right zone drift. If either side exceeds 20%, add targeted cross-court drills and consciously aim for the center zone.',
        ins_p1_3_title='Deep Zone Improving:',
        ins_p1_3_body='Deep zone percentage is trending upward — baseline ball quality is improving. Keep it up.',
        ins_p1_4_title='Forehand Watch:',
        ins_p1_4_body='Maintain forehand above 87%. Do not chase speed improvements until the backhand issue is resolved.',
        ins_yz_1_title='Forehand — Textbook Consistency:',
        ins_yz_2_title='Backhand Slight Dip — Monitor:',
        ins_yz_2_body='Backhand speed is rising while success rate dips — same early pattern as {p1}. Monitor closely; if speed keeps rising, pull back before stability drops further.',
        ins_yz_3_title='Landing Too Center-Heavy:',
        ins_yz_3_body='Center zone share is consistently high, making shots predictable. Add wide-angle and cross-court variation to landing zone work.',
        ins_yz_4_title='Deep Zone Steadily Improving:',
        ins_shared_1_title='Rally Depth Declining:',
        ins_shared_2_title='Speed Gains Are Pressuring Stability:',
        ins_shared_2_body='Both players show rising speed trends alongside success rate dips. Rule of thumb: hit FH ≥90% and BH ≥85% first — then incrementally push speed.',
        tip_template='⚡ Speed vs. stability benchmark: YZ forehand is the gold standard — {spd} km/h with {pct}% success rate. Use this as a reference: if speed rises but success rate drops below target, dial back and rebuild before pushing again.',
        plan_p1_items=[
            ('🔴', 'Backhand Specialist Work (Top Priority)', 'Drop BH speed below 60 km/h; prioritise stability over speed. Target: recover to 84%+'),
            ('🟡', 'Center Zone Targeting', 'Consciously direct shots to center and right zones; correct the leftward drift habit'),
            ('🟢', 'Extended Rally Drills', 'Target: bring Rallies 5+% back above 70%'),
            ('🔵', 'Maintain Forehand Rhythm', 'Hold current FH level; do not chase speed while BH is recovering'),
        ],
        plan_yz_items=[
            ('🟡', 'Monitor Backhand Closely', 'Keep BH above 87%. Do not repeat {p1}\'s pattern of trading stability for speed.'),
            ('🟢', 'Wide-Angle Variation', 'Add more left-zone shots; reduce predictable center clustering'),
            ('🔵', 'Forehand Speed — Continue', 'But set a quality floor: if FH drops below 90%, reduce speed'),
            ('🟠', 'Long Rally Joint Training', 'Dedicated multi-shot rally sessions with partner to lift both players\' stability'),
        ],
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
    """Wrap CJK runs in CN font, Latin runs in LAT font."""
    if not text:
        return text
    if LANG == 'en':
        safe = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        return f'<font name="LAT">{safe}</font>'
    text = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    parts, seg = [], ''
    cur_cjk = is_cjk(text[0])
    for ch in text:
        ck = is_cjk(ch)
        if ck != cur_cjk:
            parts.append(f'<font name="{"CN" if cur_cjk else "LAT"}">{seg}</font>')
            seg = ch; cur_cjk = ck
        else:
            seg += ch
    if seg:
        parts.append(f'<font name="{"CN" if cur_cjk else "LAT"}">{seg}</font>')
    return ''.join(parts)

# ══════════════════════════════════════════════════════════════════════════════
# ⑤ DATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _parse_date(d):
    m, day = int(d.split('/')[0]), int(d.split('/')[1])
    yr = 2025 if m == 12 else 2026
    return yr, m, day

def date_to_xlbl(d):
    yr, m, day = _parse_date(d)
    if LANG == 'en':
        mo = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m]
        return f"{mo} {day}"
    return d  # "3/24" for CN

def date_to_long(d):
    yr, m, day = _parse_date(d)
    if LANG == 'en':
        mo = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m]
        return f"{mo} {day}, {yr}"
    return T['date_title'].format(yr=yr, m=m, d=day)

def date_to_filestr(d):
    yr, m, day = _parse_date(d)
    return f"{yr}{m:02d}{day:02d}"

XLABELS = [date_to_xlbl(d) for d in DATES]

# ══════════════════════════════════════════════════════════════════════════════
# ⑥ MATPLOTLIB FONT SETUP
# ══════════════════════════════════════════════════════════════════════════════
if LANG == 'cn':
    fm.fontManager.addfont(CJK_PATH)
    _font_families = ['DejaVu Sans', 'Droid Sans Fallback']
else:
    _font_families = ['Liberation Sans', 'DejaVu Sans']

plt.rcParams.update({
    'font.family': _font_families,
    'axes.unicode_minus': False,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'axes.facecolor': '#fafafa',
    'figure.facecolor': 'white',
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
})

# ══════════════════════════════════════════════════════════════════════════════
# ⑦ OUTPUT PATHS
# ══════════════════════════════════════════════════════════════════════════════
_SESSION = _re.search(r'(/sessions/[^/]+)', __file__)
_SESSION_ROOT = _SESSION.group(1) if _SESSION else '/sessions/current'
IMG_DIR = f"{_SESSION_ROOT}/img_mobile_{LANG}"
os.makedirs(IMG_DIR, exist_ok=True)

_PLAYERS    = f"YZ_{P1_CODE}"
_DATE_STR   = date_to_filestr(DATES[-1])
_LANG_SUFFIX = '' if LANG == 'cn' else '_EN'
OUT = f"{_SESSION_ROOT}/mnt/outputs/{_PLAYERS}_Tennis_Report_Mobile{_LANG_SUFFIX}_{_DATE_STR}.pdf"
os.makedirs(f"{_SESSION_ROOT}/mnt/outputs", exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# ⑧ CHARTS  (taller aspect ratios for mobile)
# ══════════════════════════════════════════════════════════════════════════════
BLUE   = "#3b82f6"; BLUE2  = "#2563eb"
GREEN  = "#10b981"; RED    = "#ef4444"
AMBER  = "#f59e0b"; PURPLE = "#8b5cf6"; ORANGE = "#f97316"
n = len(XLABELS) - 1

# Chart 1: Success rates
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(XLABELS, P1['正手'], 'o-',  color=BLUE,  lw=2.5, ms=8, label=f'{P1_CODE} {T["fh"]}')
ax.plot(XLABELS, P1['反手'], 'o--', color=BLUE,  lw=2.5, ms=8, label=f'{P1_CODE} {T["bh"]}')
ax.plot(XLABELS, YZ['正手'], 's-',  color=GREEN, lw=2.5, ms=8, label=f'YZ {T["fh"]}')
ax.plot(XLABELS, YZ['反手'], 's--', color=GREEN, lw=2.5, ms=8, label=f'YZ {T["bh"]}')
ax.axhline(90, color=BLUE,  lw=1.2, linestyle=':', alpha=0.7)
ax.axhline(85, color=AMBER, lw=1.2, linestyle=':', alpha=0.7)
ax.text(n + 0.05, 90.5, T['fh_target'], fontsize=9, color=BLUE)
ax.text(n + 0.05, 85.5, T['bh_target'], fontsize=9, color=AMBER)
for label, val, col, dy in [
    (f'{P1_CODE} {T["fh"]} {P1["正手"][-1]}%', P1['正手'][-1], BLUE,   1.5),
    (f'{P1_CODE} {T["bh"]} {P1["反手"][-1]}%', P1['反手'][-1], RED,   -4.0),
    (f'YZ {T["fh"]} {YZ["正手"][-1]}%',         YZ['正手'][-1], GREEN,  2.8),
    (f'YZ {T["bh"]} {YZ["反手"][-1]}%',         YZ['反手'][-1], "#059669",-1.5),
]:
    ax.annotate(label, xy=(n, val), xytext=(n + 0.05, val + dy),
                fontsize=9, color=col, fontweight='bold')
ax.set_ylim(62, 100)
ax.set_ylabel(T['success_rate'])
ax.set_title(T['chart_stroke'], fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='lower left', framealpha=0.8, ncol=2)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_stroke.png", dpi=150, bbox_inches='tight')
plt.close()

# Chart 2: Shot speed
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(XLABELS, P1['正手速度'], 'o-',  color=BLUE,  lw=2.5, ms=8, label=f'{P1_CODE} {T["fh_spd"]}')
ax.plot(XLABELS, P1['反手速度'], 'o--', color=BLUE,  lw=2.5, ms=8, label=f'{P1_CODE} {T["bh_spd"]}')
ax.plot(XLABELS, YZ['正手速度'], 's-',  color=GREEN, lw=2.5, ms=8, label=f'YZ {T["fh_spd"]}')
ax.plot(XLABELS, YZ['反手速度'], 's--', color=GREEN, lw=2.5, ms=8, label=f'YZ {T["bh_spd"]}')
ax.set_ylim(58, max(max(YZ['正手速度']), max(P1['正手速度'])) + 6)
ax.set_ylabel(T['speed_unit'])
ax.set_title(T['chart_speed'], fontsize=13, fontweight='bold', pad=12)
ax.legend(loc='upper left', framealpha=0.8, ncol=2)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_speed.png", dpi=150, bbox_inches='tight')
plt.close()

# Chart 3: Rally stability
fig, ax1 = plt.subplots(figsize=(8, 4.5))
ax2 = ax1.twinx()
ln1 = ax1.plot(XLABELS, P1['超过5回合'], 'D-', color=PURPLE, lw=2.5, ms=8, label=T['over5'])
ax1.axhline(70, color=PURPLE, lw=1, linestyle=':', alpha=0.6)
ax1.text(0.02, 71, T['target_70'], fontsize=9, color=PURPLE)
ln2 = ax2.plot(XLABELS, P1['最长回合'], 'P--', color=ORANGE, lw=2.5, ms=9, label=T['longest'])
ax1.set_ylabel(T['over5'], color=PURPLE)
ax2.set_ylabel(T['longest_unit'], color=ORANGE)
ax1.set_ylim(50, 85); ax2.set_ylim(40, 135)
ax1.tick_params(axis='y', labelcolor=PURPLE)
ax2.tick_params(axis='y', labelcolor=ORANGE)
ax1.legend(ln1 + ln2, [T['over5'], T['longest']], loc='upper right', framealpha=0.8)
ax1.set_title(T['chart_rally'], fontsize=13, fontweight='bold', pad=12)
ax1.spines['top'].set_visible(False); ax2.spines['top'].set_visible(False)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_rally.png", dpi=150, bbox_inches='tight')
plt.close()

# Chart 4: Landing zones (stacked subplot for mobile)
def landing_chart(data, name, color_set, fname):
    fig, (ax_lr, ax_ds) = plt.subplots(2, 1, figsize=(8, 8))
    bw = 0.25; xi = np.arange(len(DATES))
    c1, c2, c3 = color_set
    b1 = ax_lr.bar(xi-bw, data['落点左'], bw, label=T['left'],   color=c1, alpha=0.85)
    b2 = ax_lr.bar(xi,    data['落点中'], bw, label=T['center'], color=c2, alpha=0.85)
    b3 = ax_lr.bar(xi+bw, data['落点右'], bw, label=T['right'],  color=c3, alpha=0.85)
    for b in (b1, b2, b3):
        ax_lr.bar_label(b, fmt='%d', fontsize=8, padding=2)
    ax_lr.set_xticks(xi); ax_lr.set_xticklabels(XLABELS)
    ax_lr.set_ylabel('%'); ax_lr.set_ylim(0, 100)
    ax_lr.set_title(T['land_lr'].format(name=name), fontsize=12, fontweight='bold')
    ax_lr.legend(fontsize=10)
    b4 = ax_ds.bar(xi-bw/2, data['落点深'], bw*1.2, label=T['deep'],    color=c2, alpha=0.85)
    b5 = ax_ds.bar(xi+bw/2, data['落点浅'], bw*1.2, label=T['shallow'], color=c1, alpha=0.5)
    for b in (b4, b5):
        ax_ds.bar_label(b, fmt='%d', fontsize=8, padding=2)
    ax_ds.set_xticks(xi); ax_ds.set_xticklabels(XLABELS)
    ax_ds.set_ylabel('%'); ax_ds.set_ylim(0, 95)
    ax_ds.set_title(T['land_ds'].format(name=name), fontsize=12, fontweight='bold')
    ax_ds.legend(fontsize=10)
    plt.tight_layout(pad=2.5)
    plt.savefig(f"{IMG_DIR}/{fname}", dpi=150, bbox_inches='tight')
    plt.close()

landing_chart(P1, P1_CODE, ['#93c5fd','#2563eb','#1e3a8a'], 'chart_p1_land.png')
landing_chart(YZ, 'YZ',    ['#6ee7b7','#059669','#064e3b'], 'chart_yz_land.png')

# Chart 5: Radar
cats   = T['radar_cats']
p1_vals = [P1['正手'][-1], P1['反手'][-1], P1['整体'][-1],
           P1['超过5回合'][-1], P1['落点深'][-1], P1['落点中'][-1]]
yz_vals = [YZ['正手'][-1], YZ['反手'][-1], YZ['整体'][-1],
           YZ['超过5回合'][-1], YZ['落点深'][-1], YZ['落点中'][-1]]
N      = len(cats)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist(); angles += angles[:1]
def pad(v): return v + v[:1]

fig, (ra, rb) = plt.subplots(1, 2, figsize=(9, 5), subplot_kw=dict(polar=True))
for ax, vals, col, nm in [(ra, p1_vals, BLUE, P1_CODE), (rb, yz_vals, GREEN, 'YZ')]:
    ax.plot(angles, pad(vals), 'o-', color=col, lw=2)
    ax.fill(angles, pad(vals), color=col, alpha=0.2)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(cats, size=10)
    ax.set_ylim(0, 100); ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25','50','75','100'], size=8, color='gray')
    ax.set_title(nm, fontsize=14, fontweight='bold', pad=22, color=col)
    ax.grid(color='gray', alpha=0.3)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/chart_radar.png", dpi=150, bbox_inches='tight')
plt.close()

print(f"[{LANG.upper()}] All mobile charts generated.")

# ══════════════════════════════════════════════════════════════════════════════
# ⑨ PDF ASSEMBLY  —  Mobile layout (single column, larger fonts)
# ══════════════════════════════════════════════════════════════════════════════
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=10*mm, rightMargin=10*mm,
    topMargin=15*mm, bottomMargin=15*mm,
    title=T['report_title'].format(p1=P1_CODE),
)
W = A4[0] - 20*mm   # 190mm — wider than desktop

def H(c): return HexColor(c)

def sty(name, **kw):
    defaults = dict(fontName=BODY_FONT, fontSize=12, leading=19, textColor=H('#374151'))
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

title_sty = sty('t1', fontName=HEAD_FONT, fontSize=22, textColor=H('#111827'), spaceAfter=5)
sub_sty   = sty('t2', fontSize=10, textColor=H('#9ca3af'), spaceAfter=16)
h2_sty    = sty('h2', fontName=HEAD_FONT, fontSize=16, textColor=H('#1f2937'), spaceBefore=18, spaceAfter=8)
h3_sty    = sty('h3', fontName=HEAD_FONT, fontSize=13, textColor=H('#374151'), spaceBefore=12, spaceAfter=5)
cap_sty   = sty('cap', fontSize=9, textColor=H('#9ca3af'), spaceAfter=10, alignment=TA_CENTER)
body_sty  = sty('body', fontSize=12, leading=20, spaceAfter=7)
foot_sty  = sty('ft',   fontSize=8,  textColor=H('#9ca3af'), alignment=TA_CENTER)

def rule(color='#e5e7eb', t=0.5):
    return HRFlowable(width='100%', thickness=t, color=H(color), spaceAfter=7, spaceBefore=7)

def img(path, h_ratio=0.55):
    return Image(path, width=W, height=W * h_ratio)

def P(text, style, **kw):
    return Paragraph(mix(text), style)

def Pcap(text):
    return P(text, cap_sty)

# ── Summary card ──────────────────────────────────────────────────────────────
def summary_card_single(metrics, bg_h, title, tc):
    rows = [[P(title, sty('ct', fontName=HEAD_FONT, fontSize=13, textColor=H(tc), alignment=TA_CENTER)), '', '', '']]
    for m in metrics:
        rows.append([
            P(m[0], sty('ml', fontSize=10, textColor=H('#6b7280'), alignment=TA_CENTER)),
            P(m[1], sty('mv', fontName=HEAD_FONT, fontSize=17, textColor=H(m[4]), alignment=TA_CENTER)),
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

def summary_section():
    latest_lbl = T['latest_label']
    p1_m = [
        (T['card_fh'], f'{P1["正手"][-1]}%',    T['vs_first'].format(val=P1['正手'][0]),   '#eff6ff', '#1d4ed8'),
        (T['card_bh'], f'{P1["反手"][-1]}%',    T['warn_keep_it'],                         '#fef2f2', '#dc2626'),
        (T['card_fh_spd'], f'{P1["正手速度"][-1]}{T["speed_suffix"]}', T['first_val'].format(val=P1['正手速度'][0]), '#f0fdf4', '#15803d'),
        (T['card_bh_spd'], f'{P1["反手速度"][-1]}{T["speed_suffix"]}', T['first_val'].format(val=P1['反手速度'][0]), '#f0fdf4', '#15803d'),
    ]
    yz_m = [
        (T['card_fh'], f'{YZ["正手"][-1]}%',    T['good_holding'],                         '#f0fdf4', '#15803d'),
        (T['card_bh'], f'{YZ["反手"][-1]}%',    T['vs_first'].format(val=YZ['反手'][0]),   '#fffbeb', '#b45309'),
        (T['card_fh_spd'], f'{YZ["正手速度"][-1]}{T["speed_suffix"]}', T['first_val'].format(val=YZ['正手速度'][0]), '#f0fdf4', '#15803d'),
        (T['card_bh_spd'], f'{YZ["反手速度"][-1]}{T["speed_suffix"]}', T['first_val'].format(val=YZ['反手速度'][0]), '#f0fdf4', '#15803d'),
    ]
    p1_title = T['p1_card'].format(p1=P1_CODE, label=f'{T["latest_label"]} {DATES[-1]}')
    yz_title = T['yz_card'].format(label=f'{T["latest_label"]} {DATES[-1]}')
    p1_card = summary_card_single(p1_m, '#dbeafe', p1_title, '#1d4ed8')
    yz_card = summary_card_single(yz_m, '#d1fae5', yz_title, '#065f46')
    return [p1_card, Spacer(1, 8), yz_card]

# ── Data tables ───────────────────────────────────────────────────────────────
def data_tables():
    hdr = T['th']
    cw  = [24*mm, 18*mm, 20*mm, 18*mm, 16*mm, 22*mm, 16*mm, 22*mm]

    def build(src, bg):
        rows = []
        for i, d in enumerate(DATES):
            rows.append([
                date_to_xlbl(d),
                f"{src['整体'][i]}%",
                str(src['最长回合'][i]),
                f"{src['超过5回合'][i]}%",
                f"{src['正手'][i]}%",
                f"{src['正手速度'][i]}",
                f"{src['反手'][i]}%",
                f"{src['反手速度'][i]}",
            ])
        data = [hdr] + rows
        pp = []
        for ri, row in enumerate(data):
            pr = []
            for ci, cell in enumerate(row):
                is_bad = (ri > 0 and ci == 6 and
                          int(str(cell).replace('%','').strip()) < 82)
                tc = H('#dc2626') if is_bad else (white if ri == 0 else H('#374151'))
                s = sty('td', fontSize=10, alignment=TA_CENTER, textColor=tc)
                pr.append(P(str(cell), s))
            pp.append(pr)
        t = Table(pp, colWidths=cw)
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

    return build(P1, '#2563eb'), build(YZ, '#059669')

# ── Training plan ─────────────────────────────────────────────────────────────
def training_plan_card(items, bg, title, tc):
    cw = [10*mm, 55*mm, W - 70*mm]
    data = [[P(title, sty('pt', fontName=HEAD_FONT, fontSize=12, textColor=H(tc))), '', '']]
    for icon, ttl, desc in items:
        data.append([
            P(icon, sty('pi', fontSize=12, alignment=TA_CENTER)),
            P(ttl,  sty('ptl', fontName=HEAD_FONT, fontSize=11, textColor=H(tc))),
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
    p1_title = T['p1_focus'].format(p1=P1_CODE)
    yz_title = T['yz_focus']
    p1_items = [(ic, ttl, desc.replace('{p1}', P1_CODE)) for ic,ttl,desc in T['plan_p1_items']]
    yz_items = [(ic, ttl, desc.replace('{p1}', P1_CODE)) for ic,ttl,desc in T['plan_yz_items']]
    p1_card = training_plan_card(p1_items, '#dbeafe', p1_title, '#1d4ed8')
    yz_card = training_plan_card(yz_items, '#d1fae5', yz_title, '#065f46')
    return [p1_card, Spacer(1, 8), yz_card]

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

# ══════════════════════════════════════════════════════════════════════════════
# ⑩ BUILD STORY
# ══════════════════════════════════════════════════════════════════════════════
p1_latest = {k: v[-1] for k, v in P1.items()}
yz_latest = {k: v[-1] for k, v in YZ.items()}
p1_tbl, yz_tbl = data_tables()
story = []
n_sessions = len(DATES)

# Header
story.append(P(T['report_title'].format(p1=P1_CODE), title_sty))
story.append(P(T['report_subtitle'].format(
    start=date_to_long(DATES[0]), end=date_to_long(DATES[-1]), n=n_sessions), sub_sty))
story.append(rule('#3b82f6', 1.5))
story.append(Spacer(1, 6))

# Summary
story.extend(summary_section())
story.append(Spacer(1, 12))

# Charts
story.append(rule())
story.append(P(T['s1'], h2_sty))
story.append(img(f"{IMG_DIR}/chart_stroke.png", 0.58))
story.append(Pcap(T['cap_stroke']))
story.append(Spacer(1, 6))

story.append(P(T['s2'], h2_sty))
story.append(img(f"{IMG_DIR}/chart_speed.png", 0.52))
story.append(Pcap(T['cap_speed']))
story.append(Spacer(1, 6))

story.append(P(T['s3'], h2_sty))
story.append(img(f"{IMG_DIR}/chart_rally.png", 0.52))
story.append(Pcap(T['cap_rally']))
story.append(Spacer(1, 6))

story.append(P(T['s4'], h2_sty))
story.append(img(f"{IMG_DIR}/chart_p1_land.png", 0.88))
story.append(Pcap(T['cap_land_p1'].format(p1=P1_CODE)))
story.append(img(f"{IMG_DIR}/chart_yz_land.png", 0.88))
story.append(Pcap(T['cap_land_yz']))
story.append(Spacer(1, 6))

story.append(P(T['s5'], h2_sty))
story.append(img(f"{IMG_DIR}/chart_radar.png", 0.52))
story.append(Pcap(T['cap_radar']))

# Data tables
story.append(rule())
story.append(P(T['s6'], h2_sty))
story.append(P(P1_CODE, h3_sty))
story.append(p1_tbl)
story.append(Spacer(1, 10))
story.append(P('YZ', h3_sty))
story.append(yz_tbl)
story.append(Pcap(T['cap_table']))

# Insights
story.append(rule())
story.append(P(T['s7'], h2_sty))

story.append(P(P1_CODE, h3_sty))
story.append(insight('⚠️', T['ins_p1_1_title'], T['ins_p1_1_body'], '#dc2626'))
story.append(Spacer(1,5))
story.append(insight('📍', T['ins_p1_2_title'], T['ins_p1_2_body'], '#d97706'))
story.append(Spacer(1,5))
story.append(insight('✅', T['ins_p1_3_title'], T['ins_p1_3_body'], '#15803d'))
story.append(Spacer(1,5))
story.append(insight('📉', T['ins_p1_4_title'], T['ins_p1_4_body'], '#6b7280'))

story.append(Spacer(1, 10))
story.append(P('YZ', h3_sty))

if LANG == 'cn':
    yz1_body = (f'正手保持 {YZ["正手"][0]}%/{YZ["正手"][1]}%/{YZ["正手"][-1]}% 高位稳定，'
                f'速度从 {YZ["正手速度"][0]} → {YZ["正手速度"][-1]} km/h 大幅提升，速度与稳定性兼顾，是两人中表现最优的指标。')
    yz2_body = (f'反手成功率从 {YZ["反手"][0]}% → {YZ["反手"][-1]}%，'
                + T['ins_yz_2_body'].format(p1=P1_CODE))
    yz4_body = f'深区比例 {YZ["落点深"][0]}% → {YZ["落点深"][-1]}%，底线球质量在提高。'
    sh1_body = (f'最长回合 {P1["最长回合"][0]} → {P1["最长回合"][-1]}；超5回合比例 {P1["超过5回合"][0]}% → {P1["超过5回合"][-1]}%。'
                '建议每次训练安排 20–30 分钟定点多拍对打专项练习。')
else:
    yz1_body = (f'Forehand held at {YZ["正手"][0]}% / {YZ["正手"][1]}% / {YZ["正手"][-1]}% across all sessions, '
                f'while speed rose from {YZ["正手速度"][0]} → {YZ["正手速度"][-1]} km/h — the best speed-stability balance in this pair.')
    yz2_body = (f'Backhand rate: {YZ["反手"][0]}% → {YZ["反手"][-1]}%.  '
                + T['ins_yz_2_body'].format(p1=P1_CODE))
    yz4_body = f'Deep zone share: {YZ["落点深"][0]}% → {YZ["落点深"][-1]}% — baseline ball quality is gradually improving.'
    sh1_body = (f'Longest rally: {P1["最长回合"][0]} → {P1["最长回合"][-1]};  Rallies 5+: {P1["超过5回合"][0]}% → {P1["超过5回合"][-1]}%.  '
                'Allocate 20–30 min of dedicated multi-shot rally drills each session.')

story.append(insight('⭐', T['ins_yz_1_title'], yz1_body, '#15803d'))
story.append(Spacer(1,5))
story.append(insight('⚠️', T['ins_yz_2_title'], yz2_body, '#b45309'))
story.append(Spacer(1,5))
story.append(insight('📍', T['ins_yz_3_title'], T['ins_yz_3_body'], '#6b7280'))
story.append(Spacer(1,5))
story.append(insight('📈', T['ins_yz_4_title'], yz4_body, '#2563eb'))

story.append(Spacer(1, 10))
story.append(P(T['shared_trends'], h3_sty))
story.append(insight('📉', T['ins_shared_1_title'], sh1_body, '#dc2626'))
story.append(Spacer(1,5))
story.append(insight('⚡', T['ins_shared_2_title'], T['ins_shared_2_body'], '#d97706'))
story.append(Spacer(1, 8))
story.append(tip_box(T['tip_template'].format(
    spd=YZ['正手速度'][-1], pct=YZ['正手'][-1])))

# Training plan
story.append(rule())
story.append(P(T['s8'], h2_sty))
story.extend(training_plan())

# Footer
story.append(Spacer(1, 18))
story.append(rule('#e5e7eb', 0.5))
story.append(P(T['footer'].format(
    start=date_to_long(DATES[0]), end=date_to_long(DATES[-1]), n=n_sessions), foot_sty))

doc.build(story)
print(f"[{LANG.upper()}] Mobile PDF saved: {OUT}")
