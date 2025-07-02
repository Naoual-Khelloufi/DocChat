# init_db.py

from core.auth.database import engine
from core.auth.models import Base

# Création des tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

print("✅ Base de données initialisée avec succès.")
