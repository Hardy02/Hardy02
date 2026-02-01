from __future__ import annotations

import re
from typing import Iterable, List


HAND_START_RE = re.compile(r"^(?:PokerStars|Ignition|Hand|Game).*(Hand #|Hand\s#|#)\d+")


def split_hands(raw_text: str) -> List[str]:
    lines = [line.rstrip("\n") for line in raw_text.splitlines() if line.strip()]
    hands: List[List[str]] = []
    current: List[str] = []
    for line in lines:
        if HAND_START_RE.search(line):
            if current:
                hands.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        hands.append(current)
    return ["\n".join(hand_lines) for hand_lines in hands if hand_lines]


def tokenize(raw_text: str) -> Iterable[str]:
    for hand_text in split_hands(raw_text):
        yield hand_text
