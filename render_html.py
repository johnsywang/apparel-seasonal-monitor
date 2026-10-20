# -*- coding: utf-8 -*-
import json, io, sys, os, html
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
MONTH = sys.argv[1] if len(sys.argv) > 1 else '10'
D = json.load(open(os.path.join(HERE, f'_data_{MONTH}.json'), encoding='utf-8'))
M = D['META']
P = (json.load(open(os.path.join(HERE, f'_data_{M["prev"]}.json'), encoding='utf-8'))
     if M.get('prev') else None)
PM = P['META'] if P else None
OUT = (r'C:\Users\johnsywang\Desktop\服饰秋冬应季品监控看板_9月重渲染.html' if MONTH == '09'
       else rf'C:\Users\johnsywang\Desktop\服饰秋冬应季品监控看板_{M["label"]}.html')

e = html.escape
W = lambda v: f'{v/10000:.1f}'          # 元 -> 万元
N = lambda v: f'{v:,.0f}'


def pct(a, b):
    return f'{a/b*100:.1f}%' if b else '-'


def chg(c, p):
    """环比涨跌标签"""
    if p is None:
        return ''
    if not p:
        return '<span class="mm up">新增</span>' if c else '<span class="mm flat">-</span>'
    r = (c - p) / p * 100
    if abs(r) < 0.05:
        return '<span class="mm flat">0.0%</span>'
    return f'<span class="mm {"up" if r > 0 else "dn"}">{"▲" if r > 0 else "▼"}{abs(r):.1f}%</span>'


def chg_pp(c, p):
    if p is None:
        return ''
    d = c - p
    if abs(d) < 0.05:
        return '<span class="mm flat">0.0pp</span>'
    return f'<span class="mm {"up" if d > 0 else "dn"}">{"+" if d > 0 else "−"}{abs(d):.1f}pp</span>'


def ratio(c, p):
    return (c - p) / p * 100 if p else 0.0


def prev_of(group, key):
    return P[group].get(key) if P else None


# ---------------- 图表：气温 vs 应季品 ----------------
def temp_chart():
    dates, north, south = D['TEMP_DATES'], D['TEMP_NORTH'], D['TEMP_SOUTH']
    waves = D['COLD_WAVES']
    nd, ed, mo = M['n_days'], M['end_day'], int(M['month'])
    CW, CH = 1240, 440
    L, R, T, B = 66, 78, 34, 62
    tmin, tmax = (13.0, 34.0) if mo == 9 else (8.0, 30.0)
    iw, ih = CW - L - R, CH - T - B
    step = iw / (nd - 1)
    X = lambda d: L + (d - 1) * step
    Y = lambda t: T + (tmax - t) / (tmax - tmin) * ih

    s = [f'<svg viewBox="0 0 {CW} {CH}" class="chart">']
    s.append('''<defs>
    <linearGradient id="gN" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#4fc3f7" stop-opacity=".30"/>
      <stop offset="100%" stop-color="#4fc3f7" stop-opacity="0"/>
    </linearGradient></defs>''')

    # 冷空气色带：实况实心 / 预报虚线框 / 信号点线框
    WSTY = {'obs': ('#3ea6ff', '.13', ''), 'proc': ('#8ea2c6', '.12', ''),
            'fc': ('#3ea6ff', '.06', 'stroke="#3ea6ff" stroke-width="1.2" stroke-dasharray="5 4"'),
            'sig': ('#b78cff', '.06', 'stroke="#b78cff" stroke-width="1.2" stroke-dasharray="2 3"')}
    for i, w in enumerate(waves):
        c, op, stk = WSTY.get(w.get('kind', 'obs'), WSTY['obs'])
        x1, x2 = X(w['s']) - step * .45, X(w['e']) + step * .45
        s.append(f'<rect x="{x1:.1f}" y="{T}" width="{x2-x1:.1f}" height="{ih}" '
                 f'fill="{c}" fill-opacity="{op}" {stk} rx="3"/>')
        ly = T - 12 - (10 if (mo != 9 and i % 2) else 0)
        s.append(f'<text x="{(x1+x2)/2:.1f}" y="{ly}" class="wv">{e(w["label"])}</text>')

    # 数据覆盖分界
    xb = X(ed) + step * .5
    s.append(f'<rect x="{xb:.1f}" y="{T}" width="{L+iw-xb:.1f}" height="{ih}" '
             f'fill="#ffffff" opacity=".035"/>')
    s.append(f'<line x1="{xb:.1f}" y1="{T}" x2="{xb:.1f}" y2="{T+ih}" '
             f'stroke="#ff9e5e" stroke-width="1.6" stroke-dasharray="5 4"/>')
    s.append(f'<text x="{xb+8:.1f}" y="{T+ih-12}" class="note-sv">{M["end"]} 消耗数据截止</text>')

    # 网格 + y 轴
    for t in range(int(tmin) + (int(tmin) % 2), int(tmax) + 1, 4):
        y = Y(t)
        s.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+iw}" y2="{y:.1f}" class="grid"/>')
        s.append(f'<text x="{L-10}" y="{y+4:.1f}" class="ax" text-anchor="end">{t}℃</text>')
    for d in range(1, nd + 1):
        if d % 2 == 1 or d == nd:
            s.append(f'<text x="{X(d):.1f}" y="{T+ih+22}" class="ax" text-anchor="middle">{d}</text>')
    s.append(f'<text x="{L+iw/2:.1f}" y="{CH-16}" class="ax-t" text-anchor="middle">2026年{mo}月（日）</text>')

    # 南方线
    ps = ' '.join(f'{X(d):.1f},{Y(t):.1f}' for d, t in zip(dates, south))
    s.append(f'<polyline points="{ps}" fill="none" stroke="#ffb74d" stroke-width="2.6" '
             'stroke-linejoin="round"/>')
    # 北方面积 + 线
    pn = ' '.join(f'{X(d):.1f},{Y(t):.1f}' for d, t in zip(dates, north))
    s.append(f'<polygon points="{X(dates[0]):.1f},{T+ih} {pn} {X(dates[-1]):.1f},{T+ih}" fill="url(#gN)"/>')
    s.append(f'<polyline points="{pn}" fill="none" stroke="#4fc3f7" stroke-width="3" '
             'stroke-linejoin="round"/>')
    for d, t in zip(dates, north):
        s.append(f'<circle cx="{X(d):.1f}" cy="{Y(t):.1f}" r="2.8" fill="#4fc3f7"/>')

    # 应季品 MTD 日均消耗基准线；有上月时同时画上月基准线
    cost = D['overall']['cost']
    yb = T + ih * .30
    s.append(f'<line x1="{L}" y1="{yb:.1f}" x2="{X(ed):.1f}" y2="{yb:.1f}" '
             'stroke="#66e08f" stroke-width="2.8" stroke-dasharray="9 5"/>')
    s.append(f'<circle cx="{X(ed):.1f}" cy="{yb:.1f}" r="4.5" fill="#66e08f"/>')
    s.append(f'<text x="{X(ed)+10:.1f}" y="{yb-10:.1f}" class="cost-lb">'
             f'应季品日均消耗 {W(cost)}万元（{M["start"]}-{M["end"]} 均值）</text>')
    s.append(f'<text x="{L+6}" y="{yb-10:.1f}" class="cost-lb2">'
             f'在投 {N(D["overall"]["live"])} SPU｜起量 {N(D["overall"]["rise"])}</text>')
    if P:
        pc = P['overall']['cost']
        yp = yb + ih * .30 * (1 - pc / cost) if cost else yb
        s.append(f'<line x1="{L}" y1="{yp:.1f}" x2="{X(ed):.1f}" y2="{yp:.1f}" '
                 'stroke="#8ea2c6" stroke-width="2" stroke-dasharray="3 5"/>')
        s.append(f'<text x="{X(ed)+10:.1f}" y="{yp+4:.1f}" class="cost-lb2">'
                 f'{PM["label"]}基准 {W(pc)}万元 → 环比 {ratio(cost, pc):+.1f}%</text>')
    s.append('</svg>')

    lg = ('<div class="legend">'
          '<span><i style="background:#4fc3f7"></i>北方代表城市日均气温（示意）</span>'
          '<span><i style="background:#ffb74d"></i>南方代表城市日均气温（示意）</span>'
          '<span><i style="background:#66e08f"></i>应季品日均消耗（MTD均值）</span>'
          + (f'<span><i style="background:#8ea2c6"></i>{PM["label"]}应季品日均消耗</span>' if P else '')
          + '<span><i style="background:rgba(62,166,255,.4)"></i>冷空气实况</span>'
          + ('<span><i style="background:transparent;border:1px dashed #3ea6ff;height:8px"></i>冷空气预报</span>'
             '<span><i style="background:transparent;border:1px dotted #b78cff;height:8px"></i>日期信号</span>'
             if any(w.get('kind') in ('fc', 'sig') for w in waves) else '')
          + '</div>')
    return ''.join(s) + lg


# ---------------- 通用表格 ----------------
def metric_table(dic, first_col, note='', group=None):
    total = D['overall']['cost']
    mom = bool(P and group)
    rows = []
    for k, v in dic.items():
        pv = prev_of(group, k) if mom else None
        mcell = ''
        if mom:
            mcell = (f'<td class="num">{chg(v["cost"], pv["cost"] if pv else 0)}</td>'
                     f'<td class="num">{chg(v["live"], pv["live"] if pv else 0)}</td>')
        rows.append(f'''<tr>
      <td class="nm">{e(k)}</td>
      <td class="num">{N(v['live'])}</td>
      <td class="num">{N(v['rise'])}</td>
      <td class="num rate">{v['rise_rate']:.1f}%</td>
      <td class="num boom">{N(v['boom'])}</td>
      <td class="num strong">{W(v['cost'])}</td>
      <td class="num">{pct(v['cost'], total)}</td>{mcell}
      <td class="barc"><div class="bar" style="width:{min(v['cost']/total*100,100):.1f}%"></div></td>
    </tr>''')
    mh = (f'<th>消耗环比</th><th>在投环比</th>' if mom else '')
    return f'''<table class="t">
  <thead><tr><th>{e(first_col)}</th><th>在投SPU</th><th>起量SPU</th><th>起量率</th>
  <th>爆量SPU</th><th>日均消耗(万)</th><th>消耗占比</th>{mh}<th style="width:150px">占比图</th></tr></thead>
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


def cat_tree_table():
    """1~4 级类目层级明细，可折叠展开（仅 3 个一级类目）"""
    tree = D['cat_tree']
    sc = D['tree_scope']
    total = sc['cost']
    mx = max((n['cost'] for n in tree if n['lvl'] == 1), default=1)
    LV_NAME = {1: '一级', 2: '二级', 3: '三级', 4: '四级'}
    rows = [f'''<tr class="tr-sum" data-lvl="0" data-path="__sum__"
      data-parent="__none__" data-kid="0">
      <td class="lvc"><span class="lvt lsum">合计</span></td>
      <td class="nmt"><span class="cr dot">Σ</span><span class="ct">三大一级类目合计</span></td>
      <td class="num">{N(sc['live'])}</td>
      <td class="num">{N(sc['rise'])}</td>
      <td class="num rate">{sc['rise_rate']:.1f}%</td>
      <td class="num boom">{N(sc['boom'])}</td>
      <td class="num">{N(sc['orders'])}</td>
      <td class="num strong">{W(sc['cost'])}</td>
      <td class="num">100.0%</td>
      <td class="num dim">占应季品 {pct(sc['cost'], D['overall']['cost'])}</td>
      <td class="barc"><div class="bar" style="width:100%"></div></td>
    </tr>''']
    for n in tree:
        lv = n['lvl']
        # 默认只展开到二级：三、四级初始隐藏
        cls = f'tr-l{lv}' + ('' if lv <= 2 else ' hid')
        caret = ('<span class="cr">▶</span>' if n['has_kid']
                 else '<span class="cr dot">·</span>')
        barw = min(n['cost'] / mx * 100, 100) if lv == 1 else min(n['cost'] / total * 100 * 2.2, 100)
        s = n['s_share']
        sbadge = (f'<span class="sb s-hi">S {s:.0f}%</span>' if s >= 60 else
                  f'<span class="sb s-mid">S {s:.0f}%</span>' if s >= 25 else
                  f'<span class="sb s-lo">S {s:.0f}%</span>')
        rows.append(f'''<tr class="{cls}" data-path="{e(n['path'])}"
      data-parent="{e(n['parent'])}" data-lvl="{lv}" data-kid="{1 if n['has_kid'] else 0}">
      <td class="lvc"><span class="lvt l{lv}">{LV_NAME[lv]}</span></td>
      <td class="nmt">{caret}<span class="ct">{e(n['name'])}</span></td>
      <td class="num">{N(n['live'])}</td>
      <td class="num">{N(n['rise'])}</td>
      <td class="num rate">{n['rise_rate']:.1f}%</td>
      <td class="num boom">{N(n['boom'])}</td>
      <td class="num">{N(n['orders'])}</td>
      <td class="num strong">{W(n['cost'])}</td>
      <td class="num">{pct(n['cost'], total)}</td>
      <td>{sbadge}</td>
      <td class="barc"><div class="bar" style="width:{barw:.1f}%"></div></td>
    </tr>''')
    scope = '、'.join(D['tree_roots'])
    return f'''<div class="tt-bar">
  <span class="tb" data-act="e2">展开到二级</span>
  <span class="tb" data-act="e3">展开到三级</span>
  <span class="tb" data-act="e4">全部展开（四级）</span>
  <span class="tb" data-act="c1">全部收起</span>
  <span class="scope-tag">统计范围：{e(scope)}</span>
  <span class="tt-hint">点击行首 ▶ 可逐级展开；共 {len(tree)} 个类目节点
  （一级 {sum(1 for n in tree if n['lvl']==1)} / 二级 {sum(1 for n in tree if n['lvl']==2)}
   / 三级 {sum(1 for n in tree if n['lvl']==3)} / 四级 {sum(1 for n in tree if n['lvl']==4)}）</span>
</div>
<div class="tw"><table class="t tt">
  <thead><tr><th style="width:52px">层级</th><th style="min-width:230px">类目名称</th>
  <th>在投SPU</th><th>起量SPU</th><th>起量率</th><th>爆量SPU</th><th>累计下单</th>
  <th>日均消耗(万)</th><th>消耗占比</th><th style="width:74px">S层占比</th>
  <th style="width:130px">消耗强度</th></tr></thead>
  <tbody>{''.join(rows)}</tbody></table></div>'''


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
    KTAG = {'obs': '实况', 'proc': '过程报道', 'fc': '预报', 'sig': '信号'}
    mo = int(M['month'])
    out = []
    for w in D['COLD_WAVES']:
        rng = f"{mo}/{w['s']}" + (f"-{w['e']}" if w['e'] != w['s'] else '')
        k = w.get('kind', 'obs')
        tag = f'<span class="wk {k}">{KTAG[k]}</span>' if mo != 9 else ''
        out.append(f'''<div class="wc {k}">
      <div class="wt">{e(w['label'])}<span class="wd">{rng}{tag}</span></div>
      <div class="wx">{e(w['desc'])}</div></div>''')
    cols = min(len(out), 5) if len(out) <= 5 else 4
    return f'<div class="grid-w" style="grid-template-columns:repeat({cols},1fr)">{"".join(out)}</div>'


# ---------------- 月环比 ----------------
def mom_section():
    if not P:
        return ''
    ov, pv = D['overall'], P['overall']
    oa, pa = D['overall_all'], P['overall_all']
    tc, tp = D['TOTAL_COST_ALL'], P['TOTAL_COST_ALL']
    sh_c, sh_p = ov['cost'] / tc * 100, pv['cost'] / tp * 100
    avg_c, avg_p = ov['cost'] / ov['live'], pv['cost'] / pv['live']
    L, PL = M['label'], PM['label']

    def kc(title, cur, prev, unit, fmt, delta_html, cls=''):
        return f'''<div class="k {cls}"><div class="kl">{title}</div>
      <div class="kv">{fmt(cur)}<span class="ku">{unit}</span></div>
      <div class="kx">{PL} {fmt(prev)}{unit}　{delta_html}</div></div>'''

    kpis = ''.join([
        kc('大盘日均消耗', tc, tp, '万', W, chg(tc, tp), 'b2'),
        kc('应季品日均消耗', ov['cost'], pv['cost'], '万', W, chg(ov['cost'], pv['cost']), 'hl'),
        kc('应季品占大盘', sh_c, sh_p, '%', lambda v: f'{v:.1f}', chg_pp(sh_c, sh_p)),
        kc('应季在投 SPU', ov['live'], pv['live'], '个', N, chg(ov['live'], pv['live'])),
        kc('应季起量 SPU', ov['rise'], pv['rise'], '个', N, chg(ov['rise'], pv['rise'])),
        kc('应季爆量 SPU', ov['boom'], pv['boom'], '个', N, chg(ov['boom'], pv['boom']), 'b3'),
        kc('应季起量率', ov['rise_rate'], pv['rise_rate'], '%', lambda v: f'{v:.1f}',
           chg_pp(ov['rise_rate'], pv['rise_rate'])),
        kc('应季日均下单', ov['ord_d'], pv['ord_d'], '次', N, chg(ov['ord_d'], pv['ord_d'])),
        kc('应季户均日耗', avg_c, avg_p, '元', N, chg(avg_c, avg_p)),
        kc('全库在投 SPU', oa['live'], pa['live'], '个', N, chg(oa['live'], pa['live'])),
    ])

    # 分维度环比明细
    def row(name, c, p, cls=''):
        return f'''<tr class="{cls}">
      <td class="nm">{e(name)}</td>
      <td class="num dim">{W(p['cost'])}</td><td class="num strong">{W(c['cost'])}</td>
      <td class="num">{chg(c['cost'], p['cost'])}</td>
      <td class="num dim">{N(p['live'])}</td><td class="num">{N(c['live'])}</td>
      <td class="num">{chg(c['live'], p['live'])}</td>
      <td class="num dim">{N(p['rise'])}</td><td class="num">{N(c['rise'])}</td>
      <td class="num">{chg_pp(c['rise_rate'], p['rise_rate'])}</td>
      <td class="num dim">{N(p['boom'])}</td><td class="num boom">{N(c['boom'])}</td>
      <td class="num">{chg(c['ord_d'], p['ord_d'])}</td></tr>'''

    big_c = {'cost': tc, 'live': oa['live'], 'rise': oa['rise'], 'boom': oa['boom'],
             'rise_rate': oa['rise_rate'], 'ord_d': D['TOTAL_ORD_ALL']}
    big_p = {'cost': tp, 'live': pa['live'], 'rise': pa['rise'], 'boom': pa['boom'],
             'rise_rate': pa['rise_rate'], 'ord_d': P['TOTAL_ORD_ALL']}
    body = [row('大盘（全库）', big_c, big_p, 'mr-big'), row('应季品合计', ov, pv, 'mr-sum')]
    for g, title in (('by_channel', '投放端'), ('by_link', '消费链路'),
                     ('by_lvl', '应季等级'), ('by_cat', '类目')):
        body.append(f'<tr class="mr-grp"><td colspan="13">{title}</td></tr>')
        for k, v in D[g].items():
            pv_ = P[g].get(k)
            if pv_:
                body.append(row(k, v, pv_))
    table = f'''<table class="t mt">
  <thead><tr><th rowspan="2">维度</th><th colspan="3">日均消耗(万)</th><th colspan="3">在投SPU</th>
  <th colspan="3">起量SPU / 起量率</th><th colspan="2">爆量SPU</th><th>日均下单</th></tr>
  <tr><th>{PL}</th><th>{L}</th><th>环比</th><th>{PL}</th><th>{L}</th><th>环比</th>
  <th>{PL}</th><th>{L}</th><th>起量率变化</th><th>{PL}</th><th>{L}</th><th>环比</th></tr></thead>
  <tbody>{''.join(body)}</tbody></table>'''

    # 消耗波动归因：延续 / 新增 / 退出 SPU
    cs, ps_ = D['season_spu_cost'], P['season_spu_cost']
    keep = set(cs) & set(ps_)
    new, gone = set(cs) - set(ps_), set(ps_) - set(cs)
    k_c, k_p = sum(cs[s] for s in keep), sum(ps_[s] for s in keep)
    n_c, g_p = sum(cs[s] for s in new), sum(ps_[s] for s in gone)
    delta = ov['cost'] - pv['cost']
    attr = [('延续 SPU 消耗变化', len(keep), k_c - k_p, f'{PL} {W(k_p)}万 → {L} {W(k_c)}万'),
            (f'{L}新增 SPU 贡献', len(new), n_c, f'{PL}未投放、{L}新进入应季投放'),
            (f'{PL}退出 SPU 流失', len(gone), -g_p, f'{PL}在投、{L}已无消耗')]
    arow = []
    for nm, n, v, tip in attr:
        w = abs(v) / max(abs(x[2]) for x in attr) * 100
        arow.append(f'''<tr><td class="nm">{e(nm)}</td><td class="num">{N(n)}</td>
      <td class="num {'up-t' if v >= 0 else 'dn-t'}">{'+' if v >= 0 else '−'}{W(abs(v))}</td>
      <td class="num">{pct(v, delta) if delta else '-'}</td>
      <td class="barc"><div class="bar {'neg' if v < 0 else ''}" style="width:{w:.1f}%"></div></td>
      <td class="tag2">{e(tip)}</td></tr>''')
    attr_tb = f'''<table class="t">
  <thead><tr><th>归因项</th><th>SPU 数</th><th>日均消耗变化(万)</th><th>占净变化</th>
  <th style="width:180px">贡献</th><th>说明</th></tr></thead>
  <tbody>{''.join(arow)}
  <tr class="mr-sum"><td class="nm">应季品净变化</td><td class="num">-</td>
  <td class="num {'up-t' if delta >= 0 else 'dn-t'}">{'+' if delta >= 0 else '−'}{W(abs(delta))}</td>
  <td class="num">100%</td><td></td><td class="tag2">{PL} {W(pv['cost'])}万 → {L} {W(ov['cost'])}万</td></tr>
  </tbody></table>'''

    # 延续 SPU 中波动最大的 TOP10（增长 / 下滑）
    nm = {**P.get('spu_name', {}), **D.get('spu_name', {})}
    ct = {**P.get('spu_cat', {}), **D.get('spu_cat', {})}
    mv = sorted(((s, cs.get(s, 0.0) - ps_.get(s, 0.0)) for s in set(cs) | set(ps_)), key=lambda x: x[1])

    def mover_tb(items):
        rr = []
        for i, (s, d) in enumerate(items, 1):
            p0, c0 = ps_.get(s, 0.0), cs.get(s, 0.0)
            st = '新增' if s not in ps_ else ('退出' if s not in cs else '延续')
            rr.append(f'''<tr><td class="num">{i}</td>
        <td class="nm2" title="{e(nm.get(s, ''))}">{e(nm.get(s, '')[:30])}</td>
        <td class="tag2">{e(ct.get(s, ''))}</td>
        <td class="num dim">{W(p0)}</td><td class="num strong">{W(c0)}</td>
        <td class="num {'up-t' if d >= 0 else 'dn-t'}">{'+' if d >= 0 else '−'}{W(abs(d))}</td>
        <td class="st2 {st}">{st}</td><td class="spu">{e(s)}</td></tr>''')
        return f'''<table class="t">
  <thead><tr><th style="width:34px">#</th><th>商品名称</th><th>类目</th><th>{PL}日耗(万)</th>
  <th>{L}日耗(万)</th><th>变化(万)</th><th>状态</th><th>SPU ID</th></tr></thead>
  <tbody>{''.join(rr)}</tbody></table>'''

    up10 = [x for x in reversed(mv) if x[1] > 0][:10]
    dn10 = [x for x in mv if x[1] < 0][:10]

    # 自动结论
    lk_c, lk_p = D['by_link'], P['by_link']
    lv_c, lv_p = D['by_lvl'], P['by_lvl']
    s_c, s_p = lv_c['S 核心秋冬'], lv_p['S 核心秋冬']
    a_c, a_p = lv_c['A 秋季过渡'], lv_p['A 秋季过渡']
    cid_c, cid_p = lk_c['CID'], lk_p['CID']
    q_c, q_p = D['by_channel']['全域通'], P['by_channel']['全域通']
    ad_c, ad_p = D['by_channel']['ADQ（非全域通）'], P['by_channel']['ADQ（非全域通）']
    gap_pp = ratio(ov['cost'], pv['cost']) - ratio(tc, tp)
    head1 = ('应季品增速跑赢大盘' if gap_pp >= 1 else '应季品增速落后大盘' if gap_pp <= -1
             else '应季品与大盘同步高增')
    concl = f'''<div class="mom-concl">
  <div class="mc"><b>① {head1}：</b>大盘日均消耗环比 {ratio(tc, tp):+.1f}%，
    应季品 {ratio(ov['cost'], pv['cost']):+.1f}%，占大盘 {sh_p:.1f}% → {sh_c:.1f}%
    （{sh_c - sh_p:+.1f}pp）；在投 SPU {ratio(ov['live'], pv['live']):+.1f}%、起量 SPU {ratio(ov['rise'], pv['rise']):+.1f}%，
    供给扩张与起量同步。</div>
  <div class="mc"><b>② S 核心秋冬款接棒：</b>S 层日均消耗 {W(s_p['cost'])}万 → {W(s_c['cost'])}万
    （{ratio(s_c['cost'], s_p['cost']):+.1f}%），爆量 SPU {N(s_p['boom'])} → {N(s_c['boom'])} 个；
    A 层 {ratio(a_c['cost'], a_p['cost']):+.1f}%、爆量 {N(a_p['boom'])} → {N(a_c['boom'])} 个。
    S 层消耗占应季比重 {s_p['cost']/pv['cost']*100:.0f}% → {s_c['cost']/ov['cost']*100:.0f}%，
    {('已反超 A 层，' if s_c['cost'] > a_c['cost'] else '仍低于 A 层，')}与{L}多轮冷空气节奏一致，深秋冬需求开始释放。</div>
  <div class="mc"><b>③ 链路分化：</b>{'、'.join(f"{k} {ratio(v['cost'], lk_p[k]['cost']):+.1f}%" for k, v in lk_c.items() if k in lk_p)}；
    CID 日均消耗 {W(cid_p['cost'])}万 → {W(cid_c['cost'])}万，爆量 SPU {N(cid_p['boom'])} → {N(cid_c['boom'])} 个，
    {'是本月唯一下滑的链路，需排查头部 SPU 断量原因（见下方下滑 TOP10）。' if cid_c['cost'] < cid_p['cost'] and all(lk_c[k]['cost'] >= lk_p[k]['cost'] for k in lk_c if k != 'CID' and k in lk_p) else '各链路同向变化。'}</div>
  <div class="mc"><b>④ 全域通铺量快于提效：</b>全域通在投 SPU {ratio(q_c['live'], q_p['live']):+.1f}%、
    消耗 {ratio(q_c['cost'], q_p['cost']):+.1f}%，但爆量仍仅 {N(q_c['boom'])} 个；
    ADQ 消耗 {ratio(ad_c['cost'], ad_p['cost']):+.1f}%、起量率 {ad_p['rise_rate']:.1f}% → {ad_c['rise_rate']:.1f}%。</div>
  <div class="mc"><b>⑤ 货盘换手大：</b>{PL}应季 SPU 中 {N(len(keep))} 个延续、{N(len(gone))} 个退出，
    {L}新增 {N(len(new))} 个；新增 SPU 贡献日耗 {W(n_c)}万，占{L}应季消耗 {pct(n_c, ov['cost'])}，
    净增长主要来自 {'新品进入' if n_c - g_p > k_c - k_p else '老品放量'}。</div>
</div>'''

    return f'''
<section>
  <div class="sh"><span class="no">2</span><h2>整体月环比：{L} vs {PL}</h2>
    <span class="hint">{L} {M['start']}-{M['end']}（{M['days']}天均值） vs {PL} {PM['start']}-{PM['end']}（{PM['days']}天均值）</span></div>
  <div class="card">
    <div class="kpis k10">{kpis}</div>
    {concl}
    <div class="sub-h">2.1 分维度环比明细</div>
    {table}
    <div class="sub-h">2.2 应季品消耗波动归因（SPU 维度）</div>
    {attr_tb}
    <div class="duo2">
      <div><div class="sub-h">2.3 日均消耗增长 TOP10 SPU</div>{mover_tb(up10)}</div>
      <div><div class="sub-h">2.4 日均消耗下滑 TOP10 SPU</div>{mover_tb(dn10)}</div>
    </div>
    <p class="note"><b>环比口径：</b>两个月均使用「日均」指标（日均消耗、日均下单），窗口长度不同
    （{PL} {PM['days']} 天 / {L} {M['days']} 天）不影响可比性；SPU 数为窗口内去重在投数。
    起量线均为「累计下单 &gt; 110 次」，折合日均 {PL} {110/PM['days']:.2f} 单 / {L} {110/M['days']:.2f} 单，
    {L}门槛略低约 {(1-PM['days']/M['days'])*100:.0f}%，起量数环比存在轻微口径放大。
    {L}窗口含国庆长假（10/1-10/7），节假日流量结构与 9 月不同，解读环比时需考虑。
    归因中「延续」指两月均有应季投放的 SPU；判定规则、类目归一规则两月完全一致。</p>
  </div>
</section>'''


ov = D['overall']
ova = D['overall_all']
ch = D['by_channel']
adq, qyt = ch['ADQ（非全域通）'], ch['全域通']
ML, MO = M['label'], int(M['month'])
WIN_TXT = f"{M['start']}-{M['end']}"

# 章节编号：有上月数据时插入「整体月环比」为第 2 节，其余顺延
SN_OV = 3 if P else 2
SN_TEMP, SN_LIST, SN_DY = SN_OV + 1, SN_OV + 2, SN_OV + 3

# ---- 数据驱动的解读文案（避免沿用上月写死的结论） ----
lk = D['by_link']
per = {k: v['cost'] / v['live'] for k, v in lk.items() if v['live']}
best_eff = max(per, key=per.get)
most_boom = max(lk, key=lambda k: lk[k]['boom'])
widest = max(lk, key=lambda k: lk[k]['live'])
low_eff = min(per, key=per.get)
LINK_NOTE = (f'{widest}链路铺量最广（{N(lk[widest]["live"])} SPU）'
             + (f'但户均日耗最低（{per[widest]:,.0f} 元）；' if widest == low_eff else f'，户均日耗 {per[widest]:,.0f} 元；')
             + f'{best_eff}链路以 {N(lk[best_eff]["live"])} 个 SPU 贡献 {W(lk[best_eff]["cost"])} 万元，'
             f'单 SPU 产出 {per[best_eff]:,.0f} 元，为效率最高链路；'
             f'爆量 SPU 最多的是{most_boom}链路（{N(lk[most_boom]["boom"])} 个）。')
if P and 'CID' in lk and 'CID' in P['by_link']:
    pc_ = P['by_link']['CID']
    LINK_NOTE += (f' 环比看，CID 户均日耗由 {pc_["cost"]/pc_["live"]:,.0f} 元降至 {per["CID"]:,.0f} 元、'
                  f'爆量由 {N(pc_["boom"])} 个降至 {N(lk["CID"]["boom"])} 个，{PM["label"]}的效率优势已不再成立。')

s_lv, a_lv = D['by_lvl']['S 核心秋冬'], D['by_lvl']['A 秋季过渡']
if s_lv['cost'] >= a_lv['cost']:
    LVL_NOTE = (f'S 核心秋冬款（羽绒/棉服/保暖/毛呢等）日均消耗 {W(s_lv["cost"])} 万元，已与 A 秋季过渡款'
                f'（{W(a_lv["cost"])} 万元）持平并略超，S 层爆量 {N(s_lv["boom"])} 个 vs A 层 {N(a_lv["boom"])} 个；'
                f'需求重心正从秋季过渡款向深秋冬款切换，S 层应继续作为加投与备货重点。')
else:
    LVL_NOTE = ('A 秋季过渡款（卫衣/夹克/外套/针织等）当前仍是消耗主力，S 核心秋冬款（羽绒/棉服/保暖/毛呢等）'
                f'在投 SPU 已达一定规模但爆量仅 {N(s_lv["boom"])} 个，'
                '随冷空气密集期到来，S 层是最需要提前备量与加投的品类。')

CID_TIP = ('CID 链路本身单 SPU 产出最高，' if best_eff == 'CID'
           else f'CID 链路户均日耗 {per.get("CID", 0):,.0f} 元，')

if MO == 9:
    TEMP_NOTE = '''<p class="note"><b>降温节点解读：</b>9月呈"北方阶梯式降温、南方秋老虎持续"的南北分裂格局。
    北方代表城市日均气温从月初 27-28℃ 降至下旬 15-19℃，累计降幅超 10℃；
    <b>9/19 起至月底连续 4 轮冷空气</b>（19-21日、23-24日、25-26日、30日前后）强度逐渐增强，
    是秋冬应季品需求释放的关键窗口；南方同期仅从 32℃ 缓降至 27℃ 左右，
    秋冬品放量节奏应显著晚于北方，建议分区域差异化投放。</p>'''
    TEMP_SRC = '中央气象台 / 中国气象局 2026年9月公开通报'
else:
    TEMP_NOTE = f'''<p class="note"><b>降温节点解读：</b>10月冷暖反复、北冷南暖。
    月初 10/1 中东部、10/3 北方已有明显降温，但 9—18 日中东部大部时段均温仍较常年偏高 2—4℃；
    <b>10/18-19 北方再度降温 8—12℃</b>，中央气象台预报 10/19-21、10/24-26 两轮冷空气接续影响中东部，
    19—28 日北方大部均温预计偏低 1—2℃，南方大部仍偏暖 2—3℃。
    本期消耗窗口截至 {M['end']}，<b>恰好落在月下旬冷空气密集期之前</b>，S 核心秋冬款的环比放量
    （见第 2 节）尚未包含 20 日以后的降温拉动，月底前北方 S 层仍有上行空间；南方继续以 A 层过渡款为主。</p>'''
    TEMP_SRC = '中央气象台 / 中国天气网 2026年10月公开通报（截至 10/19 10:00）'

HTMLDOC = f'''<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>服饰秋冬应季品消耗监控看板 · 2026年{ML}MTD</title>
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
.note code{{background:#16243f;color:#8fd0ff;padding:1px 5px;border-radius:4px;font-size:12px}}
/* 1~4 级类目树 */
.tt-bar{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:2px 0 10px}}
.tb{{background:#16243f;border:1px solid #27406b;color:#9fb4d8;padding:5px 13px;
 border-radius:7px;cursor:pointer;font-size:12.5px;user-select:none;transition:.12s}}
.tb:hover{{border-color:#3ea6ff;color:#8fd0ff}}
.tb.on{{background:linear-gradient(135deg,#3ea6ff,#66e08f);color:#04101f;font-weight:700;
 border-color:transparent}}
.tt-hint{{color:#6f86ab;font-size:11.8px;margin-left:auto;text-align:right;line-height:1.55}}
.scope-tag{{background:#66e08f1c;border:1px solid #2f6b4a;color:#7fe0a5;font-size:11.8px;
 padding:4px 11px;border-radius:7px;margin-left:6px}}
.tt tr.tr-sum{{background:linear-gradient(90deg,#1b3a2c,#14243d)}}
.tt tr.tr-sum td{{border-bottom:2px solid #2f6b4a;padding-top:11px;padding-bottom:11px}}
.tt tr.tr-sum .ct{{font-weight:700;font-size:14px;color:#66e08f}}
.tt tr.tr-sum .cr{{color:#66e08f;font-size:12px}}
.lvt.lsum{{background:#66e08f2b;color:#66e08f}}
.tw{{max-height:620px;overflow:auto;border:1px solid #1b2942;border-radius:10px}}
.tw::-webkit-scrollbar{{width:9px;height:9px}}
.tw::-webkit-scrollbar-thumb{{background:#27406b;border-radius:5px}}
.tt thead th{{position:sticky;top:0;z-index:3}}
.tt tr.hid{{display:none}}
.tt td{{border-bottom:1px solid #16243f}}
.lvc{{text-align:center!important;padding:8px 6px!important}}
.lvt{{display:inline-block;font-size:10.5px;padding:1px 6px;border-radius:4px;font-weight:600}}
.lvt.l1{{background:#3ea6ff2b;color:#8fd0ff}}
.lvt.l2{{background:#b78cff2b;color:#c4a8ff}}
.lvt.l3{{background:#66e08f22;color:#7fe0a5}}
.lvt.l4{{background:#8ea2c61f;color:#9fb4d8}}
.nmt{{text-align:left!important;white-space:nowrap}}
.cr{{display:inline-block;width:15px;color:#5c718f;font-size:9.5px;transition:transform .14s;
 transform-origin:center}}
.cr.dot{{color:#33465f;font-size:14px}}
.tt tr.open>.nmt>.cr{{transform:rotate(90deg);color:#3ea6ff}}
.tt tr.tr-l1{{background:#16243f66}}
.tt tr.tr-l1 .ct{{font-weight:700;font-size:14px;color:#fff}}
.tt tr.tr-l2 .nmt{{padding-left:26px!important}}
.tt tr.tr-l2 .ct{{font-weight:600;color:#e2ecfb}}
.tt tr.tr-l3 .nmt{{padding-left:50px!important}}
.tt tr.tr-l3 .ct{{color:#c3d4ee}}
.tt tr.tr-l4 .nmt{{padding-left:74px!important}}
.tt tr.tr-l4 .ct{{color:#9fb4d8;font-size:12.6px}}
.tt tr[data-kid="1"]{{cursor:pointer}}
.tt tr[data-kid="1"]:hover{{background:#1b2c4d}}
.sb{{font-size:10.5px;padding:1.5px 6px;border-radius:4px;font-weight:600;white-space:nowrap}}
.s-hi{{background:#ff9e5e26;color:#ff9e5e}}
.s-mid{{background:#ffd06626;color:#ffd066}}
.s-lo{{background:#8ea2c61c;color:#8ea2c6}}
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
/* 月环比 */
.mm{{font-size:11.5px;font-weight:700;white-space:nowrap}}
.mm.up{{color:#66e08f}}.mm.dn{{color:#ff7a7a}}.mm.flat{{color:#7e94b8}}
.k .kx .mm{{font-size:12px;margin-left:2px}}
.kpis.k10{{grid-template-columns:repeat(5,1fr)}}
.kpis.k10 .kv{{font-size:27px}}
.mom-concl{{display:grid;gap:8px;margin:18px 0 6px}}
.mc{{background:#0e1830;border:1px solid #22335a;border-left:3px solid #66e08f;border-radius:0 9px 9px 0;
 padding:10px 14px;color:#cfdcf2;font-size:13.2px;line-height:1.85}}
.mc b{{color:#fff}}
.t.mt th{{text-align:center}}
.t.mt thead tr:first-child th{{border-bottom:1px solid #22335a}}
.t.mt th[rowspan]{{text-align:left;vertical-align:middle}}
.t tr.mr-big td{{background:#16243f;font-weight:600}}
.t tr.mr-sum td{{background:linear-gradient(90deg,#1b3a2c,#14243d);font-weight:700}}
.t tr.mr-grp td{{text-align:left;color:#8fd0ff;font-size:12px;font-weight:700;background:#0e1830;
 padding:7px 11px;letter-spacing:1px}}
.up-t{{color:#66e08f;font-weight:700}}.dn-t{{color:#ff7a7a;font-weight:700}}
.bar.neg{{background:linear-gradient(90deg,#ff7a7a,#ffb74d)}}
.duo2{{display:grid;grid-template-columns:1fr;gap:4px}}
.st2{{text-align:left;font-size:12px}}
.st2.新增{{color:#66e08f}}.st2.退出{{color:#ff7a7a}}.st2.延续{{color:#8fd0ff}}
.wk{{font-size:10.5px;padding:0 6px;border-radius:4px;margin-left:6px;font-weight:600}}
.wk.obs{{background:#66e08f22;color:#66e08f}}.wk.proc{{background:#8ea2c622;color:#9fb4d8}}
.wk.fc{{background:#3ea6ff22;color:#8fd0ff;border:1px dashed #3ea6ff88}}
.wk.sig{{background:#b78cff22;color:#c4a8ff}}
.wc.fc,.wc.sig{{border-style:dashed}}
.dy-reuse{{color:#ffb74d}}
@media(max-width:1200px){{.duo2{{grid-template-columns:1fr}}}}
@media(max-width:1200px){{.kpis{{grid-template-columns:repeat(3,1fr)}}
 .grid-g,.grid-w{{grid-template-columns:repeat(3,1fr)}}
 .duo,.grid-r{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">

<div class="hero">
  <h1>服饰秋冬应季品消耗监控看板 · {ML}</h1>
  <div class="sub">数据窗口：{M['win']}（MTD {M['days']}天）｜口径：SPU 去重计商品数，消耗与下单次数加总</div>
  <div>
    <span class="pill">大盘日均消耗 {W(D['TOTAL_COST_ALL'])} 万元{(' ' + chg(D['TOTAL_COST_ALL'], P['TOTAL_COST_ALL'])) if P else ''}</span>
    <span class="pill">应季品日均消耗 {W(ov['cost'])} 万元{(' ' + chg(ov['cost'], P['overall']['cost'])) if P else ''}</span>
    <span class="pill">应季品占大盘 {pct(ov['cost'], D['TOTAL_COST_ALL'])}</span>
    <span class="pill">起量线：累计下单 &gt; 110 次</span>
    <span class="pill">爆量线：日均消耗 &gt; 1 万元</span>
    <span class="pill">生成时间 {'2026-09-20' if MO == 9 else '2026-10-20'}</span>
  </div>
</div>

<section>
  <div class="sh"><span class="no">1</span><h2>秋冬应季品判定规则</h2>
    <span class="hint">双通道判定：商品四级类目 + SPU 名称材质/款式词，排除优先于命中{('｜规则与' + PM['label'] + '完全一致') if P else ''}</span></div>
  <div class="card">{rule_cards()}
    <p class="note">判定结果：全库 {N(ova['live'])} 个在投 SPU 中识别出 <b>{N(ov['live'])}</b> 个秋冬应季品
    （占比 {pct(ov['live'], ova['live'])}），其中 S 核心秋冬 {N(D['by_lvl']['S 核心秋冬']['live'])} 个、
    A 秋季过渡 {N(D['by_lvl']['A 秋季过渡']['live'])} 个。
    同一 SPU 若在多个类目/链路/投放端有投放记录，分维度统计时会在各维度分别计数，
    因此分维度在投数之和 ≥ 应季品去重总数。</p>
  </div>
</section>
{mom_section()}
<section>
  <div class="sh"><span class="no">{SN_OV}</span><h2>应季品业绩总览</h2>
    <span class="hint">{ML}MTD 全量应季品{('｜表内环比均为对比' + PM['label']) if P else ''}</span></div>
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

    <div class="sub-h">{SN_OV}.1 分投放端</div>
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
    {metric_table(ch, '投放端', group='by_channel')}
    <p class="note">全域通在投 SPU 数{'已超过' if qyt['live'] > adq['live'] else '仍低于'} ADQ（{N(qyt['live'])} vs {N(adq['live'])}），
    但消耗仅为 ADQ 的 {qyt['cost']/adq['cost']*100:.0f}%、爆量 SPU 仅 {N(qyt['boom'])} 个，
    说明全域通侧仍处于"铺量未起量"阶段，单 SPU 产出（{qyt['cost']/qyt['live']:,.0f} 元 vs
    ADQ {adq['cost']/adq['live']:,.0f} 元）差距明显，是换季期重点提效方向。</p>

    <div class="sub-h">{SN_OV}.2 分类目</div>
    {metric_table(D['by_cat'], '类目',
      '类目口径：取「商品统一类目V2」首个"-"后文字，命中 男装/女装/内衣裤袜·睡衣·家居服/男鞋/女鞋 则归入该二级类目；'
      '否则取首个"-"前文字，命中 珠宝·首饰·手表/运动户外 则归入该一级类目；其余（含类目为「空」「0」的记录）统一归入「其他」。',
      group='by_cat')}

    <div class="sub-h">{SN_OV}.3 分消费链路</div>
    {metric_table(D['by_link'], '消费链路', group='by_link')}
    <p class="note">{LINK_NOTE}</p>

    <div class="sub-h">{SN_OV}.4 分应季等级</div>
    {metric_table(D['by_lvl'], '应季等级', LVL_NOTE, group='by_lvl')}

    <div class="sub-h">{SN_OV}.5 应季品 1~4 级类目明细展开</div>
    {cat_tree_table()}
    <p class="note"><b>统计范围：仅保留一级类目为 服饰鞋包 / 运动户外 / 珠宝·首饰·手表 的应季品</b>，
    共 {N(D['tree_scope']['live'])} 个 SPU、日均消耗 {W(D['tree_scope']['cost'])} 万元，
    覆盖应季品总消耗的 {pct(D['tree_scope']['cost'], ov['cost'])}；
    其余一级类目（日用百货、个护清洁、母婴用品、食品饮料等非服饰主体，以及类目为「空」「0」的记录）
    共 {N(ov['live'] - D['tree_scope']['live'])} 个 SPU、{W(ov['cost'] - D['tree_scope']['cost'])} 万元已从本表剔除。
    <br>层级口径：取「商品统一类目V2（一级～四级）」原始路径按 <code>-</code> 逐级拆分，不做归并
    （与 {SN_OV}.2 分类目表的白名单归并口径不同，此处为完整层级明细）。
    父级指标 = 其下全部子类目 SPU 去重后重算，因此父级在投数 ≤ 各子级之和；表内消耗占比以上述三大一级类目合计为分母。
    为控制表格规模，二级及以下仅展示同层消耗 ≥ 300 元的节点（二级取 TOP12、三级 TOP10、四级 TOP10）。
    <br><b>S层占比</b>指该类目中 S 核心秋冬款消耗占比，占比越高说明该类目越依赖深秋冬需求、对降温越敏感。</p>
  </div>
</section>

<section>
  <div class="sh"><span class="no">{SN_TEMP}</span><h2>气温趋势 × 应季品消耗对比</h2>
    <span class="hint">气温节点来源：{TEMP_SRC}</span></div>
  <div class="card">
    {temp_chart()}
    {wave_cards()}
    {TEMP_NOTE}
    <p class="note"><b>数据口径说明：</b>当前源表仅提供 {WIN_TXT} 的 <b>{M['days']} 天平均值</b>（日均消耗、日均下单次数），
    不含逐日明细，因此消耗侧只能以 MTD 日均基准线（绿色虚线 {W(ov['cost'])} 万元/天）呈现，
    无法绘制真实逐日曲线。如需完整的"降温节点 → 消耗爬升"弹性验证，
    需补充按日期维度拆分的逐日消耗数据（建议拉取 {MO}/1-{MO}/{M['n_days']} 分日快照）。
    气温曲线为基于上述公开通报的冷空气节点与南北格局还原的趋势示意，非逐日实测站点均值{'；10 月曲线只画到 10/19 资料截点，之后仅标注预报窗口，不补造逐日温度' if MO != 9 else ''}。</p>
  </div>
</section>

<section>
  <div class="sh"><span class="no">{SN_LIST}</span><h2>拓品清单</h2>
    <span class="hint">已验证的确定性货品，跨端 / 跨链路复制</span></div>
  <div class="card">
    <div class="sub-h">{SN_LIST}.1 全域通反拓 ADQ — 全域通已起量、ADQ 未起量 TOP10</div>
    {cross_table(D['list_qyt2adq'], '全域通', 'ADQ')}
    <p class="note">筛选逻辑：应季品中，在「是否全域通=true」侧累计下单 &gt; 110 次（已起量），
    但在「是否全域通=false」侧累计下单 ≤ 110 次（未起量，含完全未投放），按全域通侧日均消耗降序取 TOP10。
    这批商品已由全域通验证过转化能力，可直接在 ADQ 侧建计划复制。</p>

    <div class="sub-h">{SN_LIST}.2 CID 反拓小店直购 — CID 已起量、小店未起量 TOP10</div>
    {cross_table(D['list_cid2shop'], 'CID', '小店')}
    <p class="note">筛选逻辑同上，源链路为 CID、目标链路为小店。{CID_TIP}
    这批商品在 CID 已跑出规模，小店直购链路承接后可进一步放大自然流量与复购。</p>
  </div>
</section>

<section>
  <div class="sh"><span class="no">{SN_DY}</span><h2>抖音高 GMV 应季品覆盖</h2>
    <span class="hint">抖音9月商品销售榜 TOP1000（销售额均 100w+）｜应季品 {N(D['dy_season_n'])}/{N(D['dy_n'])} 个{'｜<span class="dy-reuse">本期未提供10月榜单，沿用9月榜单对标</span>' if MO != 9 else ''}</span></div>
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

    <div class="sub-h">{SN_DY}.1 抖音应季热销商品 TOP20（分类目）</div>
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

    <div class="sub-h">{SN_DY}.2 抖音热销应季类目 × 内部投放覆盖</div>
    {cover_table()}
    <p class="note">匹配口径：抖音榜单与内部投放表无共用商品 ID，故采用<b>类目级映射</b>匹配
    （抖音四级叶子类目 → 内部四级类目，如 抖音「针织衫/毛衣/羊毛衫」→ 内部「毛衣/针织衫」+「羊绒衫/羊毛衫」）。
    标注「未覆盖」的类目表示抖音有 100w+ 销售额的高 GMV 应季商品，但内部同类目零在投，是最高优先级的拓品缺口；
    「覆盖偏低」表示内部起量 SPU 少于 5 个，供给厚度不足。{'内部侧已更新为' + ML + '数据，抖音侧沿用 9 月榜单。' if MO != 9 else ''}</p>
  </div>
</section>

<div class="foot">
  数据来源：内部服饰换季品监控明细表（{WIN_TXT}，{M['days']}天均值）{('｜环比基准：' + PM['label'] + ' ' + PM['start'] + '-' + PM['end'] + '（' + str(PM['days']) + '天均值）') if P else ''}｜抖音9月商品销售榜 TOP1000<br>
  气温信息来源：{TEMP_SRC}<br>
  口径提示：商品数按 SPUid 去重；日均消耗与日均下单次数按行加总；累计下单次数 = 日均下单次数 × {M['days']}
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

/* ---- 1~4 级类目树 折叠展开 ---- */
(function(){{
  var rows = Array.prototype.slice.call(document.querySelectorAll('.tt tbody tr'));
  if (!rows.length) return;
  var byParent = {{}};
  rows.forEach(function(r){{
    var p = r.dataset.parent || '';
    (byParent[p] = byParent[p] || []).push(r);
  }});

  function hideDesc(r){{      // 递归隐藏所有后代并清除展开态
    (byParent[r.dataset.path] || []).forEach(function(c){{
      c.classList.add('hid');
      c.classList.remove('open');
      hideDesc(c);
    }});
  }}
  function toggle(r){{
    if (r.dataset.kid !== '1') return;
    var kids = byParent[r.dataset.path] || [];
    if (r.classList.contains('open')) {{
      r.classList.remove('open');
      hideDesc(r);
    }} else {{
      r.classList.add('open');
      kids.forEach(function(c){{ c.classList.remove('hid'); }});
    }}
  }}
  rows.forEach(function(r){{
    if (r.dataset.kid === '1') {{
      r.addEventListener('click', function(ev){{
        if (ev.target.tagName === 'A') return;
        toggle(r);
      }});
    }}
  }});

  function expandTo(maxLv){{
    rows.forEach(function(r){{
      var lv = parseInt(r.dataset.lvl, 10);
      if (lv <= maxLv) r.classList.remove('hid'); else r.classList.add('hid');
      if (r.dataset.kid === '1' && lv < maxLv) r.classList.add('open');
      else r.classList.remove('open');
    }});
  }}
  var acts = {{ e2: 2, e3: 3, e4: 4, c1: 1 }};
  document.querySelectorAll('.tb').forEach(function(b){{
    b.addEventListener('click', function(){{
      document.querySelectorAll('.tb').forEach(function(x){{x.classList.remove('on')}});
      b.classList.add('on');
      expandTo(acts[b.dataset.act]);
    }});
  }});
  var def = document.querySelector('.tb[data-act="e2"]');
  if (def) def.classList.add('on');
  expandTo(2);
}})();
</script>
</body></html>'''

open(OUT, 'w', encoding='utf-8').write(HTMLDOC)
print('写出:', OUT, len(HTMLDOC), 'chars')
