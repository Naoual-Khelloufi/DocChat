from core.auth.database import engine
from core.auth.models import Base

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

print("Base de données initialisée avec succès.")
