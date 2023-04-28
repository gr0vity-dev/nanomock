#!./venv_py/bin/python
import argparse
from app.mesh_manager import NanoMeshManager


def main():
    parser = argparse.ArgumentParser(description='Docker Manager CLI')
    parser.add_argument('command',
                        choices=[
                            'create', 'start', 'status', 'restart', 'init',
                            'stop', 'update', 'remove', 'reset', 'down',
                            'destroy'
                        ])
    parser.add_argument('--dir_path',
                        default="nanomesh",
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

    if args.command == 'create':
        manager.create_docker_compose_file()
    elif args.command == 'start':
        manager.start_containers(args.nodes)
    elif args.command == 'status':
        manager.network_status()
    elif args.command == 'restart':
        manager.restart_containers(args.nodes)
    elif args.command == 'reset':
        manager.reset_nodes_data(args.nodes)
    elif args.command == 'init':
        manager.init_nodes()
    elif args.command == 'stop':
        manager.stop_containers(args.nodes)
    elif args.command in ['remove', 'down']:
        manager.remove_containers()
    elif args.command == 'destroy':
        manager.destroy(remove_files=True)


if __name__ == '__main__':
    main()
