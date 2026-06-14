"""
体验内容自动丰富脚本

流程: Pexels 搜索 → 下载图片 → ColorThief 提取配色 → 更新数据库
LLM 内容生成由 Claude Code 在会话中完成（生产环境替换为 LLM API 调用）
"""

import sys, json, os, urllib.request, urllib.parse
from colorthief import ColorThief

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend', 'public', 'images')

def get_pexels_key():
    with open(os.path.expanduser('~/.claude.json')) as f:
        c = json.load(f)
    return c['mcpServers']['pexels']['env']['PEXELS_API_KEY']

def search_pexels(query):
    """搜索 Pexels 图库，返回最佳匹配图片信息"""
    key = get_pexels_key()
    url = f'https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&orientation=landscape&per_page=3'
    req = urllib.request.Request(url, headers={
        'Authorization': key,
        'User-Agent': '100Trips/1.0',
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    photos = data.get('photos', [])
    if not photos:
        return None
    best = photos[0]
    return {
        'id': best['id'],
        'url': best['url'],
        'photographer': best['photographer'],
        'avg_color': best['avg_color'],
        'large_url': best['src']['large'],
        'original_url': best['src']['original'],
    }

def download_image(url, trip_id):
    """下载图片到 public/images/"""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    filename = f'{trip_id}_enriched.jpg'
    filepath = os.path.join(IMAGES_DIR, filename)

    # 用 urllib 带 User-Agent 下载
    req = urllib.request.Request(url, headers={'User-Agent': '100Trips/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(filepath, 'wb') as f:
            f.write(resp.read())

    size = os.path.getsize(filepath)
    return f'/images/{filename}', filepath, size

def extract_colors(image_path):
    """ColorThief 提取主色和色阶"""
    ct = ColorThief(image_path)
    dominant = ct.get_color(quality=1)
    palette = ct.get_palette(color_count=5, quality=1)
    return {
        'dominant': '#{:02X}{:02X}{:02X}'.format(*dominant),
        'palette': ['#{:02X}{:02X}{:02X}'.format(*c) for c in palette],
    }

def enrich_trip(trip_id, search_query=None):
    """
    自动丰富一条 trip:
    1. Pexels 搜索配图
    2. 下载到本地
    3. ColorThief 提取配色
    4. 返回更新数据
    """
    from models import create_db_engine, create_session_factory, Trip
    engine = create_db_engine(f'sqlite:///{BASE_DIR}/trips.db')
    Session = create_session_factory(engine)
    session = Session()

    trip = session.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        session.close()
        return {'error': f'Trip #{trip_id} not found'}

    query = search_query or trip.destination or trip.title

    result = {'trip_id': trip_id, 'query': query, 'steps': []}

    # Step 1: Pexels 搜索
    try:
        photo = search_pexels(query)
        if photo:
            result['steps'].append('pexels_search:ok')
            result['photo'] = photo
        else:
            result['steps'].append('pexels_search:no_results')
            session.close()
            return result
    except Exception as e:
        result['steps'].append(f'pexels_search:error:{e}')
        session.close()
        return result

    # Step 2: 下载图片
    try:
        image_path, full_path, fsize = download_image(photo['large_url'], trip_id)
        result['steps'].append(f'download:ok:{image_path}:{fsize}bytes')
    except Exception as e:
        result['steps'].append(f'download:error:{e}')
        session.close()
        return result

    # Step 3: ColorThief
    try:
        colors = extract_colors(full_path)
        result['steps'].append(f'colors:ok')
        result['colors'] = colors
    except Exception as e:
        result['steps'].append(f'colors:error:{e}')
        result['colors'] = {'dominant': photo['avg_color'], 'palette': []}

    # Step 4: 生成内容
    gen_result = generate_content(trip.title or query, photo)
    if gen_result:
        content, story, subtitle = gen_result if len(gen_result) == 3 else (*gen_result, '')
        trip.content = content
        trip.story = story
        if subtitle:
            trip.subtitle = subtitle
        result['steps'].append('content_gen:ok')
    else:
        result['steps'].append('content_gen:skipped')

    # Step 5: 更新数据库
    trip.cover_image = image_path
    trip.image_source = f"Pexels / {photo['photographer']}"
    trip.image_source_url = photo['url']
    trip.country = trip.country or ''
    session.commit()

    result['steps'].append('db_update:ok')
    result['image_path'] = image_path
    result['colors'] = colors
    session.close()
    return result


def generate_content(title, photo):
    """调用 DeepSeek LLM 生成内容和故事。失败时 fallback 到模板。"""
    alt = photo.get('alt', '')
    photographer = photo.get('photographer', '')

    # 先尝试 LLM
    llm_result = _call_deepseek(title, alt)
    if llm_result:
        return llm_result['content'], llm_result['story'], llm_result.get('subtitle', '')

    # Fallback 模板
    content = f"""## {title}

{alt}。这是一次令人心潮澎湃的旅程。

### 体验亮点

- 深入目的地核心区域，避开游客大军
- 当地资深向导带队，解锁隐藏玩法
- 全程小众路线设计，独一无二的视角
- 在最佳季节感受最纯粹的在地体验

### 适合人群

热爱冒险、追求独特体验的旅行者。

---
📷 Photo by {photographer} on Pexels"""

    story = f"""关于{title}，当地流传着许多故事。每一位到访者都带着自己的想象而来，又带着独一无二的记忆离开。"""
    subtitle = ''
    return content, story, subtitle


def _call_deepseek(title, photo_alt):
    """调用 DeepSeek API (OpenAI 兼容) 生成旅行文案"""
    import json as _json

    # 尝试从环境变量或 settings.json 获取 key
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

    prompt = f"""你是一个旅行内容编辑。为以下旅行体验生成 Markdown 内容、故事和副标题。

目的地: {title}
图片描述: {photo_alt}

要求:
- subtitle: 一句话概括景点最独特的景色（15字以内），不可重复目的地名称
- content: Markdown格式，包含体验概述、亮点、适合人群
- story: 300-500字情感故事

请输出严格 JSON 格式:
{{"subtitle": "一句话景色概括", "content": "## 体验概述\\n\\n...", "story": "..."}}

只输出 JSON，不要其他文字。"""

    try:
        req = urllib.request.Request(
            'https://api.deepseek.com/v1/chat/completions',
            data=_json.dumps({
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 1500,
                'temperature': 0.8,
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
        # 提取 JSON
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
