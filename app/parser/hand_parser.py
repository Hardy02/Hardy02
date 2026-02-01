from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

import logging

from app.models import Action, Hand, Player


HEADER_RE = re.compile(
    r"Hand\s#(?P<hand_id>\d+):\s+(?P<game>.+?)\s+\((?P<stakes>[^)]+)\)\s+-\s+(?P<date>.+)$"
)
BUTTON_RE = re.compile(r"Seat\s+#(?P<button>\d+)\s+is the button")
SEAT_RE = re.compile(
    r"Seat\s+(?P<seat>\d+):\s+(?P<player>.+?)\s+\(\$?(?P<chips>[\d\.]+)"
)
ACTION_RE = re.compile(
    r"^(?P<player>[^:]+):\s+(?P<action>folds|checks|calls|bets|raises|posts small blind|posts big blind|posts ante|collects|shows|mucks)(?P<details>.*)$",
    re.IGNORECASE,
)
FLOP_RE = re.compile(r"\*\*\* FLOP \*\*\* \[(?P<cards>[^\]]+)")
TURN_RE = re.compile(r"\*\*\* TURN \*\*\* \[[^\]]+\] \[(?P<card>[^\]]+)\]")
RIVER_RE = re.compile(r"\*\*\* RIVER \*\*\* \[[^\]]+\] \[(?P<card>[^\]]+)\]")


STREET_MAP = {
    "*** HOLE CARDS ***": "preflop",
    "*** FLOP ***": "flop",
    "*** TURN ***": "turn",
    "*** RIVER ***": "river",
    "*** SHOWDOWN ***": "showdown",
    "*** SUMMARY ***": "summary",
}


def _parse_amount(text: str) -> float:
    match = re.search(r"\$([\d\.]+)", text)
    if not match:
        return 0.0
    return float(match.group(1))


def _parse_to_amount(text: str) -> Optional[float]:
    match = re.search(r"to\s+\$([\d\.]+)", text)
    if not match:
        return None
    return float(match.group(1))


def parse_hand(hand_text: str) -> Hand:
    lines = [line.strip() for line in hand_text.splitlines() if line.strip()]
    header_match = HEADER_RE.search(lines[0])
    hand_id = header_match.group("hand_id") if header_match else "unknown"
    game_type = header_match.group("game") if header_match else "Unknown"
    stakes = header_match.group("stakes") if header_match else ""
    played_at = None
    if header_match:
        date_raw = header_match.group("date").replace("ET", "").strip()
        for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                played_at = datetime.strptime(date_raw, fmt)
                break
            except ValueError:
                continue
    button_seat = None
    players: List[Player] = []
    actions: List[Action] = []
    board: List[str] = []
    showdown_players: List[str] = []
    winners: List[str] = []

    street = "preflop"
    action_index = 0

    for line in lines[1:]:
        if line in STREET_MAP:
            street = STREET_MAP[line]
            continue
        button_match = BUTTON_RE.search(line)
        if button_match:
            button_seat = int(button_match.group("button"))
            continue
        seat_match = SEAT_RE.search(line)
        if seat_match:
            players.append(
                Player(
                    name=seat_match.group("player").strip(),
                    seat=int(seat_match.group("seat")),
                    chips=float(seat_match.group("chips")),
                )
            )
            continue
        if line.startswith("*** FLOP ***"):
            flop_match = FLOP_RE.search(line)
            if flop_match:
                board.extend(flop_match.group("cards").split())
            street = "flop"
            continue
        if line.startswith("*** TURN ***"):
            turn_match = TURN_RE.search(line)
            if turn_match:
                board.append(turn_match.group("card"))
            street = "turn"
            continue
        if line.startswith("*** RIVER ***"):
            river_match = RIVER_RE.search(line)
            if river_match:
                board.append(river_match.group("card"))
            street = "river"
            continue

        action_match = ACTION_RE.search(line)
        if action_match:
            player = action_match.group("player").strip()
            action = action_match.group("action").lower()
            details = action_match.group("details")
            amount = _parse_amount(details)
            to_amount = _parse_to_amount(details)
            is_all_in = "all-in" in details.lower()
            actions.append(
                Action(
                    street=street,
                    player=player,
                    action=action,
                    amount=amount,
                    to_amount=to_amount,
                    is_all_in=is_all_in,
                    index=action_index,
                )
            )
            action_index += 1
            if street == "showdown":
                if action in {"shows", "mucks"}:
                    showdown_players.append(player)
                if action == "collects":
                    winners.append(player)
            continue

        if line.startswith("Uncalled bet"):
            continue
        if line.startswith("Dealt to"):
            continue

    table_size = len(players)

    return Hand(
        hand_id=hand_id,
        played_at=played_at,
        game_type=game_type,
        stakes=stakes,
        table_size=table_size,
        button_seat=button_seat,
        players=players,
        actions=actions,
        board=board,
        showdown_players=showdown_players,
        winners=winners,
    )


def parse_hands(raw_text: str) -> List[Hand]:
    from app.parser.tokenizer import tokenize

    logger = logging.getLogger("mini_pokertracker.parser")
    hands: List[Hand] = []
    for hand_text in tokenize(raw_text):
        try:
            hands.append(parse_hand(hand_text))
        except Exception as exc:
            logger.warning("Failed to parse hand: %s", exc)
            continue
    return hands
