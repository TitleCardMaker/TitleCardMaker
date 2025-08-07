from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import config


if config.IS_DOCKER:
    LOGS_DATABASE_URL = 'sqlite:////config/logs/logs.sqlite'
    LOGS_DATABASE_PATH = Path('/config/logs/logs.sqlite')
else:
    LOGS_DATABASE_URL = 'sqlite:///../config/logs/logs.sqlite'
    LOGS_DATABASE_PATH = Path('../config/logs/logs.sqlite')

logs_engine = create_engine(
    LOGS_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={'check_same_thread': False, 'timeout': 30},
    pool_size=5,
    max_overflow=-1,
)

# Session maker for connecting to logs database
LogsSessionLocal = sessionmaker(
    bind=logs_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for log models
LogsBase = declarative_base()
