#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAG Evaluation:
Builds an index from data/corpus_eval
Loads data/eval/evaluation_set.json
For each question: retrieval top-k + RAG generation
Computes Precision@k, Recall@k, MRR, EM, F1
Exports detailed CSV + summary JSON

Preferably run with:
  export LLM_TEMPERATURE=0
  export LLM_SEED=42
"""

import os
import sys
import json
import csv
import argparse
import re
from pathlib import Path
from typing import List, Tuple
from core.document import DocumentProcessor
from core.embeddings import VectorStore
from core.llm import LLMManager
from langchain_core.documents import Document as LCDocument

# ----- Enable imports from the parent directory (project_root) -----
CUR_DIR = Path(__file__).parent.resolve()
ROOT_DIR = CUR_DIR.parent.resolve()
sys.path.append(str(ROOT_DIR))

# -----------------------
#   Metrics
# -----------------------
def precision_at_k(retrieved_sources: List[str], relevant_sources: List[str], k: int) -> float:
    if k <= 0: 
        return 0.0
    topk = retrieved_sources[:k]
    tp   = sum(1 for s in topk if s in relevant_sources)
    return tp / k

def recall_at_k(retrieved_sources: List[str], relevant_sources: List[str], k: int) -> float:
    if not relevant_sources: 
        return 0.0
    topk = retrieved_sources[:k]
    tp   = sum(1 for s in topk if s in relevant_sources)
    return tp / len(relevant_sources)

def mrr(retrieved_sources: List[str], relevant_sources: List[str]) -> float:
    for rank, src in enumerate(retrieved_sources, start=1):
        if src in relevant_sources:
            return 1.0 / rank
    return 0.0

def _normalize(s: str) -> List[str]:
    s = s.lower()
    s = re.sub(r"[^a-z0-9àâçéèêëîïôûùüÿñæœ\s]", " ", s)
    return [t for t in s.split() if t]

def f1_score(pred: str, gold: str) -> float:
    p_tokens = _normalize(pred)
    g_tokens = _normalize(gold)
    if not p_tokens and not g_tokens: 
        return 1.0
    if not p_tokens or not g_tokens:  
        return 0.0
    p_set, g_set = set(p_tokens), set(g_tokens)
    tp = len(p_set & g_set)
    if tp == 0: 
        return 0.0
    prec = tp / len(p_set)
    rec  = tp / len(g_set)
    return 2 * prec * rec / (prec + rec)

def exact_match(pred: str, gold: str) -> int:
    return int(_normalize(pred) == _normalize(gold))

# -----------------------
#   Evaluation pipeline
# -----------------------
def build_index_from_corpus(corpus_dir: Path) -> VectorStore:
    """Reads all text files from the corpus, splits them, and builds an in-memory index."""
    dp = DocumentProcessor(chunk_size=700, chunk_overlap=100)
    vs = VectorStore()
    docs: List[LCDocument] = []

    for fp in sorted(corpus_dir.glob("*")):
        if not fp.is_file():
            continue
        text = fp.read_text(encoding="utf-8", errors="ignore")
        chunks = dp.split(text, source=fp.name)  # IMPORTANT: metadata['source']= file name
        docs.extend(chunks)

    # Memory index  (persist_dir=None)
    vs.create_vector_db(documents=docs, collection_name="eval-run", persist_dir=None)
    return vs

def retrieve_topk(vs: VectorStore, question: str, k: int) -> Tuple[List[LCDocument], List[str]]:
    """Renvoie (docs, sources) ordonnés par similarité (top-k)."""
    docs = vs.similarity_search(question, k=k)
    sources = []
    for d in docs:
        src = (d.metadata or {}).get("source")
        sources.append(src)
    return docs, sources

def generate_answer(llm: LLMManager, question: str, docs: List[LCDocument], max_tokens: int = 600) -> str:
    if not docs:
        # Security: during evaluation we enforce RAG mode, so no out-of-context answers are allowed.
        return "Information not found"
    return llm.generate_answer(docs, question, max_tokens=max_tokens)

def run_eval(corpus_dir: Path, dataset_path: Path, out_csv: Path, k: int):
    # 1) LLM (determinism via env: LLM_TEMPERATURE=0, LLM_SEED=42)
    llm = LLMManager(model_name=os.getenv("EVAL_MODEL", "llama3.2:latest"))

    # 2) Re-construct index from the corpus
    vs = build_index_from_corpus(corpus_dir)

    # 3) Load dataset
    items = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not items:
        raise RuntimeError("Dataset vide.")

    rows = []
    agg = {"p":[], "r":[], "mrr":[], "f1":[], "em":[]}

    for it in items:
        qid   = it["id"]
        q     = it["question"]
        gold  = it["expected_answer"]
        rel   = it.get("relevant_sources", []) or []

        # Retrieval
        docs, retrieved_srcs = retrieve_topk(vs, q, k=k)

        # Generation (RAG strict)
        ans = generate_answer(llm, q, docs, max_tokens=600)

        # Scores
        p  = precision_at_k(retrieved_srcs, rel, k)
        r  = recall_at_k(retrieved_srcs, rel, k)
        rr = mrr(retrieved_srcs, rel)
        f1 = f1_score(ans, gold)
        em = exact_match(ans, gold)

        agg["p"].append(p) 
        agg["r"].append(r) 
        agg["mrr"].append(rr) 
        agg["f1"].append(f1) 
        agg["em"].append(em)

        rows.append({
            "id": qid,
            "question": q,
            "gold_answer": gold,
            "generated_answer": ans,
            "relevant_sources": "|".join(rel),
            "retrieved_sources": "|".join([s or "" for s in retrieved_srcs]),
            f"precision@{k}": p,
            f"recall@{k}": r,
            "mrr": rr,
            "f1": f1,
            "exact_match": em
        })

    # 4) storages
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "k": k,
        "n_questions": len(rows),
        f"mean_precision@{k}": round(sum(agg["p"])/len(agg["p"]), 4) if agg["p"] else 0.0,
        f"mean_recall@{k}":    round(sum(agg["r"])/len(agg["r"]), 4) if agg["r"] else 0.0,
        "mean_mrr":            round(sum(agg["mrr"])/len(agg["mrr"]), 4) if agg["mrr"] else 0.0,
        "mean_f1":             round(sum(agg["f1"])/len(agg["f1"]), 4) if agg["f1"] else 0.0,
        "mean_em":             round(sum(agg["em"])/len(agg["em"]), 4) if agg["em"] else 0.0,
        "out_csv": str(out_csv)
    }
    out_json = out_csv.with_suffix(".json")
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus",  type=str, default=str(ROOT_DIR / "data/corpus_eval"))
    ap.add_argument("--dataset", type=str, default=str(ROOT_DIR / "data/eval/evaluation_set.json"))
    ap.add_argument("--out",     type=str, default=str(CUR_DIR / "results/eval_run.csv"))
    ap.add_argument("--k",       type=int, default=3)
    args = ap.parse_args()

    run_eval(Path(args.corpus), Path(args.dataset), Path(args.out), args.k)
