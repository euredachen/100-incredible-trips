"""
飞猪「100种不可思议旅行」— Pydantic Schema 层

分层设计：
  - TripBase:     共享字段（创建/响应共用）
  - TripCreate:   创建请求体
  - TripResponse: 单条体验 API 响应
  - TripListResponse: 分页列表响应
  - TripFilterParams: 查询参数（FastAPI Depends 兼容）
  - RandomTripResponse: 随机推荐响应（结构同单条，语义独立）
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from models import Difficulty, ExperienceType, VisualStyle


# ── 共享基类 ─────────────────────────────────────────────────────────────────

class TripBase(BaseModel):
    """体验的公共字段 — 所有 schema 继承此基类。"""
    title:            str = Field(..., max_length=255, description="体验标题")
    subtitle:         Optional[str] = Field(None, max_length=255, description="副标题/一句话亮点")
    cover_image:      Optional[str] = Field(None, max_length=500, description="封面图 URL")
    destination:      str = Field(..., max_length=255, description="目的地")
    country:          str = Field(..., max_length=100, description="国家")
    experience_type:  ExperienceType = Field(..., description="体验类型")
    uniqueness_score: int = Field(..., ge=1, le=10, description="小众程度 1–10")
    visual_style:     VisualStyle = Field(..., description="视觉风格")
    content:          str = Field(..., description="详细描述（富文本）")
    story:            Optional[str] = Field(None, description="背后故事")
    best_season:      Optional[str] = Field(None, max_length=100, description="最佳季节")
    duration_hours:   Optional[float] = Field(None, gt=0, description="体验时长（小时）")
    difficulty:       Difficulty = Field(default=Difficulty.MODERATE, description="难度")
    image_source:     Optional[str] = Field(None, max_length=255, description="图片来源名称")
    image_source_url: Optional[str] = Field(None, max_length=500, description="图片来源链接")

    model_config = {"use_enum_values": True}  # 序列化时输出 "adventure" 而非 "ExperienceType.ADVENTURE"


# ── 请求 Schema ──────────────────────────────────────────────────────────────

class TripCreate(TripBase):
    """创建新体验的请求体 — 与 TripBase 字段完全一致。"""
    pass


class TripUpdate(BaseModel):
    """更新体验 — 所有字段可选（部分更新 PATCH 语义）。"""
    title:            Optional[str] = Field(None, max_length=255)
    subtitle:         Optional[str] = Field(None, max_length=255)
    cover_image:      Optional[str] = Field(None, max_length=500)
    destination:      Optional[str] = Field(None, max_length=255)
    country:          Optional[str] = Field(None, max_length=100)
    experience_type:  Optional[ExperienceType] = None
    uniqueness_score: Optional[int] = Field(None, ge=1, le=10)
    visual_style:     Optional[VisualStyle] = None
    content:          Optional[str] = None
    story:            Optional[str] = None
    best_season:      Optional[str] = Field(None, max_length=100)
    duration_hours:   Optional[float] = Field(None, gt=0)
    difficulty:       Optional[Difficulty] = None

    model_config = {"use_enum_values": True}


# ── 响应 Schema ──────────────────────────────────────────────────────────────

class TripResponse(TripBase):
    """单条旅行体验的 API 响应 — 包含数据库生成的字段。"""
    id:         int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,   # 允许从 SQLAlchemy ORM 对象构建
        "use_enum_values": True,
    }


class TripListResponse(BaseModel):
    """分页列表响应。"""
    items: list[TripResponse] = Field(..., description="当前页体验列表")
    total: int = Field(..., description="符合条件的总记录数")
    page:  int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页条数")
    pages: int = Field(..., description="总页数")


class RandomTripResponse(TripResponse):
    """随机推荐响应 — 字段与 TripResponse 相同。
    独立类型便于未来扩展（如附带推荐理由）。"""
    pass


# ── 查询参数 Schema ─────────────────────────────────────────────────────────

class TripFilterParams(BaseModel):
    """GET /api/trips 查询参数。

    FastAPI 中可以直接 Depends() 注入：
        def list_trips(filters: TripFilterParams = Depends()):
    """
    type:           Optional[ExperienceType] = Field(None, alias="type", description="按体验类型筛选")
    min_uniqueness: Optional[int] = Field(None, ge=1, le=10, description="最小小众程度")
    visual_style:   Optional[VisualStyle] = Field(None, description="按视觉风格筛选")
    search:         Optional[str] = Field(None, max_length=200, description="搜索关键词（标题/副标题/目的地/国家/内容）")
    page:           int = Field(default=1, ge=1, description="页码")
    limit:          int = Field(default=20, ge=1, le=100, description="每页条数")

    model_config = {"use_enum_values": True}
