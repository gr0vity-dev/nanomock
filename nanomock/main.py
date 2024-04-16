import argparse
from nanomock.nanomock_manager import NanoLocalManager
from nanomock.internal.utils import is_packaged_version
from pathlib import Path
from os import environ
import asyncio
import json


def _get_default_app_dir():
    if environ.get("NL_CONF_DIR"):
        return Path(environ.get("NL_CONF_DIR"))
    if is_packaged_version():
        return Path.cwd()
    else:
        return Path.cwd() / 'nanomock'


def parse_args():
    parser = argparse.ArgumentParser(description='nanomock cli')
    parser.add_argument('command',
                        choices=[
                            'create', 'start', 'start_nodes', 'status',
                            'restart', 'init', 'init_wallets', 'conf_edit',
                            'stop', 'stop_nodes', 'update', 'remove', 'reset',
                            'down', 'destroy', 'rpc', 'beta_create', 'beta_init'
                        ])
    parser.add_argument('--path',
                        default=_get_default_app_dir(),
                        help='Path to the working directory')
    parser.add_argument(
        '--nodes',
        nargs='+',
        help='List of container names (only required for start, stop, remove, and rpc commands)'
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

    return parser.parse_args()


async def main_async(args=None):
    args = args or parse_args()
    manager = NanoLocalManager(args.path, args.project_name, environ.get(
        "NL_CONF_FILE", "nl_config.toml"))
    await manager.execute_command(args.command, args.nodes, args.payload)


def main(args=None):
    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
