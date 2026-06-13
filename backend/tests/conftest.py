"""
测试配置 & 共享 fixtures。

使用内存 SQLite 数据库，每个测试函数拥有独立的数据库会话。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 确保 backend 目录在 path 中
import sys
from pathlib import Path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from models import Base, Trip, Difficulty
from main import app, get_db


# ── 测试引擎（内存 SQLite，隔离且快速）────────────────────────────────────

TEST_DB_URL = "sqlite:///:memory:"

_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def db_session():
    """每个测试函数获得独立的数据库会话，测试结束后回滚。"""
    Base.metadata.create_all(bind=_engine)
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient，注入测试数据库会话。"""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


@pytest.fixture
def sample_trip(db_session):
    """创建一条样例 Trip 记录。"""
    trip = Trip(
        title="挪威北极圈玻璃穹顶追极光与冰下潜水",
        subtitle="与极光共眠的梦幻之夜",
        cover_image="/images/1_norway_aurora_real.jpg",
        destination="特罗姆瑟·林根峡湾",
        country="挪威",
        experience_type="nature",
        uniqueness_score=9,
        visual_style="snow",
        content="在玻璃穹顶小屋中仰望极光，体验冰下潜水的刺激。",
        story="这是我见过最美的极光...",
        best_season="10月–次年3月",
        duration_hours=48.0,
        difficulty=Difficulty.HARD,
        image_source="Flickr (CC License)",
        image_source_url="https://flickr.com/search/norway-aurora",
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    return trip


@pytest.fixture
def multiple_trips(db_session):
    """创建多条不同体验类型的 Trip 记录。"""
    trips_data = [
        {
            "title": "北极圈追极光",
            "subtitle": "极光之旅",
            "cover_image": "/images/norway.jpg",
            "destination": "特罗姆瑟",
            "country": "挪威",
            "experience_type": "nature",
            "uniqueness_score": 9,
            "visual_style": "snow",
            "content": "极光内容",
            "difficulty": "hard",
        },
        {
            "title": "亚马逊死藤水仪式",
            "subtitle": "心灵之旅",
            "cover_image": "/images/peru.jpg",
            "destination": "伊基托斯",
            "country": "秘鲁",
            "experience_type": "wellness",
            "uniqueness_score": 10,
            "visual_style": "forest",
            "content": "亚马逊内容",
            "difficulty": "moderate",
        },
        {
            "title": "瓦努阿图火山",
            "subtitle": "火山探险",
            "cover_image": "/images/vanuatu.jpg",
            "destination": "塔纳岛",
            "country": "瓦努阿图",
            "experience_type": "adventure",
            "uniqueness_score": 10,
            "visual_style": "mountain",
            "content": "火山内容",
            "difficulty": "moderate",
        },
        {
            "title": "格陵兰狗拉雪橇",
            "subtitle": "冰雪冒险",
            "cover_image": "/images/greenland.jpg",
            "destination": "伊卢利萨特",
            "country": "格陵兰",
            "experience_type": "adventure",
            "uniqueness_score": 8,
            "visual_style": "ocean",
            "content": "格陵兰内容",
            "difficulty": "hard",
        },
        {
            "title": "不丹雷龙之路",
            "subtitle": "朝圣之旅",
            "cover_image": "/images/bhutan.jpg",
            "destination": "帕罗",
            "country": "不丹",
            "experience_type": "cultural",
            "uniqueness_score": 10,
            "visual_style": "mountain",
            "content": "不丹内容",
            "difficulty": "hard",
        },
    ]
    trips = []
    for data in trips_data:
        trip = Trip(**data)
        db_session.add(trip)
        trips.append(trip)
    db_session.commit()
    for t in trips:
        db_session.refresh(t)
    return trips
