#!/usr/bin/env python3
"""
Collect JSON files in ideas/  -> build a directed graph  -> write GraphML
 - ノード:  seed_id
     * title : 短い見出し
     * tags  : "tag1,tag2,tag3"  （リストをカンマ区切り文字列へ）
 - エッジ:  link 配列に列挙された seed_id どうし
結果は mesh_logs/mesh_YYYYMM.graphml に保存
"""

import json, glob, os
from datetime import datetime
import networkx as nx

# ---------- 1. グラフ生成 ----------
G = nx.DiGraph()

for fp in glob.glob("ideas/*.json"):
    with open(fp, "r") as f:
        d = json.load(f)

    nid   = d["seed_id"]
    title = d.get("title", "")
    tags  = ",".join(d.get("tags", []))

    # ノード追加（list 型は文字列に変換済み）
    G.add_node(nid, title=title, tags=tags)

    # エッジ追加
    for tgt in d.get("link", []):
        G.add_edge(nid, tgt)

# ---------- 2. 書き出し ----------
os.makedirs("mesh_logs", exist_ok=True)
out_path = f"mesh_logs/mesh_{datetime.now():%Y%m}.graphml"
nx.write_graphml(G, out_path)
print("mesh ➜", out_path)
