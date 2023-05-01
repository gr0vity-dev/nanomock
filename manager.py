#!./venv_py/bin/python
import argparse
from app.mesh_manager import NanoMeshManager
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path


def _is_packaged_version():
    try:
        _ = version('nanomesh')
        return True
    except PackageNotFoundError:
        return False


def _get_default_app_dir():
    if _is_packaged_version():
        return Path.home() / 'nanomesh'
    else:
        return Path.cwd() / 'nanomesh'


def main():
    parser = argparse.ArgumentParser(description='Docker Manager CLI')
    parser.add_argument('command',
                        choices=[
                            'create', 'start', 'status', 'restart', 'init',
                            'stop', 'update', 'remove', 'reset', 'down',
                            'destroy'
                        ])
    parser.add_argument('--dir_path',
                        default=_get_default_app_dir(),
                        help='Path to the working directory')
    parser.add_argument(
        '--nodes',
        nargs='+',
        help=
        'List of container names (only required for start, stop, and remove commands)'
    )
    parser.add_argument(
        '--project_name',
        default="nano_mesh",
        help='project_name for docker-compose to know what to execute')

    args = parser.parse_args()
    manager = NanoMeshManager(args.dir_path, args.project_name)
    manager.execute_command(args.command, args.nodes)


if __name__ == '__main__':
    main()
