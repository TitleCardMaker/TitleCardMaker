from hashlib import md5
from importlib.util import spec_from_file_location, module_from_spec
import sys
from typing import Annotated, ClassVar, Literal

from pathlib import Path
from requests import Response, get
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

from app.cards.base import BaseCardType
from app.core.config import config
from app.logging.logger import log
from app.schemas.base import Base
from app.utils.paths import CleanPath


_loaded_files: Annotated[
    set[str],
    'Set of already loaded files'
] = set()


class RemoteDirectory:
    """
    This class describes a RemoteDirectory. A RemoteDirectory is a
    directory that is loaded from the TCM Card Types repository, and is
    necessary to allow card types to utilize non-standard directories
    that can be downloaded at runtime alongside CardType classes.
    """

    __slots__ = ('username', 'directory')


    def __init__(self, username: str, directory: str) -> None:
        """
        Construct a new RemoteDirectory object.

        Args:
            username: Username containing the directory.
            directory: Root directory to load files from.
        """

        self.username = username
        self.directory = directory.removesuffix('/')


    def __truediv__(self, filename: str) -> 'RemoteFile':
        """
        Return a new RemoteFile object for a file with the given name in
        this object's directory.

        >>> rd = RemoteDirectory('CollinHeist', 'files/fonts')
        >>> rf = rd / 'font.ttf'
        """

        return RemoteFile(self.username, f'{self.directory}/{filename}')


class RemoteFile:
    """
    This class describes a RemoteFile. A RemoteFile is a file that is
    loaded from the TCM Card Types repository, and is necessary to allow
    card types to utilize non-standard files that can be downloaded at
    runtime alongside CardType classes. This class has no real
    executable methods, and upon initialization attempts to download the
    remote file if it DNE.
    """

    BASE_URL: Annotated[
        ClassVar[str],
        'Base URL to look for remote content at'
    ] = config.CARD_TYPE_REPOSITORY.removesuffix('/')

    """Temporary directory all files will be downloaded into"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    __slots__ = ('remote_source', 'local_file', 'valid')


    def __init__(self, username: str, filename: str) -> None:
        """
        Construct a new RemoteFile object. This downloads the file for
        the given user and file into the temporary directory of the
        Maker.

        Args:
            username: Username containing the file.
            filename: Filename of the file within the user's folder to
                download.
        """

        # Object validity to be updated
        self.valid = True

        # Remote font will be stored at github/username/filename
        self.remote_source = f'{self.BASE_URL}/{username}/{filename}'

        # The file will be downloaded and exist in the temporary directory
        self.local_file = self.TEMP_DIR / username / filename.rsplit('/')[-1]

        # Create parent folder structure if necessary
        self.local_file.parent.mkdir(parents=True, exist_ok=True)

        # If file has already been loaded this run, skip
        if self.remote_source in _loaded_files:
            return None

        # Download the remote file for local use
        try:
            self.download()
            log.debug(f'Downloaded RemoteFile "{username}/{filename}"')
        except Exception:
            self.valid = False
            log.exception(
                f'Could not download RemoteFile "{username}/{filename}"'
            )
            return None

        # Add to global loaded files set
        _loaded_files.add(self.remote_source)

        return None


    def __str__(self) -> str:
        """
        Returns a string representation of the object. This is just the
        complete filepath for the locally downloaded file.
        """

        return str(self.local_file.resolve())


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return (
            f'<RemoteFile remote_source={self.remote_source}, local_file='
            f'{self.local_file}, valid={self.valid}>'
        )


    def resolve(self) -> Path:
        """
        Get the absolute path of the locally downloaded file.

        Returns:
            Path to the locally downloaded file.
        """

        return self.local_file.resolve()


    def exists(self) -> bool:
        """Wrapper for `Path.exists()` of the associated file."""

        return self.local_file.exists()


    @retry(stop=stop_after_attempt(3),
           wait=wait_fixed(3)+wait_exponential(min=1, max=16))
    def __get_remote_content(self) -> Response:
        """
        Get the content at the remote source.

        Returns:
            Response object from this object's remote source.
        """

        return get(self.remote_source, timeout=10)


    def download(self) -> None:
        """
        Download the specified remote file from the TCM CardTypes
        GitHub, and write it to a temporary local file.

        Raises:
            ValueError: The Response is not OK.
        """

        # Download remote file
        content = self.__get_remote_content()

        # Verify content is valid
        if not content.ok or not content.content:
            log.error(f'Failed to download RemoteFile ({content.text})')
            raise ValueError('File does not exist')

        # Write content to file
        with self.local_file.open('wb') as file_handle:
            file_handle.write(content.content)


    @staticmethod
    def reset_loaded_database() -> None:
        """Reset (clear) this class's global set of loaded remote files."""

        global _loaded_files
        _loaded_files.clear()
        log.debug('Reset global loaded files set')


class RemoteCardType:
    """
    This class defines a remote (or local) CardType. This is an
    encapsulation of a CardType class that, rather than being built-in,
    either queries the TCM GitHub for Python classes to dynamically
    inject in the modules namespace, or loads an arbitrary Python file.
    """

    """Base URL for all remote Card Type files to download"""
    URL_BASE = config.CARD_TYPE_REPOSITORY.removesuffix('/')

    """Temporary directory all card types are written to"""
    TEMP_DIR = Path(__file__).parent / '.objects'


    __slots__ = ('card_class', 'valid', 'source')


    def __init__(self,
            /,
            identifier: str | Path,
            file_hash: str | None = None,
        ) -> None:
        """
        Construct a new RemoteCardType. This downloads the source file
        at the specified location and loads it as a class in the global
        modules, under the interpreted class name. If the given
        identifier specification is a file that exists, that file is
        loaded.

        Args:
            identifier: Local filepath to the card class or the URL to
                remote card to inject. If a remote class, it must be
                specified like `{username}/{class_name}`.
            file_hash: MD5 hash of the file contents for the associated
                remote card. Not required if `identifier` is associated
                with a local file.
        """

        # Get database of loaded assets/cards
        self.card_class: type[BaseCardType] | None = None
        self.source: Literal['local', 'remote'] = 'remote'
        self.valid = True

        # If local file has been specified, get class name from the file
        if (file := CleanPath(identifier).sanitize()).exists():
            class_name = file.stem
            file_name = str(file.resolve())
            self.source = 'local'
        else:
            # Get username and class name from the identifier specification
            username = str(identifier).split('/')[0]
            class_name = str(identifier).split('/')[-1]

            # Download and write the CardType class into a temporary file
            file_name = self.TEMP_DIR / f'{username}-{class_name}.py'
            url = f'{self.URL_BASE}/{identifier}.py'

            # Make GET request for the contents of the specified value
            log.trace(f'Querying card from "{url}"')
            try:
                if (response := get(url, timeout=30)).status_code >= 400:
                    log.error(f'Cannot identify Card Type "{identifier}"')
                    log.debug((
                        f'Error querying card from {url} '
                        f'({response.content.decode()})'
                    ))
                    self.valid = False
                    return None
            except Exception:
                log.exception(f'Error querying card from "{url}"')
                self.valid = False
                return None

            # Validate hash of downloaded file (if present)
            if file_hash:
                if file_hash == (hash_act := md5(response.content).hexdigest()):
                    log.trace((
                        f'CardType "{identifier}" has matching MD5 hash of '
                        f'{file_hash}'
                    ))
                # Hash does not match, set invalid
                else:
                    log.error((
                        f'CardType "{identifier}" MD5 hash does not match '
                        f'{file_hash} ({hash_act}) - not loading CardType'
                    ))
                    self.valid = False
                    return None

            # Write identifier file contents to temporary class file
            self.source = 'remote'
            file_name.parent.mkdir(parents=True, exist_ok=True)
            with (file_name).open('wb') as fh:
                fh.write(response.content)

        # Import new file as module
        try:
            # Create module for newly loaded file
            if ((spec := spec_from_file_location(class_name, file_name)) is None
                or spec.loader is None):
                raise KeyError
            module = module_from_spec(spec)
            sys.modules[class_name] = module
            spec.loader.exec_module(module)

            # Get class from module namespace
            self.card_class = module.__dict__[class_name]

            # Validate that each RemoteFile of this class loaded correctly
            for attribute_name in dir(self.card_class):
                attribute = getattr(self.card_class, attribute_name)
                if isinstance(attribute, RemoteFile):
                    self.valid &= attribute.valid

            # Validate UI requirements
            self.__validate_ui_requirements(identifier)

            # Add this url to the loaded database
            if self.valid:
                log.debug(f'Loaded RemoteCardType "{identifier}"')
        # Error looking for module under class name - likely bad naming
        except KeyError:
            log.exception((
                f'Cannot load CardType "{identifier}" - cannot identify Card '
                f'class. Ensure there is a Class of the same name as the file '
                f'itself.'
            ))
            self.valid = False
        # Some error in loading, set object as invalid
        except Exception:
            log.exception(f'Cannot load CardType "{identifier}"')
            self.valid = False

        return None


    def __validate_ui_requirements(self,
            identifier: str | Path,
            /,
        ) -> None:
        """
        Validate this object's Card class UI requirements and update the
        object's validity.

        Args:
            identifier: Identifier of the (or path to the) Card class
                being validated.
        """

        if not self.card_class:
            return None

        # Validate the API implementation details are there
        if not issubclass(self.card_class, BaseCardType):
            log.error((
                f'CardType "{identifier}" must be is a subclass of '
                f'modules.BaseCardType.BaseCardType'
            ))
            self.valid = False

        if not hasattr(self.card_class, 'CardModel'):
            log.error((
                f'CardType "{identifier}" is missing the required CardModel '
                f'object'
            ))
            self.valid = False

        if (hasattr(self.card_class, 'CardModel')
            and not issubclass(self.card_class.CardModel, Base)):
            log.error((
                f'CardType "{identifier}" CardModel is invalid - must be a '
                f'Pydantic model'
            ))
            self.valid = False
