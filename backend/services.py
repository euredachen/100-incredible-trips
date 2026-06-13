"""
飞猪「100种不可思议旅行」— 业务逻辑服务层

将数据库查询逻辑从路由中抽离，便于单元测试和复用。
"""

import math
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models import Trip


class TripService:
    """旅行体验业务服务"""

    def __init__(self, db: Session):
        self.db = db

    # ── 查询方法 ──────────────────────────────────────────────────────────

    def list_trips(
        self,
        *,
        experience_type: Optional[str] = None,
        min_uniqueness: Optional[int] = None,
        visual_style: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ):
        """分页列表查询，支持多条件组合筛选。"""
        query = self.db.query(Trip)

        if experience_type is not None:
            query = query.filter(Trip.experience_type == experience_type)

        if min_uniqueness is not None:
            query = query.filter(Trip.uniqueness_score >= min_uniqueness)

        if visual_style is not None:
            query = query.filter(Trip.visual_style == visual_style)

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Trip.title.ilike(pattern),
                    Trip.subtitle.ilike(pattern),
                    Trip.destination.ilike(pattern),
                    Trip.country.ilike(pattern),
                    Trip.content.ilike(pattern),
                )
            )

        total = query.count()
        pages = max(1, math.ceil(total / limit)) if total > 0 else 1

        trips = (
            query
            .order_by(Trip.created_at.asc())
            .offset((max(page, 1) - 1) * limit)
            .limit(limit)
            .all()
        )

        return {"items": trips, "total": total, "page": max(page, 1), "limit": limit, "pages": pages}

    def get_by_id(self, trip_id: int) -> Optional[Trip]:
        """根据 ID 获取单条详情。"""
        return self.db.query(Trip).filter(Trip.id == trip_id).first()

    def get_random(self) -> Optional[Trip]:
        """随机返回一条体验（SQLite: ORDER BY RANDOM()）。"""
        return self.db.query(Trip).order_by(func.random()).first()

    # ── 辅助方法 ──────────────────────────────────────────────────────────

    def count_all(self) -> int:
        """返回总记录数。"""
        return self.db.query(func.count(Trip.id)).scalar()

    def calculate_uniqueness_score(self, experience_type: str, destination: str) -> int:
        """根据体验类型和目的地计算小众程度（示例业务逻辑）。"""
        rare_destinations = ['antarctica', 'vanuatu', 'greenland', 'bhutan', 'svalbard']
        rare_types = ['adventure', 'cultural']

        score = 5  # 基础分
        if any(d in destination.lower() for d in rare_destinations):
            score += 3
        if experience_type in rare_types:
            score += 2
        return min(score, 10)
