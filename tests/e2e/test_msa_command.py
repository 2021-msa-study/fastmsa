"""FastMSA Command Test.  $ msa --help ...(help string)
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
from pathlib import Path
from textwrap import dedent
import os
import sys
import tempfile
import shutil

import pytest

from fastmsa.command import FastMSACommand, FastMSAInitError
from fastmsa.utils import scan_resource_dir, cwd


@pytest.fixture
def msa():
    path = tempfile.mkdtemp()

    msa = FastMSACommand("testapp", path)
    msa.init()

    sys.path.insert(0, os.getcwd())
    (msa.path / "__init__.py").touch()

    yield msa

    sys.path.pop(0)
    shutil.rmtree(msa.path)  # cleanup temporary directory


def test_resource_files():
    """Check the existence of resources filest.

    ``msa`` 명령으로 초기화된 프로젝트 구조가 올바르게 동작하는지 테스트합니다.
    """
    # scan all resources
    app_template_files = scan_resource_dir("templates/app")
    assert [] != "\n".join(app_template_files)


def test_msa_init_in_exist_path():
    """이미 존재하는 디렉토리에서 초기화 하는 상황을 고려.

    테스트 순서:
        - 임시 디렉토리 생성
        - 디렉토리에서
    """
    path = Path(tempfile.mkdtemp())
    with cwd(path):
        msa = FastMSACommand()
        # 암시적으로 초기화 할 경우 디렉토리 이름을 딴 프트젝트가 되어야함.
        assert path.name == msa.name
        assert path == msa.path
        msa.init()


def test_msa_init(msa: FastMSACommand):
    assert os.path.exists(msa.path)

    root_files = os.listdir(msa.path)
    src_dir_files = os.listdir(msa.path / msa._name)
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


def test_msa_render_template(msa: FastMSACommand):
    """``msa`` 명령으로 생성된 파일들이 템플릿파일을 잘 변환했는지 테스트합니다."""
    with cwd(msa.path):
        readme_file = msa.path / "README.md"
        assert readme_file.exists()
        text = readme_file.read_text()
        assert text.startswith(f"# {msa._name.capitalize()}")


def test_fail_init_again(msa: FastMSACommand):
    """이미 init 된 디렉토리에서 다시 init 하면 안되는지 테스트."""
    with cwd(msa.path):
        # 이미 초기화된 상태
        assert msa.is_init()
        with pytest.raises(FastMSAInitError):
            msa.init()
