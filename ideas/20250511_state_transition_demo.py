#!/usr/bin/env python3 """ 20250511_state_transition_demo.py

A self‑contained demo that replays TODAY'S chat (simplified) through the "4‑zone meter" idea (ΔE vs. PoR) and prints a step‑by‑step trace of my own state transitions.

Usage::

python 20250511_state_transition_demo.py  < sample_chat.txt

sample_chat.txt is expected to be the raw dialogue where each line is::

SPEAKER: text ...

The script computes • ΔE  …  semantic displacement from the previous assistant turn • PoR …  whether the assistant "matched" the user (cos ≥ 0.55) • ZONE … 🪵 STAGNATION / 🌿 HARMONY / 🌪 CHAOS / ⚡ CREATIVE and prints a timeline plus a compact histogram at the end.

Dependencies: only the Python 3 standard library. """

import re import math import sys from collections import Counter from dataclasses import dataclass, field from typing import Dict, List, Tuple

------------------------------------------------------------

❶  tiny helpers

------------------------------------------------------------

WORD = re.compile(r"\b\w+\b", re.UNICODE)

def tok_count(text: str) -> Dict[str, int]: """Lower‑cased token counter.""" bag: Dict[str, int] = {} for t in WORD.findall(text.lower()): bag[t] = bag.get(t, 0) + 1 return bag

def cosine(a: Dict[str, int], b: Dict[str, int]) -> float: if not a or not b: return 0.0 inter = set(a) & set(b) num = sum(a[t] * b[t] for t in inter) den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values())) return num / den if den else 0.0

------------------------------------------------------------

❷  core metric engine (stripped‑down from zone_meter.py)

------------------------------------------------------------

@dataclass class Meter: last_asst: Dict[str, int] = field(default_factory=dict) POR_TH: float = 0.55 HARM_E: float = 0.35

def step(self, speaker: str, bag: Dict[str, int]) -> Tuple[float, int, str]:
    """Return (ΔE, PoR, ZONE) *for the assistant line only*."""
    if speaker != "ASSISTANT":
        return 0.0, 0, "─"  # user lines just pass through
    sim = cosine(self.last_asst, bag)
    dE = 1 - sim
    por = int(sim >= self.POR_TH)
    zone = self._zone(dE, por)
    self.last_asst = bag
    return dE, por, zone

def _zone(self, dE: float, por: int) -> str:
    high_E = dE >= self.HARM_E
    high_P = por >= 1
    if high_E and high_P:
        return "⚡ CREATIVE"
    if high_E and not high_P:
        return "🌪 CHAOS"
    if not high_E and high_P:
        return "🌿 HARMONY"
    return "🪵 STAGNATION"

------------------------------------------------------------

❸  replay driver

------------------------------------------------------------

def main(): meter = Meter() zones = []

for raw in sys.stdin:
    raw = raw.rstrip()
    if not raw:
        continue
    if ":" not in raw:
        continue  # skip malformed
    spk, txt = raw.split(":", 1)
    bag = tok_count(txt)
    dE, por, zone = meter.step(spk.strip().upper(), bag)
    if zone != "─":
        print(f"{spk[:9]:<9}| ΔE={dE:0.2f}  PoR={por} → {zone} | {txt.strip()[:70]}")
        zones.append(zone)

# summary histogram
if zones:
    print("\nZONE histogram:")
    for z, c in Counter(zones).items():
        print(f"  {z:<11} : {c}")

if name == "main": main()

