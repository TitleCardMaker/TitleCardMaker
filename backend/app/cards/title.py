from functools import lru_cache
from typing import Literal

from app.logging.logger import log

type SplitStyle = Literal['top', 'bottom', 'even', 'forced even']


class Title:
    """
    This class describes a title. A Title can either be initialized with
    a full title without any formatting done to it, and then split by
    this class into multiple lines with `split()`; or it can be
    initialized with those lines directly. For example:

    >>> t = Title("The One Where Rachel's Sister Babysits")
    >>> t.split(25, 2, False)
    ["The One Where",
     "Rachel's Sister Babysits"]
    >>> t.split(25, 2, True)
    ["The One Where Rachel's",
     "Sister Babysits"]
    """

    """Characters that should be used for priority line splitting"""
    SPLIT_CHARACTERS = (':', ',', ')', ']', '?', '!', '-', '.', '/', '|')


    __slots__ = ('full_title', 'match_title')


    def __init__(self, title: str, /) -> None:
        """
        Constructs a new instance of a Title from a full, unsplit title.

        Args:
            title: Title for this object.
        """

        self.full_title = title
        self.match_title = self.get_matching_title(self.full_title)


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return self.full_title


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'<Title "{self.full_title}">'


    def __len__(self) -> int:
        """Length of this title (without splitting)."""

        return len(self.full_title)


    def __evenly_split(self) -> str:
        """
        Attempt to evenly split this Title between two lines of text.

        Returns:
            This title split evenly.
        """

        lines: list[list[str]] = [[], []]
        def len_l1() -> int:
            return sum(map(len, lines[0]))
        def len_l2() -> int:
            return sum(map(len, lines[1]))
        def diff() -> int:
            return abs(len_l2() - len_l1())

        # Add each word to the shortest line
        words = self.full_title.split()
        for word in words:
            # Always add word to end of last line
            lines[1].append(word)

            # While there is a last line, the first line is shorter than
            # the last, and the current line length difference is at
            # least twice the length of the next-popped word, move the
            # first word of the last line to last position on first line
            while (lines[1]
                   and len_l1() < len_l2()
                   and diff() >= 2 * len(lines[1][0])):
                lines[0].append(lines[1].pop(0))

        if not lines[0]:
            return '\n'.join(map(' '.join, lines[1:]))

        return '\n'.join(map(' '.join,  lines))


    def __top_split(self, max_line_width: int, max_line_count: int) -> str:
        """
        Args:
            max_line_width: Maximum line width to base splitting on.
            max_line_count: The maximum line count to split the title
                into.

        Returns:
            This title split top-style.
        """

        all_lines = [self.full_title]
        for _ in range(max_line_count+2-1):
            # Start splitting from the last line added
            top, bottom = all_lines.pop(), ''
            while ((len(top) > max_line_width
                    or len(bottom) in range(1, 6))
                    and ' ' in top):
                # Look to split on special characters
                special_split = False
                for char in self.SPLIT_CHARACTERS:
                    # Split only if present after first third of next line
                    if f'{char} ' in top[max_line_width//2:max_line_width]:
                        top, bottom_add = top.rsplit(f'{char} ', 1)
                        top += char
                        bottom = f'{bottom_add} {bottom}'
                        special_split = True
                        break

                # If no special character splitting was done, split on space
                if not special_split:
                    try:
                        top, bottom_add = top.rsplit(' ', 1)
                        bottom = f'{bottom_add} {bottom}'.strip()
                    except ValueError:
                        break

            all_lines += [top, bottom]

        # Strip every line, delete blank entries
        all_lines = list(filter(len, map(str.strip, all_lines)))

        # If misformatted, combine overflow lines
        if len(all_lines) > max_line_count:
            all_lines[-2] = f'{all_lines[-2]} {all_lines[-1]}'
            del all_lines[-1]

        return '\n'.join(all_lines)


    def __bottom_split(self, max_line_width: int, max_line_count: int) -> str:
        """
        Args:
            max_line_width: Maximum line width to base splitting on.
            max_line_count: The maximum line count to split the title
                into.

        Returns:
            This title split bottom style.
        """

        # For bottom heavy splitting, start on bottom and move text UP
        all_lines = [self.full_title]
        for _ in range(max_line_count+2-1):
            top, bottom = '', all_lines.pop()
            while (
                ' ' in bottom and
                (len(bottom) > max_line_width or len(top) in range(1, 6))
            ):
                # Look to split on special characters
                special_split = False
                for char in self.SPLIT_CHARACTERS:
                    if f'{char} ' in bottom[:min(max_line_width,len(bottom)//2)]:
                        top_add, bottom = bottom.split(f'{char} ', 1)
                        top = f'{top} {top_add}{char}'
                        special_split = True
                        break

                # If no special character splitting was done, split on space
                if not special_split:
                    top_add, bottom = bottom.split(' ', 1)
                    top = f'{top} {top_add}'.strip()

            all_lines += [bottom, top]

        # Reverse order, strip every line, delete blank entries
        all_lines = list(filter(len, map(str.strip,all_lines[::-1])))

        # If misformatted, combine overflow lines
        if len(all_lines) > max_line_count:
            all_lines[-2] = f'{all_lines[-2]} {all_lines[-1]}'
            del all_lines[-1]

        return '\n'.join(all_lines)


    def split(self,
            max_line_width: int,
            max_line_count: int,
            split_style: SplitStyle,
        ) -> str:
        """
        Split this title's text into multiple lines. If the title cannot
        fit into the given parameters, line width might not be
        respected, but the maximum number of lines will be.

        Args:
            title_max_line_width: Maximum width of one line of title
                text, in characters.
            title_max_line_count: Maximum number of lines a title can
                take up, in total.
            title_split_style: How to split the title into multiple
                lines.

        Returns:
            Split title text.
        """

        # Is one word, return
        if ' ' not in self.full_title:
            return self.full_title

        # Split title into two "even" width lines
        if split_style == 'forced even':
            return self.__evenly_split()

        # If the title can fit on one line, is one line or one word, return
        if max_line_count <= 1 or len(self) <= max_line_width:
            return self.full_title

        # Misformat ahead..
        if len(self) > max_line_count * max_line_width:
            log.trace(f'Title {self} too long, potential misformat')

        # Split based on indicated style
        if split_style == 'even':
            return self.__evenly_split()
        if split_style == 'top':
            return self.__top_split(max_line_width, max_line_count)
        if split_style == 'bottom':
            return self.__bottom_split(max_line_width, max_line_count)

        return self.full_title


    @staticmethod
    @lru_cache(maxsize=256)
    def get_matching_title(text: str) -> str:
        """
        Remove all non A-Z characters from the given title.

        Args:
            text: The title to strip of special characters.

        Returns:
            The input text with all non A-Z characters removed.
        """

        return ''.join(filter(str.isalnum, text)).lower()


    def matches(self, *titles: 'str | Title') -> bool:
        """
        Get whether any of the given titles match this object.

        Args:
            titles: The titles to check.

        Returns:
            True if any of the given titles match this series, False
            otherwise.
        """

        def _get_title(title):
            if isinstance(title, Title):
                return self.get_matching_title(title.match_title)
            return self.get_matching_title(title)

        matching_titles = map(_get_title, titles)

        return any(title == self.match_title for title in matching_titles)


# def split_into_lines(text: str, num_lines: int) -> list[str]:
#     """
#     Split a string into `num_lines` roughly equal-length lines.

#     Args:
#         text: The text to split into lines.
#         num_lines: The number of lines to split the text into.

#     Returns:
#         A list of strings, each representing a line of the text.
#     """

#     if not (words := text.split()):
#         return [''] * num_lines

#     # Approximate target length per line
#     total_len = len(text)
#     target_len = total_len // num_lines

#     lines: list[str] = []
#     current_line: list[str] = []
#     current_len = 0

#     for word in words:
#         log.error(f'{current_len = } len({word}) = {len(word)} {len(current_line) = } {target_len = } {len(lines) = }')
#         if (current_len + len(word) + len(current_line) > target_len
#             and len(lines) < num_lines - 1):
#             lines.append(' '.join(current_line))
#             current_line = [word]
#             current_len = len(word)
#         else:
#             current_line.append(word)
#             current_len += len(word)

#     lines.append(' '.join(current_line))

#     return lines


def split_into_lines(text: str, /, num_lines: int) -> list[str]:
    """
    Split the given text into `num_lines` lines, preserving word
    boundaries and balancing line lengths as evenly as possible
    (minimizes the maximum line length). Returns a list of length
    `num_lines`, with extra empty lines appended if needed.

    The runtime of this algorithm is O(n^2 * k), and so is suitable for
    relatively short strings.

    Args:
        text: The text to split into lines.
        num_lines: The number of lines to split the text into.

    Returns:
        A list of strings, each representing a line of the text.
    """

    # Quick handling of trivial cases
    words = text.split()
    n = len(words)
    if n == 0:
        return [''] * num_lines
    if num_lines >= n:
        # put one word per line until we run out, then empty lines
        lines = [w for w in words] + [''] * (num_lines - n)
        return lines

    # Precompute prefix sums of word lengths
    # prefix[i] = sum of len(words[0:i])  (prefix[0] = 0)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + len(words[i])

    def cost(i: int, j: int) -> int:
        """
        Calculate the cost of joining the words from `i` to `j`
        inclusively.

        Returns:
            The cost of joining the words from `i` to `j` inclusive.
        """

        # words i..j-1 inclusive
        if i >= j:
            return 0
        words_len = prefix[j] - prefix[i]
        spaces = (j - i - 1) if (j - i - 1) > 0 else 0
        return words_len + spaces

    # DP tables:
    # dp[k][i] = minimal possible maximum line length when partitioning
    # first i words into k lines
    # back[k][i] = index where the last partition (k-th) starts
    K = num_lines
    dp = [[float('inf')] * (n + 1) for _ in range(K + 1)]
    back = [[0] * (n + 1) for _ in range(K + 1)]

    # Base: partitioning into 1 line
    for i in range(1, n + 1):
        dp[1][i] = cost(0, i)
        back[1][i] = 0

    # Fill DP for k = 2..K
    for k in range(2, K + 1):
        # we need at least k words to create k non-empty partitions, but
        # we allow earlier partitions empty by design
        for i in range(1, n + 1):
            # try placing the last cut at position j where previous k-1
            # partitions cover words[0:j] and last partition covers
            # words[j:i]
            best_val = float('inf')
            best_j = 0
            # j from k-1 .. i-1 (ensure at least k-1 words for first k-1
            # parts, and last part non-empty)
            start_j = k - 1
            if start_j < 0:
                start_j = 0
            for j in range(start_j, i):
                val = max(dp[k - 1][j], cost(j, i))
                if val < best_val:
                    best_val = val
                    best_j = j
            dp[k][i] = best_val
            back[k][i] = best_j

    # Reconstruct partitions from back table
    parts = []
    k = K
    i = n
    while k > 0:
        j = back[k][i]
        parts.append((j, i))  # words[j:i]
        i = j
        k -= 1
    parts.reverse()

    # Build lines and if we have fewer than num_lines non-empty
    # partitions (possible if text shorter), pad
    lines = []
    for (a, b) in parts:
        if a >= b:
            lines.append('')  # empty partition
        else:
            lines.append(' '.join(words[a:b]))

    # If we somehow produced fewer/more lines, adjust to exactly num_lines
    if len(lines) < num_lines:
        lines += [''] * (num_lines - len(lines))
    elif len(lines) > num_lines:
        # merge trailing extra lines into the last line (shouldn't normally happen)
        merged = ' '.join([ln for ln in lines[num_lines - 1:] if ln])
        lines = lines[: num_lines - 1] + [merged]

    return lines
