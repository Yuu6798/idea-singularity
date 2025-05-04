#!/usr/bin/env python3
import json, glob, networkx as nx
from datetime import datetime
G = nx.DiGraph()
for fp in glob.glob("ideas/*.json"):
    d = json.load(open(fp))
    nid = d["seed_id"]
    G.add_node(nid, **{k:v for k,v in d.items() if k!="link"})
    for tgt in d.get("link", []):
        G.add_edge(nid, tgt)
out = f"mesh_logs/mesh_{datetime.now():%Y%m}.graphml"
nx.write_graphml(G, out)
print("mesh ➜", out)
