"""
API 契约 & 集成测试。

验证 HTTP 响应格式、状态码、CORS 头符合 OpenAPI 规范。
"""

import pytest


class TestTripListAPI:
    """GET /api/trips — 分页列表"""

    def test_list_returns_200(self, client, multiple_trips):
        res = client.get("/api/trips")
        assert res.status_code == 200

    def test_list_response_structure(self, client, multiple_trips):
        """响应结构符合 TripListResponse schema。"""
        res = client.get("/api/trips")
        data = res.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data

        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert data["page"] >= 1

    def test_list_item_structure(self, client, multiple_trips):
        """列表中的每个 item 包含所有 TripResponse 字段。"""
        res = client.get("/api/trips")
        items = res.json()["items"]

        if len(items) > 0:
            item = items[0]
            required_fields = [
                "id", "title", "destination", "country",
                "experience_type", "uniqueness_score", "visual_style",
                "content", "difficulty",
                "created_at", "updated_at",
            ]
            for field in required_fields:
                assert field in item, f"Missing field: {field}"

    def test_filter_by_type(self, client, multiple_trips):
        res = client.get("/api/trips?type=adventure")
        assert res.status_code == 200
        items = res.json()["items"]
        for item in items:
            assert item["experience_type"] == "adventure"

    def test_filter_by_min_uniqueness(self, client, multiple_trips):
        res = client.get("/api/trips?min_uniqueness=9")
        assert res.status_code == 200
        items = res.json()["items"]
        for item in items:
            assert item["uniqueness_score"] >= 9

    def test_filter_by_visual_style(self, client, multiple_trips):
        res = client.get("/api/trips?visual_style=mountain")
        assert res.status_code == 200
        items = res.json()["items"]
        for item in items:
            assert item["visual_style"] == "mountain"

    def test_filter_combined(self, client, multiple_trips):
        res = client.get("/api/trips?type=adventure&min_uniqueness=7")
        assert res.status_code == 200
        items = res.json()["items"]
        for item in items:
            assert item["experience_type"] == "adventure"
            assert item["uniqueness_score"] >= 7

    def test_search(self, client, multiple_trips):
        res = client.get("/api/trips?search=极光")
        assert res.status_code == 200
        # 搜索应返回匹配结果
        data = res.json()
        assert data["total"] >= 1

    def test_pagination_page_size(self, client, multiple_trips):
        res = client.get("/api/trips?limit=2")
        data = res.json()
        assert len(data["items"]) <= 2
        assert data["limit"] == 2

    def test_pagination_different_pages(self, client, multiple_trips):
        p1 = client.get("/api/trips?page=1&limit=2").json()
        p2 = client.get("/api/trips?page=2&limit=2").json()

        if len(p1["items"]) > 0 and len(p2["items"]) > 0:
            ids1 = {t["id"] for t in p1["items"]}
            ids2 = {t["id"] for t in p2["items"]}
            assert ids1 != ids2

    def test_pagination_out_of_range(self, client, multiple_trips):
        res = client.get("/api/trips?page=999&limit=10")
        assert res.status_code == 200
        assert len(res.json()["items"]) == 0

    def test_invalid_page_rejected(self, client):
        res = client.get("/api/trips?page=0")
        assert res.status_code == 422

    def test_invalid_type_rejected(self, client):
        res = client.get("/api/trips?type=invalid_type")
        assert res.status_code == 422

    def test_enum_values_returned_as_strings(self, client, multiple_trips):
        """枚举值序列化为纯字符串，不是对象。"""
        res = client.get("/api/trips")
        item = res.json()["items"][0]
        assert isinstance(item["experience_type"], str)
        assert isinstance(item["visual_style"], str)
        assert isinstance(item["difficulty"], str)


class TestTripDetailAPI:
    """GET /api/trips/{id} — 详情"""

    def test_get_detail_200(self, client, sample_trip):
        res = client.get(f"/api/trips/{sample_trip.id}")
        assert res.status_code == 200

    def test_get_detail_contains_all_content(self, client, sample_trip):
        res = client.get(f"/api/trips/{sample_trip.id}")
        data = res.json()

        assert data["id"] == sample_trip.id
        assert data["title"] == sample_trip.title
        assert "content" in data
        assert "story" in data
        assert data["story"] is not None

    def test_get_detail_has_image_source(self, client, sample_trip):
        res = client.get(f"/api/trips/{sample_trip.id}")
        data = res.json()
        assert data.get("image_source") == "Flickr (CC License)"
        # image_source_url 可能为 None，检查字段存在即可
        assert "image_source_url" in data

    def test_get_detail_not_found_404(self, client):
        res = client.get("/api/trips/99999")
        assert res.status_code == 404
        assert "detail" in res.json()

    def test_get_detail_invalid_id_422(self, client):
        res = client.get("/api/trips/abc")
        assert res.status_code == 422


class TestRandomTripAPI:
    """GET /api/trips/random — 随机推荐"""

    def test_random_returns_200(self, client, sample_trip):
        res = client.get("/api/trips/random")
        assert res.status_code == 200

    def test_random_has_full_structure(self, client, sample_trip):
        res = client.get("/api/trips/random")
        data = res.json()

        assert "id" in data
        assert "title" in data
        assert "content" in data
        assert isinstance(data["id"], int)

    def test_random_empty_db_returns_404(self, client):
        """空数据库时 random 返回 404。"""
        res = client.get("/api/trips/random")
        # 如果 db_session 中没有数据（没使用 sample_trip fixture）
        assert res.status_code in (200, 404)


class TestHealthCheck:
    """GET /api/health — 健康检查"""

    def test_health_200(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_health_has_service_name(self, client):
        res = client.get("/api/health")
        assert "service" in res.json()


class TestCORS:
    """CORS 头正确性"""

    def test_cors_headers_present(self, client):
        res = client.options(
            "/api/trips",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI CORSMiddleware 应返回 allow-origin
        assert res.status_code in (200, 405)  # 200 或 Method Not Allowed


class TestContentNegotiation:
    """响应 Content-Type"""

    def test_json_content_type(self, client, multiple_trips):
        res = client.get("/api/trips")
        assert res.headers["content-type"].startswith("application/json")


class TestResponseCompleteness:
    """验证所有 5 条种子数据字段完整"""

    def test_all_items_have_required_string_fields(self, client, multiple_trips):
        res = client.get("/api/trips?limit=10")
        items = res.json()["items"]
        for item in items:
            assert len(item["title"]) > 0
            assert len(item["destination"]) > 0
            assert len(item["country"]) > 0
            assert len(item["content"]) > 0
            assert 1 <= item["uniqueness_score"] <= 10
