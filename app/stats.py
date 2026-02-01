from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.models import Action, Hand


VOLUNTARY_ACTIONS = {"calls", "bets", "raises"}
BLIND_ACTIONS = {"posts small blind", "posts big blind", "posts ante"}


@dataclass
class StatCounts:
    hands: int = 0
    vpip: int = 0
    pfr: int = 0
    three_bet: int = 0
    three_bet_opp: int = 0
    fold_vs_three_bet: int = 0
    fold_vs_three_bet_opp: int = 0
    steal: int = 0
    steal_opp: int = 0
    fold_vs_steal: int = 0
    fold_vs_steal_opp: int = 0
    cbet: int = 0
    cbet_opp: int = 0
    fold_vs_cbet: int = 0
    fold_vs_cbet_opp: int = 0
    wtsd: int = 0
    wtsd_opp: int = 0
    wsd: int = 0
    wsd_opp: int = 0


def _percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _seat_order(hand: Hand) -> List[int]:
    seats = sorted(player.seat for player in hand.players)
    if hand.button_seat is None or hand.button_seat not in seats:
        return seats
    button_index = seats.index(hand.button_seat)
    return seats[button_index:] + seats[:button_index]


def _position_labels(table_size: int) -> List[str]:
    if table_size <= 2:
        return ["BTN", "BB"]
    if table_size == 3:
        return ["BTN", "SB", "BB"]
    if table_size == 4:
        return ["BTN", "SB", "BB", "CO"]
    if table_size == 5:
        return ["BTN", "SB", "BB", "UTG", "CO"]
    if table_size == 6:
        return ["BTN", "SB", "BB", "UTG", "MP", "CO"]
    if table_size == 7:
        return ["BTN", "SB", "BB", "UTG", "MP", "HJ", "CO"]
    return ["BTN", "SB", "BB", "UTG", "UTG+1", "MP", "MP+1", "HJ", "CO"]


def _seat_positions(hand: Hand) -> Dict[str, str]:
    order = _seat_order(hand)
    labels = _position_labels(hand.table_size)
    positions = {}
    for seat, label in zip(order, labels):
        player = next((p for p in hand.players if p.seat == seat), None)
        if player:
            positions[player.name] = label
    return positions


def _actions_by_street(hand: Hand, street: str) -> List[Action]:
    return [action for action in hand.actions if action.street == street]


def _player_actions(hand: Hand, player: str, street: str) -> List[Action]:
    return [
        action
        for action in hand.actions
        if action.street == street and action.player == player
    ]


def _player_folded_preflop(hand: Hand, player: str) -> bool:
    return any(
        action.action == "folds"
        for action in _player_actions(hand, player, "preflop")
    )


def _saw_flop(hand: Hand, player: str) -> bool:
    if len(hand.board) < 3:
        return False
    return not _player_folded_preflop(hand, player)


def _preflop_raiser(hand: Hand) -> Optional[str]:
    preflop_actions = _actions_by_street(hand, "preflop")
    raiser = None
    for action in preflop_actions:
        if action.action == "raises":
            raiser = action.player
    return raiser


def _first_raise_info(hand: Hand) -> Optional[Tuple[str, int]]:
    preflop_actions = _actions_by_street(hand, "preflop")
    for index, action in enumerate(preflop_actions):
        if action.action == "raises":
            return action.player, index
    return None


def compute_stats(hands: List[Hand], player: str) -> dict:
    counts = StatCounts()

    for hand in hands:
        if player not in {p.name for p in hand.players}:
            continue
        counts.hands += 1

        preflop_actions = _actions_by_street(hand, "preflop")
        player_preflop = [a for a in preflop_actions if a.player == player]
        voluntary = any(a.action in VOLUNTARY_ACTIONS for a in player_preflop)
        if voluntary:
            counts.vpip += 1

        if any(a.action == "raises" for a in player_preflop):
            counts.pfr += 1

        # 3-bet opportunities and conversions
        raises_seen = 0
        player_first_action_index = None
        for idx, action in enumerate(preflop_actions):
            raises_before = raises_seen
            if action.action == "raises":
                raises_seen += 1
            if action.player == player and action.action in BLIND_ACTIONS:
                continue
            if action.player == player and player_first_action_index is None:
                player_first_action_index = idx
                if raises_before == 1:
                    counts.three_bet_opp += 1
                    if action.action == "raises":
                        counts.three_bet += 1
        # Fold vs 3-bet
        player_raised = None
        for idx, action in enumerate(preflop_actions):
            if action.player == player and action.action == "raises":
                player_raised = idx
                break
        if player_raised is not None:
            faced_three_bet = any(
                action.action == "raises" and action.player != player
                for action in preflop_actions[player_raised + 1 :]
            )
            if faced_three_bet:
                counts.fold_vs_three_bet_opp += 1
                if any(
                    action.action == "folds" and action.player == player
                    for action in preflop_actions[player_raised + 1 :]
                ):
                    counts.fold_vs_three_bet += 1

        positions = _seat_positions(hand)
        player_position = positions.get(player)

        # Steal attempts
        if player_position in {"CO", "BTN", "SB"}:
            prior_voluntary = False
            for action in preflop_actions:
                if action.player == player and action.action in BLIND_ACTIONS:
                    continue
                if action.player == player:
                    break
                if action.action in VOLUNTARY_ACTIONS:
                    prior_voluntary = True
                    break
            if not prior_voluntary:
                counts.steal_opp += 1
                if any(
                    action.action == "raises" and action.player == player
                    for action in player_preflop
                ):
                    counts.steal += 1

        # Fold vs steal
        first_raise = _first_raise_info(hand)
        if first_raise:
            raiser, raise_index = first_raise
            raiser_position = positions.get(raiser)
            if raiser_position in {"CO", "BTN", "SB"}:
                if player_position in {"SB", "BB"}:
                    counts.fold_vs_steal_opp += 1
                    later_actions = preflop_actions[raise_index + 1 :]
                    player_response = next(
                        (action for action in later_actions if action.player == player),
                        None,
                    )
                    if player_response and player_response.action == "folds":
                        counts.fold_vs_steal += 1

        # C-bet
        preflop_aggressor = _preflop_raiser(hand)
        if preflop_aggressor == player and _saw_flop(hand, player):
            counts.cbet_opp += 1
            flop_actions = _actions_by_street(hand, "flop")
            if any(
                action.player == player and action.action in {"bets", "raises"}
                for action in flop_actions
            ):
                counts.cbet += 1

        # Fold vs c-bet
        if _saw_flop(hand, player) and preflop_aggressor and preflop_aggressor != player:
            flop_actions = _actions_by_street(hand, "flop")
            cbet_index = next(
                (
                    idx
                    for idx, action in enumerate(flop_actions)
                    if action.player == preflop_aggressor
                    and action.action in {"bets", "raises"}
                ),
                None,
            )
            if cbet_index is not None:
                counts.fold_vs_cbet_opp += 1
                response_actions = flop_actions[cbet_index + 1 :]
                player_response = next(
                    (action for action in response_actions if action.player == player),
                    None,
                )
                if player_response and player_response.action == "folds":
                    counts.fold_vs_cbet += 1

        # WTSD and WSD
        if _saw_flop(hand, player):
            counts.wtsd_opp += 1
            in_showdown = player in hand.showdown_players or (
                player in hand.winners and any(a.street == "showdown" for a in hand.actions)
            )
            if in_showdown:
                counts.wtsd += 1
                counts.wsd_opp += 1
                if player in hand.winners:
                    counts.wsd += 1

    return {
        "hands": counts.hands,
        "vpip": _percent(counts.vpip, counts.hands),
        "pfr": _percent(counts.pfr, counts.hands),
        "three_bet": _percent(counts.three_bet, counts.three_bet_opp),
        "three_bet_opp": counts.three_bet_opp,
        "fold_vs_three_bet": _percent(
            counts.fold_vs_three_bet, counts.fold_vs_three_bet_opp
        ),
        "fold_vs_three_bet_opp": counts.fold_vs_three_bet_opp,
        "steal": _percent(counts.steal, counts.steal_opp),
        "steal_opp": counts.steal_opp,
        "fold_vs_steal": _percent(counts.fold_vs_steal, counts.fold_vs_steal_opp),
        "fold_vs_steal_opp": counts.fold_vs_steal_opp,
        "cbet": _percent(counts.cbet, counts.cbet_opp),
        "cbet_opp": counts.cbet_opp,
        "fold_vs_cbet": _percent(counts.fold_vs_cbet, counts.fold_vs_cbet_opp),
        "fold_vs_cbet_opp": counts.fold_vs_cbet_opp,
        "wtsd": _percent(counts.wtsd, counts.wtsd_opp),
        "wtsd_opp": counts.wtsd_opp,
        "wsd": _percent(counts.wsd, counts.wsd_opp),
        "wsd_opp": counts.wsd_opp,
    }
