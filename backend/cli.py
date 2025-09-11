from datetime import datetime
from pathlib import Path
from re import match
from sys import exit as sys_exit
from time import sleep

import click
import schedule

from app.core.config import config
from app.logging.logger import log
from modules.PreferenceParser import PreferenceParser
from modules.RemoteFile import RemoteFile
from modules.Manager import Manager


def validate_runtime(ctx, param, value):
    """Validate the given argument is a valid runtime (e.g. HH:MM)"""

    if value is None:
        return value
    try:
        hour, minute = map(int, value.split(':'))
        if hour not in range(0, 24) or minute not in range(0, 60):
            raise ValueError
        return value
    except Exception as exc:
        raise click.BadParameter('Invalid time, specify as HH:MM') from exc


def validate_frequency(ctx, param, value):
    """Get the frequency dictionary of the given frequency string."""

    if value is None:
        return value
    try:
        interval, unit = match(r'(\d+)(s|m|h|d|w)', value).groups()
        interval, unit = int(interval), unit.lower()
        assert interval > 0 and unit in ('s', 'm', 'h', 'd', 'w')
        return {
            'interval': interval,
            'unit': {
                's': 'seconds',
                'm': 'minutes',
                'h': 'hours',
                'd': 'days',
                'w': 'weeks',
            }[unit],
        }
    except Exception as exc:
        raise click.BadParameter(
            'Invalid frequency, specify as FREQUENCY[unit], i.e. 12h -> 12 '
            'hours, 1d -> 1 day'
        ) from exc


def read_preferences(preference_file: Path):
    """
    Read the indicated Preferences file, and then update the global
    `PreferenceParser` object.
    """

    return PreferenceParser(preference_file, config.IS_DOCKER)


def run(preferences_file: Path, missing_file: Path):
    """
    Create and run the Manager object's main loop - e.g.
    `Manager.run()`. This also checks for a new version of TCM.
    """

    # Create Manager, run, and write missing report
    try:
        tcm = Manager(read_preferences(preferences_file))
        tcm.run()
        tcm.report_missing(missing_file)
    except PermissionError as error:
        log.critical(f'Invalid permissions - {error}')
        sys_exit(1)


def first_run(
        frequency_dict: dict,
        missing_file: Path,
    ) -> type[schedule.CancelJob]:
    """
    First Manager run that schedules subsequent runs and then cancels
    itself.
    """

    run(missing_file)
    interval, unit = frequency_dict['interval'], frequency_dict['unit']
    getattr(schedule.every(interval), unit).do(run, missing_file)
    log.debug(f'Scheduled run() every {interval} {unit}')

    return schedule.CancelJob


def read_update_list(preferences_file: Path, tautulli_list: Path):
    """Read the Tautull update list."""

    # If the file doesn't exist (nothing to parse), exit
    if not tautulli_list.exists():
        log.debug(f'Update list does not exist')
        return None

    # Read update list contents
    try:
        with tautulli_list.open('r') as file_handle:
            update_list = set(map(int, file_handle.readlines()))
        log.debug(f'Read update list ({update_list})')
    except ValueError:
        log.error(f'Error reading update list, skipping and deleting')
        tautulli_list.unlink(missing_ok=True)
        return None

    # Delete (clear) update list
    tautulli_list.unlink(missing_ok=True)

    # Remake all indicated cards
    Manager(
        read_preferences(preferences_file),
        check_tautulli=False
    ).remake_cards(update_list)


@click.group()
@click.option(
    '-p', '--preferences', '--preference-file',
    type=Path,
    default=config.V1_PREFERENCE_FILE,
    help='File to read global preferences from.')
@click.pass_context
def cli(ctx, preferences: PreferenceParser) -> None:
    """Start TitleCardMaker"""

    # Check if preference file exists
    if not preferences.exists():
        log.critical(f'Preference file "{preferences.resolve()}" does not exist')
        sys_exit(1)

    # Store objects in global namespace
    ctx.obj = {
        'preferences_file': preferences,
        'preferences': read_preferences(preferences),
    }

@cli.command()
@click.option(
    '-m', '--missing', '--missing-file',
    type=Path,
    default=config.V1_MISSING_FILE,
    help='File to write the list of missing assets to')
@click.pass_context
def run_once(ctx, missing):
    """Run the TitleCardMaker once"""

    log.info(f'Starting TitleCardMaker ({config.CURRENT_VERSION})')
    run(ctx.obj['preferences_file'], missing)

@cli.command()
@click.pass_context
def sync(ctx):
    """Sync without running"""

    Manager(
        read_preferences(ctx.obj['preferences_file']),
        check_tautulli=False
    ).sync_series_files()

@cli.command()
@click.option(
    '-t', '--runtime', '--time',
    callback=validate_runtime,
    default=config.V1_RUNTIME,
    help='When to first run TitleCardMaker (in 24-hour time).')
@click.option(
    '-f', '--frequency',
    callback=validate_frequency,
    default=config.V1_FREQUENCY,
    help=(
        'How often to run TitleCardMaker. Units can be s/m/h/d/w for '
        'seconds/minutes/hours/days/weeks.'
    ))
@click.option(
    '-m', '--missing', '--missing-file',
    type=Path,
    default=config.V1_MISSING_FILE,
    help='File to write the list of missing assets to')
@click.option(
    '-tl', '--tautulli-list', '--tautulli-update-list',
    type=Path,
    default=config.V1_TAUTULLI_LIST,
    help='File to monitor for Tautulli-driven episode watch-status updates')
@click.option(
    '-tf', '--tautulli-frequency', '--tautulli-update-frequency',
    callback=validate_frequency,
    default=config.V1_TAUTULLI_FREQUENCY,
    help=(
        'How often to check the Tautulli update list; units can be s/m/h/d/w '
        'for seconds/minutes/hours/days/weeks'
    ))
@click.pass_context
def schedule(ctx, runtime, frequency, missing, tautulli_list, tautulli_frequency):
    """Schedule TitleCardMaker to run periodically"""

    # Schedule first run
    if runtime:
        schedule.every().day.at(runtime).do(first_run, frequency, missing)
        log.info(f'Starting first run in {schedule.idle_seconds():,.0f} seconds')

    # Schedule reading the update list
    if tautulli_list:
        interval = tautulli_frequency['interval']
        unit = tautulli_frequency['unit']
        getattr(schedule.every(interval), unit).do(
            read_update_list,
            ctx.obj['preferences_file'],
            tautulli_list
        )
        log.debug(f'Scheduled read_update_list() every {interval} {unit}')

    # Infinite loop if either infinite argument was indicated
    if runtime or tautulli_list:
        while True:
            # Run schedule, sleep until next run
            schedule.run_pending()
            next_run = schedule.next_run().strftime("%H:%M:%S %Y-%m-%d")
            log.info(f'Sleeping until {next_run}')
            sleep(max(0, (schedule.next_run()-datetime.today()).total_seconds()))


if __name__ == '__main__':
    cli()
