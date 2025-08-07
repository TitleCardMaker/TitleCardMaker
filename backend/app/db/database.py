from re import IGNORECASE, sub as re_sub, match as _regex_match
from typing import Any, Generator

from thefuzz.fuzz import partial_token_sort_ratio as partial_ratio
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.event import listens_for
from unidecode import unidecode

from app.core.config import config


# URL of the SQL Database - based on whether in Docker or not
if config.IS_DOCKER:
    SQLALCHEMY_DATABASE_URL = 'sqlite:////config/db.sqlite'
else:
    SQLALCHEMY_DATABASE_URL = 'sqlite:///../config/db.sqlite'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
    pool_pre_ping=True,
    # https://docs.sqlalchemy.org/en/20/core/pooling.html#pool-disconnects
    connect_args={'check_same_thread': False, 'timeout': 30},
    # echo=True,
    # Do not limit pool overflow since "new" connections are made inside queued
    # BackgroundTasks - see https://docs.sqlalchemy.org/en/20/errors.html for
    # reference
    pool_size=5, max_overflow=-1,
)

# URL to the Blueprints SQL database
if config.IS_DOCKER:
    BLUEPRINT_SQL_DATABASE_URL = 'sqlite:////tcm/modules/.objects/blueprints.db'
else:
    BLUEPRINT_SQL_DATABASE_URL = 'sqlite:///./modules/.objects/blueprints.db'

blueprint_engine = create_engine(
    BLUEPRINT_SQL_DATABASE_URL, connect_args={'check_same_thread': False},
)

# Session makers for connecting to each database
SessionLocal = sessionmaker(
    bind=engine, expire_on_commit=False, autocommit=False, autoflush=False,
)
Base = declarative_base()

BlueprintSessionMaker = sessionmaker(bind=blueprint_engine)
BlueprintBase = declarative_base() 


"""
Create a default __rich_repr__ which all tables subclassing this base
class can utilize for rich output in Tracebacks.
See https://rich.readthedocs.io/en/stable/pretty.html#rich-repr-protocol
"""
def default_rich_repr(self) -> Generator[tuple[str, Any, None], None, None]:
    """
    Print key/value pairs of all non-private, non-None items in this
    class.
    """

    for k, v in sorted(self.__dict__.items()):
        if not k.startswith('_'): # Skip private attributes
            yield k, v, None # Assume all defaults are None
Base.__rich_repr__ = default_rich_repr


"""
Register custom SQL functions for the database.
"""

def regex_replace(pattern: str, repl: str, string: str) -> str:
    """Regex replacement function for DB registration"""
    return re_sub(pattern, repl, string, flags=IGNORECASE)

def regex_match(pattern: str, string: str) -> bool:
    """Regex match function for DB registration"""
    return bool(_regex_match(pattern, string, flags=IGNORECASE))

@listens_for(engine, 'connect')
def register_custom_functions(
        dbapi_connection,
        connection_record, # pylint: disable=unused-argument
    ) -> None:
    """
    When the engine is connected, register the regex replacement
    function (`re_sub`) as `regex_replace`, as well as the
    `partial_ratio` fuzzy-string match function.
    """
    dbapi_connection.create_function('regex_replace', 3, regex_replace)
    dbapi_connection.create_function('regex_match', 2, regex_match)
    dbapi_connection.create_function('partial_ratio', 2, partial_ratio)
    dbapi_connection.create_function(
        'unidecode', 1, lambda s: unidecode(s, errors='preserve')
    )

@listens_for(blueprint_engine, 'connect')
def register_custom_functions_blueprints(
        dbapi_connection,
        connection_record, # pylint: disable=unused-argument
    ) -> None:
    """When the engine is connected, register the `regex_replace` function"""
    dbapi_connection.create_function('regex_replace', 3, regex_replace)


__all__ = [
    'Base',
    'BlueprintBase',
    'BlueprintSessionMaker',
    'engine',
    'SessionLocal',
]
