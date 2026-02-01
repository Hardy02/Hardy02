from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from app.models import Hand

DB_PATH = Path("data/hands.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS hands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hand_id TEXT,
            played_at TEXT,
            game_type TEXT,
            stakes TEXT,
            table_size INTEGER,
            button_seat INTEGER,
            payload TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def insert_hands(hands: Iterable[Hand]) -> int:
    conn = get_connection()
    count = 0
    for hand in hands:
        conn.execute(
            """
            INSERT INTO hands (hand_id, played_at, game_type, stakes, table_size, button_seat, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hand.hand_id,
                hand.played_at.isoformat() if hand.played_at else None,
                hand.game_type,
                hand.stakes,
                hand.table_size,
                hand.button_seat,
                json.dumps(hand.to_dict()),
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def fetch_hands(
    player_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    game_type: Optional[str] = None,
    stakes: Optional[str] = None,
    table_size: Optional[int] = None,
) -> list[Hand]:
    conn = get_connection()
    filters = []
    params: list[object] = []

    if start_date:
        filters.append("played_at >= ?")
        params.append(start_date)
    if end_date:
        filters.append("played_at <= ?")
        params.append(end_date)
    if game_type:
        filters.append("game_type LIKE ?")
        params.append(f"%{game_type}%")
    if stakes:
        filters.append("stakes LIKE ?")
        params.append(f"%{stakes}%")
    if table_size:
        filters.append("table_size = ?")
        params.append(table_size)

    query = "SELECT payload FROM hands"
    if filters:
        query += " WHERE " + " AND ".join(filters)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    hands: list[Hand] = []
    for row in rows:
        payload = json.loads(row["payload"])
        hand = Hand.from_dict(payload)
        if player_name and player_name not in {player.name for player in hand.players}:
            continue
        hands.append(hand)
    return hands


def list_players() -> list[str]:
    conn = get_connection()
    rows = conn.execute("SELECT payload FROM hands").fetchall()
    conn.close()
    players: set[str] = set()
    for row in rows:
        payload = json.loads(row["payload"])
        for player in payload.get("players", []):
            players.add(player.get("name"))
    return sorted(players)
