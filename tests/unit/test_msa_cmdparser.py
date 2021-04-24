import argparse


def test_argparse_subcommand():
    """``argparse`` 사용법을 익히기 위한 테스트."""
    parser = argparse.ArgumentParser(
        "msa", description="FastMSA : command line helper", exit_on_error=False
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "init",
        description="Initialize FastMSA project settings in current directory",
    )

    ns = parser.parse_args(["init"])
    assert "init" == ns.command
    subparser = subparsers._name_parser_map[ns.command]
    assert subparser
