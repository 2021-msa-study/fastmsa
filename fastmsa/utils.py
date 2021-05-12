import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from colorama import init as init_colors
from pkg_resources import resource_isdir, resource_listdir

init_colors()  # For Windows environment

from colorama import Fore, Style


def fg(text, color=Fore.WHITE):
    """텍스트를 지정된 ANSI 컬러로 출력합니다."""
    return f"{color}{text}{Fore.RESET}"


def bold(text, color=Fore.WHITE):
    """텍스트를 지정된 ANSI 컬러와 밝기 효과를 주어 출력합니다."""
    return f"{Style.BRIGHT}{color}{text}{Style.RESET_ALL}"


@contextmanager
def cwd(path: Path) -> Generator:
    """Helper to guarantee work in the path only during the context.

    Restore previous working directory when exit the context block.
    """
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


def scan_resource_dir(basedir: str, files_found: list[str] = None, pkg_name="fastmsa"):
    if not files_found:
        files_found = []

    files = resource_listdir(pkg_name, basedir)

    for fname in files:
        path = basedir + "/" + fname
        if resource_isdir(pkg_name, path):
            scan_resource_dir(path, files_found, pkg_name)
        else:
            files_found.append(path)

    return files_found
