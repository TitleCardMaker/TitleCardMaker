from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.auth import get_secret_key, verify_password
from app.dependencies import get_database
from app.models.user import User
from app.settings import settings


# OAuth2 scheme for authentication
oath2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v2/auth/authenticate')


def get_user(db: Session, username: str) -> User | None:
    """
    Query the database for the `User` with the given username.

    Args:
        db: Database to query.
        username: Name of the User to query for.

    Returns:
        User with the matching Username; `None` if no matching User
        exists.
    """

    return db.query(User).filter_by(username=username).first()


_creds: dict[str, User] = {}
def get_current_user(
        db: Session = Depends(get_database),
        token: str = Depends(oath2_scheme),
    ) -> User | None:
    """
    Dependency to get the User whose username matches the given token.
    If Authorization is globally disabled, then no validation is
    performed.

    Args:
        db: Session to query for Users.
        token: OAuth2 JWT whose data is the encrypted username of the
            active User.

    Returns:
        None if Authorization is disabled. Otherwise, the User with the
        encoded username.

    Raises:
        HTTPException (401): The credentials encoded in `token` do not
        correspond to a valid User.
    """

    # Do not authenticate if globally disabled
    if not settings.require_auth:
        return None

    credential_exception = HTTPException(
        status_code=401,
        detail='Invalid credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    # Decode JWT, get encoded username
    try:
        payload = jwt.decode(
            token,
            get_secret_key(),
            algorithms=[settings.config.CRYPTO_ALGORITHM],
        )
        username: str | None = payload.get('sub')
        uid: str | None = payload.get('uid')
    except JWTError as exc:
        raise credential_exception from exc

    # If username or UID are missing, raise 401
    if username is None or uid is None:
        raise credential_exception

    # If credentials are not cached or don't match, query DB
    if ((user := _creds.get(username)) is None
        or user.hashed_password != uid):
        # User not cached, nor in database, raise 401
        if (user := get_user(db, username)) is None:
            raise credential_exception

        # Add User to cache, verify phash
        _creds[username] = user
        if user.hashed_password != uid:
            raise credential_exception

    # Credentials are cached and match
    return user


def authenticate_user(
        db: Session,
        username: str,
        password: str,
    ) -> User | None:
    """
    Authenticate the given credentials, returning the associated User.

    Args:
        db: Database with Users to query.
        username: Username of the User to authenticate.
        password: Plaintext password to authenticate.

    Returns:
        The User with the given username and password. None if there are
        no matches.
    """

    # If there is no User or the password does not match, return None
    if (user := get_user(db, username)) is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
