"""
Trip 数据模型单元测试。

验证字段约束、枚举值、ORM 行为。
"""

import pytest
from sqlalchemy.exc import IntegrityError

from models import Trip, ExperienceType, VisualStyle, Difficulty


class TestTripModel:
    """Trip ORM 模型测试"""

    def test_create_trip_minimal_fields(self, db_session):
        """最少必填字段即可创建 Trip，自动生成 id 和时间戳。"""
        trip = Trip(
            title="测试旅行",
            destination="测试目的地",
            country="测试国",
            experience_type="adventure",
            uniqueness_score=5,
            visual_style="mountain",
            content="测试内容描述",
        )
        db_session.add(trip)
        db_session.commit()

        assert trip.id is not None
        assert trip.id > 0
        assert trip.created_at is not None
        assert trip.updated_at is not None
        # 默认值
        assert trip.difficulty == "moderate"

    def test_create_trip_all_fields(self, db_session):
        """所有字段（含可选字段）均可正常写入和读取。"""
        trip = Trip(
            title="完整测试旅行",
            subtitle="副标题",
            cover_image="/images/test.jpg",
            destination="目的地",
            country="国家",
            experience_type="cultural",
            uniqueness_score=8,
            visual_style="urban",
            content="详细描述",
            story="背后故事",
            best_season="春季",
            duration_hours=72.0,
            difficulty="hard",
            image_source="Unsplash",
            image_source_url="https://unsplash.com/test",
        )
        db_session.add(trip)
        db_session.commit()
        db_session.refresh(trip)

        assert trip.subtitle == "副标题"
        assert trip.story == "背后故事"
        assert trip.image_source == "Unsplash"
        assert trip.image_source_url == "https://unsplash.com/test"
        assert trip.duration_hours == 72.0
        assert trip.difficulty == "hard"

    @pytest.mark.parametrize("score", [1, 5, 10])
    def test_uniqueness_score_valid_range(self, db_session, score):
        """uniqueness_score 1-10 均为合法值。"""
        trip = Trip(
            title=f"score-{score}",
            destination="地",
            country="国",
            experience_type="adventure",
            uniqueness_score=score,
            visual_style="snow",
            content="内容",
        )
        db_session.add(trip)
        db_session.commit()
        assert trip.uniqueness_score == score

    def test_uniqueness_score_out_of_range_rejected(self, db_session):
        """uniqueness_score 超出 1-10 应触发数据库约束错误。"""
        for bad_score in [0, 11, -1, 99]:
            trip = Trip(
                title=f"bad-{bad_score}",
                destination="地",
                country="国",
                experience_type="adventure",
                uniqueness_score=bad_score,
                visual_style="snow",
                content="内容",
            )
            db_session.add(trip)
            with pytest.raises(IntegrityError):
                db_session.commit()
            db_session.rollback()

    def test_missing_required_fields_raises(self, db_session):
        """缺少必填字段（如 title, content）应触发错误。"""
        trip = Trip(title="只有标题")  # 缺少 destination, country 等
        db_session.add(trip)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_repr(self, sample_trip):
        """__repr__ 包含 id、title、country。"""
        r = repr(sample_trip)
        assert str(sample_trip.id) in r
        assert sample_trip.title[:10] in r

    def test_created_at_updated_at_auto_set(self, db_session):
        """created_at 和 updated_at 自动设置为 UTC 时间。"""
        trip = Trip(
            title="时间测试",
            destination="地",
            country="国",
            experience_type="nature",
            uniqueness_score=5,
            visual_style="forest",
            content="内容",
        )
        db_session.add(trip)
        db_session.commit()

        assert trip.created_at is not None
        assert trip.updated_at is not None
        # 创建时两者时间差 < 1 秒（两次 lambda 调用有微妙级差异）
        delta = abs((trip.created_at - trip.updated_at).total_seconds())
        assert delta < 1.0


class TestEnums:
    """枚举值正确性测试"""

    def test_experience_type_values(self):
        values = [e.value for e in ExperienceType]
        assert values == ["adventure", "cultural", "nature", "food", "art", "wellness"]

    def test_visual_style_values(self):
        values = [e.value for e in VisualStyle]
        assert values == ["urban", "ocean", "forest", "mountain", "snow"]

    def test_difficulty_values(self):
        values = [e.value for e in Difficulty]
        assert values == ["easy", "moderate", "hard"]

    def test_enums_are_strings(self):
        """枚举值是字符串，可直接与数据库值比较。"""
        assert ExperienceType.ADVENTURE == "adventure"
        assert VisualStyle.SNOW == "snow"
        assert Difficulty.HARD == "hard"


class TestQueryBehavior:
    """ORM 查询行为测试"""

    def test_order_by_uniqueness_desc(self, db_session, multiple_trips):
        """查询可按 uniqueness_score 降序排列。"""
        from sqlalchemy import desc
        trips = (
            db_session.query(Trip)
            .order_by(desc(Trip.uniqueness_score))
            .all()
        )
        scores = [t.uniqueness_score for t in trips]
        assert scores == sorted(scores, reverse=True)

    def test_filter_by_experience_type(self, db_session, multiple_trips):
        """可按 experience_type 精确筛选。"""
        adventures = (
            db_session.query(Trip)
            .filter(Trip.experience_type == "adventure")
            .all()
        )
        assert len(adventures) == 2
        for t in adventures:
            assert t.experience_type == "adventure"

    def test_filter_by_uniqueness_range(self, db_session, multiple_trips):
        """可按 uniqueness_score 范围筛选。"""
        high = (
            db_session.query(Trip)
            .filter(Trip.uniqueness_score >= 9)
            .all()
        )
        assert len(high) == 4  # scores: 9, 10, 10, 8→4条 ≥9
        for t in high:
            assert t.uniqueness_score >= 9

    def test_random_returns_one(self, db_session, sample_trip):
        """ORDER BY RANDOM() 返回一条记录。"""
        from sqlalchemy import func
        trip = db_session.query(Trip).order_by(func.random()).first()
        assert trip is not None
        assert trip.id == sample_trip.id
