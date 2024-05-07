"""Module for make changes to README files before commit.

Uses pre-commit hook.
"""

import os
import re
import shutil
from pathlib import Path

import toml

READMES = [
    "README.md",
]
SOURCE_CODE_DIR = "telethon_multimongo_session/"


def insert_py_versions(readme: str) -> None:
    """Insert the available Python versions in the README.

    Raises
    ------
    FileNotFoundError:
        If `readme` file are not found.
    """
    if not Path(readme).exists():
        raise FileNotFoundError(readme)

    # Get the python version from pyproject.toml
    with open("pyproject.toml") as file:
        pyproject = toml.load(file)

    dependencies = pyproject["tool"]["poetry"]["dependencies"]
    python_version_specifier: str = dependencies["python"]

    # Make changes to readme file
    with open(readme) as file:
        readme_content = file.read()

    python_version_specifier = python_version_specifier.replace("_", "__")
    python_version_specifier = python_version_specifier.replace("-", "--")

    readme_content = re.sub(
        "(shields.io.*Python_versions)-(.*)-(.*)",
        rf"\1-{python_version_specifier}-\3",
        readme_content,
    )

    with open(readme, "w") as file:
        file.write(readme_content)


def replace_code_size(readme: str) -> None:
    """Insert code size into `readme`."""
    symbols_count = 0
    lines_count = 0
    for root, _dirs, files in os.walk(SOURCE_CODE_DIR):
        for file in files:
            if file.endswith(".pyc"):
                continue

            with open(Path(root) / file) as f:
                filedata = f.read()
            symbols_count += len(filedata)
            lines_count += len(filedata.splitlines())

    # Make changes to readme file
    with open(readme) as file:
        readme_content = file.read()

    readme_content = re.sub(
        "(shields.io.*Code_Lines)-(.*)-(.*)",
        rf"\1-{lines_count}-\3",
        readme_content,
    )
    readme_content = re.sub(
        "(shields.io.*Code_Symbols)-(.*)-(.*)",
        rf"\1-{symbols_count}-\3",
        readme_content,
    )

    with open(readme, "w") as file:
        file.write(readme_content)


def make_backups(readme: str) -> None:
    """Make backups of README files."""
    if not Path(f"{readme}.bak").exists():
        shutil.copy(readme, f"{readme}.bak")
    else:
        bak_num = 0
        for _ in Path().glob(f"{readme}.bak*"):
            bak_num += 1
        shutil.copy(readme, f"{readme}.bak{bak_num}")


def main() -> None:
    """Make changes to README files."""
    # Make backup of README
    for readme in READMES:
        make_backups(readme=readme)

        insert_py_versions(readme=readme)
        replace_code_size(readme=readme)


if __name__ == "__main__":
    main()
