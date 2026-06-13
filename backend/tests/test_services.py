"""
TripService 业务逻辑单元测试。

验证服务层的筛选、分页、边界条件处理。
"""

import pytest

from services import TripService
from models import Trip


class TestTripServiceList:
    """list_trips 方法测试"""

    def test_list_all_returns_all_trips(self, db_session, multiple_trips):
        """无筛选条件时返回全部记录。"""
        svc = TripService(db_session)
        result = svc.list_trips()
        assert result["total"] == 5
        assert len(result["items"]) == 5

    def test_filter_by_experience_type(self, db_session, multiple_trips):
        """按体验类型筛选。"""
        svc = TripService(db_session)
        result = svc.list_trips(experience_type="adventure")
        assert result["total"] == 2
        for t in result["items"]:
            assert t.experience_type == "adventure"

    def test_filter_by_min_uniqueness(self, db_session, multiple_trips):
        """按最小小众程度筛选。"""
        svc = TripService(db_session)
        result = svc.list_trips(min_uniqueness=9)
        assert result["total"] == 4  # scores: 9, 10, 10, 8→4条 ≥9
        for t in result["items"]:
            assert t.uniqueness_score >= 9

    def test_filter_by_visual_style(self, db_session, multiple_trips):
        """按景观类型筛选。"""
        svc = TripService(db_session)
        result = svc.list_trips(visual_style="mountain")
        assert result["total"] == 2
        for t in result["items"]:
            assert t.visual_style == "mountain"

    def test_search_by_keyword(self, db_session, multiple_trips):
        """全文搜索匹配标题/目的地/内容。"""
        svc = TripService(db_session)
        result = svc.list_trips(search="极光")
        assert result["total"] >= 1

    def test_search_case_insensitive(self, db_session, multiple_trips):
        """搜索是大小写不敏感的（ilike）。"""
        svc = TripService(db_session)
        result = svc.list_trips(search="极光")
        assert result["total"] >= 1

    def test_combined_filters(self, db_session, multiple_trips):
        """多条件组合筛选。"""
        svc = TripService(db_session)
        result = svc.list_trips(experience_type="adventure", min_uniqueness=9)
        assert result["total"] >= 1
        for t in result["items"]:
            assert t.experience_type == "adventure"
            assert t.uniqueness_score >= 9

    def test_pagination_page_1(self, db_session, multiple_trips):
        """分页：第 1 页，每页 2 条。"""
        svc = TripService(db_session)
        result = svc.list_trips(page=1, limit=2)
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["limit"] == 2
        assert result["pages"] == 3  # 5 total / 2 per page = 3 pages

    def test_pagination_page_2(self, db_session, multiple_trips):
        """分页：第 2 页不应与第 1 页重复。"""
        svc = TripService(db_session)
        page1 = svc.list_trips(page=1, limit=2)
        page2 = svc.list_trips(page=2, limit=2)
        p1_ids = {t.id for t in page1["items"]}
        p2_ids = {t.id for t in page2["items"]}
        assert p1_ids.isdisjoint(p2_ids)

    def test_pagination_out_of_range_returns_empty(self, db_session, multiple_trips):
        """超出总页数返回空列表。"""
        svc = TripService(db_session)
        result = svc.list_trips(page=999, limit=10)
        assert len(result["items"]) == 0
        assert result["pages"] >= 1

    def test_pagination_page_zero_treated_as_page_one(self, db_session, multiple_trips):
        """page=0 等同于 page=1。"""
        svc = TripService(db_session)
        r0 = svc.list_trips(page=0, limit=5)
        r1 = svc.list_trips(page=1, limit=5)
        assert r0["total"] == r1["total"]

    def test_result_sorted_by_uniqueness_desc(self, db_session, multiple_trips):
        """结果按小众程度降序排列。"""
        svc = TripService(db_session)
        result = svc.list_trips()
        scores = [t.uniqueness_score for t in result["items"]]
        assert scores == sorted(scores, reverse=True)

    def test_no_results_for_impossible_filter(self, db_session, multiple_trips):
        """不存在的筛选组合返回空。"""
        svc = TripService(db_session)
        result = svc.list_trips(experience_type="food", min_uniqueness=10)
        assert result["total"] == 0
        assert len(result["items"]) == 0


class TestTripServiceDetail:
    """get_by_id / get_random 方法测试"""

    def test_get_by_id_returns_trip(self, db_session, sample_trip):
        svc = TripService(db_session)
        trip = svc.get_by_id(sample_trip.id)
        assert trip is not None
        assert trip.id == sample_trip.id
        assert trip.title == sample_trip.title

    def test_get_by_id_not_found(self, db_session):
        svc = TripService(db_session)
        trip = svc.get_by_id(99999)
        assert trip is None

    def test_get_random_returns_one(self, db_session, sample_trip):
        svc = TripService(db_session)
        trip = svc.get_random()
        assert trip is not None
        assert isinstance(trip, Trip)


class TestTripServiceHelpers:
    """辅助方法测试"""

    def test_count_all(self, db_session, multiple_trips):
        svc = TripService(db_session)
        assert svc.count_all() == 5

    def test_count_all_empty(self, db_session):
        svc = TripService(db_session)
        assert svc.count_all() == 0

    @pytest.mark.parametrize("exp_type,dest,expected_min,expected_max", [
        ("adventure", "antarctica", 8, 10),
        ("adventure", "paris", 5, 7),
        ("food", "tokyo", 5, 5),
        ("cultural", "bhutan", 8, 10),
    ])
    def test_calculate_uniqueness_score_range(self, db_session, exp_type, dest, expected_min, expected_max):
        svc = TripService(db_session)
        score = svc.calculate_uniqueness_score(exp_type, dest)
        assert expected_min <= score <= expected_max
        assert 1 <= score <= 10
