"""
体验内容自动丰富脚本 — 多源搜索 + 智能图片匹配版

流程:
  Phase 1: Wikipedia(EN+ZH) + NatGeo 多源搜索 → 提取正确地点名 + 介绍文本
  Phase 2: 智能图片搜索 — Wikipedia 头图 → Pexels 精确匹配 → 景观关键词 fallback
  Phase 3: LLM 文案生成（含完整上下文：正确地点 + 多源文本）
  Phase 4: 写库（更新 destination/subtitle/content/cover_image）
"""

import sys, json, os, re, urllib.request, urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend', 'public', 'images')


# ═══════════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════════

def _json_load(path):
    with open(os.path.expanduser(path)) as f:
        return json.load(f)

def _strip_html(s):
    return re.sub(r'<[^>]+>', '', s)

def _http_get(url, timeout=10):
    req = urllib.request.Request(url, headers={'User-Agent': '100Trips/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: 多源搜索
# ═══════════════════════════════════════════════════════════════════════════════

def _clean_query(query):
    """清洗搜索词 — 移除活动描述词、影视/人物名、后缀噪声，只保留地点名"""
    # 活动/攻略类噪声
    noise = ['内部徒步', '徒步', '旅行', '体验', '攻略', '一日游', '深度游',
             '探险', '打卡', '自由行', '跟团', '自助', '旅游', '之行', '之旅',
             '怎么去', '怎么玩', '门票', '价格', '路线', '环线', '穿越',
             '全景', '日落', '日出', '最佳', '推荐', '必去', '必打卡']
    # 影视/人物/文学噪声 — 这些不是地名
    culture_noise = [
        '宫崎骏', '幽灵公主', '千与千寻', '龙猫', '哈尔的移动城堡', '天空之城',
        '哈利波特', '指环王', '魔戒', '权力的游戏', '星际穿越', '盗梦空间',
        '阿凡达', '指环王', '霍比特人', '蝙蝠侠', '蜘蛛侠', '复仇者联盟',
        '你的名字', '天气之子', '铃芽之旅', '新海诚',
    ]
    # 地点后缀噪声（保留核心地名，去掉这些后缀）
    suffix_noise = ['原址', '拍摄地', '取景地', '取景', '外景地', '电影场景',
                   '原型', '原型地', '灵感来源', '场景', '片场', '主题公园',
                   '打卡点', '观景台', '眺望台', '展望台']

    cleaned = query
    # 先移除长噪声（影视/人物名）
    for w in culture_noise:
        cleaned = cleaned.replace(w, '')
    # 再移除活动噪声
    for w in noise:
        cleaned = cleaned.replace(w, '')
    # 最后移除后缀
    for w in suffix_noise:
        cleaned = cleaned.replace(w, '')

    return cleaned.strip()


def wiki_search(query, lang='en', limit=3):
    """Wikipedia 搜索 → [{title, snippet, pageid}]"""
    url = (
        f'https://{lang}.wikipedia.org/w/api.php'
        f'?action=query&list=search&srsearch={urllib.parse.quote(query)}'
        f'&format=json&origin=*&srlimit={limit}'
    )
    try:
        data = _http_get(url)
        return [{'title': r['title'], 'snippet': _strip_html(r.get('snippet', '')),
                 'pageid': r['pageid']}
                for r in data.get('query', {}).get('search', [])]
    except Exception:
        return []


def wiki_langlinks(pageid, lang='en'):
    """通过 langlinks 获取中文页面对应的英文 Wikipedia 页面"""
    url = (
        f'https://zh.wikipedia.org/w/api.php'
        f'?action=query&format=json&origin=*'
        f'&pageids={pageid}&prop=langlinks&lllimit=5'
    )
    try:
        data = _http_get(url)
        pages = data.get('query', {}).get('pages', {})
        page = pages.get(str(pageid), {})
        langlinks = page.get('langlinks', [])
        for ll in langlinks:
            if ll.get('lang') == lang:
                return ll.get('*', '')  # English title
    except Exception:
        pass
    return ''


def multi_wiki_search(query):
    """
    多策略 Wikipedia 搜索:
    1. 清洗中文查询词 → 搜 ZH Wikipedia
    2. 从 ZH 页面用 langlinks 获 EN 标题 → 搜 EN Wikipedia
    3. 若失败 → 直接 EN 搜索清洗后的中文词
    """
    cleaned = _clean_query(query)

    # 1. 中文 Wikipedia
    zh_results = wiki_search(cleaned, 'zh')
    if not zh_results and cleaned != query:
        zh_results = wiki_search(query, 'zh')

    # 2. 从 ZH 结果获取英文对应页面
    en_title = ''
    pageid = None
    en_summary = ''
    zh_text = ''

    if zh_results:
        zh_pageid = zh_results[0]['pageid']
        zh_text = wiki_extract(zh_pageid, 'zh', sentences=8)

        # langlinks: 中文页面 → 英文标题
        en_title = wiki_langlinks(zh_pageid, 'en')
        if en_title:
            # 用英文标题搜 EN Wikipedia 获取 pageid
            en_results = wiki_search(en_title, 'en', limit=1)
            if en_results:
                pageid = en_results[0]['pageid']
                en_summary = wiki_extract(pageid, 'en')

    # 3. 如果 langlinks 失败 → 直接用清洗后中文词搜 EN
    if not en_title:
        en_results = wiki_search(cleaned, 'en')
        if not en_results and cleaned != query:
            en_results = wiki_search(query, 'en')
        if en_results:
            en_title = en_results[0]['title']
            pageid = en_results[0]['pageid']
            en_summary = wiki_extract(pageid, 'en')

    return en_title, pageid, en_summary, zh_text, zh_results


def wiki_extract(pageid, lang='en', sentences=8):
    """Wikipedia 页面摘要"""
    url = (
        f'https://{lang}.wikipedia.org/w/api.php'
        f'?action=query&format=json&origin=*'
        f'&pageids={pageid}&prop=extracts&exintro=1'
        f'&explaintext=1&exsentences={sentences}'
    )
    try:
        data = _http_get(url)
        pages = data.get('query', {}).get('pages', {})
        return pages.get(str(pageid), {}).get('extract', '')
    except Exception:
        return ''


def wiki_page_image(pageid, lang='en'):
    """Wikipedia 页面头图（PageImages extension）"""
    url = (
        f'https://{lang}.wikipedia.org/w/api.php'
        f'?action=query&format=json&origin=*'
        f'&pageids={pageid}&prop=pageimages&piprop=thumbnail|name'
        f'&pithumbsize=1200'
    )
    try:
        data = _http_get(url)
        pages = data.get('query', {}).get('pages', {})
        page = pages.get(str(pageid), {})
        thumb = page.get('thumbnail', {})
        if thumb.get('source'):
            return {'url': thumb['source'], 'source': f'Wikipedia / {page.get("title", "")}'}
    except Exception:
        pass
    return None


def natgeo_search(query):
    """National Geographic 搜索 — 返回文章列表"""
    url = (
        f'https://www.nationalgeographic.com/search?q={urllib.parse.quote(query)}'
        f'&sort=relevancy'
    )
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; 100Trips/1.0)',
            'Accept': 'text/html',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        # 提取搜索结果标题
        titles = re.findall(r'<h[23][^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h[23]>', html,
                            re.DOTALL | re.IGNORECASE)
        titles = [_strip_html(t).strip() for t in titles[:5] if _strip_html(t).strip()]
        return titles if titles else []
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2: 智能图片搜索
# ═══════════════════════════════════════════════════════════════════════════════

# 景观关键词 → Pexels 英文搜索词映射
LANDSCAPE_KEYWORDS = {
    '火山': 'volcano lava crater',
    '岩浆': 'lava magma volcanic',
    '熔岩': 'lava flow volcanic rock',
    '雪': 'snow winter landscape',
    '极光': 'aurora northern lights',
    '冰川': 'glacier ice fjord',
    '冰': 'ice frozen arctic',
    '北极': 'arctic snow polar',
    '南极': 'antarctica ice',
    '沙漠': 'desert sand dune',
    '海滩': 'beach tropical ocean',
    '海洋': 'ocean sea waves',
    '海岛': 'tropical island beach',
    '森林': 'forest jungle rainforest',
    '雨林': 'rainforest jungle tropical',
    '山峰': 'mountain peak alpine',
    '高山': 'mountain alpine',
    '湖泊': 'lake water reflection',
    '瀑布': 'waterfall cascade',
    '峡谷': 'canyon gorge valley',
    '洞穴': 'cave underground cavern',
    '草原': 'grassland prairie savanna',
    '温泉': 'hot spring geothermal',
    '城市': 'city skyline urban',
    '寺庙': 'temple monastery ancient',
    '古城': 'ancient city historic',
    '城堡': 'castle fortress medieval',
}


def _extract_landscape_keywords(query):
    """从中文查询中提取景观特征 → 映射为英文搜索词"""
    keywords = []
    for cn, en in LANDSCAPE_KEYWORDS.items():
        if cn in query:
            keywords.append(en)
    return ' '.join(keywords) if keywords else ''


def _get_pexels_key():
    """获取 Pexels API key — 优先环境变量，其次 ~/.claude.json"""
    key = os.environ.get('PEXELS_API_KEY', '')
    if key:
        return key
    try:
        c = _json_load('~/.claude.json')
        return c['mcpServers']['pexels']['env']['PEXELS_API_KEY']
    except Exception:
        return ''


def pexels_search(query, per_page=5):
    """Pexels 图片搜索"""
    key = _get_pexels_key()
    if not key:
        return None

    url = (
        f'https://api.pexels.com/v1/search'
        f'?query={urllib.parse.quote(query)}&orientation=landscape&per_page={per_page}'
    )
    try:
        req = urllib.request.Request(url, headers={
            'Authorization': key, 'User-Agent': '100Trips/1.0',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        photos = data.get('photos', [])
        if not photos:
            return None
        p = photos[0]
        return {
            'id': p['id'], 'url': p['url'], 'photographer': p['photographer'],
            'avg_color': p['avg_color'], 'alt': p.get('alt', ''),
            'large_url': p['src']['large'], 'original_url': p['src']['original'],
            'source': f"Pexels / {p['photographer']}",
        }
    except Exception:
        return None


def smart_image_search(query, wiki_title, wiki_pageid):
    """
    三级智能图片搜索:
    L1: Wikipedia 页面头图（最权威）
    L2: Pexels 用 Wikipedia 英文标题精确搜
    L3: Pexels 用景观关键词搜（火山/雪原/海滩等特征匹配）
    """
    # L1: Wikipedia 头图
    if wiki_pageid:
        img = wiki_page_image(wiki_pageid)
        if img:
            return img, 'wikipedia_page_image'

    # L2: Pexels + Wikipedia 英文标题
    if wiki_title and wiki_title != query:
        img = pexels_search(wiki_title)
        if img:
            return img, 'pexels_wiki_title'

    # L2b: Pexels + 原始查询
    img = pexels_search(query)
    if img:
        return img, 'pexels_query'

    # L3: 景观关键词 fallback
    landscape = _extract_landscape_keywords(query)
    if landscape:
        # 拼接地点信息使搜索更精准
        enhanced = f"{query} {landscape}"
        img = pexels_search(enhanced)
        if img:
            return img, 'pexels_landscape'
        # 纯景观词
        img = pexels_search(landscape)
        if img:
            return img, 'pexels_landscape_only'

    # 最后尝试
    img = pexels_search(query)
    if img:
        return img, 'pexels_fallback'

    return None, None


# ═══════════════════════════════════════════════════════════════════════════════
# 图片下载 & 配色
# ═══════════════════════════════════════════════════════════════════════════════

def download_image(url, trip_id):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    filename = f'{trip_id}_enriched.jpg'
    filepath = os.path.join(IMAGES_DIR, filename)
    req = urllib.request.Request(url, headers={'User-Agent': '100Trips/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(filepath, 'wb') as f:
            f.write(resp.read())
    return f'/images/{filename}', filepath, os.path.getsize(filepath)


def extract_colors(filepath):
    from colorthief import ColorThief
    ct = ColorThief(filepath)
    d = ct.get_color(quality=1)
    p = ct.get_palette(color_count=5, quality=1)
    return {
        'dominant': '#{:02X}{:02X}{:02X}'.format(*d),
        'palette': ['#{:02X}{:02X}{:02X}'.format(*c) for c in p],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3: LLM 文案生成
# ═══════════════════════════════════════════════════════════════════════════════

def build_llm_prompt(title, destination, country, wiki_en_title, wiki_summary,
                     wiki_zh_text, natgeo_titles, photo_alt):
    """构建带完整上下文信息的 LLM Prompt"""

    # ── 确定位置信息 ──────────────────────────────────────────────────
    if wiki_en_title:
        # Wikipedia 匹配 → 高置信度，直接使用
        location_display = f'{wiki_en_title}, {country}' if country and country not in wiki_en_title else wiki_en_title
        location_instruction = f'正确地点(必须使用): {location_display}'
    else:
        # 无 Wikipedia 匹配 → 让 LLM 根据自身知识判断实际地理位置
        cleaned_dest = _clean_query(destination) if destination else ''
        location_display = cleaned_dest or title
        location_instruction = (
            f'体验名称/搜索词: {title}。'
            f'请根据你的知识判断这个体验的实际地理位置（可能不是字面意思），'
            f'并在 content 中用 📍 标记正确的地名。'
            f'例如: 搜索词"宫崎骏幽灵公主原址"→实际地点是"屋久岛"；'
            f'搜索词"千与千寻取景地"→实际地点是"银山温泉"或"道后温泉"。'
        )

    # 构建上下文
    context_parts = []
    context_parts.append(f'体验名称: {title}')
    context_parts.append(location_instruction)
    if country:
        context_parts.append(f'国家: {country}')
    context_parts.append(f'图片描述: {photo_alt}')

    if wiki_summary:
        context_parts.append(f'\nWikipedia 英文介绍:\n{wiki_summary[:1200]}')
    if wiki_zh_text:
        context_parts.append(f'\nWikipedia 中文介绍:\n{wiki_zh_text[:600]}')
    if natgeo_titles:
        context_parts.append(f'\nNational Geographic 相关文章:\n' +
                             '\n'.join(f'- {t}' for t in natgeo_titles[:3]))

    context = '\n'.join(context_parts)

    prompt = f"""你是专业旅行编辑。根据以下参考资料，为旅行体验生成内容。

{context}

要求:
- subtitle: 一句话客观描述该景点最具辨识度的核心自然或人文景色(20字内)。
  必须是客观的景色描述。禁止使用夸张营销修辞(如"触手可及""一生必去""此生无憾")。
  正确示例: "火山内部的七彩岩浆房" / "冰雪中的极光穹顶玻璃屋"
- content: Markdown格式。第一行必须写 📍 实际地理位置（根据你查证的真实地名，不得编造）。
  包含三个段落: 体验概述(2-3句)、亮点(3-4个bullet)、适合人群(1-2句)。
- story: 300-500字，融入参考资料中的真实地理或人文背景。

只输出 JSON，不要其他文字:
{{"subtitle":"准确的景色描述","content":"## 体验概述\\n\\n📍 {location_display}\\n\\n...","story":"..."}}"""

    return prompt, location_display


def call_llm(prompt):
    """DeepSeek API 调用 — 安全解析 JSON，缺字段用默认值"""
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        try:
            api_key = _json_load('~/.claude/settings.json').get('env', {}).get(
                'ANTHROPIC_AUTH_TOKEN', '')
        except Exception:
            pass
    if not api_key:
        return None

    try:
        req = urllib.request.Request(
            'https://api.deepseek.com/v1/chat/completions',
            data=json.dumps({
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 2000, 'temperature': 0.7,
            }).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
                'User-Agent': '100Trips/1.0',
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        text = data['choices'][0]['message']['content'].strip()
        # 提取 JSON
        if text.startswith('```'):
            text = text.split('\n', 1)[1].rsplit('```', 1)[0]
        # 找 JSON 对象
        if '{' in text:
            text = text[text.index('{'):text.rindex('}') + 1]
        result = json.loads(text)
        # 确保必填字段存在
        return {
            'subtitle': result.get('subtitle', ''),
            'content': result.get('content', ''),
            'story': result.get('story', ''),
        }
    except Exception:
        return None


def fallback_content(title, destination, country, photo_source):
    location = destination or title
    location_display = f'{location}, {country}' if country else location
    content = f"""## 体验概述

📍 {location_display}

这是一次令人心潮澎湃的旅程。

### 体验亮点

- 深入目的地核心区域，避开游客大军
- 当地资深向导带队，解锁隐藏玩法
- 全程小众路线设计，独一无二的视角

### 适合人群

热爱冒险、追求独特体验的旅行者。

---
📷 Photo by {photo_source}"""
    story = f"""关于{title}，{location}流传着许多故事。每一位到访者都带着自己的想象而来，又带着独一无二的记忆离开。"""
    subtitle = f'{location}的极致体验' if destination else ''
    return content, story, subtitle


def _extract_location_from_content(content, wiki_title, destination, query):
    """从多个来源提取正确的地点名，优先级: Wikipedia > LLM内容📍 > clean(query)"""
    # 1. Wikipedia 是最权威的来源
    if wiki_title:
        return wiki_title

    # 2. 从 LLM 生成内容中解析 📍 标记
    if content:
        m = re.search(r'📍\s*(.+?)(?:\n|$)', content)
        if m:
            loc = m.group(1).strip()
            # 去掉常见后缀和噪声
            loc = re.sub(r'[，,].*$', '', loc)  # 去掉逗号后的内容
            loc = _clean_query(loc)  # 清洗掉"徒步""探险"等活动词
            if len(loc) >= 2 and len(loc) <= 30:
                return loc

    # 3. 用 _clean_query 清洗 destination
    cleaned = _clean_query(destination or query)
    if cleaned and cleaned != destination:
        return cleaned

    return destination


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4: 主流程
# ═══════════════════════════════════════════════════════════════════════════════

def enrich(trip_id, search_query=None):
    from models import create_db_engine, create_session_factory, Trip
    engine = create_db_engine(f'sqlite:///{BASE_DIR}/trips.db')
    Session = create_session_factory(engine)
    session = Session()

    trip = session.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        session.close()
        return {'error': f'Trip #{trip_id} not found'}

    query = search_query or trip.title or trip.destination
    result = {'trip_id': trip_id, 'query': query, 'steps': []}

    # ── Phase 1: 多源搜索 ───────────────────────────────────────────────
    wiki_en_title = ''
    wiki_pageid = None
    wiki_summary = ''
    wiki_zh_text = ''
    natgeo_articles = []

    # Wikipedia (EN + ZH 多策略搜索，含 langlinks)
    try:
        wiki_en_title, wiki_pageid, wiki_summary, wiki_zh_text, wr_zh = \
            multi_wiki_search(query)
        if wiki_en_title:
            result['steps'].append(f'wiki_en:{wiki_en_title}')
            if wiki_summary:
                result['steps'].append(f'wiki_en_extract:{len(wiki_summary)}c')
        else:
            result['steps'].append('wiki_en:none')
        if wr_zh:
            result['steps'].append(f'wiki_zh:{wr_zh[0]["title"]}')
    except Exception as e:
        result['steps'].append(f'wiki:err:{e}')

    # National Geographic
    try:
        natgeo_articles = natgeo_search(query)
        if natgeo_articles:
            result['steps'].append(f'natgeo:{len(natgeo_articles)}')
        else:
            result['steps'].append('natgeo:none')
    except Exception:
        result['steps'].append('natgeo:none')

    # ── Phase 2: 智能图片搜索 ──────────────────────────────────────────
    photo = None
    img_source = 'unknown'

    try:
        photo, img_source = smart_image_search(query, wiki_en_title, wiki_pageid)
        if photo:
            result['steps'].append(f'image:{img_source}')
        else:
            result['steps'].append('image:none')
            session.close()
            return result
    except Exception as e:
        result['steps'].append(f'image:err:{e}')
        session.close()
        return result

    # ── 下载图片 ────────────────────────────────────────────────────────
    try:
        img_path, full_path, fsize = download_image(photo.get('large_url') or photo.get('url'), trip_id)
        result['steps'].append(f'download:{fsize}b')
    except Exception as e:
        result['steps'].append(f'download:err:{e}')
        session.close()
        return result

    # ── ColorThief ──────────────────────────────────────────────────────
    try:
        result['colors'] = extract_colors(full_path)
        result['steps'].append('colors:ok')
    except Exception as e:
        result['steps'].append(f'colors:err:{e}')
        result['colors'] = {'dominant': photo.get('avg_color', '#666'), 'palette': []}

    # ── Phase 3: LLM 文案生成 ──────────────────────────────────────────
    prompt, correct_location = build_llm_prompt(
        title=trip.title or query,
        destination=trip.destination or '',
        country=trip.country or '',
        wiki_en_title=wiki_en_title,
        wiki_summary=wiki_summary,
        wiki_zh_text=wiki_zh_text,
        natgeo_titles=natgeo_articles,
        photo_alt=photo.get('alt', ''),
    )

    try:
        llm = call_llm(prompt)
        if llm:
            trip.content = llm['content']
            trip.story = llm['story']
            if llm.get('subtitle'):
                trip.subtitle = llm['subtitle']
            result['steps'].append('llm:ok')
            result['subtitle'] = llm.get('subtitle', '')
        else:
            ct, st, sub = fallback_content(
                trip.title or query, trip.destination or '', trip.country or '',
                photo.get('source', photo.get('photographer', 'Pexels')))
            trip.content = ct
            trip.story = st
            if sub:
                trip.subtitle = sub
            result['steps'].append('llm:fallback')
    except Exception as e:
        result['steps'].append(f'llm:err:{e}')
        llm = None  # 确保后续 Phase 4 可安全引用
        ct, st, sub = fallback_content(
            trip.title or query, trip.destination or '', trip.country or '',
            photo.get('source', photo.get('photographer', 'Pexels')))
        trip.content = ct
        trip.story = st
        if sub:
            trip.subtitle = sub

    # ── Phase 4: 写库（更新正确地点） ───────────────────────────────────
    trip.cover_image = img_path
    trip.image_source = photo.get('source', f"Pexels / {photo.get('photographer', '')}")
    trip.image_source_url = photo.get('url', '')

    # 修正 destination 和 country
    corrected_dest = _extract_location_from_content(
        llm.get('content', '') if llm else '',
        wiki_en_title,
        trip.destination or '',
        query
    )
    if corrected_dest and corrected_dest != trip.destination:
        result['steps'].append(f'destination_corrected:{trip.destination}→{corrected_dest}')
        trip.destination = corrected_dest

    # 如果 country 为空，尝试从 Wikipedia 摘要、查询词或内容推断
    if not trip.country:
        inferred = None
        country_map = [
            ('挪威', 'Norway'), ('冰岛', 'Iceland'), ('秘鲁', 'Peru'),
            ('日本', 'Japan'), ('韩国', 'South Korea'), ('Korea', 'South Korea'),
            ('法国', 'France'), ('意大利', 'Italy'), ('美国', 'United States'),
            ('中国', 'China'), ('纳米比亚', 'Namibia'), ('摩洛哥', 'Morocco'),
            ('新西兰', 'New Zealand'), ('澳大利亚', 'Australia'), ('泰国', 'Thailand'),
            ('格陵兰', 'Greenland'), ('不丹', 'Bhutan'), ('瓦努阿图', 'Vanuatu'),
            ('尼泊尔', 'Nepal'), ('印度', 'India'), ('瑞士', 'Switzerland'),
            ('加拿大', 'Canada'), ('墨西哥', 'Mexico'), ('巴西', 'Brazil'),
            ('阿根廷', 'Argentina'), ('智利', 'Chile'), ('埃及', 'Egypt'),
            ('肯尼亚', 'Kenya'), ('南非', 'South Africa'),
        ]
        for cn_name, en_name in country_map:
            if cn_name in query or cn_name in (trip.destination or '') or cn_name in (trip.title or ''):
                inferred = cn_name
                break
            if wiki_en_title and en_name.lower() in wiki_en_title.lower():
                inferred = cn_name
                break
        # 也从 LLM 内容中查找
        if not inferred and llm:
            content_text = llm.get('content', '')
            for cn_name, _ in country_map:
                if cn_name in content_text:
                    inferred = cn_name
                    break
        if inferred:
            trip.country = inferred
            result['steps'].append(f'country_inferred:{inferred}')
    session.commit()
    result['steps'].append('db:ok')
    result['image_path'] = img_path
    result['correct_location'] = wiki_en_title or trip.destination
    session.close()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python enrich.py <trip_id> [search_query]")
        sys.exit(1)
    tid = int(sys.argv[1])
    sq = sys.argv[2] if len(sys.argv) > 2 else None
    result = enrich(tid, sq)
    print(json.dumps(result, ensure_ascii=False, indent=2))
