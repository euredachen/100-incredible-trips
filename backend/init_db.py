"""
飞猪「100种不可思议旅行」— 数据库初始化 & 种子数据

执行方式:
    cd backend
    python init_db.py

行为:
    1. 删除旧表（如果存在）
    2. 创建新表
    3. 插入 5 条种子数据
    4. 验证并打印结果
"""

from datetime import datetime, timezone

from sqlalchemy import text

from models import (
    Difficulty,
    ExperienceType,
    Trip,
    VisualStyle,
    create_db_engine,
    create_session_factory,
)
from models import Base, init_db as _init_tables

DB_URL = "sqlite:///./trips.db"


# ── 种子数据 ─────────────────────────────────────────────────────────────────
# 设计理念：每一条都是"不可思议" — 罕见、极致、难以复制的旅行体验

SEED_TRIPS = [
    {
        "title": "北极圈玻璃穹顶下追逐极光与冰下潜水",
        "subtitle": "躺在恒温玻璃屋里看欧若拉起舞，再潜入冰海触摸另一个世界",
        "cover_image": "/images/1_norway_aurora_real.jpg",
        "destination": "特罗姆瑟·林根峡湾",
        "country": "挪威",
        "experience_type": ExperienceType.NATURE,
        "uniqueness_score": 9,
        "visual_style": VisualStyle.SNOW,
        "image_source": "Flickr (CC License)",
        "image_source_url": "https://www.flickr.com/search/?text=norway%20aurora%20northern%20lights",
        "content": """## 体验概述

在北极圈以北 350 公里的特罗姆瑟，你将入住悬浮于峡湾之上的 **全景玻璃穹顶小屋**。全透明穹顶让极光成为你的天花板——当欧若拉女神的绿色裙摆在头顶流转，你躺在斯堪的纳维亚羊毛被中，壁炉里松木噼啪作响。

第二天清晨，专业潜水向导将带你进行地球上最极端的潜水体验之一：**冰下潜水 (Ice Diving)**。在厚达 60cm 的冰层下，阳光被折射成钻石般的碎光，海豹可能好奇地从你身边滑过。

## 行程亮点

- 玻璃穹顶小屋配备极光唤醒系统 — 极光出现时床头灯光自动渐变亮起
- 冰下潜水由前挪威海军潜水教官一对一陪同
- 晚餐为北欧极地料理：烟熏驯鹿肉、云莓甜点、深海帝王蟹
- 可选附加体验：哈士奇雪橇追逐极光、萨米人帐篷篝火夜话

## 适合人群

对寒冷有一定耐受度、持开放水域潜水证 (OW) 即可。冰潜体验无需干式潜水衣经验——我们会提供完整培训。""",
        "story": """1987 年冬天，挪威极地探险家 **Lars Eriksen** 在特罗姆瑟峡湾冰潜时迷路。在能见度不足两米的冰下水域，他忽然看到头顶出现一片翡翠色的光——那是极光穿透冰层的模样。

"那一刻我忘记了恐惧，"Lars 在航海日志中写道，"我意识到自己正漂浮在两个世界的交界处：上方是星辰的舞蹈，下方是深海的寂静。"

三十年后，Lars 的孙子在祖父的日志启发下，将家族渔猎小屋改造成玻璃穹顶旅馆，并在同一条峡湾开设了冰潜课程。这个体验不仅是一次旅行，更是三代人对极地荒野守望的延续。""",
        "best_season": "10月–次年3月（极光季）",
        "duration_hours": 48.0,
        "difficulty": Difficulty.HARD,
    },
    {
        "title": "秘鲁亚马逊雨林与萨满共饮死藤水仪式",
        "subtitle": "在万物有灵的绿色圣殿中，开启一场关于自我与宇宙的对话",
        "cover_image": "/images/2_peru_amazon_real.jpg",
        "destination": "伊基托斯·亚马逊上游",
        "country": "秘鲁",
        "experience_type": ExperienceType.WELLNESS,
        "uniqueness_score": 10,
        "visual_style": VisualStyle.FOREST,
        "image_source": "Flickr (CC License)",
        "image_source_url": "https://www.flickr.com/search/?text=amazon%20rainforest%20peru",
        "content": """## 体验概述

这不是一次普通的"心灵疗愈 retreat"——这是由 **Shipibo 部落第七代萨满** 主持的正统死藤水仪式。在亚马逊雨林深处的传统 Maloca（仪式木屋）中，你将在萨满的 Icaros（圣歌）吟唱中，饮下这杯被称为"灵魂之藤"的棕色苦液。

仪式前后持续 7 天，包括：
- 3 次死藤水仪式（隔日进行，留出体悟整合时间）
- 每日亚马逊植物学徒步 — 萨满教你辨识 40+ 种药用植物
- 河豚粉色河豚观测（亚马逊河特有物种）
- 与部落女性学习 Shipibo 几何纹样编织（已被 UNESCO 列为非遗候选）

## 重要须知

这不是"娱乐性体验"。死藤水在南美原住民文化中是严肃的疗愈仪式。参与者需提前两周进行饮食准备（禁红肉、酒精、辛辣、发酵食品）。全程有随队西医监测生命体征。""",
        "story": """Shipibo 部落流传着一则创世神话：世界之初，森林、河流、动物和人类都说同一种语言。后来人类造了巴别塔，语言便四分五裂。但亚马逊雨林依然记得那种古老的语言——死藤水就是重新听懂它的钥匙。

主持仪式的萨满 **Dona Maria** 今年 74 岁，12 岁开始跟随祖母学习植物医学。"白人把死藤水叫致幻剂，"她说，"但它不是幻觉。幻觉是假的。死藤水让你看到的是真的一直存在、只是你平时看不到的东西。"

2024 年，一位来自上海的神经科学家在参加 Dona Maria 的仪式后，主动暂停了自己的药物研发项目。"现代医学花了几百年研究如何用分子对抗症状。而这片雨林里的人，花了几千年学习如何与整个生态系统对话。"她回到中国后创办了一个融合植物医学与脑科学的研究实验室。""",
        "best_season": "5月–9月（旱季，雨林小径可通行）",
        "duration_hours": 168.0,  # 7 天
        "difficulty": Difficulty.MODERATE,
    },
    {
        "title": "瓦努阿图活火山熔岩湖直升机导览",
        "subtitle": "站在地球的脉搏之上，俯瞰沸腾的岩浆之海",
        "cover_image": "/images/3_vanuatu_volcano_real.jpg",
        "destination": "塔纳岛·亚苏尔火山",
        "country": "瓦努阿图",
        "experience_type": ExperienceType.ADVENTURE,
        "uniqueness_score": 10,
        "visual_style": VisualStyle.MOUNTAIN,
        "image_source": "Flickr (CC License)",
        "image_source_url": "https://www.flickr.com/search/?text=vanuatu%20yasur%20volcano%20lava",
        "content": """## 体验概述

亚苏尔火山 (Mount Yasur) 是地球上 **最易接近的活火山熔岩湖**，也是世界上少数几座可以站在火山口边缘直接俯瞰沸腾熔岩的火山。这座火山已经持续喷发了 800 多年——库克船长在 1774 年就记录下了它的火光。

本体验采用 **直升机 + 徒步双模式**：

1. **直升机环飞**（日落前 1 小时）：从空中俯瞰火山口全貌，熔岩湖在你的脚下翻滚——这是地球上最像异星表面的景观之一
2. **火山口边缘徒步**（日落后）：在火山学家陪同下徒步至火山口南缘，距离熔岩湖仅 150 米。每 5-10 分钟，火山会喷发一次——岩浆弹在夜空中划出红色弧线，炸裂声比雷声更响

## 安全说明

亚苏尔火山活动等级实时监控。本体验仅在 Alert Level ≤ 2 时执行。随行火山学家有 15 年以上亚苏尔观测经验。直升机飞行员为前澳大利亚皇家空军。""",
        "story": """瓦努阿图原住民视亚苏尔火山为 **先祖灵魂的居所**。每年一度的 Toka 舞蹈仪式上，岛民会赤脚爬上火山口，向熔岩湖中投掷卡瓦根作为祭品。

2015 年，飓风 Pam 以 5 级强度正面袭击瓦努阿图，塔纳岛 90% 的房屋被毁。但奇迹般地，全岛无一人死亡——因为飓风来临前 24 小时，亚苏尔火山的喷发模式突然改变，岛民从中读出了预警，提前全员撤入洞穴。

英国火山学家 **John Seach** 自 1990 年代起就在塔纳岛定居。"亚苏尔教会了我一件事：地球是活的，"他说，"大多数人类已经忘记了这一点。站在火山口边缘，你会重新记起——那种震撼不是恐惧，而是敬畏。" """,
        "best_season": "4月–10月（南半球旱季，气流稳定）",
        "duration_hours": 6.0,
        "difficulty": Difficulty.MODERATE,
    },
    {
        "title": "格陵兰岛狗拉雪橇横穿冰峡湾",
        "subtitle": "像因纽特人一样，用最古老的方式穿越世界尽头的白色荒野",
        "cover_image": "/images/4_greenland_sled_real.jpg",
        "destination": "伊卢利萨特·迪斯科湾",
        "country": "格陵兰（丹麦）",
        "experience_type": ExperienceType.ADVENTURE,
        "uniqueness_score": 9,
        "visual_style": VisualStyle.OCEAN,
        "image_source": "Flickr (CC License)",
        "image_source_url": "https://www.flickr.com/search/?text=greenland%20sled%20dog%20ice%20fjord",
        "content": """## 体验概述

格陵兰狗 (Greenland Dog) 是地球上最古老的犬种之一——基因研究显示它们与一万年前的北极狼几乎没有分化。它们不是宠物，是工作伙伴。每一队 12-14 只格陵兰狗拉着一架传统木制雪橇，在 **联合国世界遗产伊卢利萨特冰峡湾** 的冰面上疾驰。

本体验为 **4 天 3 夜狗拉雪橇远征**：

- **Day 1**: 伊卢利萨特出发，学习驾驶雪橇基本口令（格陵兰狗只听格陵兰语指令）
- **Day 2**: 穿越 Sermermiut 山谷，追踪北极狐和北极兔踪迹，夜宿猎人木屋
- **Day 3**: 抵达冰峡湾深处 — 65 公里宽、浮冰高达 100 米的巨大冰墙前。这里每天崩解 2000 万吨冰山入海
- **Day 4**: 返回途中绕行 Eqi 冰川，在冰崩的轰鸣声中野餐

## 你将学会

- 格陵兰狗雪橇驾驶（全程由因纽特猎人指导）
- 冰面情况判断——哪些白色是雪、哪些是薄冰
- 北极生存基础：搭建 Igloo、极地定向、冻伤预防""",
        "story": """16 世纪，因纽特猎人发现了一个奇怪的现象：冬天，巨大的冰山会从北方的峡湾漂来，即使在最冷的月份也不结冰的海域里缓慢漂移。他们相信那是 **Sila（风与天气之灵）** 在呼吸。

直到 2004 年，冰川学家才揭示了背后的科学：伊卢利萨特冰川是全世界移动最快的冰川，每天前进 40 米。它崩落的冰山体积如此之大，以至于当年撞击泰坦尼克号的那座冰山极可能就诞生于此。

然而，因纽特猎人 **Nuka** 对"冰川移动速度"的数据不感兴趣。"你们用卫星测量它走了多远，"他说，"我们用耳朵听。当冰峡湾的轰鸣声变调的那一刻，我们就知道该换一条路线了。你们的科学说我们落后，但我们的耳朵比你们的卫星早了 400 年。" """,
        "best_season": "2月–4月（海冰最厚，日照充足）",
        "duration_hours": 72.0,  # 4 天 3 夜
        "difficulty": Difficulty.HARD,
    },
    {
        "title": "不丹徒步'雷龙之路'，夜宿悬崖寺庙",
        "subtitle": "在最后的香格里拉，与雷声同行，与僧人的诵经声一同入眠",
        "cover_image": "/images/5_bhutan_monastery_real.jpg",
        "destination": "帕罗·廷布",
        "country": "不丹",
        "experience_type": ExperienceType.CULTURAL,
        "uniqueness_score": 10,
        "visual_style": VisualStyle.MOUNTAIN,
        "image_source": "Flickr (CC License)",
        "image_source_url": "https://www.flickr.com/search/?text=bhutan%20monastery%20temple%20mountain",
        "content": """## 体验概述

**雷龙之路 (Druk Path)** 是不丹最古老的徒步路线之一，连接帕罗与首都廷布，全长约 54 公里。这条古道曾经是不丹王室巡游之路，沿途经过海拔 2400–4200 米的高山湖泊、千年杜鹃林和雪山垭口。

本体验的"不可思议"之处在于 **住宿**——并非帐篷，而是沿途的 **悬崖佛教寺庙 (Lhakhang)**：

- **Jangchulakha 寺**（海拔 3800m）：建在一块突出悬崖的巨石上，三面悬空。清晨云海从墙外流过
- **Jimilangtso 寺**（海拔 3900m）：以湖命名，僧人每天傍晚在湖边喂食 300+ 条高山鳟鱼——这些鱼被认为是放生的生灵
- **Phajoding 寺**（海拔 3700m）：位于廷布上方的云雾森林中，终点的晨钟声预示着旅程结束

## 独特规定

- 不丹政府规定所有徒步必须有持证向导陪同
- 每日需向寺庙供奉酥油灯（费用已含在体验费中）
- 全程禁飞无人机（不丹全国禁飞）——但你的眼睛会记住一切""",
        "story": """1999 年，不丹国王 **吉格梅·辛格·旺楚克** 提出了后来闻名世界的概念——"国民幸福总值 (Gross National Happiness, GNH)"。当时西方媒体大多将其视为一个发展中国家领导人的浪漫幻想。

25 年后的今天，不丹是全球唯一一个碳中和国家。全国森林覆盖率 72%，宪法规定必须保持在 60% 以上。所有建筑必须保留传统不丹风格。每年入境的国际游客数量被严格限制。

雷龙之路上的一位老僧 **Lopen Dorji** 对此有自己的解释："GNH 不是一个经济学概念。它是一个生存策略。你们的世界在讨论如何让经济增长 5%。我们讨论的是——如何让半个世纪后的年轻人，依然能在这些山路上听到雷声，而不是引擎声。"

当你夜宿悬崖寺庙，在酥油灯和经文的陪伴中入睡时，你会明白 Lopen Dorji 所说的那种"生存策略"到底是什么意思。""",
        "best_season": "3月–5月（杜鹃花季），9月–11月（天高云淡）",
        "duration_hours": 120.0,  # 5 天 4 夜
        "difficulty": Difficulty.HARD,
    },
]


# ── 初始化逻辑 ──────────────────────────────────────────────────────────────

def reset_and_seed(engine=None) -> None:
    """删除旧表 → 建新表 → 插入种子数据。"""
    if engine is None:
        engine = create_db_engine(DB_URL)

    SessionLocal = create_session_factory(engine)

    # 1. 删除旧表
    print("🗑️  删除旧表...")
    Base.metadata.drop_all(engine)

    # 2. 建表
    print("🏗️  创建新表...")
    Base.metadata.create_all(engine)

    # 3. 插入种子数据
    print(f"🌱 插入 {len(SEED_TRIPS)} 条种子数据...")
    with SessionLocal() as session:
        for trip_data in SEED_TRIPS:
            trip = Trip(**trip_data)
            session.add(trip)
        session.commit()

        # 4. 验证
        count = session.query(Trip).count()
        print(f"✅ 完成！当前 trips 表共 {count} 条记录\n")

        # 打印摘要
        trips = session.query(Trip).order_by(Trip.id).all()
        for t in trips:
            print(
                f"  [{t.id}] {t.title}  "
                f"| {t.country}  "
                f"| 🏷 {t.experience_type.value}  "
                f"| ⭐ {t.uniqueness_score}/10  "
                f"| 🎨 {t.visual_style.value}  "
                f"| 💪 {t.difficulty.value}"
            )

    print("\n🎉 数据库就绪: trips.db")


if __name__ == "__main__":
    reset_and_seed()
