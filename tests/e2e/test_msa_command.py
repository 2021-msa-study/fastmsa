"""FastMsa Command Test.

$ msa --help
...(help string)

$ msa create testapp
$ msa create testapp --template=event-driven

(아래 두 명령 합쳐놓은 명령)
$ mkdir testapp && cd testapp
testapp $ msa init
...
...

$ cd testapp
testapp $ msa domain MyClothing

  created: domain/models/MyChothing.py
  (사용자가 도메인 모델 클래스를 수정)

testapp $ msa mapper MyClothing

  created: adapters/orm/MyClothing.py

"""
from textwrap import dedent
import os
import sys
import tempfile
import shutil

import pytest

from fastmsa.command import FastMsaCommand
from fastmsa.utils import scan_resource_dir, cwd


def test_resource_files():
    """Check the existence of resources filest.

    ``msa`` 명령으로 초기화된 프로젝트 구조가 올바르게 동작하는지 테스트합니다.
    """
    # scan all resources
    app_template_files = scan_resource_dir("templates/app")
    assert [] != "\n".join(app_template_files)


@pytest.fixture
def msa():
    path = tempfile.mkdtemp()

    msa = FastMsaCommand("testapp", path)
    msa.init()

    sys.path.insert(0, os.getcwd())
    (msa.path / "__init__.py").touch()

    yield msa

    sys.path.pop(0)
    shutil.rmtree(msa.path)  # cleanup temporary directory


def test_msa_init(msa: FastMsaCommand):
    assert os.path.exists(msa.path)

    root_files = os.listdir(msa.path)
    src_dir_files = os.listdir(msa.path / msa.name)
    test_dir_files = os.listdir(msa.path / "tests")

    assert 8 == len(root_files)
    assert 5 == len(src_dir_files)
    assert 5 == len(test_dir_files)

    with cwd(msa.path):
        ret = pytest.main(["tests"])
        assert pytest.ExitCode.OK == ret
        (msa.path / "tests" / "unit" / "test_fail.py").write_text(dedent("""
        def test_fail():
            assert False
        """))  # fmt: skip
        ret = pytest.main(["tests"])
        assert pytest.ExitCode.TESTS_FAILED == ret


def test_msa_render_template(msa: FastMsaCommand):
    """``msa`` 명령으로 생성된 파일들이 템플릿파일을 잘 변환했는지 테스트합니다."""
    msa: FastMsaCommand

    with cwd(msa.path):
        readme_file = msa.path / "README.md"
        assert readme_file.exists()
        text = readme_file.read_text()
        assert text.startswith(f"# {msa.name.capitalize()}")


def test_domain_test():
    ...
