import os
import re
import shutil
import subprocess
import logging
from typing import List, Optional
from app.internal.dependency_checker import DependencyChecker
from app.modules.nl_parse_config import ConfigParser
from app.internal.nl_initialise import InitialBlocks
from app.modules.nl_rpc import NanoRpc
from app.internal.utils import log_and_auto_retry_on_error, NanoMeshLogger
from typing import List, Dict, Optional, Tuple, Union
import concurrent.futures
from math import floor
import yaml
import json
import time

logger = NanoMeshLogger.get_logger(__name__)


class NanoMeshManager:

    def __init__(self, dir_path, project_name):
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

    def _run_docker_compose_command(self,
                                    command,
                                    nodes: Optional[List[str]] = None):
        base_command = [
            "docker-compose", "-f", self.compose_yml_path, "-p",
            self.project_name
        ]
        base_command.extend(command)
        if nodes: base_command.extend(nodes)

        subprocess.run(base_command, check=True)

    def _get_default(self, config_name):
        """ Load config with default values"""
        #minimal node config if no file is provided in the nl_config.toml
        if config_name == "config_node":
            default_config_path = os.path.join(self.services_dir,
                                               "default_config-node.toml")
            return self.conf_p.conf_rw.read_toml(default_config_path)
        elif config_name == "config_rpc":
            default_rpc_path = os.path.join(self.services_dir,
                                            "default_config-rpc.toml")
            return self.conf_p.conf_rw.read_toml(default_rpc_path)
        else:
            return {}

    def _generate_docker_compose_env_file(self):
        env_variables = self.conf_p.get_docker_compose_env_variables()
        self.conf_p.conf_rw.write_list(f'{self.compose_env_path}',
                                       env_variables)

    def _generate_docker_compose_yml_file(self):
        conf_p = ConfigParser(self.dir_path)
        conf_p.set_docker_compose()
        conf_p.write_docker_compose()

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

    def _count_online_containers(self, node_names: List[str]) -> int:
        online_count = 0

        for container in node_names:
            cmd = f"docker ps |grep {container}$ | wc -l"
            res = subprocess.run(cmd,
                                 capture_output=True,
                                 text=True,
                                 shell=True)
            online = int(res.stdout.strip())

            if online == 1:
                online_count += 1

        return online_count

    def _get_nodes_block_counts(
            self,
            nodes_rpc: List[NanoRpc]) -> List[Dict[str, Union[str, int]]]:
        nodes_block_count = []

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
            self, nodes_block_count: List[Dict[str, Union[str, int]]]) -> str:
        max_count = max(int(bc["count"]) for bc in nodes_block_count)

        report = []
        for bc in nodes_block_count:
            node_version = f'{bc["version"]["node_vendor"]} {bc["version"]["build_info"].split(" ")[0]}'
            synced_percentage = floor(
                int(bc["cemented"]) / max_count * 10000) / 100
            report_line = '{:<16} {:<20} {:>6.2f}% synced | {}/{} blocks cemented'.format(
                bc["node_name"], node_version, synced_percentage,
                bc["cemented"], bc["count"])
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

        while len(nodes_name) > 0:
            if not wait:
                break

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(
                    executor.map(self._is_rpc_available, nodes_name,
                                 [timeout] * len(nodes_name)))

            nodes_name = [
                container for container, available in results if not available
            ]

            if time.time() - start_time > max_timeout_s:
                raise ValueError(
                    f"TIMEOUT: RPCs not reachable for nodes {nodes_name}")

            if len(nodes_name) > 0:
                time.sleep(1)

        logger.info(f"Nodes {self.conf_p.get_nodes_name()} reachable")

    def online_containers_status(self, node_names: List[str]) -> str:
        online_count = self._count_online_containers(node_names)
        total_nodes = len(node_names)

        if online_count == total_nodes:
            return f"All {online_count} containers online"
        else:
            return f"{online_count}/{total_nodes} containers online"

    def network_status(self, nodes_name: Optional[List[str]] = None) -> str:
        if nodes_name == []:
            return ""

        nodes_name = self.conf_p.get_nodes_name()
        nodes_rpc = ([
            NanoRpc(self.conf_p.get_node_rpc(node)) for node in nodes_name
        ] if nodes_name is not None else self._get_all_rpc())

        status_msg = self.online_containers_status(nodes_name)
        if "All" not in status_msg:
            return status_msg

        nodes_block_count = self._get_nodes_block_counts(nodes_rpc)
        logger.info(self._generate_network_status_report(nodes_block_count))

    def create_docker_compose_file(self):
        self._prepare_nodes()
        self._generate_docker_compose_env_file()
        self._generate_docker_compose_yml_file()
        logger.info(
            f"SUCCESS: Docker Compose file created at {self.compose_yml_path}")

    @log_and_auto_retry_on_error
    def init_wallets(self):
        #self.start_nodes('all')  #fixes a bug on mac m1
        init_blocks = InitialBlocks(rpc_url=self.conf_p.get_nodes_rpc()[0])
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

    @log_and_auto_retry_on_error
    def init_nodes(self):
        self.init_wallets()
        init_blocks = InitialBlocks(rpc_url=ConfigParser().get_nodes_rpc()[0])
        init_blocks.publish_initial_blocks()

    @log_and_auto_retry_on_error
    def reset_nodes_data(self, nodes: Optional[List[str]] = None):
        self.stop_containers(nodes)
        nodes_to_process = nodes or ['.']
        for node in nodes_to_process:
            node_path = f'{self.nano_nodes_path}/{node}' if nodes else self.nano_nodes_path
            command = 'rm -f $(find . -name "*.ldb")'
            subprocess.run(command, shell=True, check=True, cwd=node_path)

    def overwrite_files(self, src, dst):
        if not os.path.exists(dst):
            os.makedirs(dst)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                self.overwrite_files(s, d)
            else:
                shutil.copy2(s, d)

    def init_containers(self):
        self.create_docker_compose_file()
        self.build_containers()

    @log_and_auto_retry_on_error
    def restart_containers(self, nodes: Optional[List[str]] = None):
        self._run_docker_compose_command(["restart"], nodes)

    @log_and_auto_retry_on_error
    def build_containers(self):
        self._run_docker_compose_command(["build"])

    @log_and_auto_retry_on_error
    def start_containers(self, nodes: Optional[List[str]] = None):
        self._run_docker_compose_command(["up", "-d"], nodes)
        self._wait_for_rpc_availability()

    @log_and_auto_retry_on_error
    def stop_containers(self, nodes: Optional[List[str]] = None):
        self._run_docker_compose_command(["stop"], nodes)

    @log_and_auto_retry_on_error
    def remove_containers(self):
        self._run_docker_compose_command(["down"])

    @log_and_auto_retry_on_error
    def destroy(self, remove_files=False):
        # Stop and remove containers
        self.remove_containers()

        # Remove the created files and folders if remove_files is True
        if remove_files:
            shutil.rmtree(self.nano_nodes_path)
            print(f"Removed directory: {self.nano_nodes_path}")

    @log_and_auto_retry_on_error
    def update(self):
        self._run_docker_compose_command(["pull"])
        # Remove containers and networks
        self.remove_containers()
        self.build_containers()

    def auto_heal(self, error):
        if "Error response from daemon: driver failed programming external connectivity on endpoint" in error:
            container_name = re.search(
                r"Error response from daemon:.*?on endpoint (\w+)",
                error).group(1)
            self.stop_containers(container_name)
            time.sleep(5)
            return True
        return False


if __name__ == "__main__":
    pass
