from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Crear engine para PostgreSQL (Supabase)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.ENVIRONMENT == "development"
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# Dependency para obtener DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inicializar base de datos
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos inicializada correctamente (Supabase PostgreSQL)")
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        raise e