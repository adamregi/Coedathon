import os
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.errors import AppException
from app.core.logging import logger

def get_database_url() -> str:
    # 1. Direct environment variable
    if os.environ.get("MYSQL_DATABASE_URL"):
        return os.environ["MYSQL_DATABASE_URL"]
    # 2. Read directly from .env file if present
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("MYSQL_DATABASE_URL="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass
    # 3. Fallback to settings or local sqlite
    return settings.MYSQL_DATABASE_URL or settings.DATABASE_URL or "sqlite:///./codethon_local.db"


_engine: Optional[Engine] = None
_last_url: Optional[str] = None


def get_engine() -> Engine:
    global _engine, _last_url
    current_url = get_database_url()
    if _engine is None or _last_url != current_url:
        _last_url = current_url
        connect_args = {}
        if current_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            current_url,
            echo=False,
            future=True,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
    return _engine


# Default engine for backwards compatibility with migrations/metadata
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy database session."""
    current_engine = get_engine()
    sm = sessionmaker(autocommit=False, autoflush=False, bind=current_engine, future=True)
    db = sm()
    try:
        db.execute(text("SELECT 1"))
    except OperationalError as exc:
        logger.error(f"MySQL database connection failed: {exc}")
        db.close()
        raise AppException(
            status_code=500,
            code="DATABASE_CONNECTION_ERROR",
            message="Could not connect to MySQL database. Please update MYSQL_DATABASE_URL in your .env file with your local MySQL password.",
            details={"error": str(exc)},
        )
    except Exception as exc:
        logger.error(f"Database error: {exc}")
        db.close()
        raise AppException(
            status_code=500,
            code="DATABASE_ERROR",
            message=f"Database connection error: {str(exc)}",
            details={},
        )
    try:
        yield db
    finally:
        db.close()
