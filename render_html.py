# -*- coding: utf-8 -*-
import json, io, sys, os, html
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, '_data.json'), encoding='utf-8'))
OUT = r'C:\Users\johnsywang\Desktop\服饰秋冬应季品监控看板.html'

e = html.escape
W = lambda v: f'{v/10000:.1f}'          # 元 -> 万元
N = lambda v: f'{v:,.0f}'


def pct(a, b):
    return f'{a/b*100:.1f}%' if b else '-'


# ---------------- 图表：气温 vs 应季品 ----------------
def temp_chart():
    dates, north, south = D['TEMP_DATES'], D['TEMP_NORTH'], D['TEMP_SOUTH']
    waves = D['COLD_WAVES']
    CW, CH = 1240, 440
    L, R, T, B = 66, 78, 34, 62
    tmin, tmax = 13.0, 34.0
    iw, ih = CW - L - R, CH - T - B
    step = iw / (len(dates) - 1)
    X = lambda d: L + (d - 1) * step
    Y = lambda t: T + (tmax - t) / (tmax - tmin) * ih

    s = [f'<svg viewBox="0 0 {CW} {CH}" class="chart">']
    s.append('''<defs>
    <linearGradient id="gN" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#4fc3f7" stop-opacity=".30"/>
      <stop offset="100%" stop-color="#4fc3f7" stop-opacity="0"/>
    </linearGradient></defs>''')

    # 冷空气色带
    for w in waves:
        x1, x2 = X(w['s']) - step * .45, X(w['e']) + step * .45
        s.append(f'<rect x="{x1:.1f}" y="{T}" width="{x2-x1:.1f}" height="{ih}" '
                 f'fill="#3ea6ff" opacity=".13" rx="3"/>')
        s.append(f'<text x="{(x1+x2)/2:.1f}" y="{T-12}" class="wv">{e(w["label"])}</text>')

    # 数据覆盖分界（9/18）
    xb = X(18) + step * .5
    s.append(f'<rect x="{xb:.1f}" y="{T}" width="{L+iw-xb:.1f}" height="{ih}" '
             f'fill="#ffffff" opacity=".035"/>')
    s.append(f'<line x1="{xb:.1f}" y1="{T}" x2="{xb:.1f}" y2="{T+ih}" '
             f'stroke="#ff9e5e" stroke-width="1.6" stroke-dasharray="5 4"/>')
    s.append(f'<text x="{xb+8:.1f}" y="{T+16}" class="note-sv">9/18 消耗数据截止</text>')

    # 网格 + y 轴
    for t in range(14, 35, 4):
        y = Y(t)
        s.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+iw}" y2="{y:.1f}" class="grid"/>')
        s.append(f'<text x="{L-10}" y="{y+4:.1f}" class="ax" text-anchor="end">{t}℃</text>')
    for d in dates:
        if d % 2 == 1 or d == 30:
            s.append(f'<text x="{X(d):.1f}" y="{T+ih+22}" class="ax" text-anchor="middle">{d}</text>')
    s.append(f'<text x="{L+iw/2:.1f}" y="{CH-16}" class="ax-t" text-anchor="middle">2026年9月（日）</text>')

    # 南方线
    ps = ' '.join(f'{X(d):.1f},{Y(t):.1f}' for d, t in zip(dates, south))
    s.append(f'<polyline points="{ps}" fill="none" stroke="#ffb74d" stroke-width="2.6" '
             'stroke-linejoin="round"/>')
    # 北方面积 + 线
    pn = ' '.join(f'{X(d):.1f},{Y(t):.1f}' for d, t in zip(dates, north))
    s.append(f'<polygon points="{L},{T+ih} {pn} {L+iw},{T+ih}" fill="url(#gN)"/>')
    s.append(f'<polyline points="{pn}" fill="none" stroke="#4fc3f7" stroke-width="3" '
             'stroke-linejoin="round"/>')
    for d, t in zip(dates, north):
        s.append(f'<circle cx="{X(d):.1f}" cy="{Y(t):.1f}" r="2.8" fill="#4fc3f7"/>')

    # 应季品 MTD 日均消耗基准线（右轴）
    cost = D['overall']['cost']
    yb = T + ih * .30
    s.append(f'<line x1="{L}" y1="{yb:.1f}" x2="{X(18):.1f}" y2="{yb:.1f}" '
             'stroke="#66e08f" stroke-width="2.8" stroke-dasharray="9 5"/>')
    s.append(f'<circle cx="{X(18):.1f}" cy="{yb:.1f}" r="4.5" fill="#66e08f"/>')
    s.append(f'<text x="{X(18)+10:.1f}" y="{yb-10:.1f}" class="cost-lb">'
             f'应季品日均消耗 {W(cost)}万元（9/1-9/18 均值）</text>')
    s.append(f'<text x="{L+6}" y="{yb-10:.1f}" class="cost-lb2">'
             f'在投 {N(D["overall"]["live"])} SPU｜起量 {N(D["overall"]["rise"])}</text>')
    s.append('</svg>')

    lg = ('<div class="legend">'
          '<span><i style="background:#4fc3f7"></i>北方代表城市日均气温</span>'
          '<span><i style="background:#ffb74d"></i>南方代表城市日均气温</span>'
          '<span><i style="background:#66e08f"></i>应季品日均消耗（MTD均值）</span>'
          '<span><i style="background:rgba(62,166,255,.4)"></i>冷空气过程</span>'
          '</div>')
    return ''.join(s) + lg


# ---------------- 通用表格 ----------------
def metric_table(dic, first_col, note=''):
    total = D['overall']['cost']
    rows = []
    for k, v in dic.items():
        rows.append(f'''<tr>
      <td class="nm">{e(k)}</td>
      <td class="num">{N(v['live'])}</td>
      <td class="num">{N(v['rise'])}</td>
      <td class="num rate">{v['rise_rate']:.1f}%</td>
      <td class="num boom">{N(v['boom'])}</td>
      <td class="num strong">{W(v['cost'])}</td>
      <td class="num">{pct(v['cost'], total)}</td>
      <td class="barc"><div class="bar" style="width:{min(v['cost']/total*100,100):.1f}%"></div></td>
    </tr>''')
    return f'''<table class="t">
  <thead><tr><th>{e(first_col)}</th><th>在投SPU</th><th>起量SPU</th><th>起量率</th>
  <th>爆量SPU</th><th>日均消耗(万)</th><th>消耗占比</th><th style="width:150px">占比图</th></tr></thead>
  <tbody>{''.join(rows)}</tbody></table>''' + (f'<p class="note">{note}</p>' if note else '')


def cross_table(lst, src, dst):
    rows = []
    for i, x in enumerate(lst, 1):
        st = '未投放' if not x['in_dst'] else f"已投未起量（累计{N(x['dst_ord'])}单）"
        rows.append(f'''<tr>
      <td class="num">{i}</td>
      <td class="nm2" title="{e(x['name'])}">{e(x['name'][:34])}</td>
      <td class="tag2">{e(x['cat'])}</td>
      <td class="num strong">{W(x['src_cost'])}</td>
      <td class="num">{N(x['src_ord'])}</td>
      <td class="num dim">{W(x['dst_cost'])}</td>
      <td class="st">{st}</td>
      <td class="spu">{e(x['spu'])}</td>
    </tr>''')
    return f'''<table class="t">
  <thead><tr><th style="width:38px">#</th><th>商品名称</th><th>类目</th>
  <th>{e(src)}日均消耗(万)</th><th>{e(src)}累计下单</th><th>{e(dst)}日均消耗(万)</th>
  <th>{e(dst)}状态</th><th>SPU ID</th></tr></thead>
  <tbody>{''.join(rows)}</tbody></table>'''


def dy_cards(rows):
    out = []
    for i, x in enumerate(rows, 1):
        out.append(f'''<a class="gcard" href="{e(x['url'])}" target="_blank">
      <div class="rk">{i}</div>
      <div class="ph"><img src="{e(x['img'])}" loading="lazy" alt=""
        onerror="this.parentNode.classList.add('noimg')"></div>
      <div class="gi">
        <div class="gn" title="{e(x['name'])}">{e(x['name'][:40])}</div>
        <div class="gm"><span class="vol">销量 {e(x['vol_txt'])}</span>
          <span class="lv {x['lvl']}">{'核心秋冬' if x['lvl']=='S' else '秋季过渡'}</span></div>
        <div class="gs">{e(x['leaf'])}｜{e(x['brand'] or x['shop'])}</div>
        <div class="gr">判定：{e(x['reason'])}</div>
      </div></a>''')
    return f'<div class="grid-g">{"".join(out)}</div>'


def cover_table():
    rows = []
    for x in D['cover']:
        gap = '<span class="warn">未覆盖</span>' if x['live'] == 0 else (
            '<span class="low">覆盖偏低</span>' if x['rise'] < 5 else '<span class="ok">覆盖良好</span>')
        rows.append(f'''<tr>
      <td class="nm">{e(x['dy_leaf'])}</td>
      <td class="num">{N(x['dy_vol'])}</td>
      <td class="num dim">{x['dy_n']}</td>
      <td class="tag2">{e(x['in_keys'])}</td>
      <td class="num">{N(x['live'])}</td>
      <td class="num">{N(x['rise'])}</td>
      <td class="num boom">{N(x['boom'])}</td>
      <td class="num strong">{W(x['cost'])}</td>
      <td>{gap}</td></tr>''')
    return f'''<table class="t">
  <thead><tr><th>抖音应季类目</th><th>抖音榜单销量(估)</th><th>榜单商品数</th>
  <th>对应内部类目</th><th>在投SPU</th><th>起量SPU</th><th>爆量SPU</th>
  <th>日均消耗(万)</th><th>覆盖评估</th></tr></thead>
  <tbody>{''.join(rows)}</tbody></table>'''


def leaf_table():
    rows = []
    mx = D['top_leaf'][0][1]['cost'] if D['top_leaf'] else 1
    for i, (k, v) in enumerate(D['top_leaf'], 1):
        rows.append(f'''<tr><td class="num">{i}</td><td class="nm">{e(k)}</td>
      <td class="num">{N(v['n'])}</td><td class="num">{N(v['ord'])}</td>
      <td class="num strong">{W(v['cost'])}</td>
      <td class="barc"><div class="bar" style="width:{v['cost']/mx*100:.1f}%"></div></td></tr>''')
    return f'''<table class="t">
  <thead><tr><th style="width:38px">#</th><th>应季四级类目</th><th>在投SPU</th>
  <th>累计下单</th><th>日均消耗(万)</th><th style="width:220px"></th></tr></thead>
  <tbody>{''.join(rows)}</tbody></table>'''


# ---------------- 规则表 ----------------
RULES = [
    ('L0', '硬排除', '#ff7a7a',
     '先剔除夏季品与无季节属性品，避免误判',
     '类目：T恤 / Polo衫 / 背心吊带 / 泳装 / 拖鞋凉鞋 / 防晒衣帽 / 速干裤 / 蕾丝雪纺衫<br>'
     '名称：短袖、无袖、短裤、冰丝、凉感、速干、防晒、雪纺、蕾丝、泳、拖鞋、五分/七分裤、超薄、轻薄、薄款'),
    ('L1', 'S 核心秋冬', '#ff9e5e',
     '强季节属性，降温直接驱动转化，是监控主对象',
     '类目：羽绒服 / 棉衣棉服 / 毛呢大衣 / 羊绒衫羊毛衫 / 保暖上衣·裤·套装 / 雪地靴 / 马丁靴 / '
     '冲锋衣 / 抓绒摇粒绒 / 皮衣皮草 / 连裤袜打底袜 / 长筒袜<br>'
     '名称材质：羽绒、鹅绒、鸭绒、羊绒、羊毛、德绒、摇粒绒、抓绒、加绒、貂绒、驼绒、法兰绒、灯芯绒、'
     '毛呢、加厚、夹棉、棉服棉袄棉裤、保暖、发热、蓄热、锁温、御寒、磨毛'),
    ('L2', 'A 秋季过渡', '#66e08f',
     '秋季主力款式，换季初期先起量，是拓品窗口',
     '类目：卫衣 / 夹克 / 风衣 / 短外套中长款外套 / 毛衣针织衫 / 马甲 / 打底衫 / 打底裤 / '
     '围巾披肩 / 睡衣家居服 / 新中式 / 西装套装 / 塑身衣<br>'
     '名称款式：长袖、外套、开衫、高领、堆堆领、连帽、针织、毛衣、卫衣、夹克、风衣、马甲、'
     '长款/中长款、套头、立领、秋冬/秋款/冬款'),
    ('L3', '全年款需材质佐证', '#8ea2c6',
     '避免把全年常销款整体计入应季，虚高分母',
     '休闲裤 / 牛仔裤 / 衬衫 / 各类皮鞋板鞋运动鞋 / 内裤 / 文胸 / 短袜 / 帽子 / 连衣裙 / 半身裙 等，'
     '<b>仅当 SPU 名称含 L1 秋冬材质词时</b>（如「加绒牛仔裤」「羊毛衬衫」）才计入应季，否则判非应季'),
]


def rule_cards():
    out = []
    for code, name, color, why, detail in RULES:
        out.append(f'''<div class="rc" style="--c:{color}">
      <div class="rh"><span class="rcode">{code}</span><span class="rname">{e(name)}</span></div>
      <div class="rwhy">{e(why)}</div>
      <div class="rdet">{detail}</div></div>''')
    return f'<div class="grid-r">{"".join(out)}</div>'


def wave_cards():
    out = []
    for w in D['COLD_WAVES']:
        rng = f"9/{w['s']}" + (f"-{w['e']}" if w['e'] != w['s'] else '')
        out.append(f'''<div class="wc">
      <div class="wt">{e(w['label'])}<span class="wd">{rng}</span></div>
      <div class="wx">{e(w['desc'])}</div></div>''')
    return f'<div class="grid-w">{"".join(out)}</div>'


ov = D['overall']
ova = D['overall_all']
ch = D['by_channel']
adq, qyt = ch['ADQ（非全域通）'], ch['全域通']

HTMLDOC = f'''<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>服饰秋冬应季品消耗监控看板 · 2026年9月MTD</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0b1220;color:#e8eefc;font:14px/1.6 "Microsoft YaHei","Segoe UI",sans-serif;
 -webkit-font-smoothing:antialiased}}
.wrap{{max-width:1400px;margin:0 auto;padding:30px 26px 70px}}
.hero{{background:linear-gradient(115deg,#14213d 0%,#1b2f52 45%,#123044 100%);
 border-radius:18px;padding:32px 36px;border:1px solid #27406b;position:relative;overflow:hidden}}
.hero:after{{content:"";position:absolute;right:-70px;top:-70px;width:280px;height:280px;
 background:radial-gradient(circle,#3ea6ff44,transparent 70%)}}
h1{{font-size:29px;letter-spacing:.5px}}
.sub{{color:#9fb4d8;margin-top:9px;font-size:13.5px}}
.pill{{display:inline-block;background:#3ea6ff22;border:1px solid #3ea6ff55;color:#8fd0ff;
 padding:3px 11px;border-radius:20px;font-size:12px;margin-right:7px;margin-top:11px}}
section{{margin-top:34px}}
.sh{{display:flex;align-items:center;gap:12px;margin-bottom:16px}}
.sh .no{{background:linear-gradient(135deg,#3ea6ff,#66e08f);color:#04101f;font-weight:700;
 width:30px;height:30px;border-radius:9px;display:grid;place-items:center;font-size:15px}}
.sh h2{{font-size:19.5px}}
.sh .hint{{color:#7e94b8;font-size:12.5px;margin-left:auto}}
.card{{background:#111b2e;border:1px solid #22335a;border-radius:14px;padding:22px 24px}}
.sub-h{{font-size:15px;color:#bdd2f2;margin:22px 0 11px;padding-left:10px;
 border-left:3px solid #3ea6ff;font-weight:600}}
.sub-h:first-child{{margin-top:0}}
/* KPI */
.kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}}
.k{{background:linear-gradient(160deg,#152442,#101a2e);border:1px solid #243a63;
 border-radius:13px;padding:18px 18px 16px;position:relative}}
.k .kl{{color:#8ea6cc;font-size:12.5px}}
.k .kv{{font-size:31px;font-weight:700;margin-top:5px;letter-spacing:-.5px}}
.k .ku{{font-size:14px;color:#9fb4d8;margin-left:3px;font-weight:400}}
.k .kx{{color:#6f86ab;font-size:11.5px;margin-top:6px}}
.k.hl{{background:linear-gradient(160deg,#1b3a2c,#102318);border-color:#2f6b4a}}
.k.hl .kv{{color:#66e08f}}
.k.b2 .kv{{color:#8fd0ff}}
.k.b3 .kv{{color:#ffb74d}}
/* 2 端对比 */
.duo{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:4px}}
.dbox{{background:#0e1830;border:1px solid #22335a;border-radius:13px;padding:19px 21px}}
.dbox h3{{font-size:16px;display:flex;align-items:center;gap:8px}}
.dbox h3 em{{font-style:normal;font-size:11.5px;color:#7e94b8;font-weight:400}}
.dline{{margin-top:14px;font-size:14.6px;line-height:2.1;color:#cfdcf2}}
.dline b{{color:#fff;font-size:18px;font-weight:700}}
.dline .g{{color:#66e08f}}.dline .o{{color:#ffb74d}}.dline .bl{{color:#8fd0ff}}
.dbox.adq{{border-left:3px solid #3ea6ff}}
.dbox.qyt{{border-left:3px solid #b78cff}}
/* 表格 */
.t{{width:100%;border-collapse:collapse;margin-top:6px;font-size:13.2px}}
.t th{{background:#16243f;color:#9fb4d8;font-weight:600;padding:10px 11px;text-align:right;
 border-bottom:1px solid #27406b;white-space:nowrap;font-size:12.5px}}
.t th:first-child,.t th:nth-child(2){{text-align:left}}
.t td{{padding:9px 11px;border-bottom:1px solid #1b2942;text-align:right}}
.t tbody tr:hover{{background:#16243f88}}
.t .nm{{text-align:left;color:#e8eefc;font-weight:600}}
.t .nm2{{text-align:left;color:#dce7f8}}
.t .num{{font-variant-numeric:tabular-nums}}
.t .strong{{color:#66e08f;font-weight:700;font-size:14px}}
.t .rate{{color:#8fd0ff}}
.t .boom{{color:#ffb74d;font-weight:600}}
.t .dim{{color:#6f86ab}}
.t .tag2{{text-align:left;color:#9fb4d8;font-size:12.3px}}
.t .st{{text-align:left;color:#ffb74d;font-size:12.3px}}
.t .spu{{text-align:left;color:#5c718f;font-size:11.5px;font-family:Consolas,monospace}}
.barc{{padding:9px 11px!important}}
.bar{{height:7px;background:linear-gradient(90deg,#3ea6ff,#66e08f);border-radius:4px;min-width:2px}}
.warn{{color:#ff7a7a;background:#ff7a7a1c;padding:2px 8px;border-radius:5px;font-size:12px}}
.low{{color:#ffb74d;background:#ffb74d1c;padding:2px 8px;border-radius:5px;font-size:12px}}
.ok{{color:#66e08f;background:#66e08f1c;padding:2px 8px;border-radius:5px;font-size:12px}}
.note{{color:#7e94b8;font-size:12.3px;margin-top:11px;padding:9px 12px;background:#0e1830;
 border-left:2px solid #3ea6ff66;border-radius:0 7px 7px 0}}
/* 规则卡 */
.grid-r{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
.rc{{background:#0e1830;border:1px solid #22335a;border-left:3px solid var(--c);
 border-radius:11px;padding:17px 19px}}
.rh{{display:flex;align-items:center;gap:10px}}
.rcode{{background:var(--c);color:#06101d;font-weight:700;font-size:11.5px;padding:2px 8px;border-radius:5px}}
.rname{{font-size:15.5px;font-weight:700;color:var(--c)}}
.rwhy{{color:#9fb4d8;font-size:12.6px;margin:8px 0 10px}}
.rdet{{color:#cfdcf2;font-size:12.8px;line-height:1.95}}
.rdet b{{color:#ffb74d}}
/* 图表 */
.chart{{width:100%;height:auto;display:block}}
.grid{{stroke:#1e2d4b;stroke-width:1}}
.ax{{fill:#7e94b8;font-size:11.5px}}
.ax-t{{fill:#9fb4d8;font-size:12.5px}}
.wv{{fill:#8fd0ff;font-size:11.5px;text-anchor:middle}}
.note-sv{{fill:#ff9e5e;font-size:11.5px}}
.cost-lb{{fill:#66e08f;font-size:13px;font-weight:700}}
.cost-lb2{{fill:#9fb4d8;font-size:11.5px}}
.legend{{display:flex;gap:22px;flex-wrap:wrap;justify-content:center;margin-top:8px;
 color:#9fb4d8;font-size:12.5px}}
.legend i{{display:inline-block;width:13px;height:4px;border-radius:2px;margin-right:6px;
 vertical-align:middle}}
.grid-w{{display:grid;grid-template-columns:repeat(5,1fr);gap:11px;margin-top:18px}}
.wc{{background:#0e1830;border:1px solid #22335a;border-radius:10px;padding:13px 14px}}
.wt{{font-size:13.5px;font-weight:700;color:#8fd0ff}}
.wd{{display:block;color:#ffb74d;font-size:12px;font-weight:600;margin-top:2px}}
.wx{{color:#9fb4d8;font-size:11.8px;margin-top:7px;line-height:1.7}}
/* 抖音卡片 */
.tabs{{display:flex;gap:8px;margin-bottom:16px}}
.tab{{background:#16243f;border:1px solid #27406b;color:#9fb4d8;padding:7px 18px;
 border-radius:8px;cursor:pointer;font-size:13.5px;user-select:none}}
.tab.on{{background:linear-gradient(135deg,#3ea6ff,#66e08f);color:#04101f;font-weight:700;
 border-color:transparent}}
.pane{{display:none}}.pane.on{{display:block}}
.grid-g{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}
.gcard{{background:#0e1830;border:1px solid #22335a;border-radius:11px;overflow:hidden;
 text-decoration:none;color:inherit;position:relative;transition:.15s;display:block}}
.gcard:hover{{border-color:#3ea6ff;transform:translateY(-2px)}}
.rk{{position:absolute;left:8px;top:8px;z-index:2;background:#04101fcc;color:#66e08f;
 font-size:11.5px;font-weight:700;width:22px;height:22px;border-radius:6px;display:grid;
 place-items:center}}
.ph{{aspect-ratio:1;background:#16243f;overflow:hidden}}
.ph img{{width:100%;height:100%;object-fit:cover;display:block}}
.ph.noimg:after{{content:"图片需外网";display:grid;place-items:center;height:100%;
 color:#5c718f;font-size:11.5px}}
.ph.noimg img{{display:none}}
.gi{{padding:10px 11px 12px}}
.gn{{font-size:12.4px;line-height:1.55;height:3.1em;overflow:hidden;color:#e8eefc}}
.gm{{display:flex;align-items:center;gap:6px;margin-top:7px;flex-wrap:wrap}}
.vol{{color:#66e08f;font-size:12px;font-weight:700}}
.lv{{font-size:10.5px;padding:1px 6px;border-radius:4px}}
.lv.S{{background:#ff9e5e26;color:#ff9e5e}}
.lv.A{{background:#66e08f26;color:#66e08f}}
.gs{{color:#7e94b8;font-size:11.3px;margin-top:5px;white-space:nowrap;overflow:hidden;
 text-overflow:ellipsis}}
.gr{{color:#5c718f;font-size:10.8px;margin-top:4px}}
.foot{{margin-top:40px;color:#5c718f;font-size:12px;text-align:center;line-height:1.9;
 border-top:1px solid #1b2942;padding-top:20px}}
@media(max-width:1200px){{.kpis{{grid-template-columns:repeat(3,1fr)}}
 .grid-g,.grid-w{{grid-template-columns:repeat(3,1fr)}}
 .duo,.grid-r{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">

<div class="hero">
  <h1>服饰秋冬应季品消耗监控看板</h1>
  <div class="sub">数据窗口：2026年9月1日 — 9月18日（MTD 18天）｜口径：SPU 去重计商品数，消耗与下单次数加总</div>
  <div>
    <span class="pill">大盘日均消耗 {W(D['TOTAL_COST_ALL'])} 万元</span>
    <span class="pill">应季品占大盘 {pct(ov['cost'], D['TOTAL_COST_ALL'])}</span>
    <span class="pill">起量线：累计下单 &gt; 110 次</span>
    <span class="pill">爆量线：日均消耗 &gt; 1 万元</span>
    <span class="pill">生成时间 2026-09-20</span>
  </div>
</div>

<section>
  <div class="sh"><span class="no">1</span><h2>秋冬应季品判定规则</h2>
    <span class="hint">双通道判定：商品四级类目 + SPU 名称材质/款式词，排除优先于命中</span></div>
  <div class="card">{rule_cards()}
    <p class="note">判定结果：全库 {N(ova['live'])} 个在投 SPU 中识别出 <b>{N(ov['live'])}</b> 个秋冬应季品
    （占比 {pct(ov['live'], ova['live'])}），其中 S 核心秋冬 {N(D['by_lvl']['S 核心秋冬']['live'])} 个、
    A 秋季过渡 {N(D['by_lvl']['A 秋季过渡']['live'])} 个。
    同一 SPU 若在多个类目/链路/投放端有投放记录，分维度统计时会在各维度分别计数，
    因此分维度在投数之和 ≥ 应季品去重总数。</p>
  </div>
</section>

<section>
  <div class="sh"><span class="no">2</span><h2>应季品业绩总览</h2>
    <span class="hint">9月MTD 全量应季品</span></div>
  <div class="card">
    <div class="kpis">
      <div class="k b2"><div class="kl">在投应季商品数</div>
        <div class="kv">{N(ov['live'])}<span class="ku">个</span></div>
        <div class="kx">SPU 去重｜占全库在投 {pct(ov['live'], ova['live'])}</div></div>
      <div class="k"><div class="kl">起量商品数</div>
        <div class="kv">{N(ov['rise'])}<span class="ku">个</span></div>
        <div class="kx">累计下单&gt;110次｜起量率 {ov['rise_rate']:.1f}%</div></div>
      <div class="k b3"><div class="kl">爆量商品数</div>
        <div class="kv">{N(ov['boom'])}<span class="ku">个</span></div>
        <div class="kx">日均消耗&gt;1万元｜爆量率 {pct(ov['boom'], ov['live'])}</div></div>
      <div class="k hl"><div class="kl">应季品日均消耗</div>
        <div class="kv">{W(ov['cost'])}<span class="ku">万元</span></div>
        <div class="kx">占大盘 {pct(ov['cost'], D['TOTAL_COST_ALL'])}</div></div>
      <div class="k"><div class="kl">应季品户均日耗</div>
        <div class="kv">{ov['cost']/ov['live']:,.0f}<span class="ku">元</span></div>
        <div class="kx">全库均值 {ova['cost']/ova['live']:,.0f} 元</div></div>
    </div>

    <div class="sub-h">2.1 分投放端</div>
    <div class="duo">
      <div class="dbox adq"><h3>ADQ<em>是否全域通 = false</em></h3>
        <div class="dline">在投 spu 数 <b class="bl">{N(adq['live'])}</b> 个，
          起量 spu 数 <b class="g">{N(adq['rise'])}</b> 个（起量率 {adq['rise_rate']:.1f}%），
          爆量 spu 数 <b class="o">{N(adq['boom'])}</b> 个，
          共带来日均消耗 <b class="g">{W(adq['cost'])}</b> 万元
          （占应季品 {pct(adq['cost'], ov['cost'])}）。</div></div>
      <div class="dbox qyt"><h3>全域通<em>是否全域通 = true</em></h3>
        <div class="dline">在投 spu 数 <b class="bl">{N(qyt['live'])}</b> 个，
          起量 spu 数 <b class="g">{N(qyt['rise'])}</b> 个（起量率 {qyt['rise_rate']:.1f}%），
          爆量 spu 数 <b class="o">{N(qyt['boom'])}</b> 个，
          共带来日均消耗 <b class="g">{W(qyt['cost'])}</b> 万元
          （占应季品 {pct(qyt['cost'], ov['cost'])}）。</div></div>
    </div>
    {metric_table(ch, '投放端')}
    <p class="note">全域通在投 SPU 数已超过 ADQ（{N(qyt['live'])} vs {N(adq['live'])}），
    但消耗仅为 ADQ 的 {qyt['cost']/adq['cost']*100:.0f}%、爆量 SPU 仅 {N(qyt['boom'])} 个，
    说明全域通侧仍处于"铺量未起量"阶段，单 SPU 产出（{qyt['cost']/qyt['live']:,.0f} 元 vs
    ADQ {adq['cost']/adq['live']:,.0f} 元）差距明显，是换季期重点提效方向。</p>

    <div class="sub-h">2.2 分类目</div>
    {metric_table(D['by_cat'], '类目',
      '类目口径：取「商品统一类目V2」首个"-"后文字，命中 男装/女装/内衣裤袜·睡衣·家居服/男鞋/女鞋 则归入该二级类目；'
      '否则取首个"-"前文字，命中 珠宝·首饰·手表/运动户外 则归入该一级类目；其余（含类目为「空」「0」的记录）统一归入「其他」。')}

    <div class="sub-h">2.3 分消费链路</div>
    {metric_table(D['by_link'], '消费链路')}
    <p class="note">小店链路铺量最广（{N(D['by_link']['小店']['live'])} SPU）但户均日耗最低；
    CID 链路以 {N(D['by_link']['CID']['live'])} 个 SPU 贡献 {W(D['by_link']['CID']['cost'])} 万元，
    爆量 SPU 达 {N(D['by_link']['CID']['boom'])} 个（全链路最多），单 SPU 产出
    {D['by_link']['CID']['cost']/D['by_link']['CID']['live']:,.0f} 元，为效率最高链路。</p>

    <div class="sub-h">2.4 分应季等级</div>
    {metric_table(D['by_lvl'], '应季等级',
      'A 秋季过渡款（卫衣/夹克/外套/针织等）当前仍是消耗主力，S 核心秋冬款（羽绒/棉服/保暖/毛呢等）'
      '在投 SPU 已达一定规模但爆量仅 ' + N(D['by_lvl']['S 核心秋冬']['boom']) + ' 个，'
      '随 9 月下旬冷空气密集期到来，S 层是最需要提前备量与加投的品类。')}

    <div class="sub-h">2.5 应季品 TOP20 细分类目</div>
    {leaf_table()}
  </div>
</section>

<section>
  <div class="sh"><span class="no">3</span><h2>气温趋势 × 应季品消耗对比</h2>
    <span class="hint">气温节点来源：中央气象台 / 中国气象局 2026年9月公开通报</span></div>
  <div class="card">
    {temp_chart()}
    {wave_cards()}
    <p class="note"><b>降温节点解读：</b>9月呈"北方阶梯式降温、南方秋老虎持续"的南北分裂格局。
    北方代表城市日均气温从月初 27-28℃ 降至下旬 15-19℃，累计降幅超 10℃；
    <b>9/19 起至月底连续 4 轮冷空气</b>（19-21日、23-24日、25-26日、30日前后）强度逐渐增强，
    是秋冬应季品需求释放的关键窗口；南方同期仅从 32℃ 缓降至 27℃ 左右，
    秋冬品放量节奏应显著晚于北方，建议分区域差异化投放。</p>
    <p class="note"><b>数据口径说明：</b>当前源表仅提供 9/1-9/18 的 <b>18 天平均值</b>（日均消耗、日均下单次数），
    不含逐日明细，因此消耗侧只能以 MTD 日均基准线（绿色虚线 {W(ov['cost'])} 万元/天）呈现，
    无法绘制真实逐日曲线。如需完整的"降温节点 → 消耗爬升"弹性验证，
    需补充按日期维度拆分的逐日消耗数据（建议拉取 9/1-9/30 分日快照）。
    气温曲线为基于上述公开通报的冷空气节点与南北格局还原的趋势示意，非逐日实测站点均值。</p>
  </div>
</section>

<section>
  <div class="sh"><span class="no">4</span><h2>拓品清单</h2>
    <span class="hint">已验证的确定性货品，跨端 / 跨链路复制</span></div>
  <div class="card">
    <div class="sub-h">4.1 全域通反拓 ADQ — 全域通已起量、ADQ 未起量 TOP10</div>
    {cross_table(D['list_qyt2adq'], '全域通', 'ADQ')}
    <p class="note">筛选逻辑：应季品中，在「是否全域通=true」侧累计下单 &gt; 110 次（已起量），
    但在「是否全域通=false」侧累计下单 ≤ 110 次（未起量，含完全未投放），按全域通侧日均消耗降序取 TOP10。
    这批商品已由全域通验证过转化能力，可直接在 ADQ 侧建计划复制。</p>

    <div class="sub-h">4.2 CID 反拓小店直购 — CID 已起量、小店未起量 TOP10</div>
    {cross_table(D['list_cid2shop'], 'CID', '小店')}
    <p class="note">筛选逻辑同上，源链路为 CID、目标链路为小店。CID 链路本身单 SPU 产出最高，
    这批商品在 CID 已跑出规模，小店直购链路承接后可进一步放大自然流量与复购。</p>
  </div>
</section>

<section>
  <div class="sh"><span class="no">5</span><h2>抖音高 GMV 应季品覆盖</h2>
    <span class="hint">抖音9月商品销售榜 TOP1000（销售额均 100w+）｜应季品 {N(D['dy_season_n'])}/{N(D['dy_n'])} 个</span></div>
  <div class="card">
    <div class="kpis">
      <div class="k b2"><div class="kl">抖音榜单应季商品</div>
        <div class="kv">{N(D['dy_season_n'])}<span class="ku">个</span></div>
        <div class="kx">按同一规则筛选｜占 TOP1000 的 {pct(D['dy_season_n'], D['dy_n'])}</div></div>
      <div class="k"><div class="kl">对标类目内部在投</div>
        <div class="kv">{N(D['cover_total']['live'])}<span class="ku">个</span></div>
        <div class="kx">SPU 去重</div></div>
      <div class="k b3"><div class="kl">对标类目内部起量</div>
        <div class="kv">{N(D['cover_total']['rise'])}<span class="ku">个</span></div>
        <div class="kx">起量率 {D['cover_total']['rise_rate']:.1f}%｜爆量 {N(D['cover_total']['boom'])} 个</div></div>
      <div class="k hl"><div class="kl">对标类目日均消耗</div>
        <div class="kv">{W(D['cover_total']['cost'])}<span class="ku">万元</span></div>
        <div class="kx">占应季品总消耗 {pct(D['cover_total']['cost'], ov['cost'])}</div></div>
      <div class="k"><div class="kl">未覆盖类目数</div>
        <div class="kv">{sum(1 for x in D['cover'] if x['live']==0)}<span class="ku">个</span></div>
        <div class="kx">抖音有高销、内部零在投</div></div>
    </div>

    <div class="sub-h">5.1 抖音应季热销商品 TOP20（分类目）</div>
    <div class="tabs">
      <div class="tab on" data-p="p1">女装 TOP20</div>
      <div class="tab" data-p="p2">男装 TOP20</div>
      <div class="tab" data-p="p3">内衣 TOP20</div>
    </div>
    <div class="pane on" id="p1">{dy_cards(D['dy_top']['女装'])}</div>
    <div class="pane" id="p2">{dy_cards(D['dy_top']['男装'])}</div>
    <div class="pane" id="p3">{dy_cards(D['dy_top']['内衣'])}</div>
    <p class="note">排序依据：榜单「销量」区间中值（榜单销售额字段 1000 条均为 100w+，无区分度）。
    商品图片来自抖音 CDN，需外网环境才能加载。点击卡片可跳转抖音商品页。</p>

    <div class="sub-h">5.2 抖音热销应季类目 × 内部投放覆盖</div>
    {cover_table()}
    <p class="note">匹配口径：抖音榜单与内部投放表无共用商品 ID，故采用<b>类目级映射</b>匹配
    （抖音四级叶子类目 → 内部四级类目，如 抖音「针织衫/毛衣/羊毛衫」→ 内部「毛衣/针织衫」+「羊绒衫/羊毛衫」）。
    标注「未覆盖」的类目表示抖音有 100w+ 销售额的高 GMV 应季商品，但内部同类目零在投，是最高优先级的拓品缺口；
    「覆盖偏低」表示内部起量 SPU 少于 5 个，供给厚度不足。</p>
  </div>
</section>

<div class="foot">
  数据来源：内部服饰换季品监控明细表（9/1-9/18，18天均值）｜抖音9月商品销售榜 TOP1000<br>
  气温信息来源：中央气象台、中国气象局 2026年9月公开通报与新闻发布会<br>
  口径提示：商品数按 SPUid 去重；日均消耗与日均下单次数按行加总；累计下单次数 = 日均下单次数 × 18
</div>
</div>
<script>
document.querySelectorAll('.tab').forEach(function(t){{
  t.addEventListener('click',function(){{
    document.querySelectorAll('.tab').forEach(function(x){{x.classList.remove('on')}});
    document.querySelectorAll('.pane').forEach(function(x){{x.classList.remove('on')}});
    t.classList.add('on');
    document.getElementById(t.dataset.p).classList.add('on');
  }});
}});
</script>
</body></html>'''

open(OUT, 'w', encoding='utf-8').write(HTMLDOC)
print('写出:', OUT, len(HTMLDOC), 'chars')
