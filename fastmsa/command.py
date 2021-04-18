"""Command line script for FastMSA.

Test
"""
from __future__ import annotations
import os
from typing import Optional, Sequence
from pathlib import Path
from pkg_resources import resource_string
from argparse import ArgumentParser, Namespace
import sys

import jinja2

from fastmsa.core import FastMSAError
from fastmsa.utils import cwd, scan_resource_dir


class FastMSAInitError(FastMSAError):
    """프로젝트 초기화 실패 에러."""

    ...


class FastMSACommand:
    def __init__(self, name: str = None, path: str = None):
        """Constructor.

        ``name`` should include only alpha-numeric chracters and underscore('_').
        """
        self.path = Path(os.path.abspath(path or "."))
        self._name: Optional[str] = name
        if not name:
            self._name = self.path.name

    @property
    def name(self):
        return self._name

    @name.setter
    def set_name(self, value: str):
        """프로젝트 이름을 설정합니다.

        프로젝트 이름은 반드시 알파벳으로 시작해야 합니다.
        """
        name = value.strip()
        assert name
        assert name[0].isalpha()
        assert name.isalnum()
        self._name = name

    def is_init(self):
        """이미 초기화된 프트젝트인지 확인합니다.

        체크 방법:`
            현재 디렉토리가 비어 있지 않은 경우 초기화된 프로젝트로 판단합니다.
        """
        return any(self.path.iterdir())

    def init(self):
        """Initialize project.

        Steps:
            1. Copy ``templates/app``  to ``project_name``
            j2. Rename ``templates/app`` to ``project_name/project_name``
        """

        if self.is_init():
            raise FastMSAInitError(
                f"FastMSA project already initialized at: {self.path}"
            )

        with cwd(self.path):
            template_dir = "templates/app"
            res_names = scan_resource_dir(template_dir)

            for res_name in res_names:
                rel_path = res_name.replace(template_dir + "/", "")
                target_path = self.path / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                text = resource_string("fastmsa", res_name).decode()

                if target_path.name.endswith(".j2"):  # Jinja2 template
                    target_path = target_path.parent / target_path.name[:-3]
                    template = jinja2.Template(text)
                    text = template.render(msa=self)

                target_path.write_text(text)

            (self.path / "app").rename(self._name)


class FastMSACommandParser:
    def __init__(self):
        """기본 생성자."""
        self.parser = ArgumentParser(
            "msa", description="FastMSA : command line utility..."
        )
        self._subparsers = self.parser.add_subparsers(dest="command")
        self._msa_command = FastMSACommand()

        # init subparsers
        for handler in [self.init]:
            self._subparsers.add_parser(
                handler.__name__,
                description=handler.__doc__,
            )

    def parse_args(self, args: Sequence[str]):
        if not args:
            self.parser.print_help()
            return

        ns = self.parser.parse_args(args)
        getattr(self, ns.command)()

    def init(self):
        """Initialize FastMSA project settings in current directory."""
        self._msa_command.init()


def console_main():
    parser = FastMSACommandParser()
    parser.parse_args(sys.argv[1:])


if __name__ == "__main__":
    console_main()
