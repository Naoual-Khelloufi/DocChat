"""
migrate_add_feedback.py
One-time safe migration: add 'feedback' column to 'events' if missing.
Usage: python migrate_add_feedback.py
"""

import os
import shutil
from sqlalchemy import text
try:
    # Prefer the same import used by our app
    from reporting.db import engine
except Exception:
    # Fallback if our package/module path is different in this environment
    from db import engine

def backup_sqlite_db_if_possible():
    url = str(engine.url)
    # This handles sqlite:///./reporting.db and similar
    if url.startswith("sqlite:///"):
        db_path = url.replace("sqlite:///", "", 1)
        db_path = os.path.abspath(db_path)
        if os.path.exists(db_path):
            backup_path = db_path + ".bak"
            # Don't overwrite an existing backup
            if not os.path.exists(backup_path):
                shutil.copy2(db_path, backup_path)
                print(f"Backup créé: {backup_path}")
            else:
                print(f"Backup déjà présent: {backup_path}")
        else:
            print(f"Fichier SQLite introuvable pour backup: {db_path}")
    else:
        print("Base non-SQLite (pas de backup fichier automatique).")

def ensure_feedback_column():
    with engine.begin() as conn:
        cols = conn.execute(text("PRAGMA table_info(events)")).all()
        colnames = {c[1] for c in cols}
        if "feedback" in colnames:
            print("Colonne 'feedback' déjà existante. Aucune action requise.")
            return False
        # Add the column with a simple VARCHAR(10) type
        conn.execute(text("ALTER TABLE events ADD COLUMN feedback VARCHAR(10)"))
        print("Colonne 'feedback' ajoutée avec succès.")
        return True

if __name__ == "__main__":
    backup_sqlite_db_if_possible()
    changed = ensure_feedback_column()
    if changed:
        print("Migration terminée. Redémarrez votre app et testez un clic Up/Down.")
    else:
        print("Rien à migrer.")

