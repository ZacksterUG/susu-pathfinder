"""Репозитории — запросы к БД."""

import json
from typing import Optional

import asyncpg

from app.database import get_pool


# ─── Building ────────────────────────────────────────────────

async def get_all_buildings() -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, short_name FROM map_app.building ORDER BY name")
        result = []
        for r in rows:
            d = dict(r)
            d["id"] = str(d["id"])
            result.append(d)
        return result


async def get_building(building_id: str) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, short_name FROM map_app.building WHERE id = $1", building_id
        )
        if row:
            d = dict(row)
            d["id"] = str(d["id"])
            return d
        return None


# ─── Floor ───────────────────────────────────────────────────

async def get_floors_by_building(building_id: str) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, building_id, floor_number, corridor_points "
            "FROM map_app.floor WHERE building_id = $1 ORDER BY floor_number::int",
            building_id,
        )
        result = []
        for r in rows:
            d = dict(r)
            d["id"] = str(d["id"])
            d["building_id"] = str(d["building_id"])
            if d["corridor_points"] is not None:
                d["corridor_points"] = json.loads(d["corridor_points"])
            result.append(d)
        return result


# ─── Room ────────────────────────────────────────────────────

async def get_rooms_by_floor(building_id: str, floor_number: str) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, building_id, floor_number, number, name, room_type, coordinates "
            "FROM map_app.room WHERE building_id = $1 AND floor_number = $2",
            building_id, floor_number,
        )
        result = []
        for r in rows:
            d = dict(r)
            d["id"] = str(d["id"])
            d["building_id"] = str(d["building_id"])
            if d["coordinates"] is not None:
                d["coordinates"] = json.loads(d["coordinates"])
            result.append(d)
        return result


async def get_room_by_id(room_id: str) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, building_id, floor_number, number, name, room_type, coordinates "
            "FROM map_app.room WHERE id = $1", room_id,
        )
        if row:
            d = dict(row)
            d["id"] = str(d["id"])
            d["building_id"] = str(d["building_id"])
            if d["coordinates"] is not None:
                d["coordinates"] = json.loads(d["coordinates"])
            return d
        return None


# ─── Technical ───────────────────────────────────────────────

async def get_technical_by_floor(building_id: str, floor_number: str) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, building_id, floor_number, name, type, coordinates, "
            "has_entrance, linked "
            "FROM map_app.technical WHERE building_id = $1 AND floor_number = $2",
            building_id, floor_number,
        )
        result = []
        for r in rows:
            d = dict(r)
            d["id"] = str(d["id"])
            d["building_id"] = str(d["building_id"])
            if d["coordinates"] is not None:
                d["coordinates"] = json.loads(d["coordinates"])
            if d["linked"] is not None:
                d["linked"] = [str(u) for u in d["linked"]]
            else:
                d["linked"] = []
            result.append(d)
        return result


# ─── Entrance ────────────────────────────────────────────────

async def get_entrances_by_floor(building_id: str, floor_number: str) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT object_id, object_type, building_id, floor_number, x, y, room_number "
            "FROM map_app.entrance WHERE building_id = $1 AND floor_number = $2",
            building_id, floor_number,
        )
        result = []
        for r in rows:
            d = dict(r)
            d["object_id"] = str(d["object_id"])
            d["building_id"] = str(d["building_id"])
            result.append(d)
        return result


# ─── Grid ────────────────────────────────────────────────────

async def get_grid_by_floor(building_id: str, floor_number: str) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT building_id, floor_number, cell_size, nodes, edges, entrance_connections "
            "FROM map_app.grid WHERE building_id = $1 AND floor_number = $2",
            building_id, floor_number,
        )
        if not row:
            return None
        d = dict(row)
        d["building_id"] = str(d["building_id"])
        d["nodes"] = json.loads(d["nodes"])
        d["edges"] = json.loads(d["edges"])
        d["entrance_connections"] = json.loads(d["entrance_connections"])
        return d


# ─── Path Cache ──────────────────────────────────────────────

async def get_cached_path(
    building_id: str, start_id: str, end_id: str
) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT path_nodes, path_length FROM map_app.path_cache "
            "WHERE building_id = $1 AND room_start_id = $2 AND room_end_id = $3",
            building_id, start_id, end_id,
        )
        if row:
            return {
                "path_nodes": json.loads(row["path_nodes"]),
                "path_length": row["path_length"],
            }
        return None


async def save_cached_path(
    building_id: str, start_id: str, end_id: str, path_nodes: list, path_length: float
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO map_app.path_cache (building_id, room_start_id, room_end_id, "
            "path_nodes, path_length) VALUES ($1, $2, $3, $4, $5) "
            "ON CONFLICT (room_start_id, room_end_id) "
            "DO UPDATE SET path_nodes = $4, path_length = $5, created_at = CURRENT_TIMESTAMP",
            str(building_id), str(start_id), str(end_id),
            json.dumps(path_nodes, ensure_ascii=False),
            path_length,
        )
