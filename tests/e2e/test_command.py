"""MSA 커맨드 실행 테스트를위한 E2E Test.

TODO: Unit Test로 분리할 부분이 있는지 확인.
"""
from unittest.mock import MagicMock, patch
import sys
import shutil
import tempfile
import importlib
import importlib.util
import pytest

from fastmsa.utils import cwd, scan_resource_dir
from fastmsa.command import FastMSACommand, TEMPLATE_DIR


@pytest.fixture
def raw_cmd():
    """`cmd.init()` 이 실행되기 전 `FastMSACommand` 픽스쳐."""
    tempdir = tempfile.mkdtemp()
    app_path = ""

    with cwd(tempdir):
        command = FastMSACommand()
        app_path = str(command.path)
        sys.path.insert(0, app_path)
        yield command

    sys.path.remove(app_path)
    shutil.rmtree(tempdir)


def prepare_module_import(cmd: FastMSACommand):
    (cmd.path / "__init__.py").touch()  # pytest 실행을 위해 반드시 필요.
    test_module_name = cmd.path.name + ".tests"
    sys.modules[cmd.path.name] = importlib.import_module(cmd.path.name)
    spec = importlib.util.spec_from_file_location(
        test_module_name, str(cmd.path / "tests" / "__init__.py")
    )
    if spec:
        sys.modules[test_module_name] = importlib.util.module_from_spec(spec)


@pytest.fixture
def cmd(raw_cmd: FastMSACommand):
    raw_cmd.init()
    prepare_module_import(raw_cmd)
    # `cmd.init()` 실행으로 생성된 `setup.cfg` 에서 FastMSACommand() 를
    # 다시 초기화하여 리턴한다.
    yield FastMSACommand()


def test_msa_cmd_init_generated_files(raw_cmd: FastMSACommand):
    """Check the number of generated files is the same with template files."""
    res_names = scan_resource_dir(TEMPLATE_DIR)
    raw_cmd.init()
    created_files = (p for p in raw_cmd.path.glob("**/*") if not p.is_dir())
    assert len(res_names) == len(list(created_files))


def test_msa_cmd_init_pytest(cmd: FastMSACommand):
    res = pytest.main(["./tests"])
    assert pytest.ExitCode.OK == res


def test_msa_cmd_info(cmd: FastMSACommand):
    with patch("os.get_terminal_size") as mock:
        mock.return_value = MagicMock(columns=50)
        cmd.info()


def test_msa_cmd_init_app(cmd: FastMSACommand):
    cmd.init_app()


def test_msa_cmd_run_dry(cmd: FastMSACommand):
    with patch("os.get_terminal_size") as mock:
        mock.return_value = MagicMock(columns=50)
        cmd.run(dry_run=True)
