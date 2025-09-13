import time
from contextlib import contextmanager
from .db import SessionLocal, Event

FEEDBACK_ENABLED = False
def log_event(**kwargs):
    """Écrit un événement simple (upload, error...)."""
     # ⛔️ Ne rien enregistrer pour le feedback
    if not FEEDBACK_ENABLED and kwargs.get("event_type") == "feedback":
        return
    #if kwargs.get("event_type") == "feedback":
    #    return
    with SessionLocal() as s:
        s.add(Event(**kwargs))
        s.commit()

@contextmanager

def track_event(event_type, user_id=None, session_id=None, **meta):
    """
    Entoure un bloc de code pour mesurer latence + statut.
    Utilise-le autour des appels RAG/LLM (event_type='query').
    """
    # ⛔️ Ne rien logger pour le feedback
    if event_type == "feedback":
        yield
        return

    t0 = time.perf_counter()
    status = "ok"
    err = None
    try:
        yield
    except Exception as e:
        status = "error"
        err = str(e)[:300]
        raise
    finally:
        latency_ms = (time.perf_counter() - t0) * 1000
        payload = meta.get("payload") or {}
        if err:
            payload = {**payload, "error": err}
        log_event(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            status=status,
            latency_ms=latency_ms,
            tokens_in=meta.get("tokens_in"),
            tokens_out=meta.get("tokens_out"),
            score=meta.get("score"),
            #feedback=meta.get("feedback"),
            prompt=(meta.get("prompt") or "")[:500],  # éviter PII trop longues
            response_summary=meta.get("response_summary"),
            payload=payload,
        )