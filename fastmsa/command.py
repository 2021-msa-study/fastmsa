"""Command line script for FastMSA."""
import glob
import importlib
import os
import sys
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from inspect import getmembers
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional, Sequence, cast

import jinja2
import uvicorn
from pkg_resources import resource_string
from sqlalchemy.sql.schema import MetaData
from starlette.routing import BaseRoute

from fastmsa.config import FastMSA
from fastmsa.core import AbstractFastMSA, FastMSAError, FastMSAInitError
from fastmsa.event import MessageHandlerMap
from fastmsa.logging import get_logger
from fastmsa.utils import Fore, Style, bold, cwd, fg, scan_resource_dir

YELLOW, CYAN, RED, GREEN, WHITE = (
    Fore.YELLOW,
    Fore.CYAN,
    Fore.RED,
    Fore.GREEN,
    Fore.WHITE,
)
WHITE_EX, CYAN_EX = Fore.LIGHTWHITE_EX, Fore.LIGHTCYAN_EX
BRIGHT, RESET_ALL = Style.BRIGHT, Style.RESET_ALL

TEMPLATE_DIR = "templates/app"


logger = get_logger("fastmsa.command")


class FastMSACommand:
    def __init__(self):
        """Constructor.

        작업 순서:
            1. `<pkg_name>/config.py` 위치를 찾기 위해 앱 name 을 구한다.
            2. <pkg_name> 은 암시적으로는 현재 경로의 이름인데, `setup.cfg` 파일에
               `[fastmsa]` 섹션에도 지정 가능하다.
            3. config 파일을 로드해서 나머지 정보를 읽는다.
        """
        self.path = Path(os.path.abspath("."))
        self.msa = cast(FastMSA, FastMSA.load_from_config(self.path))

        if self.msa.is_implicit_name:
            # 앞에서 어떤 경우에도 이름을 못얻으면 현재 경로를 암시적으로
            # 이름으로 정한다.
            # self.print_warn(
            #    f"app name is implicitly given as *{bold(self.msa.name)}* by the current path."
            # )
            ...

    def print_warn(self, msg: str):
        print(f"{bold('FastMSA WARNING:', YELLOW)} {msg}")

    def is_init(self):
        """이미 초기화된 프트젝트인지 확인합니다.

        체크 방법:`
            현재 디렉토리가 비어 있지 않은 경우 초기화된 프로젝트로 판단합니다.
        """
        return any(self.path.iterdir())

    def init(self, force=False):
        """FastMSA 앱 프로젝트 디렉토리를 권장 구조로 초기화 합니다."""
        if self.is_init():
            if force:
                self.print_warn(f"*{bold('force')}* initializing project...")
            else:
                raise FastMSAInitError(f"project already initialized at: {self.path}")

        with cwd(self.path):
            res_names = scan_resource_dir(TEMPLATE_DIR)

            assert res_names

            for res_name in res_names:
                res_name.startswith("templates/app/app/")
                res_name2 = res_name.replace(
                    "templates/app/app/", f"templates/app/{self.msa.name}/"
                )
                # XXX: Temporary fix
                if "__pycache__" in res_name:
                    continue
                rel_path = res_name2.replace(TEMPLATE_DIR + "/", "")
                target_path = self.path / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                text = resource_string("fastmsa", res_name)
                text = text.decode()

                if target_path.name.endswith(".j2"):  # Jinja2 template
                    target_path = target_path.parent / target_path.name[:-3]
                    template = jinja2.Template(text)
                    text = template.render(msa=self.msa)

                target_path.write_text(text, encoding="utf8")

            # if self._name:
            #    (self.path / "app").rename(self._name)

    def init_app(self, init_routes=True):
        """FastMSA 앱을 초기화 합니다."""
        logger.info(bold("Load config and initialize app..."))
        bullet = bold("✓" if os.name != "nt" else "v", GREEN)

        logger.info(
            f"{bullet} init {fg('domain models', CYAN)}... %s",
            bold(f"{len(self.load_domain())}", YELLOW) + " models loaded.",
        )

        logger.info(
            f"{bullet} init {fg('ORM mappings', CYAN)}.... %s",
            bold(f"{len(self.load_orm_mappers().tables)}", YELLOW) + " tables mapped.",
        )

        if init_routes:
            logger.info(
                f"{bullet} init {fg('API endpoints', CYAN)}... %s",
                bold(f"{len(self.load_routes())}", YELLOW) + " routes installed.",
            )

            self.msa.init_fastapi()

        msg_handlers = self.load_msg_handlers()
        logger.info(
            f"{bullet} init {fg('event handlers', CYAN)}.. %s handlers mounted.",
            bold(f"{len(msg_handlers)}", YELLOW),
        )

        logger.info(
            f"{bullet} init {fg('database', CYAN)}........ %s",
            bold(f"{self.msa.get_db_url()}", YELLOW),
        )

        return self.msa

    def banner(self, msg, icon=""):
        """프로젝트 배너를 표시합니다."""
        if os.name == "nt":
            icon = ""
        term_width = os.get_terminal_size().columns
        banner_width = min(75, term_width)
        print("─" * banner_width)
        print(f"{icon} {msg}")
        print("─" * banner_width)

    def info(self):
        """FastMSA 앱 정보를 출력합니다."""
        dot = bold("-", YELLOW)
        self.banner(f"{bold('FastMSA Information')}", icon="💡")
        print(dot, fg("Name", CYAN), "  :", fg(self.msa.name, WHITE_EX))
        print(dot, fg("Title", CYAN), " :", fg(self.msa.title, WHITE_EX))
        print(dot, fg("Module", CYAN), ":", fg(self.msa.module_name, WHITE_EX))
        print(dot, fg("Path", CYAN), "  :", fg(self.path, WHITE_EX))

    def run(
        self,
        app_name: Optional[str] = None,
        dry_run=False,
        reload=True,
        banner=True,
        **kwargs,
    ):
        """FastMSA 애플리케이션을 실행합니다."""
        if banner:
            msg = "".join(
                [
                    bold("Launching FastMSA: ", CYAN),
                    bold(self.msa.title, WHITE),
                ]
            )
            self.banner(msg, icon="🚀")

        if not app_name:
            app_name = f"{self.msa.module_name}.__main__:app"

        if not dry_run:
            sys.path.insert(0, str(self.path))
            if os.name == "nt":
                content = (uvicorn_init := Path(uvicorn.__file__)).read_text()
                if "colorama" not in content:
                    uvicorn_init.write_text(
                        content + "\nfrom colorama import init; init()"
                    )
            uvicorn.run(app_name, reload=reload, port=self.msa.get_api_port())

    def load_domain(self) -> list[type]:
        """도메인 클래스를 로드합니다.

        ./<package_dir>/domain/**/*.py 파일을 읽어서 클래스 타입 리스트를 리턴합니다.
        """
        domains = list[type]()

        for fname in glob.glob("./" + str(self.msa.module_path) + "/domain/*.py"):
            if Path(fname).name.startswith("_"):
                continue
            module_name = fname[2:-3].replace("/", ".").replace("\\", ".")
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

        mapper_file_path = self.msa.module_path / "adapters" / "orm.py"
        mapper_paths = list[Path]()

        if mapper_file_path.exists():
            mapper_paths = [mapper_file_path]
        else:
            mapper_paths = [
                Path(p) for p in glob.glob(f"{self.msa.module_path}/adapters/orm/*.py")
            ]

        mapper_paths = [p.relative_to(self.msa.module_path) for p in mapper_paths]

        for path in mapper_paths:
            if path.name.startswith("_"):
                continue
            mapper_modname = ".".join(
                [self.msa.module_name or self.msa.name] + list(path.parts)
            )[:-3]
            module = importlib.import_module(mapper_modname)
            # 모듈에 `init_mappers()` 함수가 있다면 호출합니다.
            init_mappers = getattr(module, "init_mappers", None)
            if init_mappers and callable(init_mappers):
                init_mappers(metadata)

        return metadata

    def load_routes(self) -> list[BaseRoute]:
        from fastmsa.api import app

        modules = []

        for fname in glob.glob(f"./{self.msa.module_path}/routes/*.py"):
            if Path(fname).name.startswith("_"):
                continue
            module_name = fname[2:-3].replace("/", ".").replace("\\", ".")
            if sys.modules.get(module_name):
                continue
            module = importlib.import_module(module_name)
            modules.append(module)

        routes: list[Any] = app.routes
        return [
            r
            for r in routes
            if r.endpoint.__module__.startswith(self.msa.module_name + ".routes")
        ]

    def load_msg_handlers(
        self, msa: Optional[AbstractFastMSA] = None
    ) -> MessageHandlerMap:
        from fastmsa.event import MESSAGE_HANDLERS, messagebus

        modules = []

        for fname in glob.glob(f"./{self.msa.module_path}/handlers/*.py"):
            if Path(fname).name.startswith("_"):
                continue
            module_name = fname[2:-3].replace("/", ".").replace("\\", ".")
            if sys.modules.get(module_name):
                continue
            module = importlib.import_module(module_name)
            modules.append(module)

        messagebus.msa = msa or self.msa  # Dependency Injection
        messagebus.uow = (msa and msa.uow) or self.msa.uow

        return MESSAGE_HANDLERS


class FastMSACommandParser:
    """콘솔 커맨드 명령어 파서.

    실제 작업은 `FastMSACommand` 객체에 위임합니다.
    """

    def __init__(self):
        """기본 생성자."""
        self.parser = ArgumentParser(
            "msa",
            description=f"✨ {bold('FastMSA')} : {fg('command line utility', CYAN_EX)}",
        )
        self._subparsers = self.parser.add_subparsers(dest="command")
        self._cmd = FastMSACommand()

        # init subparsers
        for handler in [
            self._cmd.info,
            self._cmd.init,
            self._cmd.run,
        ]:
            command = handler.__name__
            # 핸들러 함수의 주석을 커맨드라인 도움말로 변환하기 위한 작업입니다.
            doc = None
            if handler.__doc__:
                lines = handler.__doc__.splitlines()
                doc = lines[0] + "\n" + dedent("\n".join(lines[1:]))
            parser = self._subparsers.add_parser(
                command,
                description=doc,
                formatter_class=RawTextHelpFormatter,
            )
            if command == "init":
                parser.add_argument(
                    "--force", action="store_true", help="무조건 프로젝트 구조 덮어쓰기"
                )
                parser.add_argument(
                    "--title",
                    action="store_const",
                    help="외부에 보여질 앱 제목",
                    const="",
                )
            if command == "run":
                parser.add_argument("app_name", metavar="app_name", nargs="?")

    def parse_args(self, args: Sequence[str]):
        """콘솔 명령어를 해석해서 적절한 작업을 수행합니다."""
        if not args:
            self.parser.print_help()
            return

        ns = self.parser.parse_args(args)
        try:
            if hasattr(self, ns.command):
                # 커맨드 명령어와 동일한 이름의 메소드가 파서 클래스에 있으면
                # 그 메소드를 호출해서 적당한 처리 후 실제 메소드를 호출합니다.
                getattr(self, ns.command)(ns)
            else:
                # 아닐 경우 FastMSACommand 클래스에서 핸를러를 호출합니다.
                getattr(self._cmd, ns.command)()
        except FastMSAError as e:
            print(
                f"{bold('FastMSA ERROR:', RED)} {fg(e.message, YELLOW)}",
                file=sys.stderr,
            )

    def init(self, ns: Namespace):
        """`init` 명령어 처리."""
        self._cmd.init(force=ns.force)

    def run(self, ns: Namespace):
        """`run` 명령어 처리."""
        self._cmd.run(app_name=ns.app_name)


def console_main():
    parser = FastMSACommandParser()
    parser.parse_args(sys.argv[1:])


if __name__ == "__main__":
    console_main()
