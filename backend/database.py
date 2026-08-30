import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

# Engine/session creation is deferred to first use, not done at import
# time. Previously this module raised RuntimeError as soon as it was
# imported if DATABASE_URL wasn't set — which meant every other module
# that imports models.py (clustering.py, consensus.py, reasoning/*.py,
# main.py, and any test file that touches them) also failed to import
# without a live DB configured. That made it impossible to unit test
# pure logic (e.g. reasoning-agent output parsing, DBSCAN clustering
# math) in isolation. Now the check only fires when a DB connection is
# actually needed.
_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not set. Add it to backend/.env, "
                "e.g. DATABASE_URL=postgresql://<user>:<password>@<host>/<database>?sslmode=require"
            )
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


# Public accessor for anything that needs the raw engine (e.g. a manual
# DB-connectivity check script).
get_engine = _get_engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


class _LazySessionLocal:
    """Allows existing call sites (`SessionLocal()`) to keep working
    unchanged, while the underlying engine/session factory is only
    built on first actual use."""
    def __call__(self, *args, **kwargs):
        return _get_session_factory()(*args, **kwargs)


SessionLocal = _LazySessionLocal()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()