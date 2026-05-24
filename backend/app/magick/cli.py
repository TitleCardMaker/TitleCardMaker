from json import dumps as json_dumps
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.cards.base import BaseCardType
from app.logging.logger import log
from app.magick.base import ImageMaker
from app.schemas.base import BaseCardModel


def _cli_param_key(val: str, /) -> str:
    """Convert a CLI flag name to a validator keyword argument."""

    return val.lstrip('-').replace('-', '_')


def _parse_cli_params(args: list[str], /) -> dict[str, Any]:
    """
    Parse `--key value` pairs from CLI positional arguments.

    Flags without a following value are treated as ``True`` (for boolean
    options such as ``--borderless``).
    """

    params: dict[str, Any] = {}
    i = 0
    while i < len(args):
        key = _cli_param_key(args[i])
        if i + 1 < len(args) and not args[i + 1].startswith('-'):
            params[key] = args[i + 1]
            i += 2
        else:
            params[key] = True
            i += 1

    return params


def _schema_type_label(info: dict[str, Any], /) -> str:
    """
    Get the type label for a validator parameter.

    Args:
        info: The info dictionary for the validator parameter.

    Returns:
        The type label for the validator parameter.
    """

    if info.get('format') == 'path':
        return 'path'

    if field_type := info.get('type'):
        return field_type

    if any_of := info.get('anyOf'):
        types = [
            option.get('type')
            for option in any_of
            if option.get('type') != 'null'
        ]
        if any(option.get('type') == 'null' for option in any_of):
            return ' | '.join(types) + ' | null'
        return ' | '.join(types)

    return 'unknown'


def _format_validator_params(
        validator_model: type[BaseModel],
        /,
        *,
        as_json: bool = False,
    ) -> str:
    """
    Format the parameters accepted by a card or poster validator model.
    """

    schema = validator_model.model_json_schema()
    if as_json:
        return json_dumps(schema, indent=2)

    properties = schema.get('properties', {})
    required = set(schema.get('required', []))
    lines: list[str] = []

    for name, info in properties.items():
        flag = f'--{name.replace("_", "-")}'
        requirement = 'required' if name in required else 'optional'
        type_label = _schema_type_label(info)
        default = info.get('default')
        default_suffix = (
            f', default={default!r}'
            if default is not None and name not in required
            else ''
        )
        line = f'  {flag} ({requirement}, {type_label}{default_suffix})'
        if description := info.get('description'):
            line += f'\n      {description}'
        lines.append(line)

    return '\n'.join(lines)


def add_poster_cli(
        dname: str,
        /,
        poster_type: type[ImageMaker],
        validator_model: type[BaseModel],
    ) -> None:
    """
    Add CLI functionality for the given poster type.

    Args:
        dname: Name of the module to run poster creation from - this
            should be provided via `__name__`.
        poster_type: Poster type whose `__init__()` and `create()`
            methods will be called during poster creation.
        validator_model: Pydantic model to use for validation of the
            poster creation arguments.
    """

    # Only add CLI functionality if not running as a module - i.e. the
    # poster file was run from the command line
    if dname != '__main__':
        return None

    import click

    @click.group()
    def cli():
        """Create posters from the command line."""

    @cli.command(context_settings={
        'ignore_unknown_options': True,
        'allow_extra_args': True,
    })
    @click.pass_context
    def create(ctx: click.Context) -> None:
        """
        Create a poster from the given arguments.

        Run ``params`` on this module to list accepted arguments.

        Example:

            python -m app.magick.posters.genre create \\
                --source input.jpg \\
                --genre Action \\
                --output output.jpg
        """

        params = _parse_cli_params(list(ctx.args))
        poster_maker = poster_type(**validator_model(**params).model_dump())
        poster_maker.create()
        poster_maker.image_magick.print_command_history()

    @cli.command('params')
    @click.option(
        '--json',
        'as_json',
        is_flag=True,
        help='Print JSON Schema instead of a summary.',
    )
    def params_cmd(as_json: bool) -> None:
        """List parameters accepted by the ``create`` command."""

        click.echo(_format_validator_params(validator_model, as_json=as_json))

    cli()


class PreviewCard(BaseModel):
    filename: str
    variables: dict[str, Any]

class CardDocumentation(BaseModel):
    static_variables: dict[str, Any]
    cards: list[PreviewCard] = []
    extension: str = '.webp'


def add_card_cli(
        dname: str,
        /,
        card_type: type[BaseCardType],
        validator_model: type[BaseCardModel],
        *,
        documentation: CardDocumentation | None = None,
    ) -> None:
    """
    Add CLI functionality for the given card type.

    Args:
        dname: Name of the module to run the card creation from - this
            should be provided via `__name__`.
        card_type: Card type whose `__init__()` and `create()` methods
            will be called during card creation.
        validator_model: Pydantic model to use for validation of the
            card creation arguments.
        documentation: Definition of how to create card documentation
            assets for this card. If provided, a `docs` command will be
            added.
    """

    # Only add CLI functionality if not running as a module - i.e. the
    # card file was run from the command line
    if dname != '__main__':
        return None

    import click

    @click.group()
    def cli():
        """Create cards from the command line."""

    @cli.command(context_settings={
        'ignore_unknown_options': True,
        'allow_extra_args': True,
    })
    @click.pass_context
    def card(ctx: click.Context) -> None:
        """
        Create a card from the given arguments.

        Run ``params`` on this module to list accepted arguments.

        Example:

            python -m app.cards.types.Standard card \\
                --source-file input.jpg \\
                --card-file output.jpg \\
                --title-text "Episode Title" \\
                --season-text "SEASON 1" \\
                --episode-text "EPISODE 1"
        """

        params = _parse_cli_params(list(ctx.args))
        card_maker = card_type(**validator_model(**params).model_dump())
        card_maker.create()
        card_maker.image_magick.print_command_history()

    @cli.command('params')
    @click.option(
        '--json',
        'as_json',
        is_flag=True,
        help='Print JSON Schema instead of a summary.',
    )
    def params_cmd(as_json: bool) -> None:
        """List parameters accepted by the ``card`` command."""

        click.echo(_format_validator_params(validator_model, as_json=as_json))


    @click.option(
        '--source', '-s', 'source_file',
        required=True,
        type=click.Path(exists=True),
        help='Path to the source image to use for the documentation cards',
    )
    @click.option(
        '--output', '-o', 'output_dir',
        required=True,
        type=click.Path(file_okay=False),
        help='Output directory to save the documentation cards',
    )
    @click.option('--logo-file', '-l', 'logo_file',
        required=False,
        type=click.Path(exists=True),
        help='Path to the logo file to use for the documentation cards',
    )
    @click.option(
        '--debug', '-d', 'debug',
        is_flag=True,
        help='Enable debug mode',
    )
    def docs(
            source_file: Path,
            output_dir: Path,
            logo_file: Path | None = None,
            debug: bool = False,
        ) -> None:
        """
        Create the documentation preview images.
        Example:
            python app.py docs -s input.jpg -o ./out
        """

        if documentation is None:
            return None

        (output_dir := Path(output_dir)).mkdir(parents=True, exist_ok=True)
        for preview_card in documentation.cards:
            # Combine static variables with preview card variables
            kwargs = documentation.static_variables | preview_card.variables
            kwargs['source_file'] = source_file
            kwargs['card_file'] = (
                output_dir / preview_card.filename
            ).with_suffix(documentation.extension)
            if logo_file is not None:
                kwargs['logo_file'] = logo_file

            # Create card
            card_maker = card_type(**validator_model(**kwargs).model_dump())
            card_maker.create()
            log.info(f'Created "{kwargs["card_file"].relative_to(output_dir)}"')

            if debug:
                log.debug(f'{kwargs = !r}')
                card_maker.image_magick.print_command_history()

    if documentation is not None:
        cli.add_command(cli.command(docs))

    cli()
