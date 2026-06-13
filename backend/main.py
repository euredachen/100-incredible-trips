"""
飞猪「100种不可思议旅行」— FastAPI 应用入口

启动方式:
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

验证:
    curl http://localhost:8000/api/trips
    curl http://localhost:8000/api/trips/random
    curl http://localhost:8000/api/trips/1
    curl "http://localhost:8000/api/trips?type=adventure&min_uniqueness=7&page=1&limit=5"
    curl "http://localhost:8000/api/trips?search=极光"
"""

import math
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from urllib.parse import quote

# 确保 backend 目录在 sys.path 中（支持从项目根目录或 backend 目录启动）
_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from models import (
    Base,
    Trip,
    create_db_engine,
    create_session_factory,
)
from schemas import (
    TripFilterParams,
    TripListResponse,
    TripResponse,
    TripCreate,
)

# ── 应用生命周期 ─────────────────────────────────────────────────────────────

# 全局引擎 & 会话工厂（模块加载时创建一次）
_engine = create_db_engine("sqlite:///./trips.db")
_SessionLocal = create_session_factory(_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期管理。"""
    # ── 启动 ──────────────────────────────────────────────────────────────
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🛫 飞猪「100种不可思议旅行」API                            ║")
    print("║  API 文档: http://localhost:8000/docs                        ║")
    print("║  OpenAPI:  http://localhost:8000/openapi.json                ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # 确保表存在（幂等）
    Base.metadata.create_all(_engine)

    # 打印当前数据库状态
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    with _SessionLocal() as session:
        count = session.query(func.count(Trip.id)).scalar()
        print(f"\n📊 数据库状态: trips 表共 {count} 条记录\n")

        # 打印摘要
        if count > 0:
            trips = session.query(Trip).order_by(Trip.uniqueness_score.desc()).limit(5).all()
            for t in trips:
                print(f"   [{t.id}] {t.title[:30]}… | {t.country} | ⭐{t.uniqueness_score}/10")
            if count > 5:
                print(f"   … 以及其他 {count - 5} 条记录")
        else:
            print("   ⚠️  数据库为空，请先运行 init_db.py 插入种子数据")

    print(f"\n✅ 服务就绪，监听 http://0.0.0.0:8000\n")

    yield  # ← 应用运行期间挂起

    # ── 关闭 ──────────────────────────────────────────────────────────────
    print("\n👋 服务关闭")
    _engine.dispose()


# ── FastAPI 应用实例 ────────────────────────────────────────────────────────

app = FastAPI(
    title="飞猪「100种不可思议旅行」API",
    description="为产品页提供旅行体验数据服务 — 分页列表、详情、随机推荐",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS 配置 ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite 开发服务器
        "http://localhost:3000",   # Next.js / 备选
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],  # 当前阶段仅需 GET
    allow_headers=["*"],
)


# ── 依赖注入：数据库会话 ────────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """每个请求获取一个独立的数据库会话，请求结束时自动关闭。"""
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 路由 ────────────────────────────────────────────────────────────────────
# ⚠️ 注意: /api/trips/random 必须在 /api/trips/{id} 之前注册，
#    否则 FastAPI 会将 "random" 作为 id 参数解析。

@app.get("/api/trips/random", response_model=TripResponse, tags=["trips"])
def get_random_trip(db: Session = Depends(get_db)):
    """随机推荐一条旅行体验 — 首页 Hero 区使用。

    从全量体验中随机选取一条。若无数据则返回 404。
    """
    trip = db.query(Trip).order_by(func.random()).first()
    if trip is None:
        raise HTTPException(status_code=404, detail="暂无旅行体验数据")
    return trip


@app.get("/api/trips", response_model=TripListResponse, tags=["trips"])
def list_trips(
    db: Session = Depends(get_db),
    filters: TripFilterParams = Depends(),
):
    """分页查询旅行体验列表。

    支持多维度组合筛选：
    - `type`: 体验类型
    - `min_uniqueness`: 最小小众程度
    - `visual_style`: 视觉风格
    - `search`: 全文搜索（标题/副标题/目的地/国家/内容）
    - `page` / `limit`: 分页
    """
    # 基础查询
    query = db.query(Trip)

    # ── 筛选条件 ──────────────────────────────────────────────────────────
    if filters.type is not None:
        query = query.filter(Trip.experience_type == filters.type)

    if filters.min_uniqueness is not None:
        query = query.filter(Trip.uniqueness_score >= filters.min_uniqueness)

    if filters.visual_style is not None:
        query = query.filter(Trip.visual_style == filters.visual_style)

    if filters.search:
        pattern = f"%{filters.search}%"
        query = query.filter(
            or_(
                Trip.title.ilike(pattern),
                Trip.subtitle.ilike(pattern),
                Trip.destination.ilike(pattern),
                Trip.country.ilike(pattern),
                Trip.content.ilike(pattern),
            )
        )

    # ── 总数 & 分页 ──────────────────────────────────────────────────────
    total = query.count()
    pages = max(1, math.ceil(total / filters.limit))

    # 按小众程度降序（越"不可思议"越靠前），同分按 id 降序
    trips = (
        query
        .order_by(Trip.created_at.asc())
        .offset((filters.page - 1) * filters.limit)
        .limit(filters.limit)
        .all()
    )

    return TripListResponse(
        items=[TripResponse.model_validate(t) for t in trips],
        total=total,
        page=filters.page,
        limit=filters.limit,
        pages=pages,
    )


@app.get("/api/trips/{trip_id}", response_model=TripResponse, tags=["trips"])
def get_trip_by_id(trip_id: int, db: Session = Depends(get_db)):
    """根据 ID 获取单条旅行体验详情。"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip is None:
        raise HTTPException(status_code=404, detail=f"体验 #{trip_id} 不存在")
    return trip


# ── 自动丰富体验内容 ──────────────────────────────────────────────────

@app.post("/api/trips/{trip_id}/enrich", tags=["trips"])
def enrich_trip(trip_id: int, request: Request, db: Session = Depends(get_db)):
    """触发自动丰富流水线: Pexels 搜索 → 下载图片 → ColorThief 配色 → 更新数据库。"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip is None:
        raise HTTPException(status_code=404, detail=f"体验 #{trip_id} 不存在")

    # 如果前端传了英文搜索词，用它；否则用 destination
    search_query = request.query_params.get("q") or trip.destination or trip.title

    import subprocess, os
    script = os.path.join(os.path.dirname(__file__), "enrich.py")
    result = subprocess.run(
        ["python3", script, str(trip_id), search_query],
        capture_output=True, text=True, timeout=30
    )

    db.refresh(trip)

    try:
        output = json.loads(result.stdout)
    except Exception:
        output = {"raw": result.stdout, "stderr": result.stderr}

    return {
        "success": trip.cover_image and trip.cover_image.startswith("/"),
        "trip_id": trip_id,
        "cover_image": trip.cover_image,
        "image_source": trip.image_source,
        "steps": output.get("steps", []),
        "colors": output.get("colors", {}),
    }


# ── 搜索验证代理 ────────────────────────────────────────────────────────

@app.post("/api/search/validate", tags=["search"])
def validate_search(query: str = Query(..., description="搜索词")):
    """验证搜索词是否能在 Wikipedia 找到匹配结果。
    后端代理 Wikipedia API，避免浏览器跨域/CORS问题。
    """
    import urllib.request
    import urllib.parse
    import json as _json

    encoded = urllib.parse.quote(query)
    url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&list=search&srsearch={encoded}&format=json&origin=*&srlimit=5"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "100Trips/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = _json.loads(resp.read())
        results = data.get("query", {}).get("search", [])
    except Exception as e:
        return {"valid": False, "results": [], "reason": f"搜索服务异常: {str(e)}"}

    # 模糊匹配
    q = query.lower()
    keywords = [k.lower() for k in q.split() if len(k) > 1]

    matched = False
    for r in results:
        title = (r.get("title", "")).lower()
        snippet = (r.get("snippet", "")).lower()
        if any(kw in title for kw in keywords):
            matched = True; break
        if len(title) > 3 and title in q:
            matched = True; break
        if sum(1 for kw in keywords if kw in title or kw in snippet) >= 2:
            matched = True; break

    return {
        "valid": len(results) > 0 and matched,
        "total_results": len(results),
        "top_hits": [r["title"] for r in results[:3]],
        "reason": "匹配成功" if matched else ("无结果" if not results else f"关键词不匹配（最近: {results[0]['title']}）"),
    }


# ── 创建新体验 ──────────────────────────────────────────────────────────

@app.post("/api/trips", response_model=TripResponse, status_code=201, tags=["trips"])
def create_trip(trip_data: TripCreate, db: Session = Depends(get_db)):
    """创建一条新的旅行体验。AI 生成的内容可以直接 POST 到此端点。"""
    trip = Trip(**trip_data.model_dump())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


# ── 飞猪预订跳转 ──────────────────────────────────────────────────────────

@app.get("/api/booking/search", tags=["booking"])
def booking_search(
    destination: str = Query(..., description="目的地关键词"),
    country: str = Query("", description="国家"),
):
    """生成飞猪预订搜索链接。

    示例:
        GET /api/booking/search?destination=特罗姆瑟&country=挪威
    """
    query_parts = [destination]
    if country:
        query_parts.append(country)
    query_parts.append("旅游")
    query = " ".join(query_parts)

    return {
        "platform": "飞猪",
        "searchUrl": f"https://www.fliggy.com/search?q={quote(query)}",
        "flightUrl": f"https://www.fliggy.com/flight?arrivalCity={quote(destination)}",
        "hotelUrl": f"https://www.fliggy.com/hotel?destination={quote(destination)}",
        "destination": destination,
        "country": country,
    }


# ── 外部内容来源 ──────────────────────────────────────────────────────────

# 简单的内存存储（生产环境应使用数据库）
_external_sources_store: dict = {}


@app.post("/api/trips/{trip_id}/external-sources", tags=["trips"])
def add_external_source(
    trip_id: int,
    source: dict = None,
    db: Session = Depends(get_db),
):
    """为旅行体验添加外部内容来源（Wikipedia、National Geographic 等）。

    请求体:
        {"type": "wikipedia", "url": "...", "title": "...", "snippet": "..."}
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip is None:
        raise HTTPException(status_code=404, detail=f"体验 #{trip_id} 不存在")

    from pydantic import BaseModel

    class ExternalSource(BaseModel):
        type: str
        url: str
        title: str
        snippet: str = ""

    try:
        src = ExternalSource(**(source or {}))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid source format")

    if trip_id not in _external_sources_store:
        _external_sources_store[trip_id] = []

    entry = src.model_dump()
    _external_sources_store[trip_id].append(entry)

    return {
        "success": True,
        "trip_id": trip_id,
        "source": entry,
        "total_sources": len(_external_sources_store[trip_id]),
    }


@app.get("/api/trips/{trip_id}/external-sources", tags=["trips"])
def get_external_sources(trip_id: int, db: Session = Depends(get_db)):
    """获取旅行体验的外部内容来源列表。"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip is None:
        raise HTTPException(status_code=404, detail=f"体验 #{trip_id} 不存在")

    return {
        "trip_id": trip_id,
        "sources": _external_sources_store.get(trip_id, []),
    }


# ── 健康检查 ────────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["system"])
def health_check():
    """简单健康检查端点。"""
    return {"status": "ok", "service": "100-incredible-trips"}


# ── 直接运行支持 ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
