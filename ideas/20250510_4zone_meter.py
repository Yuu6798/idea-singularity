#!/usr/bin/env python3
"""
zone_meter.py — UGH-3 4-zone classifier (minimal demo)

Usage:
    cat sample_chat.txt | python zone_meter.py
"""

import sys
import re
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Dict

# ---------------------------
# ❶ 超簡易ユーティリティ
# ---------------------------

WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)


def tokens(text: str) -> List[str]:
    """Lower-cased word tokens."""
    return WORD_RE.findall(text.lower())


def cosine(v1: Dict[str, int], v2: Dict[str, int]) -> float:
    """Cosine similarity between 2 sparse token-count dicts."""
    inter = set(v1) & set(v2)
    num = sum(v1[t] * v2[t] for t in inter)
    den = math.sqrt(sum(c * c for c in v1.values())) * math.sqrt(
        sum(c * c for c in v2.values())
    )
    return num / den if den else 0.0


# ---------------------------
# ❷ UGH-3 メトリクス
# ---------------------------

@dataclass
class Turn:
    speaker: str
    text: str
    tok: Dict[str, int] = field(init=False)

    def __post_init__(self):
        self.tok = {}
        for t in tokens(self.text):
            self.tok[t] = self.tok.get(t, 0) + 1


@dataclass
class Metrics:
    por_count: int = 0         # 累積 PoR
    grv: Dict[str, int] = field(default_factory=dict)
    last_tok: Dict[str, int] = field(default_factory=dict)

    # パラメータ（雑に決め打ち）
    POR_COS_TH: float = 0.55   # 照合トリガ閾値
    HARM_E: float = 0.35       # ΔE しきい値（μ±σ など本来動的）
    LOW_POR: int = 0

    def step(self, turn: Turn) -> Tuple[float, int]:
        """1 ターン進めて ΔE と PoR(0/1) を返す."""
        # --- ΔE: 1 − cos(sim) で表現
        sim = cosine(self.last_tok, turn.tok) if self.last_tok else 0.0
        dE = 1 - sim                      # 0 (近) → 1 (遠)
        # --- PoR: 類似度高ければ 1
        por = int(sim >= self.POR_COS_TH)
        self.por_count += por
        # --- grv 更新：PoR 成功語の頻度を加算
        if por:
            for t in turn.tok:
                self.grv[t] = self.grv.get(t, 0) + 1
        # --- 状態更新
        self.last_tok = turn.tok
        return dE, por

    def zone(self, dE: float, por: int) -> str:
        """ΔE, PoR を 4 ゾーンにマッピング."""
        hi_E = dE >= self.HARM_E
        hi_P = por >= 1
        if hi_E and hi_P:
            return "⚡ CREATIVE"
        if hi_E and not hi_P:
            return "🌪 CHAOS"
        if not hi_E and hi_P:
            return "🌿 HARMONY"
        return "🪵 STAGNATION"


# ---------------------------
# ❸ メイン処理
# ---------------------------

def main():
    metric = Metrics()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            spk, txt = line.split(":", 1)
        else:
            spk, txt = "UNK", line
        turn = Turn(spk.strip(), txt.strip())
        dE, por = metric.step(turn)
        zone = metric.zone(dE, por)
        print(f"{spk:8s} | ΔE={dE:0.2f}  PoR={por}  → {zone} | {txt}")

    # --- おまけ：grv Top-5
    top = sorted(metric.grv.items(), key=lambda x: -x[1])[:5]
    if top:
        print("\nTop-5 grv words:", ", ".join(f"{w}({c})" for w, c in top))


if __name__ == "__main__":
    main()