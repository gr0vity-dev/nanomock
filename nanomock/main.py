import argparse
from nanomock.nanomock_manager import NanoLocalManager
from nanomock.internal.utils import is_packaged_version
from pathlib import Path
import json


def _get_default_app_dir():
    if is_packaged_version():
        return Path.cwd()
    else:
        return Path.cwd() / 'nanomock'


def main():
    parser = argparse.ArgumentParser(description='Docker Manager CLI')
    parser.add_argument('command',
                        choices=[
                            'create', 'start', 'status', 'restart', 'init',
                            'stop', 'update', 'remove', 'reset', 'down',
                            'destroy', 'rpc'
                        ])
    parser.add_argument('--dir_path',
                        default=_get_default_app_dir(),
                        help='Path to the working directory')
    parser.add_argument(
        '--nodes',
        nargs='+',
        help=
        'List of container names (only required for start, stop, remove, and rpc commands)'
    )
    parser.add_argument(
        '--project_name',
        default="nanomock",
        help='project_name for docker-compose to know what to execute')

    # Add the optional --payload argument
    parser.add_argument(
        '--payload',
        type=json.loads,
        help="JSON request payload (only required for rpc command)")

    args = parser.parse_args()
    manager = NanoLocalManager(args.dir_path, args.project_name)

    if args.command == 'rpc':
        if not args.payload:
            parser.error(
                "The --payload argument is required for the 'rpc' command.")
        manager.execute_command(args.command, args.nodes, args.payload)
    else:
        manager.execute_command(args.command, args.nodes)


if __name__ == '__main__':
    main()
