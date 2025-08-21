from hashlib import md5
from importlib.util import spec_from_file_location, module_from_spec
import sys
from typing import Literal

from pathlib import Path
from requests import get
from tinydb import where

from app.core.config import config
from app.logging.logger import Logger, log
from app.schemas.base import Base
from modules.BaseCardType import BaseCardType
from modules.CleanPath import CleanPath
from modules.PersistentDatabase import PersistentDatabase
from modules.RemoteFile import RemoteFile


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
            *,
            log: Logger = log,
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
            log: Logger for all log messages.
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
            if (response := get(url, timeout=30)).status_code >= 400:
                log.error(f'Cannot identify Card Type "{identifier}"')
                log.debug(
                    f'Error querying card from {url} '
                    f'({response.content.decode()})'
                )
                self.valid = False
                return None

            # Validate hash of downloaded file (if present)
            if file_hash:
                if file_hash == (hash_act := md5(response.content).hexdigest()):
                    log.trace(
                        f'CardType "{identifier}" has matching MD5 hash of '
                        f'{file_hash}'
                    )
                # Hash does not match, set invalid
                else:
                    log.error(
                        f'CardType "{identifier}" MD5 hash does not match '
                        f'{file_hash} ({hash_act}) - not loading CardType'
                    )
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
            log.exception(
                f'Cannot load CardType "{identifier}" - cannot identify Card '
                f'class. Ensure there is a Class of the same name as the file '
                f'itself.'
            )
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
            log.error(
                f'CardType "{identifier}" must be is a subclass of '
                f'modules.BaseCardType.BaseCardType'
            )
            self.valid = False

        if not hasattr(self.card_class, 'CardModel'):
            log.error(
                f'CardType "{identifier}" is missing the required CardModel '
                f'object'
            )
            self.valid = False

        if (hasattr(self.card_class, 'CardModel')
            and not issubclass(self.card_class.CardModel, Base)):
            log.error(
                f'CardType "{identifier}" CardModel is invalid - must be a '
                f'Pydantic model'
            )
            self.valid = False


class RemoteCardTypeV1:
    """
    This class defines a remote CardType. This is an encapsulation of a
    CardType class that, rather than being defined locally, queries the
    Maker GitHub for Python classes to dynamically inject in the modules
    namespace.
    """

    """Base URL for all remote Card Type files to download"""
    URL_BASE = (
        'https://raw.githubusercontent.com/CollinHeist/'
        'TitleCardMaker-CardTypes/master'
    )

    """Temporary directory all card types are written to"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    """Database of assets that have been loaded already this run"""
    LOADED = 'remote_assets.json'

    __slots__ = ('loaded', 'card_class', 'valid')


    def __init__(self, remote: str) -> None:
        """
        Construct a new RemoteCardType. This downloads the source file
        at the specified location and loads it as a class in the global
        modules, under the interpreted class name. If the given remote
        specification is a file that exists, that file is loaded.

        Args:
            database_directory: Base Path to read/write any databases
                from.
            remote: URL to remote card to inject. Should omit repo base.
                Should be specified like {username}/{class_name}. Can
                also be a local filepath.
        """

        # Get database of loaded assets/cards
        self.card_class: BaseCardType | None = None
        self.loaded = PersistentDatabase(self.LOADED)
        self.valid = True

        # If local file has been specified..
        if (file := CleanPath(remote).sanitize()).exists():
            # Get class name from file
            class_name = file.stem
            file_name = str(file.resolve())
        else:
            # Get username and class name from the remote specification
            username = remote.split('/', maxsplit=1)[0]
            class_name = remote.split('/')[-1]

            # Download and write the CardType class into a temporary file
            file_name = self.TEMP_DIR / f'{username}-{class_name}.py'
            url = f'{self.URL_BASE}/{remote}.py'

            # Only request and write file if not loaded this run
            if (not self.loaded.get(where('remote') == url)
                or not file_name.exists()):
                # Make GET request for the contents of the specified value
                if (response := get(url, timeout=30)).status_code >= 400:
                    log.error(f'Cannot identify remote Card Type "{remote}"')
                    self.valid = False
                    return None

                # Write remote file contents to temporary class
                file_name.parent.mkdir(parents=True, exist_ok=True)
                with (file_name).open('wb') as fh:
                    fh.write(response.content)

        # Import new file as module
        try:
            # Create module for newly loaded file
            spec = spec_from_file_location(class_name, file_name)
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

            # Add this url to the loaded database
            try:
                self.loaded.insert({'remote': url})
                log.debug(f'Loaded RemoteCardType "{remote}"')
            except Exception:
                pass
        except Exception as e:
            # Some error in loading, set object as invalid
            log.error(f'Cannot load CardType "{remote}", returned "{e}"')
            self.card_class = None
            self.valid = False
        return None
