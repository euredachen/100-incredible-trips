"""
飞猪「100种不可思议旅行」— SQLAlchemy 数据模型

SQLite 数据库，单表设计。
枚举使用 Python Enum 约束，CheckConstraint 兜底。
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# ── 枚举定义 ──────────────────────────────────────────────────────────────────

class ExperienceType(str, enum.Enum):
    """旅行体验类型"""
    ADVENTURE  = "adventure"   # 探险
    CULTURAL   = "cultural"    # 人文
    NATURE     = "nature"      # 自然
    FOOD       = "food"        # 美食
    ART        = "art"         # 艺术
    WELLNESS   = "wellness"    # 康养


class VisualStyle(str, enum.Enum):
    """景观类型 — 旅行体验所处的自然环境"""
    URBAN      = "urban"       # 城市
    OCEAN      = "ocean"       # 海洋
    FOREST     = "forest"      # 森林
    MOUNTAIN   = "mountain"    # 山峰
    SNOW       = "snow"        # 雪原


class Difficulty(str, enum.Enum):
    """体验难度"""
    EASY    = "easy"
    MODERATE = "moderate"
    HARD    = "hard"


# ── 基类 ──────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Trip 模型 ─────────────────────────────────────────────────────────────────

class Trip(Base):
    __tablename__ = "trips"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基础信息
    title        = Column(String(255), nullable=False, comment="体验标题")
    subtitle     = Column(String(255), nullable=True,  comment="副标题/一句话亮点")
    cover_image  = Column(String(500), nullable=True,  comment="封面图 URL")

    # 地理信息
    destination  = Column(String(255), nullable=False, comment="目的地")
    country      = Column(String(100), nullable=False, comment="国家")

    # 分类标签
    experience_type = Column(
        Enum(ExperienceType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        comment="体验类型",
    )
    uniqueness_score = Column(
        Integer,
        nullable=False,
        comment="小众程度 1–10",
    )
    visual_style = Column(
        Enum(VisualStyle, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        comment="视觉风格",
    )

    # 内容
    content = Column(Text, nullable=False, comment="详细描述（富文本/Markdown）")
    story   = Column(Text, nullable=True,  comment="背后故事 — 情感连接")

    # 图片来源
    image_source     = Column(String(255), nullable=True, comment="图片来源名称")
    image_source_url = Column(String(500), nullable=True, comment="图片来源链接")

    # 实用信息
    best_season    = Column(String(100), nullable=True, comment="最佳季节")
    duration_hours = Column(Float,        nullable=True, comment="体验时长（小时）")
    difficulty     = Column(
        Enum(Difficulty, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=Difficulty.MODERATE,
        comment="难度",
    )

    # 时间戳
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间",
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新时间",
    )

    # ── 表级约束 ──────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "uniqueness_score >= 1 AND uniqueness_score <= 10",
            name="ck_uniqueness_range",
        ),
        CheckConstraint(
            "duration_hours > 0",
            name="ck_duration_positive",
        ),
        # 复合索引：按体验类型 + 小众程度快速筛选
        Index("idx_type_uniqueness", "experience_type", "uniqueness_score"),
        # 单列索引：视觉风格筛选
        Index("idx_visual_style", "visual_style"),
        # 单列索引：按国家检索
        Index("idx_country", "country"),
    )

    def __repr__(self) -> str:
        return f"<Trip(id={self.id}, title='{self.title}', country='{self.country}')>"


# ── 数据库工厂函数 ───────────────────────────────────────────────────────────

def create_db_engine(db_url: str = "sqlite:///./trips.db"):
    """创建 SQLAlchemy 引擎。"""
    return create_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    )


def create_session_factory(engine=None):
    """创建 session factory。"""
    if engine is None:
        engine = create_db_engine()
    return sessionmaker(bind=engine)


def init_db(engine=None) -> None:
    """建表（幂等 — CREATE TABLE IF NOT EXISTS）。"""
    if engine is None:
        engine = create_db_engine()
    Base.metadata.create_all(engine)


def get_db() -> Session:
    """依赖注入用：每次请求获取独立 session。"""
    factory = create_session_factory()
    return factory()
