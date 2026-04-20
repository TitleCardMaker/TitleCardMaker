#!/usr/bin/env python3

import os
from pathlib import Path
import re
import sys


def get_section(body: str, heading: str) -> str | None:
    """
    Return markdown body under ### <heading> until the next ### or EOF.
    """

    pattern = rf'^### {re.escape(heading)}\s*$(.*?)(?=^### |\Z)'
    m = re.search(pattern, body, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not m:
        return None

    return m.group(1).strip()


def develop_confirmation_checked(body: str) -> bool:

    if not (section := get_section(body, 'Develop branch confirmation')):
        return False

    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- [x]") and "develop branch" in line.lower():
            return True
    return False


def user_reported_version(body: str) -> str | None:
    if not (raw := get_section(body, 'Application version')):
        return None

    return raw.strip().strip("`").strip('"').strip("'")


def read_version_file(version_path: Path) -> str:
    
    if not (text := version_path.read_text(encoding="utf-8").strip()):
        raise ValueError("empty version file")

    return text


def versions_match(reported: str, expected: str) -> bool:
    """Compare after trim; allow optional leading v on either side."""
    a, b = reported.strip(), expected.strip()
    if a.casefold() == b.casefold():
        return True

    a_core = a[1:] if len(a) > 1 and a[0] in "vV" else a
    b_core = b[1:] if len(b) > 1 and b[0] in "vV" else b

    return a_core.casefold() == b_core.casefold()


def write_output(name: str, value: str) -> None:
    out = os.environ.get('GITHUB_OUTPUT')
    if not out:
        return None

    with open(out, 'a', encoding='utf-8') as fh:
        if '\n' in value:
            fh.write(f'{name}<<__MSG__\n')
            fh.write(value)
            fh.write('\n__MSG__\n')
        else:
            fh.write(f'{name}={value}\n')

    return None


def main() -> int:
    body = (os.environ.get('ISSUE_BODY', '') or '').replace('\r\n', '\n').replace('\r', '\n')
    version_file = Path(os.environ.get('VERSION_FILE_PATH', 'backend/.version'))

    if not develop_confirmation_checked(body):
        write_output("result", "close")
        write_output(
            "close_comment",
            "This issue was automatically closed because **develop branch confirmation** was not checked, "
            "or the confirmation does not match the expected format.\n\n"
            "Bug reports must be filed from the **latest `develop`** (GitHub branch or Docker `develop` image). "
            "Please update, check the confirmation box, ensure **Application version** matches `backend/.version` on "
            "`develop`, then open a new issue if the problem persists.",
        )
        return 0

    reported = user_reported_version(body)
    if not reported:
        write_output("result", "close")
        write_output(
            "close_comment",
            "This issue was automatically closed because no **Application version** could be read from the form.\n\n"
            "Please reopen after filling the version field (see `backend/.version` on `develop`).",
        )
        return 0

    try:
        expected = read_version_file(version_file)
    except (OSError, ValueError) as e:
        print(f"Failed to read expected version: {e}", file=sys.stderr)
        write_output("result", "error")
        return 1

    if not versions_match(reported, expected):
        write_output("result", "close")
        write_output(
            "close_comment",
            "This issue was automatically closed because the **Application version** you entered does not match "
            "the version on the latest `develop` branch.\n\n"
            f"- **You reported:** `{reported}`\n"
            f"- **Current `develop` (`backend/.version`):** `{expected}`\n\n"
            "Please update to the latest `develop` (or `develop` Docker image), confirm the checkbox, and submit again "
            "if the problem persists.",
        )
        return 0

    write_output("result", "ok")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
