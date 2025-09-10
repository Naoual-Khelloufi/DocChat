#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Offline RAG Evaluation (STRICT prompt, no num_predict)
- Builds an in-memory vector index from data/corpus_eval
- Loads data/eval/evaluation_set.json
- For each question: retrieval top-k + strict RAG generation
- Computes metrics: Precision@k, Recall@k, MRR, EM, F1
- Saves detailed CSV + JSON summary

Recommended for stability:
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
from core.embeddings import VectorStore
from core.llm import LLMManager
from langchain_core.documents import Document as LCDocument

# ----- Make project root importable -----
CUR_DIR = Path(__file__).parent.resolve()
ROOT_DIR = CUR_DIR.parent.resolve()
sys.path.append(str(ROOT_DIR))

# -----------------------
#   Text splitting & index
# -----------------------
def build_index_from_corpus(corpus_dir: Path) -> VectorStore:
    """
    Reads all text files from the corpus, splits them into chunks,
    and builds an in-memory vector index.
    """
    # Prefer the new package; fallback for older LangChain versions
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception:
        from langchain.text_splitter import RecursiveCharacterTextSplitter  # compatibility for versions < 0.2

    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)

    vs = VectorStore()
    docs: List[LCDocument] = []

    for fp in sorted(corpus_dir.glob("*")):
        if not fp.is_file():
            continue
        text = fp.read_text(encoding="utf-8", errors="ignore")
        # Keep filename in metadata so we can compute P@k / R@k / MRR by source
        chunks = splitter.create_documents([text], metadatas=[{"source": fp.name}])
        docs.extend(chunks)

    # In-memory index (no persistence needed for evaluation)
    vs.create_vector_db(documents=docs, collection_name="eval-run", persist_dir=None)
    return vs

# -----------------------
#   Metrics
# -----------------------
def _uniq_topk(sources: List[str], k: int) -> List[str]:
    """Return up to k distinct sources in original order."""
    seen, uniq = set(), []
    for s in sources:
        if s is None:
            continue
        if s not in seen:
            seen.add(s)
            uniq.append(s)
            if len(uniq) == k:
                break
    return uniq

def precision_at_k(retrieved_sources: List[str], relevant_sources: List[str], k: int) -> float:
    if k <= 0:
        return 0.0
    topk = _uniq_topk(retrieved_sources, k)  # distinct docs only
    if not topk:
        return 0.0
    rel_set = set(relevant_sources or [])
    tp = sum(1 for s in topk if s in rel_set)
    # precision@k is tp divided by the number of results considered (≤ k after de-dup)
    return tp / len(topk)

def recall_at_k(retrieved_sources: List[str], relevant_sources: List[str], k: int) -> float:
    """Recall@k ∈ [0,1] measured over distinct documents, not chunks."""
    rel_set = set(relevant_sources or [])
    if not rel_set:
        return 0.0
    topk = _uniq_topk(retrieved_sources, k)  # distinct docs only
    tp = sum(1 for s in topk if s in rel_set)
    return tp / len(rel_set)


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
#   Retrieval + strict generation
# -----------------------
def retrieve_topk(vs: VectorStore, question: str, k: int) -> Tuple[List[LCDocument], List[str]]:
    """
    Returns (documents, sources) ordered by similarity (top-k).
    """
    docs = vs.similarity_search(question, k=k)
    sources = []
    for d in docs:
        sources.append((d.metadata or {}).get("source"))
    return docs, sources

def generate_answer(llm: LLMManager, question: str, docs: List[LCDocument]) -> str:
    """
    Uses the STRICT evaluation prompt to produce short, comparable answers.
    We do NOT rely on num_predict; concision is enforced by the prompt itself.
    """
    if not docs:
        # Strict eval: no general answer if nothing is retrieved
        return "Information not found"

    context_text = "\n\n".join([d.page_content for d in docs])

    prompt = llm._get_rag_prompt_eval().format(
        context=context_text,
        question=question
    )

    resp = llm.llm.invoke(prompt)
    return (resp.content or "").strip()

# -----------------------
#   Evaluation loop
# -----------------------
def run_eval(corpus_dir: Path, dataset_path: Path, out_csv: Path, k: int):
    # Optional but recommended for determinism
    os.environ.setdefault("LLM_TEMPERATURE", "0")
    os.environ.setdefault("LLM_SEED", "42")

    # LLM + index
    llm = LLMManager(model_name=os.getenv("EVAL_MODEL", "llama3.2:latest"))
    vs = build_index_from_corpus(corpus_dir)

    # Dataset
    items = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not items:
        raise RuntimeError("Empty dataset.")

    rows = []
    agg = {"p": [], "r": [], "mrr": [], "f1": [], "em": []}

    for it in items:
        rel = list(dict.fromkeys(it.get("relevant_sources", []) or []))  # dedupe
        qid  = it["id"]
        q    = it["question"]
        gold = it["expected_answer"]

        docs, retrieved_srcs = retrieve_topk(vs, q, k=k)
        ans = generate_answer(llm, q, docs)

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

    # Write outputs
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "k": k,
        "n_questions": len(rows),
        f"mean_precision@{k}": round(sum(agg["p"]) / len(agg["p"]), 4) if agg["p"] else 0.0,
        f"mean_recall@{k}":    round(sum(agg["r"]) / len(agg["r"]), 4) if agg["r"] else 0.0,
        "mean_mrr":            round(sum(agg["mrr"]) / len(agg["mrr"]), 4) if agg["mrr"] else 0.0,
        "mean_f1":             round(sum(agg["f1"]) / len(agg["f1"]), 4) if agg["f1"] else 0.0,
        "mean_em":             round(sum(agg["em"]) / len(agg["em"]), 4) if agg["em"] else 0.0,
        "out_csv": str(out_csv)
    }
    out_json = out_csv.with_suffix(".json")
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

# -----------------------
#   CLI
# -----------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus",  type=str, default=str(ROOT_DIR / "data/corpus_eval"))
    ap.add_argument("--dataset", type=str, default=str(ROOT_DIR / "data/eval/evaluation_set.json"))
    ap.add_argument("--out",     type=str, default=str(CUR_DIR / "results/eval_run.csv"))
    ap.add_argument("--k",       type=int, default=3, help="top-k for retrieval")
    args = ap.parse_args()

    run_eval(
        Path(args.corpus),
        Path(args.dataset),
        Path(args.out),
        args.k
    )
