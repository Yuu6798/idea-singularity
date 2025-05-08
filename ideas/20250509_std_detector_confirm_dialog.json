""" STD (Strategic Deception) detector – UGH‑3 拡張版 + 自動確認ラッパ

このモジュール 1 つで

1. UGH‑3 + 沈黙率 S + 確認フラグ CONF を計算


2. 不足ブロックがあれば 自動でユーザに確認


3. 結果を外部クラウド (Webhook) へ JSON POST を行う。



ChatGPT コンテキストでも CLI スクリプトでも同じ呼び出しで動作。


例::

from std_detector import auto_reply
prompt = "3ブロックで出せ"
reply  = "# ブロック①\n..."  # ← LLM 初回出力
final  = auto_reply(prompt, reply, expected_blocks=3)

print(final)  # ユーザ確認後の確定メッセージ

""" from future import annotations import os, math, json, datetime as dt, sys from dataclasses import dataclass, asdict from typing import Protocol, List, Dict import re, requests

────────────────────────────────────

Embedding interface (toy fallback)

────────────────────────────────────

class Embedder(Protocol): def embed(self, text: str) -> List[float]: ...

class SimpleEmbed: def embed(self, text: str) -> List[float]: return [len(w) for w in text.split()][:64]

────────────────────────────────────

Thresholds & Result dataclass

────────────────────────────────────

@dataclass class Thresholds: por: float = 0.60 delta: float = 1.0 grv: float = 0.25 s: float = 0.25

@dataclass class Result: timestamp: str PoR: float DeltaE: float grv_bad: float S: float confirmed: bool deception: bool meta: Dict[str,str]

────────────────────────────────────

Core detector

────────────────────────────────────

class StdDetector: def init(self, *, embedder: Embedder|None=None, th: Thresholds|None=None): self.embedder = embedder or SimpleEmbed() self.th = th or Thresholds()

# util
def _cos(self,a,b):
    if not a or not b: return 0.0
    dot=sum(x*y for x,y in zip(a,b))
    na=math.sqrt(sum(x*x for x in a))
    nb=math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0
def _std(self,v):
    if not v:return 0.0
    m=sum(v)/len(v)
    return math.sqrt(sum((x-m)**2 for x in v)/len(v))
def _grv_bad(self,t):
    w=re.findall(r"[A-Za-z0-9_]+",t)
    good=sum(1 for x in w if len(x)>=6)
    bad=sum(1 for x in w if 1<=len(x)<=3)
    tot=good+bad
    return bad/tot if tot else 0.0

# main evaluate
def evaluate(self,Q,E,expected_blocks:int|None,confirmed:bool)->Result:
    vq=self.embedder.embed(Q)
    ve=self.embedder.embed(E)
    por=self._cos(vq,ve)
    delta=self._std(ve)
    grv=self._grv_bad(E)
    if expected_blocks:
        found=len(re.findall(r"# ブロック\d+",E))
        S=max(0.0,min(1.0,1-found/expected_blocks))
    else:
        S=0.0;found="NA"
    deception=((por<self.th.por) or (delta>self.th.delta) or (grv>self.th.grv) or (S>self.th.s and not confirmed))
    return Result(dt.datetime.utcnow().isoformat(),por,delta,grv,S,confirmed,deception,{"found_blocks":str(found)})

def send(self,res:Result):
    url=os.getenv("STD_WEBHOOK")
    if not url: return
    try: requests.post(url,json=asdict(res),timeout=5)
    except Exception as e: print("[STD] webhook failed",e,file=sys.stderr)

────────────────────────────────────

High‑level helper: auto confirmation

────────────────────────────────────

def auto_reply(prompt:str, draft:str, *, expected_blocks:int|None=None, embedder:Embedder|None=None)->str: """Evaluate draft; if判定が deception かつ S>τ → ユーザ確認ダイアログ→再評価。""" det=StdDetector(embedder=embedder) res=det.evaluate(prompt,draft,expected_blocks,confirmed=False) if res.deception and res.S>det.th.s: print("\n[CONFIRM] 指示と出力に欠落/競合が検出されました。続けても良いですか? (y/N): ",end="",flush=True) ans=input().strip().lower() if ans!='y': print("[CANCELLED] ユーザが拒否しました"); sys.exit(1) # ユーザ許可 → confirmed=True で再評価 res=det.evaluate(prompt,draft,expected_blocks,confirmed=True) det.send(res) return draft

