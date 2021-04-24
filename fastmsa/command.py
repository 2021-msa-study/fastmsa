"""Command line script for FastMSA."""
from __future__ import annotations

import glob
import importlib
import logging
import os
import sys
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from inspect import getmembers
from pathlib import Path
from textwrap import dedent
from typing import Sequence, cast

import jinja2
import uvicorn
from colorama import Fore, Style
from pkg_resources import resource_string
from sqlalchemy.sql.schema import MetaData
from starlette.routing import BaseRoute

from fastmsa.core import AbstractConfig, FastMSA, FastMSAError
from fastmsa.utils import cwd, scan_resource_dir

YELLOW, CYAN, RED = Fore.YELLOW, Fore.CYAN, Fore.RED


def fg(text, color=Fore.WHITE):
    """텍스트를 지정된 ANSI 컬러로 출력합니다."""
    return f"{color}{text}{Fore.RESET}"


def bold(text, color=Fore.WHITE):
    """텍스트를 지정된 ANSI 컬러와 밝기 효과를 주어 출력합니다."""
    return f"{Style.BRIGHT}{color}{text}{Style.RESET_ALL}"


class FastMSAInitError(FastMSAError):
    """프로젝트 초기화 실패 에러."""

    ...


class FastMSACommand:
    def __init__(self, name: str = None, path: str = None):
        """Constructor.

        ``name`` should include only alpha-numeric chracters and underscore('_').
        """
        self.path = Path(os.path.abspath(path or "."))
        self._name: str

        if name:
            self.assert_valid_name(name)
            self._name = name
        else:
            self._name = self.path.name

    def assert_valid_name(self, name: str):
        assert name.isidentifier()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        """프로젝트 이름을 설정합니다.

        프로젝트 이름은 반드시 알파벳으로 시작해야 합니다.
        """
        name = value.strip()
        self.assert_valid_name(name)
        self._name = name

    def is_init(self):
        """이미 초기화된 프트젝트인지 확인합니다.

        체크 방법:`
            현재 디렉토리가 비어 있지 않은 경우 초기화된 프로젝트로 판단합니다.
        """
        return any(self.path.iterdir())

    def init(self, force=False):
        """Initialize project.

        Steps:
            1. Copy `templates/app`  to `<project_name>`
            2. Move `templates/app` to `<project_name>/<project_name>`
        """
        if self.is_init():
            if force:
                print(
                    f"{bold('FastMSA WARN:', YELLOW)} *{bold('force')}* initializing project..."
                )
            else:
                raise FastMSAInitError(f"project already initialized at: {self.path}")

        with cwd(self.path):
            template_dir = "templates/app"
            res_names = scan_resource_dir(template_dir)

            assert res_names

            for res_name in res_names:
                res_name.startswith("templates/app/app/")
                res_name2 = res_name.replace(
                    "templates/app/app/", f"templates/app/{self._name}/"
                )
                # XXX: Temporary fix
                if "__pycache__" in res_name:
                    continue
                rel_path = res_name2.replace(template_dir + "/", "")
                target_path = self.path / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                text = resource_string("fastmsa", res_name)
                text = text.decode()

                if target_path.name.endswith(".j2"):  # Jinja2 template
                    target_path = target_path.parent / target_path.name[:-3]
                    template = jinja2.Template(text)
                    text = template.render(msa=self)

                target_path.write_text(text)

            # if self._name:
            #    (self.path / "app").rename(self._name)

    def init_app(self):
        logger = logging.getLogger("uvicorn")
        logger.info(bold("Load config and initialize app..."))

        self._msa = FastMSA(self._name, self.load_config())
        bullet = bold("✔️", Fore.GREEN)

        logger.info(
            f"{bullet} init {fg('domain models', CYAN)}... %s",
            bold(f"{len(self.load_domain())}", YELLOW) + " models loaded.",
        )

        logger.info(
            f"{bullet} init {fg('ORM mappings', CYAN)}.... %s",
            bold(f"{len(self.load_orm_mappers().tables)}", YELLOW) + " tables mapped.",
        )

        logger.info(
            f"{bullet} init {fg('API endpoints', CYAN)}... %s",
            bold(f"{len(self.load_routes())}", YELLOW) + " routes installed.",
        )

        logger.info(
            f"{bullet} init {fg('database', CYAN)}........ %s",
            bold(f"{self._msa.config.get_db_url()}", YELLOW),
        )
        return self._msa

    def run(self, dry_run=False, reload=True, banner=True, **kwargs):
        """FastMSA 애플리케이션을 실행합니다."""
        term_width = os.get_terminal_size().columns
        banner_width = min(75, term_width)
        if banner:
            print("─" * banner_width)
            print(
                f"🚀 {Fore.CYAN}{Style.BRIGHT}Launching FastMSA:",
                f"{Fore.WHITE}{Style.BRIGHT}{self.name}{Style.RESET_ALL}",
            )
            print("─" * banner_width)

        if not dry_run:
            sys.path.insert(0, str(self.path))
            uvicorn.run(f"{self.name}.__main__:app", reload=reload)

    def load_config(self) -> AbstractConfig:
        sys.path.insert(0, str(self.path))
        module_name = f"{self.name}.config"
        Config = getattr(importlib.import_module(module_name), "Config")
        return cast(AbstractConfig, Config())

    def load_domain(self) -> list[type]:
        """도메인 클래스를 로드합니다.

        ./<package_dir>/domain/**/*.py 파일을 읽어서 클래스 타입 리스트를 리턴합니다.
        """
        domains = list[type]()

        for fname in glob.glob(f"./{self.name}/domain/*.py"):
            if Path(fname).name.startswith("_"):
                continue
            module_name = fname[2:-3].replace("/", ".")
            module = importlib.import_module(module_name)

            members = getmembers(module)
            for name, member in members:
                if name.startswith("_"):
                    continue
                if type(member) != type:
                    continue
                if member.__module__ != module_name:
                    continue
                domains.append(member)

        return domains

    def load_orm_mappers(self) -> MetaData:
        fastmsa_orm = importlib.import_module("fastmsa.orm")
        metadata = MetaData()
        setattr(fastmsa_orm, "metadata", metadata)

        for fname in glob.glob(f"./{self.name}/adapters/orm/*.py"):
            if Path(fname).name.startswith("_"):
                continue
            module_name = fname[2:-3].replace("/", ".")
            importlib.import_module(module_name)

        return metadata

    def load_routes(self) -> list[BaseRoute]:
        from fastmsa.api import app

        modules = []

        for fname in glob.glob(f"./{self.name}/routes/*.py"):
            if Path(fname).name.startswith("_"):
                continue
            module_name = fname[2:-3].replace("/", ".")
            module = importlib.import_module(module_name)
            modules.append(module)

        return app.routes


class FastMSACommandParser:
    def __init__(self):
        """기본 생성자."""
        self.parser = ArgumentParser(
            "msa", description="FastMSA : command line utility..."
        )
        self._subparsers = self.parser.add_subparsers(dest="command")
        self._cmd = FastMSACommand()

        # init subparsers
        for handler in [self._cmd.init, self._cmd.run]:
            doc = handler.__doc__
            lines = doc.splitlines()
            doc = lines[0] + "\n" + dedent("\n".join(lines[1:]))
            parser = self._subparsers.add_parser(
                handler.__name__,
                description=doc,
                formatter_class=RawTextHelpFormatter,
            )
            parser.add_argument("--force", action="store_true")

    def parse_args(self, args: Sequence[str]):
        if not args:
            self.parser.print_help()
            return

        ns = self.parser.parse_args(args)
        try:
            if hasattr(self, ns.command):
                getattr(self, ns.command)(ns)
            else:
                getattr(self._cmd, ns.command)()
        except FastMSAError as e:
            print(
                f"{bold('FastMSA ERROR:', RED)} {fg(e.message, YELLOW)}",
                file=sys.stderr,
            )

    def init(self, ns: Namespace):
        self._cmd.init(force=ns.force)


def console_main():
    parser = FastMSACommandParser()
    parser.parse_args(sys.argv[1:])


if __name__ == "__main__":
    console_main()
