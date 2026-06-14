"""
体验内容自动丰富脚本

流程: Wikipedia 提取英文关键词 → Pexels 搜索 → 下载图片 → ColorThief 提取配色
     → DeepSeek LLM 生成内容（含目的地/国家/Wikipedia摘要上下文）→ 更新数据库
"""

import sys, json, os, urllib.request, urllib.parse
from colorthief import ColorThief

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend', 'public', 'images')


def get_pexels_key():
    with open(os.path.expanduser('~/.claude.json')) as f:
        c = json.load(f)
    return c['mcpServers']['pexels']['env']['PEXELS_API_KEY']


# ── Wikipedia 辅助 ──────────────────────────────────────────────────────────

def search_wikipedia(query, lang='en', limit=3):
    """搜索 Wikipedia，返回 {title, snippet, pageid} 列表"""
    url = (
        f'https://{lang}.wikipedia.org/w/api.php'
        f'?action=query&list=search&srsearch={urllib.parse.quote(query)}'
        f'&format=json&origin=*&srlimit={limit}'
    )
    try:
        req = urllib.request.Request(url, headers={'User-Agent': '100Trips/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        results = data.get('query', {}).get('search', [])
        return [{'title': r['title'], 'snippet': _strip_html(r.get('snippet', '')),
                 'pageid': r['pageid']} for r in results]
    except Exception:
        return []


def get_wikipedia_extract(pageid, lang='en', sentences=5):
    """获取 Wikipedia 页面摘要"""
    url = (
        f'https://{lang}.wikipedia.org/w/api.php'
        f'?action=query&format=json&origin=*'
        f'&pageids={pageid}&prop=extracts&exintro=1'
        f'&explaintext=1&exsentences={sentences}'
    )
    try:
        req = urllib.request.Request(url, headers={'User-Agent': '100Trips/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        pages = data.get('query', {}).get('pages', {})
        page = pages.get(str(pageid), {})
        return page.get('extract', '')
    except Exception:
        return ''


def _strip_html(text):
    """去除 HTML 标签"""
    import re
    return re.sub(r'<[^>]+>', '', text)


# ── Pexels 搜索（改进版）───────────────────────────────────────────────────

def search_pexels(query, orientation='landscape', per_page=5):
    """搜索 Pexels 图库。query 应为英文关键词以获取准确结果。"""
    key = get_pexels_key()
    url = (
        f'https://api.pexels.com/v1/search'
        f'?query={urllib.parse.quote(query)}'
        f'&orientation={orientation}&per_page={per_page}'
    )
    req = urllib.request.Request(url, headers={
        'Authorization': key,
        'User-Agent': '100Trips/1.0',
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    photos = data.get('photos', [])
    if not photos:
        return None
    # 取第一张（per_page=5 时已是 Pexels 按相关度排序的前5）
    best = photos[0]
    return {
        'id': best['id'],
        'url': best['url'],
        'photographer': best['photographer'],
        'avg_color': best['avg_color'],
        'alt': best.get('alt', ''),
        'large_url': best['src']['large'],
        'original_url': best['src']['original'],
    }


def search_pexels_with_fallback(query_cn, destination, country):
    """
    智能图片搜索:
    1. 先用 Wikipedia 英文搜索结果 → 提取地点英文名 → Pexels
    2. fallback: country + destination 英文翻译 → Pexels
    3. fallback: 原始中文词 → Pexels
    """
    # Step 1: 从 Wikipedia 获取正确英文关键词
    wiki_results = search_wikipedia(query_cn)
    if wiki_results:
        # 用 Wikipedia 页面标题作为英文关键词
        en_keyword = wiki_results[0]['title']
        photo = search_pexels(en_keyword)
        if photo:
            return photo, en_keyword, wiki_results

    # Step 2: 拼接 country + destination 尝试
    if country and destination:
        en_query = f"{destination} {country}"
        photo = search_pexels(en_query)
        if photo:
            return photo, en_query, wiki_results

    # Step 3: 原始中文词
    photo = search_pexels(query_cn)
    return photo, query_cn, wiki_results


# ── 图片下载 ────────────────────────────────────────────────────────────────

def download_image(url, trip_id):
    """下载图片到 public/images/"""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    filename = f'{trip_id}_enriched.jpg'
    filepath = os.path.join(IMAGES_DIR, filename)

    req = urllib.request.Request(url, headers={'User-Agent': '100Trips/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(filepath, 'wb') as f:
            f.write(resp.read())

    size = os.path.getsize(filepath)
    return f'/images/{filename}', filepath, size


# ── ColorThief ──────────────────────────────────────────────────────────────

def extract_colors(image_path):
    """ColorThief 提取主色和色阶"""
    ct = ColorThief(image_path)
    dominant = ct.get_color(quality=1)
    palette = ct.get_palette(color_count=5, quality=1)
    return {
        'dominant': '#{:02X}{:02X}{:02X}'.format(*dominant),
        'palette': ['#{:02X}{:02X}{:02X}'.format(*c) for c in palette],
    }


# ── 主流程 ──────────────────────────────────────────────────────────────────

def enrich_trip(trip_id, search_query=None):
    """
    自动丰富一条 trip:
    1. Wikipedia 搜索 → 提取英文关键词 + 获取摘要
    2. Pexels 用英文关键词搜图（解决中文搜索不准确）
    3. 下载图片到本地
    4. ColorThief 提取配色
    5. DeepSeek LLM 生成内容（含 destination/country/Wikipedia摘要上下文）
    6. 更新数据库
    """
    from models import create_db_engine, create_session_factory, Trip
    engine = create_db_engine(f'sqlite:///{BASE_DIR}/trips.db')
    Session = create_session_factory(engine)
    session = Session()

    trip = session.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        session.close()
        return {'error': f'Trip #{trip_id} not found'}

    query = search_query or trip.title or trip.destination
    destination = trip.destination or ''
    country = trip.country or ''

    result = {'trip_id': trip_id,
              'query': query,
              'destination': destination,
              'country': country,
              'steps': []}

    # ── Step 1: Wikipedia 搜索（获取英文关键词 + 摘要） ──────────────────
    wiki_summary = ''
    wiki_keyword = query
    try:
        wiki_results = search_wikipedia(query)
        if wiki_results:
            wiki_keyword = wiki_results[0]['title']
            result['wiki_title'] = wiki_keyword
            result['wiki_results'] = [w['title'] for w in wiki_results[:3]]
            result['steps'].append(f'wikipedia:ok:{wiki_keyword}')

            # 获取摘要作为 LLM 上下文
            wiki_summary = get_wikipedia_extract(wiki_results[0]['pageid'])
            if wiki_summary:
                result['steps'].append(f'wikipedia_extract:{len(wiki_summary)}chars')
        else:
            result['steps'].append('wikipedia:no_results')
    except Exception as e:
        result['steps'].append(f'wikipedia:error:{e}')

    # ── Step 2: Pexels 搜索（用英文关键词） ──────────────────────────────
    try:
        photo = search_pexels(wiki_keyword)
        if photo:
            result['steps'].append(f'pexels_search:ok:{wiki_keyword}')
            result['photo'] = {'id': photo['id'], 'photographer': photo['photographer']}
        else:
            # fallback: 用中文原始词
            photo = search_pexels(query)
            if photo:
                result['steps'].append(f'pexels_search:fallback_cn:{query}')
            else:
                result['steps'].append('pexels_search:no_results')
                session.close()
                return result
    except Exception as e:
        result['steps'].append(f'pexels_search:error:{e}')
        session.close()
        return result

    # ── Step 3: 下载图片 ────────────────────────────────────────────────
    try:
        image_path, full_path, fsize = download_image(photo['large_url'], trip_id)
        result['steps'].append(f'download:ok:{fsize}bytes')
    except Exception as e:
        result['steps'].append(f'download:error:{e}')
        session.close()
        return result

    # ── Step 4: ColorThief ──────────────────────────────────────────────
    try:
        colors = extract_colors(full_path)
        result['steps'].append('colors:ok')
        result['colors'] = colors
    except Exception as e:
        result['steps'].append(f'colors:error:{e}')
        result['colors'] = {'dominant': photo.get('avg_color', '#888888'), 'palette': []}

    # ── Step 5: LLM 生成内容（增强版 Prompt） ──────────────────────────
    gen_result = generate_content(
        title=trip.title or query,
        destination=destination,
        country=country,
        photo_alt=photo.get('alt', ''),
        photographer=photo.get('photographer', ''),
        wiki_summary=wiki_summary,
    )
    if gen_result:
        content, story, subtitle = gen_result
        trip.content = content
        trip.story = story
        if subtitle:
            trip.subtitle = subtitle
        result['steps'].append('content_gen:ok')
    else:
        result['steps'].append('content_gen:skipped')

    # ── Step 6: 更新数据库 ──────────────────────────────────────────────
    trip.cover_image = image_path
    trip.image_source = f"Pexels / {photo['photographer']}"
    trip.image_source_url = photo['url']
    session.commit()

    result['steps'].append('db_update:ok')
    result['image_path'] = image_path
    result['colors'] = colors
    if wiki_summary:
        result['wiki_summary_preview'] = wiki_summary[:200]
    session.close()
    return result


# ── LLM 内容生成（改进版）──────────────────────────────────────────────────

def generate_content(title, destination='', country='', photo_alt='',
                     photographer='', wiki_summary=''):
    """
    调用 DeepSeek LLM 生成内容和故事。
    Prompt 现在包含 destination/country/Wikipedia 摘要，
    确保生成内容的地点信息和景色描述准确。
    """
    llm_result = _call_deepseek(
        title=title,
        destination=destination,
        country=country,
        photo_alt=photo_alt,
        wiki_summary=wiki_summary,
    )
    if llm_result:
        return llm_result['content'], llm_result['story'], llm_result.get('subtitle', '')

    # Fallback 模板（含正确的地点信息）
    location_line = f"📍 {destination}, {country}" if destination else ''
    content = f"""## 体验概述

{location_line}

{photo_alt or title}。这是一次令人心潮澎湃的旅程。

### 体验亮点

- 深入目的地核心区域，避开游客大军
- 当地资深向导带队，解锁隐藏玩法
- 全程小众路线设计，独一无二的视角

### 适合人群

热爱冒险、追求独特体验的旅行者。

---
📷 Photo by {photographer} on Pexels"""

    story = f"""关于{title}，{destination}流传着许多故事。每一位到访者都带着自己的想象而来，又带着独一无二的记忆离开。"""
    subtitle = f"{destination}的极致体验" if destination else ''
    return content, story, subtitle


def _call_deepseek(title, destination='', country='', photo_alt='', wiki_summary=''):
    """调用 DeepSeek API 生成旅行文案（增强版 Prompt）"""
    import json as _json

    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        try:
            with open(os.path.expanduser('~/.claude/settings.json')) as f:
                c = _json.load(f)
            api_key = c.get('env', {}).get('ANTHROPIC_AUTH_TOKEN', '')
        except Exception:
            pass

    if not api_key:
        return None

    # 构建上下文信息
    location_context = ''
    if destination:
        location_context += f'目的地: {destination}'
        if country:
            location_context += f', {country}'
        location_context += '\n'

    wiki_context = ''
    if wiki_summary:
        wiki_context = f'\n参考信息（Wikipedia）:\n{wiki_summary[:800]}\n'

    prompt = f"""你是一个专业的旅行内容编辑。为以下旅行体验生成 Markdown 内容、故事和副标题。

体验名称: {title}
{location_context}{wiki_context}
图片描述: {photo_alt}

要求:
- subtitle: 用一句话准确描述该景点最核心、最具辨识度的自然或人文景色（20字以内）。
  必须是客观的景色描述，禁止使用夸张营销修辞（如"触手可及""一生必去""此生无憾"等）。
  示例格式: "火山口内的七彩岩浆房" 而非 "地心入口触手可及"
- content: Markdown格式。开头必须包含一行 📍 目的地, 国家（从上方信息获取，不得编造）。
  包含三个段落: 体验概述、亮点（3-4个要点）、适合人群。
- story: 300-500字情感故事，融入目的地的真实历史或人文背景。

请输出严格 JSON 格式:
{{"subtitle": "准确的景色一句话描述", "content": "## 体验概述\\n\\n📍 目的地, 国家\\n\\n...", "story": "..."}}

只输出 JSON，不要其他文字。"""

    try:
        req = urllib.request.Request(
            'https://api.deepseek.com/v1/chat/completions',
            data=_json.dumps({
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 1500,
                'temperature': 0.7,  # 降低温度减少随机编造
            }).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
                'User-Agent': '100Trips/1.0',
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = _json.loads(resp.read())

        text = data['choices'][0]['message']['content']
        text = text.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1].rsplit('```', 1)[0]
        return _json.loads(text)
    except Exception:
        return None


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python enrich.py <trip_id> [search_query]")
        sys.exit(1)

    tid = int(sys.argv[1])
    sq = sys.argv[2] if len(sys.argv) > 2 else None
    result = enrich_trip(tid, sq)
    print(json.dumps(result, ensure_ascii=False, indent=2))
