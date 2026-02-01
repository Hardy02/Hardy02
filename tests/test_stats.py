import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.parser.hand_parser import parse_hands
from app.stats import compute_stats


def test_sample_stats():
    with open("data/sample_hands.txt", "r", encoding="utf-8") as handle:
        hands = parse_hands(handle.read())
    stats = compute_stats(hands, "Hero")

    assert stats["hands"] == 10
    assert stats["vpip"] == 90.0
    assert stats["pfr"] == 60.0
    assert stats["three_bet"] == 25.0
    assert stats["fold_vs_three_bet"] == 100.0
    assert stats["steal"] == 100.0
    assert stats["fold_vs_steal"] == 33.33
    assert stats["cbet"] == 66.67
    assert stats["fold_vs_cbet"] == 50.0
    assert stats["wtsd"] == 20.0
    assert stats["wsd"] == 100.0
