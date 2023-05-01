import os
import re
import shutil
import subprocess
import logging
from typing import List, Optional
from .internal.dependency_checker import DependencyChecker
from .modules.nl_parse_config import ConfigParser
from .internal.nl_initialise import InitialBlocks
from .modules.nl_rpc import NanoRpc
from .internal.utils import log_on_success, NanoLocalLogger
from typing import List, Dict, Optional, Tuple, Union
import concurrent.futures
from math import floor
import yaml
import json
import time
import inspect

logger = NanoLocalLogger.get_logger(__name__)


class NanoLocalManager:

    def __init__(self, dir_path, project_name):
        self.command_mapping = self._initialize_command_mapping()
        self.dir_path = dir_path
        self.dependency_checker = DependencyChecker()
        self.dependency_checker.check_dependencies()
        self.conf_p = ConfigParser(dir_path)

        self.nano_nodes_path = self.conf_p.nano_nodes_path
        self.compose_yml_path = self.conf_p.compose_out_path
        self.compose_env_path = os.path.join(self.nano_nodes_path,
                                             "dc_nano_local_env")
        self.project_name = project_name
        self.services_dir = self.conf_p.services_dir
        self.data_path = f"{self.nano_nodes_path}/{{node_name}}/NanoTest"
        self.config_node_path = f"{self.nano_nodes_path}/{{node_name}}/NanoTest/config-node.toml"
        self.config_rpc_path = f"{self.nano_nodes_path}/{{node_name}}/NanoTest/config-rpc.toml"

        os.makedirs(self.nano_nodes_path, exist_ok=True)

    def _initialize_command_mapping(self):
        return {
            'create': self.create_docker_compose_file,
            'start': self.start_containers,
            'status': self.network_status,
            'restart': self.restart_containers,
            'reset': self.reset_nodes_data,
            'init': self.init_nodes,
            'stop': self.stop_containers,
            'remove': self.remove_containers,
            'down': self.remove_containers,
            'destroy': lambda: self.destroy(remove_files=True),
            'rpc': self.run_rpc
        }

    def subprocess_capture_raise(self, cmd, shell=True, cwd=None, increment=0):
        #Capture output to stdout or raise CalledProcessError if the command returns a non-zero exit code
        try:
            result = subprocess.run(cmd,
                                    shell=shell,
                                    check=True,
                                    capture_output=True,
                                    text=True,
                                    cwd=cwd)

            #print(str.join(" ", [str(e) for e in cmd]))
            return result
        except subprocess.CalledProcessError as e:
            response = self.auto_heal(e, cmd, shell, cwd, increment)
            return response

    def _run_docker_compose_command(self,
                                    command,
                                    nodes: Optional[List[str]] = None):
        base_command = [
            "docker-compose", "-f", self.compose_yml_path, "-p",
            self.project_name
        ]
        base_command.extend(command)
        if nodes: base_command.extend(nodes)

        return self.subprocess_capture_raise(base_command, shell=False)

    def _get_default(self, config_name):
        """ Load config with default values"""
        #minimal node config if no file is provided in the nl_config.toml
        if config_name == "config_node":
            default_config_path = os.path.join(self.services_dir,
                                               "default_config-node.toml")
            return self.conf_p.conf_rw.read_toml(default_config_path,
                                                 is_packaged=True)
        elif config_name == "config_rpc":
            default_rpc_path = os.path.join(self.services_dir,
                                            "default_config-rpc.toml")
            return self.conf_p.conf_rw.read_toml(default_rpc_path,
                                                 is_packaged=True)
        else:
            return {}

    def _generate_docker_compose_env_file(self):
        env_variables = self.conf_p.get_docker_compose_env_variables()
        self.conf_p.conf_rw.write_list(f'{self.compose_env_path}',
                                       env_variables)

    def _generate_docker_compose_yml_file(self):
        self.conf_p.set_docker_compose()
        self.conf_p.write_docker_compose()

    def _generate_config_node_file(self, node_name):
        config_node = self.conf_p.get_config_from_path(node_name,
                                                       "config_node_path")
        if config_node is None:
            logger.warning(
                "No config-node.toml found. minimal version was created")
            config_node = self._get_default("config_node")

        config_node["node"][
            "preconfigured_peers"] = self.conf_p.preconfigured_peers
        self.conf_p.conf_rw.write_toml(
            self.config_node_path.format(node_name=node_name), config_node)

    def _generate_config_rpc_file(self, node_name):
        config_rpc = self.conf_p.get_config_from_path(node_name,
                                                      "config_rpc_path")
        if config_rpc is None:
            logger.warning(
                "No config-rpc.toml found. minimal version was created")
            config_rpc = self._get_default("config_rpc")

        self.conf_p.conf_rw.write_toml(
            self.config_rpc_path.format(node_name=node_name), config_rpc)

    def _generate_nanomonitor_config_file(self, node_name):
        if self.conf_p.get_config_value("nanomonitor_enable"):
            self.conf_p.write_nanomonitor_config(node_name)

    def _create_node_folders(self, node_name):
        nano_node_path = os.path.join(self.nano_nodes_path, node_name)
        nano_test_path = os.path.join(nano_node_path, "NanoTest")

        os.makedirs(nano_node_path, exist_ok=True)
        os.makedirs(nano_test_path, exist_ok=True)

        if self.conf_p.get_config_value("nanomonitor_enable"):
            nano_monitor_path = os.path.join(nano_node_path, "nanoNodeMonitor")
            os.makedirs(nano_monitor_path, exist_ok=True)

    def _prepare_nodes(self):
        #prepare genesis
        for node_name in self.conf_p.get_nodes_name():
            self._prepare_node_env(node_name)

    def _prepare_node_env(self, node_name):
        node_name = node_name.lower(
        )  # docker-compose requires lower case names
        self._create_node_folders(node_name)
        self._generate_config_node_file(node_name)
        self._generate_config_rpc_file(node_name)
        self._generate_nanomonitor_config_file(node_name)

    def _online_containers(self, node_names: List[str]) -> List[str]:
        online_containers = []
        for container in node_names:
            cmd = f"docker ps |grep {container}$ | wc -l"
            res = self.subprocess_capture_raise(cmd)
            online = int(res.stdout.strip())

            if online == 1:
                online_containers.append(container)

        return online_containers

    def _count_online_containers(self, node_names: List[str]) -> int:
        online_containers = self._online_containers(node_names)
        online_count = len(online_containers)
        return online_count

    def _get_nodes_block_counts(
            self, nodes_name: List[str]) -> List[Dict[str, Union[str, int]]]:
        nodes_block_count = []

        nodes_rpc = ([
            NanoRpc(self.conf_p.get_node_rpc(node)) for node in nodes_name
        ] if nodes_name is not None else self._get_all_rpc())

        for nano_rpc in nodes_rpc:
            block_count = nano_rpc.block_count()
            version_rpc_call = nano_rpc.version()
            node_name = self.conf_p.get_node_name_from_rpc_url(nano_rpc)
            count = int(block_count["count"])
            nodes_block_count.append({
                "node_name": node_name,
                "count": count,
                "cemented": block_count["cemented"],
                "version": version_rpc_call
            })

        return nodes_block_count

    def _generate_network_status_report(
            self, nodes: List[str],
            nodes_block_count: List[Dict[str, Union[str, int]]]) -> str:

        if not nodes_block_count:
            return ""

        max_count = max(int(bc["count"]) for bc in nodes_block_count)

        def get_node_data(
                node_name: str) -> Union[Dict[str, Union[str, int]], None]:
            for bc in nodes_block_count:
                if bc["node_name"] == node_name:
                    return bc
            return None

        def format_report_line(bc: Dict[str, Union[str, int]]) -> str:
            node_version = f'{bc["version"]["node_vendor"]} {bc["version"]["build_info"].split(" ")[0]}'
            synced_percentage = floor(
                int(bc["cemented"]) / max_count * 10000) / 100
            return '{:<16} {:<20} {:>6.2f}% synced | {}/{} blocks cemented'.format(
                bc["node_name"], node_version, synced_percentage,
                bc["cemented"], bc["count"])

        report = []
        for node_name in nodes:
            node_data = get_node_data(node_name)
            if node_data:
                report_line = format_report_line(node_data)
            else:
                report_line = f'{node_name} [down]'
            report.append(report_line)

        return '\n' + '\n'.join(report)

    def _get_all_rpc(self):
        return [NanoRpc(x) for x in self.conf_p.get_nodes_rpc()]

    def _is_rpc_available(self,
                          container: str,
                          timeout: int = 3) -> Tuple[str, bool]:
        rpc_url = self.conf_p.get_node_rpc(container)
        try:
            nano_rpc = NanoRpc(rpc_url)
            logging.info("call _is_rpc_available")
            if nano_rpc.block_count(max_retry=0):
                return container, True
        except Exception as e:
            logging.warning(
                f"RPC {rpc_url} not yet reachable for node {container}: {str(e)}"
            )

        return container, False

    def _wait_for_rpc_availability(self,
                                   nodes_name: List[str] = None,
                                   wait: bool = True,
                                   timeout: int = 10,
                                   max_timeout_s: int = 15) -> None:
        start_time = time.time()

        if not nodes_name:
            nodes_name = self.conf_p.get_nodes_name()

        nodes_to_check = nodes_name.copy()

        def get_unavailable_nodes(nodes: List[str], timeout: int) -> List[str]:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(
                    executor.map(self._is_rpc_available, nodes,
                                 [timeout] * len(nodes)))
            return [
                container for container, available in results if not available
            ]

        while len(nodes_to_check) > 0:
            if not wait:
                break

            nodes_to_check = get_unavailable_nodes(nodes_to_check, timeout)

            if time.time() - start_time > max_timeout_s:
                raise ValueError(
                    f"TIMEOUT: RPCs not reachable for nodes {nodes_to_check}")

            if len(nodes_to_check) > 0:
                time.sleep(1)

        logger.info(f"Nodes {nodes_name} reachable")

    def online_containers_status(self, online_containers: List[str],
                                 total_nodes) -> str:

        online_count = len(online_containers)
        if online_count == total_nodes:
            return f"All {online_count} containers online"
        else:
            return f"{online_count}/{total_nodes} containers online"

    @log_on_success
    def network_status(self, nodes_name: Optional[List[str]] = None) -> str:
        if nodes_name == []:
            return ""

        nodes_name = self.conf_p.get_nodes_name()
        online_containers = self._online_containers(nodes_name)
        status_msg = self.online_containers_status(online_containers,
                                                   len(nodes_name))
        # if "All" not in status_msg:
        #     return status_msg

        nodes_block_count = self._get_nodes_block_counts(online_containers)
        return status_msg + self._generate_network_status_report(
            nodes_name, nodes_block_count)

    def create_docker_compose_file(self):
        self._prepare_nodes()
        self._generate_docker_compose_env_file()
        self._generate_docker_compose_yml_file()
        logger.success(
            f"Docker Compose file created at {self.compose_yml_path}")

    @log_on_success
    def run_rpc(self, payload=None, nodes=None):
        responses = []
        if nodes is None:
            nodes = self.conf_p.get_nodes_name()

        for node in nodes:
            node_rpc = NanoRpc(self.conf_p.get_node_rpc(node))
            response = node_rpc.post_with_auth(payload)
            responses.append(response)

        return json.dumps(responses, indent=2)

    @log_on_success
    def init_wallets(self):
        #self.start_nodes('all')  #fixes a bug on mac m1
        init_blocks = InitialBlocks(self.dir_path,
                                    self.conf_p.get_nodes_rpc()[0],
                                    logger=logger)
        for node_name in self.conf_p.get_nodes_name():
            if node_name == self.conf_p.get_genesis_node_name():
                init_blocks.create_node_wallet(
                    self.conf_p.get_node_config(
                        self.conf_p.get_genesis_node_name())["rpc_url"],
                    self.conf_p.get_genesis_node_name(),
                    private_key=self.conf_p.config_dict["genesis_key"])
            else:
                init_blocks.create_node_wallet(
                    self.conf_p.get_node_config(node_name)["rpc_url"],
                    node_name,
                    seed=self.conf_p.get_node_config(node_name)["seed"])

    @log_on_success
    def init_nodes(self):
        self.init_wallets()
        init_blocks = InitialBlocks(self.dir_path,
                                    self.conf_p.get_nodes_rpc()[0],
                                    logger=logger)
        init_blocks.publish_initial_blocks()

    @log_on_success
    def reset_nodes_data(self, nodes: Optional[List[str]] = None):
        self.stop_containers(nodes)
        nodes_to_process = nodes or ['.']
        for node in nodes_to_process:
            node_path = f'{self.nano_nodes_path}/{node}' if nodes else self.nano_nodes_path
            cmd = 'rm -f $(find . -name "*.ldb")'
            self.subprocess_capture_raise(cmd, node_path)

    def init_containers(self):
        self.create_docker_compose_file()
        self.build_containers()

    @log_on_success
    def restart_containers(self, nodes: Optional[List[str]] = None):
        self._run_docker_compose_command(["restart"], nodes)

    @log_on_success
    def build_containers(self):
        self._run_docker_compose_command(["build"])

    @log_on_success
    def start_containers(self, nodes: Optional[List[str]] = None):
        self._run_docker_compose_command(["up", "-d"], nodes)
        self._wait_for_rpc_availability(nodes)

    @log_on_success
    def stop_containers(self, nodes: Optional[List[str]] = None):
        self._run_docker_compose_command(["stop"], nodes)

    @log_on_success
    def remove_containers(self):
        self._run_docker_compose_command(["down"])

    @log_on_success
    def destroy(self, remove_files=False):
        # Stop and remove containers
        self.remove_containers()

        # Remove the created files and folders if remove_files is True
        if remove_files:
            shutil.rmtree(self.nano_nodes_path)
            return f"Removed directory: {self.nano_nodes_path}"

    @log_on_success
    def update(self):
        self._run_docker_compose_command(["pull"])
        # Remove containers and networks
        self.remove_containers()
        self.build_containers()

    def auto_heal(self,
                  error: subprocess.CalledProcessError,
                  cmd,
                  cmd_shell,
                  cmd_cwd,
                  increment=0):
        if increment >= 10:
            raise (error)

        stderr = error.stderr
        healable_errors = {
            "address_in_use": ("programming external connectivity on endpoint",
                               self._heal_address_in_use),
            "docker_in_use":
            ("Error response from daemon: Conflict. The container name",
             self._heal_docker_in_use),
        }

        for error_key, (error_msg, heal_func) in healable_errors.items():
            if error_msg not in stderr:
                continue

            logger.warning(
                f"Retry attempt {increment}... {error_key}: \n {stderr}")

            if heal_func(error_msg, stderr):
                increment += 1
                return self.subprocess_capture_raise(cmd,
                                                     cmd_shell,
                                                     cmd_cwd,
                                                     increment=increment)

        raise (error)

    def _heal_address_in_use(self, error_msg, stderr):
        container_name = re.search(r"{} (\w+)".format(error_msg),
                                   stderr).group(1)
        self.subprocess_capture_raise(
            f"docker stop {container_name} && sleep 5 && docker start {container_name}",
            shell=True)
        return True

    def _heal_docker_in_use(self, error_msg, stderr):
        pattern = r'{} "/([^"]+)"'.format(error_msg)
        match = re.search(pattern, stderr)
        if match:
            container_name = match.group(1)
            self.subprocess_capture_raise(
                f"docker stop {container_name} && docker rm {container_name} && sleep 5",
                shell=True)
            return True
        return False

    # def auto_heal(self,
    #               error: subprocess.CalledProcessError,
    #               cmd,
    #               increment=0):
    #     if increment >= 3: raise (error)

    #     stderr = error.stderr
    #     healable_errors = {
    #         "address_in_use":
    #         "programming external connectivity on endpoint",
    #         "docker_in_use":
    #         "Error response from daemon: Conflict. The container name"
    #     }

    #     for error_key, error_msg in healable_errors.items():
    #         if error_msg not in stderr: continue
    #         logger.warn(
    #             f"Retry attempt {increment}... {error_key}: \n {stderr}")

    #         retry = False

    #         if error_key == "address_in_use":
    #             container_name = re.search(r"{} (\w+)".format(error_msg),
    #                                        stderr).group(1)
    #             self.subprocess_capture_raise(
    #                 f"docker stop {container_name} && sleep 5 && docker start {container_name}",
    #                 shell=True)
    #             retry = True

    #         if error_key == "docker_in_use":
    #             pattern = r'{} "/([^"]+)"'.format(error_msg)
    #             match = re.search(pattern, stderr)
    #             if match:
    #                 container_name = match.group(1)
    #                 self.subprocess_capture_raise(
    #                     f"docker stop {container_name} && docker rm {container_name} && sleep 5",
    #                     shell=True)
    #                 retry = True

    #         if retry:
    #             increment = increment + 1
    #             return self.subprocess_capture_raise(cmd, increment=increment)

    #     raise (error)

    def execute_command(self, command, nodes=None, payload=None):
        if command not in self.command_mapping:
            raise ValueError(f"Invalid command: {command}")

        func = self.command_mapping[command]
        if command == 'rpc':
            func(payload=payload, nodes=nodes)
        elif nodes:
            func(nodes=nodes)
        else:
            func()


if __name__ == "__main__":
    pass
