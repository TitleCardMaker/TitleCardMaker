from json import dumps
from pathlib import Path
from sys import exit as sys_exit
from typing import NamedTuple

from fastapi import HTTPException

from app.interfaces.base import Interface
from app.interfaces.web import WebInterface
from app.logging.logger import Logger, log


class IntegratedStatus(NamedTuple):
    recently_added: bool
    watched: bool


class TautulliInterface(WebInterface, Interface):
    """
    This class describes an interface to Tautulli. This interface can
    configure notification agents within Tautulli to enable fast card
    updating/creation.
    """

    INTERFACE_TYPE: str = 'Tautulli'

    """Default configurations for the notification agent(s)"""
    DEFAULT_AGENT_NAME = 'Update TitleCardMaker (v3)'

    """Agent ID for a Webhook"""
    AGENT_ID = 25


    def __init__(self,
            tcm_url: str,
            tautulli_url: str,
            api_key: str,
            plex_interface_id: int,
            use_ssl: bool = True,
            agent_name: str = DEFAULT_AGENT_NAME,
            trigger_watched: bool = True,
            username: str | None = None,
            *,
            log: Logger = log,
        ) -> None:
        """
        Construct a new instance of an interface to Sonarr.

        Args:
            tcm_url: Base URL of TitleCardMaker for the API endpoint.
            tautulli_url: The API URL for interfacing with Tautulli.
            api_key: The API key for API requests.
            use_ssl: Whether to use SSL for the interface.
            agent_name: Name of the Notification Agent to check for and/
                or create on Tautulli.
            trigger_watched: Whether to create a second agent to trigger
                for recently watched episodes.
            username: User whose watched content should trigger the
                recently watched agent (if indicated).
            log: Logger for all log messages.

        Raises:
            HTTPException (400): Tautulli cannot be connected to.
            HTTPException (401): Tautulli's status cannot be queried.
            HTTPException (422): The URL is invalid.
        """

        # Initialize parent classes
        super().__init__('Tautulli', use_ssl, cache=False)

        # Get correct TCM URL
        tcm_url = tcm_url.removesuffix("/")
        self.tcm_url = f'{tcm_url}/api/v2/webhooks/plex/rating-key?' \
            + f'interface_id={plex_interface_id}'

        # Get correct Tautulli URL
        tautulli_url = tautulli_url.removesuffix('/') + '/'
        if tautulli_url.endswith('/api/v2/'):
            self.tautulli_url = tautulli_url
        elif (re_match := self._URL_REGEX.match(tautulli_url)) is None:
            raise HTTPException(
                status_code=422,
                detail='Invalid Tautulli URL'
            )
        else:
            self.tautulli_url = f'{re_match.group(1)}/api/v2/'

        # Base parameters for sending requests to Sonarr
        self.__params = {'apikey': api_key}

        # Query system status to verify connection to Tautulli
        try:
            status = self.get(
                self.tautulli_url,
                self.__params | {'cmd': 'status'}
            )
            if status.get('response', {}).get('result') != 'success':
                log.debug(f'Tautulli returned response: {status}')
                raise HTTPException(
                    status_code=401,
                    detail=f'Invalid Tautulli URL or API key'
                )
        except Exception as exc:
            log.exception(f'Tautulli connection error')
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Tautulli',
            ) from exc

        # Store attributes
        self._name = agent_name
        self._trigger_watched = trigger_watched
        self._username = username
        self.activate()


    def is_integrated(self) -> IntegratedStatus:
        """
        Check if this interface's Tautulli instance already has both
        integrations set up.

        Returns:
            Tuple of whether the recently added and watched Notification
            Agents have been created.
        """

        # Get all notifiers
        response = self.get(
            self.tautulli_url,
            self.__params | {'cmd': 'get_notifiers'}
        )
        notifiers = response['response']['data']

        # Integrated if any active Webhook agent has this name
        return IntegratedStatus(
            any(
                agent['agent_label'] == 'Webhook'
                and agent['friendly_name'] == f'{self._name} - Recently Added'
                and agent['active'] == 1
                for agent in notifiers
            ),
            any(
                agent['agent_label'] == 'Webhook'
                and agent['friendly_name'] == f'{self._name} - Watched'
                and agent['active'] == 1
                for agent in notifiers
            ),
        )


    def __create_agent(self, *, log: Logger = log) -> int | None:
        """
        Create a new Notification Agent. The created agent will be blank
        and of the Webhook type.

        Args:
            log: Logger for all log messages.

        Returns:
            Notifier ID of created agent, None if agent was not created.
        """

        # Get all existing notifier ID's
        response = self.get(
            self.tautulli_url,
            self.__params | {'cmd': 'get_notifiers'}
        )['response']['data']
        existing_ids: set[int] = {agent['id'] for agent in response}

        # Create new notifier
        params = {'cmd': 'add_notifier_config', 'agent_id': self.AGENT_ID}
        self.get(self.tautulli_url,  self.__params | params)

        # Get notifier ID's after adding new one
        response = self.get(
            self.tautulli_url,
            self.__params | {'cmd': 'get_notifiers'}
        )['response']['data']
        new_ids: set[int] = {agent['id'] for agent in response}

        # If no new ID's are returned
        if len(new_ids - existing_ids) == 0:
            log.error(f'Failed to create new notification agent on Tautulli')
            return None

        # Get ID of created notifier
        return list(new_ids - existing_ids)[0]


    def integrate(self, *, log: Logger = log) -> None:
        """
        Integrate this interface's instance of Tautulli with TCM. This
        configures a new notification agent if a valid one does not
        exist or cannot be identified.

        Args:
            log: Logger for all log messages.
        """

        integrated = self.is_integrated()
        if not integrated.recently_added:
            # Create Agent, raise if fails
            if (created_id := self.__create_agent(log=log)) is None:
                raise HTTPException(
                    status_code=400,
                    detail='Failed to create Notification Agent',
                )

            # Only condition is that the content be a show, season, or episode
            conditions = [{
                'parameter': 'media_type',
                'operator':  'is',
                'value':     ['show', 'season', 'episode'],
                'type':      'str',
            }]

            # Configure this Agent
            params = self.__params | {
                # API arguments
                'cmd': 'set_notifier_config',
                'notifier_id': created_id,
                'agent_id': self.AGENT_ID,
                # Agent Configuration
                'friendly_name': f'{self._name} - Recently Added',
                'webhook_hook': self.tcm_url,
                'webhook_method': 'POST',
                # Agent Triggers
                'on_created': 1,
                # Agent Conditions
                'custom_conditions': dumps(conditions),
                # POST Arguments
                'on_created_body': '"{rating_key}"',
            }
            self.get(self.tautulli_url, params)
            log.info(
                f'Created and configured Recently Added Tautulli Notification '
                f'Agent {created_id}'
            )
        else:
            log.debug('Recently Added Tautulli integration detected')

        if self._trigger_watched and not integrated.watched:
            # Create Agent, raise if fails
            if (created_id := self.__create_agent(log=log)) is None:
                raise HTTPException(
                    status_code=400,
                    detail='Failed to create Notification Agent',
                )

            # Only trigger on Episodes; add condition for username match if
            # indicated
            conditions = [{
                'parameter': 'media_type',
                'operator':  'is',
                'value':     ['episode'],
                'type':      'str',
            }] + (
                [{
                    'parameter': 'username',
                    'operator': 'is',
                    'value': [self._username],
                    'type': 'str',
                }]
                if self._username else []
            )

            # Configure this Agent
            params = self.__params | {
                # API arguments
                'cmd': 'set_notifier_config',
                'notifier_id': created_id,
                'agent_id': self.AGENT_ID,
                # Agent Configuration
                'friendly_name': f'{self._name} - Watched',
                'webhook_hook': self.tcm_url,
                'webhook_method': 'POST',
                # Agent Triggers
                'on_watched': 1,
                # Agent Conditions
                'custom_conditions': dumps(conditions),
                # POST Arguments
                'on_watched_body': '"{rating_key}"',
            }
            self.get(self.tautulli_url, params)
            log.info(
                f'Created and configured Watched Tautulli Notification Agent '
                f'{created_id}'
            )
        elif self._trigger_watched:
            log.debug('Watched Tautulli integration detected')


class TautulliInterfaceV1(WebInterface):
    """
    This class describes an interface to Tautulli. This interface can
    configure notification agents within Tautulli to enable fast card
    updating/creation.
    """

    """Default configurations for the notification agent(s)"""
    DEFAULT_AGENT_NAME = 'Update TitleCardMaker'
    DEFAULT_SCRIPT_TIMEOUT = 30

    """Agent ID for a custom Script"""
    AGENT_ID = 15


    def __init__(self,
            url: str,
            api_key: str,
            verify_ssl: bool,
            update_script: Path,
            agent_name: str = DEFAULT_AGENT_NAME,
            script_timeout: int = DEFAULT_SCRIPT_TIMEOUT,
            username: str | None = None
        ) -> None:
        """
        Construct a new instance of an interface to Sonarr.

        Args:
            url: The API url communicating with Tautulli.
            api_key: The API key for API requests.
            verify_ssl: Whether to verify SSL requests.

        Raises:
            SystemExit: Invalid Sonarr URL/API key provided.
        """

        # Initialize parent WebInterface
        super().__init__('Tautulli', verify_ssl, cache=False)

        # Get correct URL
        url = url if url.endswith('/') else f'{url}/'
        if url.endswith('/api/v2/'):
            self.url = url
        elif (re_match := self._URL_REGEX.match(url)) is None:
            log.critical(f'Invalid Tautulli URL "{url}"')
            sys_exit(1)
        else:
            self.url = f'{re_match.group(1)}/api/v2/'

        # Base parameters for sending requests to Sonarr
        self.__params = {'apikey': api_key}

        # Query system status to verify connection to Tautulli
        try:
            status = self.get(self.url, self.__params | {'cmd': 'status'})
            if status.get('response', {}).get('result') != 'success':
                log.critical(f'Cannot get Tautulli status - invalid URL/API key')
                sys_exit(1)
        except Exception as e:
            log.critical(f'Cannot connect to Tautulli - returned error: "{e}"')
            sys_exit(1)

        # Store attributes
        self.update_script = update_script
        self.agent_name = agent_name
        self.script_timeout = script_timeout
        self.username = username

        # Warn if invalid timeout was provided
        if self.script_timeout < 0:
            log.error(f'Script timeout must be >= 0 (seconds) - using 0')
            self.script_timeout = 0


    def is_integrated(self) -> tuple[bool, bool]:
        """
        Check if this interface's Tautulli instance already has
        integration set up.

        Returns:
            Tuple of booleans. First value is True if the watched agent
            is already integrated (False otherwise); second value is
            True if the newly added agent is already integrated (False
            otherwise).
        """

        # Get all notifiers
        response = self.get(self.url, self.__params | {'cmd': 'get_notifiers'})
        notifiers = response['response']['data']

        # Check each agent's name
        watched_integrated, created_integrated = False, False
        for agent in notifiers:
            # Exit loop if both agents found
            if watched_integrated and created_integrated:
                break

            # If agent is a Script with the right name..
            if (agent['agent_label'] == 'Script'
                and agent['friendly_name'].startswith(self.agent_name)):
                # Get the config of this agent, check action flags
                params = self.__params | {'cmd': 'get_notifier_config',
                                          'notifier_id': agent['id']}
                response = self.get(self.url, params)['response']['data']
                if response['actions']['on_watched'] == 1:
                    watched_integrated = True
                if response['actions']['on_created'] == 1:
                    created_integrated = True

        return watched_integrated, created_integrated


    def __create_agent(self) -> int | None:
        """
        Create a new Notification Agent.

        Returns:
            Notifier ID of created agent, None if agent was not created.
        """

        # Get all existing notifier ID's
        response = self.get(self.url, self.__params | {'cmd': 'get_notifiers'})
        existing_ids = {agent['id'] for agent in response['response']['data']}

        # Create new notifier
        params = {'cmd': 'add_notifier_config', 'agent_id': self.AGENT_ID}
        self.get(self.url,  self.__params | params)

        # Get notifier ID's after adding new one
        response = self.get(self.url, self.__params | {'cmd': 'get_notifiers'})
        new_ids = {agent['id'] for agent in response['response']['data']}

        # If no new ID's are returned
        if len(new_ids - existing_ids) == 0:
            log.error(f'Failed to create new notification agent on Tautulli')
            return None

        # Get ID of created notifier
        return list(new_ids - existing_ids)[0]


    def integrate(self) -> None:
        """
        Integrate this interface's instance of Tautulli with TCM. This
        configures a new notification agent if a valid one does not
        exist or cannot be identified.
        """

        # If already integrated, skip
        watched_integrated, created_integrated = self.is_integrated()
        if watched_integrated and created_integrated:
            log.debug('Tautulli integrated detected')
            return None

        # Integrate watched agent if required
        if (not watched_integrated
            and (watched_id := self.__create_agent()) is not None):
            # Conditions for watched agent
            # Always add condition for the episode
            conditions = [{
                'parameter': 'media_type',
                'operator':  'is',
                'value':     ['episode'],
                'type':      'str',
            }]
            # If provided, add condition for username
            if self.username is not None:
                conditions.append({
                    'parameter': 'username',
                    'operator':  'is',
                    'value':     [self.username],
                    'type':      'str',
                })

            # Configure this agent
            friendly_name = f'{self.agent_name} - Watched'
            params = self.__params | {
                # API arguments
                'cmd': 'set_notifier_config',
                'notifier_id': watched_id,
                'agent_id': self.AGENT_ID,
                # Configuration
                'friendly_name': friendly_name,
                'scripts_script_folder': str(self.update_script.parent.resolve()),
                'scripts_script': str(self.update_script.resolve()),
                'scripts_timeout': self.script_timeout,
                # Triggers
                'on_watched': 1,
                # Conditions
                'custom_conditions': dumps(conditions),
                # Arguments
                'on_watched_subject': '{rating_key}',
            }
            self.get(self.url, params)
            log.info(f'Creatd and configured Tautulli notification agent '
                     f'{watched_id} ("{friendly_name}")')

        # Integrate created agent if required
        if (not created_integrated
            and (created_id := self.__create_agent()) is not None):
            # Conditions for new content is just a show/season/episode
            conditions = [{
                'parameter': 'media_type',
                'operator':  'is',
                'value':     ['show', 'season', 'episode'],
                'type':      'str',
            }]

            # Configure this agent
            friendly_name = f'{self.agent_name} - Recently Added'
            params = self.__params | {
                # API arguments
                'cmd': 'set_notifier_config',
                'notifier_id': created_id,
                'agent_id': self.AGENT_ID,
                # Configuration
                'friendly_name': friendly_name,
                'scripts_script_folder': str(self.update_script.parent.resolve()),
                'scripts_script': str(self.update_script.resolve()),
                'scripts_timeout': self.script_timeout,
                # Triggers
                'on_created': 1,
                # Conditions
                'custom_conditions': dumps(conditions),
                # Arguments
                'on_created_subject': '{rating_key}',
            }
            self.get(self.url, params)
            log.info(f'Created and configured Tautulli notification agent '
                     f'{created_id} ("{friendly_name}")')

        return None
