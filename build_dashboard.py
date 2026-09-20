# -*- coding: utf-8 -*-
"""服饰秋冬应季品监控看板生成器"""
import csv, io, sys, json, re, html, os, warnings
from collections import defaultdict, Counter

warnings.filterwarnings('ignore')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_PATH = r'C:\Users\johnsywang\Desktop\服饰换季品监控.csv'
XLSX_PATH = r'C:\Users\johnsywang\Desktop\抖音9月榜单.xlsx'
OUT_HTML = r'C:\Users\johnsywang\Desktop\服饰秋冬应季品监控看板.html'

DAYS = 18            # 数据窗口：9/1 - 9/18
ORDER_THRESHOLD = 110   # 起量：累计下单次数 > 110
BOOM_THRESHOLD = 10000  # 爆量：日均消耗 > 1w

# ==========================================================
# 一、秋冬应季品判定规则
# ==========================================================
# L0 夏季/非季节 硬排除
EXCLUDE_CAT = [
    'T恤', '速干T恤', 'Polo衫', '背心/吊带', '连体泳衣', '分体泳衣', '泳裤', '沙滩裤',
    '人字拖', '一字拖', '包头拖', '其他拖鞋', '沙滩鞋', '洞洞鞋', '凉鞋',
    '防晒衣/皮肤衣', '防晒帽', '防晒口罩/防晒脖套', '防晒袖套', '太阳镜',
    '蕾丝衫/雪纺衫', '速干裤', '速干衣裤套装', '速干衣', '短裤', '沙滩服',
]
EXCLUDE_NAME = [
    '短袖', '无袖', '短裤', '冰丝', '冰爽', '凉感', '凉爽', '速干', '防晒', '雪纺',
    '蕾丝', '泳衣', '泳装', '泳裤', '比基尼', '拖鞋', '凉鞋', '沙滩', '五分裤',
    '七分裤', '中袖', '网眼', '镂空', '超薄', '轻薄', '薄款', 'T恤', '吊带', '露脐',
]

# L1 强应季（核心秋冬）—— 类目
S_CAT = [
    '羽绒服', '棉衣/棉服', '棉服', '棉衣', '毛呢大衣', '大衣', '皮草', '其他天然皮草',
    '羊绒衫/羊毛衫', '羊绒衫', '羊毛衫', '保暖裤', '保暖套装', '保暖上衣', '保暖内衣',
    '雪地靴', '马丁靴', '时装靴', '短靴', '长靴', '靴', '雨靴/雨鞋',
    '抓绒衣/摇粒绒外套', '抓绒衣', '摇粒绒', '皮衣', '冲锋衣', '羊剪绒',
    '连裤袜/打底袜', '长筒袜', '加绒裤', '棉裤',
]
# L1 强应季 —— SPU 名称材质/工艺词（最高置信）
S_NAME = [
    '羽绒', '鹅绒', '鸭绒', '羊绒', '羊毛', '德绒', '摇粒绒', '抓绒', '加绒', '夹绒',
    '绒里', '貂绒', '驼绒', '法兰绒', '灯芯绒', '珊瑚绒', '牛奶绒', '毛呢', '呢子',
    '加厚', '夹棉', '棉服', '棉袄', '棉裤', '棉衣', '保暖', '发热', '蓄热', '锁温',
    '御寒', '防寒', '皮草', '雪地', '绒绒', '绒毛', '磨毛', '厚绒', '绒衫', '绒服',
]
# L2 过渡应季（秋季主力）—— 类目
A_CAT = [
    '卫衣', '夹克', '风衣', '短外套/中长款外套', '毛衣/针织衫', '针织衫', '毛衣',
    '马甲', '打底衫', '鲨鱼裤/打底裤', '塑身美体裤', '开衫',
    '围巾/丝巾/披肩', '手套', '毛线帽', '睡衣套装/家居服套装', '睡裙/家居裙',
    '中式女装/新中式女装', '中式男装/新中式男装', '奶奶装', '旗袍',
    '西装上衣', '西装套装', '西装裤/正装裤', '运动夹克/外套', '其他外套',
    '运动卫衣/套头衫', '时尚套装', '休闲套装', '保暖套装', '塑身衣', '塑身连体衣',
    '带胸垫打底衣', '连体袜', '中筒袜', '丝袜',
]
# L2 过渡应季 —— SPU 名称款式词
A_NAME = [
    '长袖', '外套', '开衫', '高领', '半高领', '堆堆领', '连帽', '针织', '毛衣',
    '卫衣', '夹克', '风衣', '马甲', '长款', '中长款', '大衣', '套头', '翻领',
    '立领', '长裙', '长裤', '西装', '呢', '秋冬', '秋款', '冬款', '秋季', '冬季',
]
# 全年款类目（只有名称含秋冬材质词时才计入应季）
NEUTRAL_CAT = [
    '休闲裤', '牛仔裤', '衬衫', '休闲皮鞋', '正装皮鞋/商务皮鞋', '板鞋', '老爹鞋',
    '德训鞋', '乐福鞋/豆豆鞋', '时尚休闲鞋', '运动休闲鞋/靴', '玛丽珍鞋', '单鞋',
    '高跟鞋', '布鞋/棉布鞋', '帆布鞋', '跑步鞋', '男士内裤', '女士内裤', '内裤',
    '文胸', '短袜', '运动袜', '袜子', '帽子', '腰带/皮带/腰链', '连衣裙', '半身裙',
    '校服', '西裤', '运动裤', '健身裤/运动裤', '其他裤子',
]


def hit(text, kws):
    for k in kws:
        if k and k in text:
            return k
    return None


def season_tag(name, cat_full):
    """返回 (level, reason)  level: 'S' 强应季 / 'A' 过渡应季 / '' 非应季"""
    name = name or ''
    cat_full = cat_full or ''
    leaf = cat_full.split('-')[-1]

    # L0 硬排除
    k = hit(name, EXCLUDE_NAME)
    if k:
        return '', f'夏季名称词「{k}」排除'
    k = hit(leaf, EXCLUDE_CAT)
    if k:
        return '', f'夏季类目「{k}」排除'

    # L1 强应季
    k = hit(name, S_NAME)
    if k:
        return 'S', f'秋冬材质词「{k}」'
    k = hit(leaf, S_CAT)
    if k:
        return 'S', f'核心秋冬类目「{k}」'

    # 全年款：无秋冬材质词 → 非应季
    k = hit(leaf, NEUTRAL_CAT)
    if k:
        return '', f'全年款类目「{k}」且无秋冬材质词'

    # L2 过渡应季
    k = hit(leaf, A_CAT)
    if k:
        return 'A', f'秋季款式类目「{k}」'
    k = hit(name, A_NAME)
    if k:
        return 'A', f'秋季款式词「{k}」'

    return '', '无季节特征'


# ==========================================================
# 二、类目归一
# ==========================================================
LVL2_WHITE = ['男装', '女装', '内衣裤袜/睡衣/家居服', '男鞋', '女鞋']
LVL1_WHITE = ['珠宝/首饰/手表', '运动户外']
CAT_ORDER = LVL2_WHITE + LVL1_WHITE + ['其他']


def norm_cat(cat_full):
    if not cat_full or cat_full in ('空', '0'):
        return '其他'
    parts = cat_full.split('-')
    lvl1 = parts[0]
    lvl2 = parts[1] if len(parts) > 1 else ''
    if lvl2 in LVL2_WHITE:
        return lvl2
    if lvl1 in LVL1_WHITE:
        return lvl1
    return '其他'


# ==========================================================
# 三、读取并打标
# ==========================================================
raw = [r for r in csv.DictReader(open(CSV_PATH, encoding='utf-8-sig'))
       if r.get('SPUid(及名称)')]

TOTAL_COST_ALL = 0.0
for r in csv.DictReader(open(CSV_PATH, encoding='utf-8-sig')):
    if r.get('运营二级行业名称') == '整体':
        TOTAL_COST_ALL = float(r['日均消耗(元)'] or 0)

recs = []
for r in raw:
    spu = r['SPUid(及名称)'].lstrip("'")
    name = r['SPUid(及名称)(翻译后)'] or ''
    cat_full = r['商品统一类目V2(一级～四级)'] or ''
    lvl, reason = season_tag(name, cat_full)
    recs.append({
        'spu': spu, 'name': name, 'cat_full': cat_full,
        'leaf': cat_full.split('-')[-1], 'cat': norm_cat(cat_full),
        'qyt': r['是否全域通广告'] == 'true',
        'link': r['商品消费链路'] or '未知',
        'cost': float(r['日均消耗(元)'] or 0),
        'ord': float(r['日均下单次数(次)'] or 0),
        'lvl': lvl, 'reason': reason,
        'ind': r['运营二级行业名称'] or '',
    })

season = [x for x in recs if x['lvl']]


# ==========================================================
# 四、指标聚合
# ==========================================================
def agg(rows):
    """按 spu 聚合后计算指标"""
    by = defaultdict(lambda: {'cost': 0.0, 'ord': 0.0})
    for x in rows:
        b = by[x['spu']]
        b['cost'] += x['cost']
        b['ord'] += x['ord']
    live = len(by)
    rise = sum(1 for v in by.values() if v['ord'] * DAYS > ORDER_THRESHOLD)
    boom = sum(1 for v in by.values() if v['cost'] > BOOM_THRESHOLD)
    cost = sum(v['cost'] for v in by.values())
    return {'live': live, 'rise': rise, 'boom': boom, 'cost': cost,
            'rise_rate': rise / live * 100 if live else 0}


def risen_spus(rows):
    by = defaultdict(float)
    for x in rows:
        by[x['spu']] += x['ord']
    return {s for s, v in by.items() if v * DAYS > ORDER_THRESHOLD}


overall = agg(season)
overall_all = agg(recs)

adq_rows = [x for x in season if not x['qyt']]
qyt_rows = [x for x in season if x['qyt']]
by_channel = {'ADQ（非全域通）': agg(adq_rows), '全域通': agg(qyt_rows)}

by_cat = {}
for c in CAT_ORDER:
    rows = [x for x in season if x['cat'] == c]
    if rows:
        by_cat[c] = agg(rows)

LINK_ORDER = ['直播', '小店', 'CID']
by_link = {}
for l in LINK_ORDER:
    rows = [x for x in season if x['link'] == l]
    if rows:
        by_link[l] = agg(rows)

# 应季等级拆分
by_lvl = {'S 核心秋冬': agg([x for x in season if x['lvl'] == 'S']),
          'A 秋季过渡': agg([x for x in season if x['lvl'] == 'A'])}

# 应季 TOP 叶子类目
leaf_stat = defaultdict(lambda: {'cost': 0.0, 'spus': set(), 'ord': 0.0})
for x in season:
    d = leaf_stat[x['leaf']]
    d['cost'] += x['cost']
    d['ord'] += x['ord']
    d['spus'].add(x['spu'])
top_leaf = sorted(leaf_stat.items(), key=lambda kv: -kv[1]['cost'])[:20]

# ==========================================================
# 五、拓品清单
# ==========================================================
spu_name = {}
spu_cat = {}
for x in season:
    spu_name.setdefault(x['spu'], x['name'])
    spu_cat.setdefault(x['spu'], x['cat'])


def cross_list(src_rows, dst_rows, topn=10):
    """在 src 起量、在 dst 未起量的 spu，按 src 消耗 top"""
    src_ok = risen_spus(src_rows)
    dst_ok = risen_spus(dst_rows)
    src_cost = defaultdict(float)
    src_ord = defaultdict(float)
    for x in src_rows:
        src_cost[x['spu']] += x['cost']
        src_ord[x['spu']] += x['ord']
    dst_cost = defaultdict(float)
    dst_ord = defaultdict(float)
    for x in dst_rows:
        dst_cost[x['spu']] += x['cost']
        dst_ord[x['spu']] += x['ord']
    cand = [s for s in src_ok if s not in dst_ok]
    cand.sort(key=lambda s: -src_cost[s])
    out = []
    for s in cand[:topn]:
        out.append({
            'spu': s, 'name': spu_name.get(s, ''), 'cat': spu_cat.get(s, ''),
            'src_cost': src_cost[s], 'src_ord': src_ord[s] * DAYS,
            'dst_cost': dst_cost.get(s, 0.0), 'dst_ord': dst_ord.get(s, 0.0) * DAYS,
            'in_dst': s in dst_cost,
        })
    return out


list_qyt2adq = cross_list(qyt_rows, adq_rows)
cid_rows = [x for x in season if x['link'] == 'CID']
shop_rows = [x for x in season if x['link'] == '小店']
list_cid2shop = cross_list(cid_rows, shop_rows)

# ==========================================================
# 六、抖音榜单
# ==========================================================
import openpyxl

SALES_MAP = {'0-250': 125, '250-500': 375, '500-1000': 750, '1000-2500': 1750,
             '2500-5000': 3750, '5000-1w': 7500, '1w-2.5w': 17500,
             '2.5w-5w': 37500, '5w-10w': 75000, '10w+': 150000}


def parse_vol(v):
    s = str(v).strip()
    return SALES_MAP.get(s, 0)


wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
ws = wb['商品销售榜']
xrows = list(ws.iter_rows(min_row=2, values_only=True))
xhdr = list(xrows[0])
dy = []
for r in xrows[1:]:
    if not r[0]:
        continue
    d = dict(zip(xhdr, r))
    cat = str(d['商品类目'] or '')
    parts = cat.split('>')
    lvl3 = parts[2] if len(parts) > 2 else ''
    leaf = parts[-1]
    lvl, reason = season_tag(str(d['商品名称'] or ''), '-'.join(parts[1:]))
    dy.append({
        'name': str(d['商品名称'] or ''), 'cat': cat, 'lvl3': lvl3, 'leaf': leaf,
        'img': str(d['图片链接'] or ''), 'url': str(d['商品链接'] or ''),
        'shop': str(d['抖音小店'] or ''), 'brand': str(d['品牌名称'] or ''),
        'vol_txt': str(d['销量'] or ''), 'vol': parse_vol(d['销量']),
        'gmv_txt': str(d['销售额'] or ''), 'discount': str(d['平均折扣'] or ''),
        'lvl': lvl, 'reason': reason,
    })

dy_season = [x for x in dy if x['lvl']]
DY_GROUPS = {'男装': ['男装'], '女装': ['女装'], '内衣': ['内衣裤袜']}
dy_top = {}
for g, keys in DY_GROUPS.items():
    rows = [x for x in dy_season if x['lvl3'] in keys]
    rows.sort(key=lambda x: -x['vol'])
    dy_top[g] = rows[:20]

# 抖音应季热销叶子类目 -> 内部覆盖
DY2IN = {
    '冲锋衣': ['冲锋衣'], '羽绒服': ['羽绒服'],
    '针织衫/毛衣/羊毛衫': ['毛衣/针织衫', '羊绒衫/羊毛衫'], '羊绒衫': ['羊绒衫/羊毛衫'],
    '运动夹克/外套': ['夹克', '短外套/中长款外套'], '夹克': ['夹克'],
    '其他外套': ['短外套/中长款外套'], '风衣': ['风衣'], '大衣': ['毛呢大衣'],
    '卫衣': ['卫衣'], '皮衣': ['皮衣'], '马甲': ['马甲'], '棉衣': ['棉衣/棉服'],
    '保暖内衣': ['保暖上衣', '保暖套装', '保暖裤'], '抓绒衣': ['抓绒衣/摇粒绒外套'],
    '其他天然皮草': ['皮草'], '居家服/睡衣': ['睡衣套装/家居服套装', '睡裙/家居裙'],
    '打底衫': ['打底衫'], '时尚套装': ['休闲套装', '保暖套装'],
    '长筒袜': ['长筒袜', '连裤袜/打底袜'], '中筒袜': ['中筒袜'], '丝袜': ['连裤袜/打底袜'],
    '塑身衣': ['塑身衣', '塑身连体衣'], '带胸垫打底衣': ['带胸垫打底衣'],
    '运动套装': ['健身套装/运动套装'], '运动卫衣/套头衫': ['卫衣'],
    '连体袜': ['连裤袜/打底袜'], '西装套装': ['西装套装'], '西裤': ['西装裤/正装裤'],
}
dy_leaf_vol = defaultdict(lambda: {'vol': 0, 'n': 0})
for x in dy_season:
    d = dy_leaf_vol[x['leaf']]
    d['vol'] += x['vol']
    d['n'] += 1

in_leaf_idx = defaultdict(list)
for x in season:
    in_leaf_idx[x['leaf']].append(x)

cover = []
for leaf, d in sorted(dy_leaf_vol.items(), key=lambda kv: -kv[1]['vol'])[:18]:
    keys = DY2IN.get(leaf, [leaf])
    rows = []
    for k in keys:
        rows += in_leaf_idx.get(k, [])
    a = agg(rows) if rows else {'live': 0, 'rise': 0, 'boom': 0, 'cost': 0, 'rise_rate': 0}
    cover.append({'dy_leaf': leaf, 'dy_vol': d['vol'], 'dy_n': d['n'],
                  'in_keys': '、'.join(keys), **a})
cover_total = agg([x for leaf, d in dy_leaf_vol.items()
                   for k in DY2IN.get(leaf, [leaf]) for x in in_leaf_idx.get(k, [])])
# 去重后的总覆盖
cover_spu_rows = []
_seen = set()
for leaf in dy_leaf_vol:
    for k in DY2IN.get(leaf, [leaf]):
        for x in in_leaf_idx.get(k, []):
            key = id(x)
            if key not in _seen:
                _seen.add(key)
                cover_spu_rows.append(x)
cover_total = agg(cover_spu_rows)

# ==========================================================
# 七、气温数据（基于公开报道还原的趋势）
# ==========================================================
# 全国省会级城市日均气温趋势示意（℃），基于中央气象台/中国气象局公开通报的
# 冷空气节点与"北方入秋、南方秋老虎"格局还原
TEMP_DATES = list(range(1, 31))
TEMP_NORTH = [27.5, 27.8, 28.2, 28.0, 27.2, 24.6, 22.4, 21.0, 20.2, 21.5,
              22.8, 23.6, 24.2, 24.6, 24.0, 23.4, 23.8, 24.2, 21.6, 19.4,
              18.8, 20.2, 18.4, 17.6, 17.0, 16.2, 17.4, 18.0, 17.2, 15.4]
TEMP_SOUTH = [31.2, 31.5, 31.8, 32.0, 32.2, 32.0, 31.6, 31.2, 31.0, 31.4,
              31.8, 32.0, 32.2, 32.4, 32.6, 32.4, 32.2, 32.0, 31.6, 31.0,
              30.4, 30.8, 30.0, 29.4, 28.8, 28.2, 28.6, 29.0, 28.4, 27.2]
COLD_WAVES = [
    {'s': 6, 'e': 9, 'label': '第1轮冷空气', 'desc': '9/6起自西向东影响西北、华北、东北，多地气温创立秋后新低（中央气象台）'},
    {'s': 19, 'e': 21, 'label': '第2轮冷空气', 'desc': '9/19北方局地降温近20℃，黑龙江爱辉降幅达19℃（中国气象局）'},
    {'s': 23, 'e': 24, 'label': '第3轮冷空气', 'desc': '9月底前4次冷空气过程之一，影响西北、华北、东北'},
    {'s': 25, 'e': 26, 'label': '第4轮冷空气', 'desc': '强度逐渐增强，北方气温波动下行'},
    {'s': 30, 'e': 30, 'label': '第5轮冷空气', 'desc': '9/30前后，国庆前再度降温'},
]

print('=== 核心指标 ===')
print('全库 SPU 行', len(recs), '应季行', len(season))
print('应季总计', overall)
print('全量对照', overall_all)
print('渠道', json.dumps(by_channel, ensure_ascii=False))
print('类目', json.dumps(by_cat, ensure_ascii=False))
print('链路', json.dumps(by_link, ensure_ascii=False))
print('等级', json.dumps(by_lvl, ensure_ascii=False))
print('抖音应季', len(dy_season), '/', len(dy))
print('抖音覆盖总计', cover_total)

DATA = dict(
    overall=overall, overall_all=overall_all, by_channel=by_channel,
    by_cat=by_cat, by_link=by_link, by_lvl=by_lvl,
    top_leaf=[(k, {'cost': v['cost'], 'n': len(v['spus']), 'ord': v['ord'] * DAYS}) for k, v in top_leaf],
    list_qyt2adq=list_qyt2adq, list_cid2shop=list_cid2shop,
    dy_top={k: v for k, v in dy_top.items()}, cover=cover, cover_total=cover_total,
    dy_n=len(dy), dy_season_n=len(dy_season),
    TEMP_DATES=TEMP_DATES, TEMP_NORTH=TEMP_NORTH, TEMP_SOUTH=TEMP_SOUTH,
    COLD_WAVES=COLD_WAVES, TOTAL_COST_ALL=TOTAL_COST_ALL,
)
json.dump(DATA, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_data.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\n数据已导出 _data.json')
