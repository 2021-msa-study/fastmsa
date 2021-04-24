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
import os
import shutil
import sys
import tempfile
from pathlib import Path
from textwrap import dedent
from types import ModuleType

import pytest
from _pytest.python import Module

from fastmsa.command import FastMSACommand, FastMSAInitError
from fastmsa.utils import cwd, scan_resource_dir


@pytest.fixture
def tempdir():
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)


@pytest.fixture
def msa():
    from fastmsa.api import app

    path = tempfile.mkdtemp()

    msa = FastMSACommand(Path(path).name, path)
    msa.init()

    sys.path.insert(0, str(msa.path))

    # `tests` 로 시작하는 모듈이 이미 로드되어 테스트를 위해 만든
    # 프로의트의 `tests` 모듈과 충돌하므로 기존 모듈을 잠시 pop 해둔다.

    old_modules = dict[str, ModuleType]()
    old_routes = list(app.routes)
    app.router.routes.clear()

    for name, module in list(sys.modules.items()):
        if name.startswith("tests"):
            old_modules[name] = sys.modules.pop(name)

    yield msa

    for name, module in old_modules.items():
        sys.modules[name] = module

    app.router.routes = old_routes
    sys.path.pop(0)
    shutil.rmtree(msa.path)  # cleanup temporary directory


def test_resource_files():
    """Check the existence of resources filest.

    ``msa`` 명령으로 초기화된 프로젝트 구조가 올바르게 동작하는지 테스트합니다.
    """
    # scan all resources
    app_template_files = scan_resource_dir("templates/app")
    assert [] != "\n".join(app_template_files)


def test_msa_init_in_exist_path(tempdir: Path):
    """이미 존재하는 디렉토리에서 초기화 하는 상황을 고려.

    테스트 순서:
        - 임시 디렉토리 생성
        - 디렉토리에서
    """
    with cwd(tempdir):
        msa = FastMSACommand()
        # 암시적으로 초기화 할 경우 디렉토리 이름을 딴 프트젝트가 되어야함.
        assert tempdir.name == msa.name
        assert tempdir == msa.path

        msa.init()


def test_msa_init(msa: FastMSACommand):
    assert os.path.exists(msa.path)

    root_files = os.listdir(msa.path)
    src_dir_files = os.listdir(msa.path / msa.name)
    test_dir_files = os.listdir(msa.path / "tests")

    assert 8 == len(root_files)
    assert 6 == len(src_dir_files)
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


def test_msa_generate_orm_code(msa: FastMSACommand):
    with cwd(msa.path):
        ret = pytest.main(["tests"])
        assert (msa.path / msa.name / "domain" / "models.py").exists()
        assert pytest.ExitCode.OK == ret


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


def test_msa_run_command(msa: FastMSACommand):
    """다음처럼 부트스트랩 과정을 진행합니다.

    $ msa run --verbose
    Booting FastMSA app...
    - init domain models... 3 models found.
    - init orm mappings.... 2 tables mapped.
    - init api endpoints... 4 routes installed.
    Done in 0.1s.
    Server listening at localhost:5000...
    """
    with cwd(msa.path):
        msa.run(dry_run=True)


def test_msa_load_domain(msa: FastMSACommand):
    with cwd(msa.path):
        assert 3 == len(msa.load_domain())


def test_msa_load_orm_mappers(msa: FastMSACommand):
    with cwd(msa.path):
        assert 3 == len(msa.load_orm_mappers().tables)
