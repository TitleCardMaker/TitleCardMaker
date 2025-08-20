from pathlib import Path
from re import sub as re_sub, IGNORECASE
from typing import Any, Iterable, Optional, TYPE_CHECKING

from sqlalchemy import JSON, String, event
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.logging.logger import log # noqa: F401
from app.schemas.blueprint import BlueprintFont
from app.schemas.font import TitleCase
from app.settings import settings


if TYPE_CHECKING:
    from sqlalchemy.event import Events
    from app.models.episode import Episode
    from app.models.series import Series
    from app.models.template import Template


class Font(Base):
    """
    SQL Table that defines a Named Font. This contains Font
    customizations, as well as relational objects to linked Episodes,
    Series, and Templates.
    """

    __tablename__ = 'font'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    episodes: Mapped[list['Episode']] = relationship(back_populates='font')
    series: Mapped[list['Series']] = relationship(back_populates='font')
    templates: Mapped[list['Template']] = relationship(back_populates='font')

    name: Mapped[str]
    sort_name: Mapped[str] = mapped_column(index=True)
    color: Mapped[Optional[str]]
    file_name: Mapped[Optional[str]]
    interline_spacing: Mapped[int] = mapped_column(default=0)
    interword_spacing: Mapped[int] = mapped_column(default=0)
    kerning: Mapped[float] = mapped_column(default=1.0)
    replacements_in: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON), # type: ignore
        default=[],
    )
    replacements_out: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON), # type: ignore
        default=[],
    )
    size: Mapped[float] = mapped_column(default=1.0)
    stroke_width: Mapped[float] = mapped_column(default=1.0)
    title_case: Mapped[Optional[TitleCase]] = mapped_column(String,default=None)
    vertical_shift: Mapped[int] = mapped_column(default=0)
    line_split_modifier: Mapped[int] = mapped_column(default=0)


    def __repr__(self) -> str:
        return f'Font[{self.id}] "{self.name}"'


    @property
    def file(self) -> Optional[Path]:
        """
        Get the name of this Font's file, if indicated.  None if this
        Font has no file, or if the file does not exist.
        """

        if self.file_name is None:
            return None

        font_directory = settings.asset_directory / 'fonts'
        if not (file := font_directory / str(self.id)/ self.file_name).exists():
            return None

        return file


    @staticmethod
    def apply_replacements(
            text: str,
            in_: Iterable[str],
            out_: Iterable[str],
            *,
            pre: bool,
        ) -> str:
        """
        Apply the given paired lists of character replacements to the
        given text.

        Args:
            text: Input text to apply replacements to.
            in_: List of input strings to sequentially replace.
            out_: List of output strings to replace with.
            pre: Whether this is a pre-replacement. If True, all `post:`
                prefixed replacements are skipped; if False all `pre:`
                replacements are skipped.

        Returns:
            Modified text.
        """

        for repl_in, repl_out in zip(in_, out_):
            # Skip replacements from pre if post; and from post if pre
            if ((pre and repl_in.startswith('post:'))
                or (not pre and repl_in.startswith('pre:'))):
                continue

            # Skip pre: and post: prefix in replacement
            if repl_in.startswith('pre:'):
                repl_in = repl_in[4:]
            elif repl_in.startswith('post:'):
                repl_in = repl_in[5:]

            text = text.replace(repl_in, repl_out)

        return text


    @property
    def card_properties(self) -> dict[str, Any]:
        """Properties to utilize and merge in Title Card creation."""

        if (file := self.file) is None:
            return {
                f'font_{key}': value
                for key, value in self.__dict__.items()
                if not key.startswith('_')
            }

        return {
            f'font_{key}': value
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        } | {'font_file': str(file)}


    @property
    def export_properties(self) -> dict[str, Any]:
        """
        Properties to export in Blueprints. These properties can be used
        in a NewNamedFont model to recreate this object.
        """

        if self.line_split_modifier == 0:
            modifier = None
        else:
            modifier = self.line_split_modifier

        return {
            'name': self.name,
            'color': self.color,
            'file': self.file_name,
            'interline_spacing': self.interline_spacing or None,
            'interword_spacing': self.interword_spacing or None,
            'kerning': None if self.kerning == 1.0 else self.kerning,
            'line_split_modifier': modifier,
            'replacements_in': self.replacements_in,
            'replacements_out': self.replacements_out,
            'size': None if self.size == 1.0 else self.size,
            'stroke_width': None if self.stroke_width == 1.0 else self.stroke_width,
            'title_case': self.title_case,
            'vertical_shift': self.vertical_shift or None,
        }


    def equals(self, other: BlueprintFont, /) -> bool:
        """
        Determine whether this Font is equivalent to another.

        Args:
            other: The other Font being evaluated.

        Returns:
            True if the Font is equivalent, False otherwise.
        """

        other_dict = other.model_dump(exclude_unset=True)

        return (
            self.color == other_dict.get('color', None)
            and self.file_name == other_dict.get('file', None)
            and self.interline_spacing == other_dict.get('interline_spacing', 0)
            and self.interword_spacing == other_dict.get('interword_spacing', 0)
            # Do not evaluate since these frequently change
            # and self.replacements_in == 
            # and self.replacements_out == 
            and self.kerning == other_dict.get('kerning', 1.0)
            and self.size == other_dict.get('size', 1.0)
            and self.stroke_width == other_dict.get('stroke_width', 1.0)
            and self.title_case == other_dict.get('title_case', None)
            and self.vertical_shift == other_dict.get('vertical_shift', 0)
            and self.line_split_modifier == other_dict.get('line_split_modifier', 0)
        )


@event.listens_for(Font.name, 'set')
def set_font_sort_name(
        target: Font,
        value: str,
        oldvalue: str,
        initiator: 'Events',
    ) -> None:
    """Update the Font sort name when the name attribute is modified."""

    target.sort_name = re_sub(
        r'^(a|an|the)(\s)',
        '',
        value.lower(),
        flags=IGNORECASE
    )
