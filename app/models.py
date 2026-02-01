from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Player:
    name: str
    seat: int
    chips: float


@dataclass
class Action:
    street: str
    player: str
    action: str
    amount: float = 0.0
    to_amount: Optional[float] = None
    is_all_in: bool = False
    index: int = 0


@dataclass
class Hand:
    hand_id: str
    played_at: Optional[datetime]
    game_type: str
    stakes: str
    table_size: int
    button_seat: Optional[int]
    players: List[Player] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    board: List[str] = field(default_factory=list)
    showdown_players: List[str] = field(default_factory=list)
    winners: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "hand_id": self.hand_id,
            "played_at": self.played_at.isoformat() if self.played_at else None,
            "game_type": self.game_type,
            "stakes": self.stakes,
            "table_size": self.table_size,
            "button_seat": self.button_seat,
            "players": [player.__dict__ for player in self.players],
            "actions": [action.__dict__ for action in self.actions],
            "board": self.board,
            "showdown_players": self.showdown_players,
            "winners": self.winners,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Hand":
        played_at = (
            datetime.fromisoformat(payload["played_at"])
            if payload.get("played_at")
            else None
        )
        players = [Player(**player) for player in payload.get("players", [])]
        actions = [Action(**action) for action in payload.get("actions", [])]
        return cls(
            hand_id=payload["hand_id"],
            played_at=played_at,
            game_type=payload.get("game_type", ""),
            stakes=payload.get("stakes", ""),
            table_size=payload.get("table_size", 0),
            button_seat=payload.get("button_seat"),
            players=players,
            actions=actions,
            board=payload.get("board", []),
            showdown_players=payload.get("showdown_players", []),
            winners=payload.get("winners", []),
        )
