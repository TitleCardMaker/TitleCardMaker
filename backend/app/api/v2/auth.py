from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    get_password_hash
)
from app.dependencies import get_database, get_logger
from app.db.users import authenticate_user, get_current_user, get_user
from app.logging.logger import Logger
from app.models.user import User as UserModel
from app.schemas.auth import (
    CreateUserSchema,
    ReturnTokenSchema,
    ReturnUserSchema,
    UpdateUser,
)
from app.settings import settings


# Create sub router for all /auth API requests
auth_router = APIRouter(
    prefix='/auth',
    tags=['Authentication'],
)


@auth_router.post('/enable', dependencies=[Depends(get_current_user)])
def enable_authentication(
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> ReturnUserSchema:
    """
    Enable Authentication on this server. If there are no existing Users
    when enabled then a temporary User is created.
    """

    # Enable authentication globally
    settings.require_auth = True
    settings.commit(log=log)

    # Get current users
    users = db.query(UserModel).all()
    if users:
        return users[0]

    # No existing Users, create temporary
    new_user = CreateUserSchema(username='admin', password='password')
    new_user = UserModel(
        username=new_user.username,
        hashed_password=get_password_hash(new_user.password),
    )
    db.add(new_user)
    db.commit()
    log.warning('Created temporary User("admin", "password")')

    return ReturnUserSchema(
        username=new_user.username,
        hashed_password=new_user.hashed_password,
        temporary=True, # Temporary credentials need to be flagged
    )


@auth_router.post('/disable', dependencies=[Depends(get_current_user)])
def disable_authentication(
        revoke_access: bool = Query(default=False),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Disable the Authentication requirement on this server.

    - revoke_access: Whether to revoke access from all existing Users.
    """

    # Disable authentication requirement
    settings.require_auth = False
    settings.commit(log=log)
    log.warning('Disabling Authentication')

    # If revoking access, deleting existing User entries
    if revoke_access:
        log.warning('Revoking access from all existing Users')
        db.query(UserModel).delete()
        db.commit()


@auth_router.post('/new-user', dependencies=[Depends(get_current_user)])
def add_new_user(
        db: Session = Depends(get_database),
        new_user: CreateUserSchema = Body(...),
        log: Logger = Depends(get_logger),
    ) -> ReturnUserSchema:
    """
    Add a new User - must be called by an already authenticated User.

    - new_user: New User details to give access to.
    """

    # Verify no User exists with this username
    existing = (
        db.query(UserModel)
            .filter(UserModel.username == new_user.username)
            .first()
    )
    if existing:
        raise HTTPException(
            status_code=422,
            detail='Username taken',
        )

    # Hash this Password, add to database
    user = UserModel(
        username=new_user.username,
        hashed_password=get_password_hash(new_user.password),
    )
    db.add(user)
    db.commit()
    log.info(f'Created new User({new_user.username})')

    return user


@auth_router.delete('/user', dependencies=[Depends(get_current_user)])
def delete_user(
        username: str = Query(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Delete the User with the given Username. If there are no remaining
    Users, authentication is globally disabled to prevent accidental
    lockout.

    - username: Username of the User to delete.
    """

    # Find this User
    user = db.query(UserModel).filter_by(username=username).first()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail=f'User "{username}" does not exist',
        )

    # Delete User
    db.delete(user)
    db.commit()
    log.info(f'Deleted User({username})')

    # If there are no more active Users, disable authentication to avoid L/O
    if db.query(UserModel).count() == 0:
        log.warning('No remaining active users - disabling authentication')
        settings.require_auth = False
        settings.commit(log=log)


@auth_router.get('/all', dependencies=[Depends(get_current_user)])
def get_all_usernames(db: Session = Depends(get_database)) -> list[str]:
    """Get the usernames of all Users in the database."""

    return [user.username for user in db.query(UserModel).all()]


@auth_router.get('/active')
def get_active_username(
        user: UserModel | None = Depends(get_current_user),
    ) -> str | None:
    """Get the username of the active User."""

    return None if user is None else user.username


@auth_router.post('/edit')
def update_user_credentials(
        update_user: UpdateUser = Body(...),
        db: Session = Depends(get_database),
        user: UserModel | None = Depends(get_current_user),
        log: Logger = Depends(get_logger),
    ) -> ReturnUserSchema:
    """
    Update the credentials of the current User.
    - update_user: New credentials to utilize for this User.
    """

    # Authorization is disabled, cannot edit credentials
    if user is None:
        raise HTTPException(
            status_code=401,
            detail='Cannot edit credentials while unauthorized'
        )

    # Get user
    if (user := get_user(db, user.username)) is None:
        raise HTTPException(
            status_code=404,
            detail='No User found',
        )

    # Verify new username does not conflict with existing user
    existing_user = db.query(UserModel)\
        .filter_by(username=update_user.username)\
        .first()
    if existing_user and existing_user != user:
        raise HTTPException(
            status_code=422,
            detail='Username taken',
        )

    # Change username/password
    log.warning(f'Modified credentials for User({user.username})')
    user.username = update_user.username
    user.hashed_password = get_password_hash(update_user.password)
    db.commit()

    return user


@auth_router.post('/authenticate')
def login_for_access_token(
        db: Session = Depends(get_database),
        form_data: OAuth2PasswordRequestForm = Depends(),
        log: Logger = Depends(get_logger),
    ) -> ReturnTokenSchema:
    """
    Authenticate the given User and return an appropriate access token.

    - form_data: OAuth2 form with the username and password being
    authenticated.
    """

    # Authenticate User
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    # Create new access token for this User
    access_token = create_access_token(
        data={'sub': user.username, 'uid': user.hashed_password},
        expires_delta=settings.config.AUTH_EXPIRATION_TIME,
    )
    log.info((
        f'Authenticated User({user.username}) for '
        f'{settings.config.AUTH_EXPIRATION_TIME}'
    ))

    return ReturnTokenSchema(
        access_token=access_token,
        token_type='bearer',
    )


@auth_router.post('/reset')
def reset_all_authentication(
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Reset all authentication of the current server. This requires the
    appropriate environment variable to be set in order to function.

    Intended only for testing setup and teardown.
    """

    if not settings.config.TESTING_MODE:
        raise HTTPException(status_code=401, detail='Unauthorized')

    # Delete all Users from the database
    log.warning('Resetting all authentication')
    db.query(UserModel).delete()
    db.commit()

    # Do not require authentication
    settings.require_auth = False
    settings.commit(log=log)
