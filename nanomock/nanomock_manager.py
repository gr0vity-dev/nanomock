from typing import List, Dict, Optional, Tuple, Union
from math import floor
import json
import time
import inspect
import asyncio
import os
import shutil
from pathlib import Path
from asyncio import TimeoutError

import logging

from nanomock.internal.dependency_checker import DependencyChecker
from nanomock.modules.nl_parse_config import ConfigParser, ConfigReadWrite
from nanomock.internal.nl_initialise import InitialBlocks
from nanomock.docker import create_docker_interface
from nanomock.modules.nl_rpc import NanoRpc
from nanomock.internal.utils import log_on_success, shutil_rmtree, extract_packaged_services_to_disk, subprocess_run_capture_output
from nanomock.internal.utils import logger


class NanoLocalManager:

    def __init__(self, dir_path, project_name, config_file="nl_config.toml"):
        self.command_mapping = self._initialize_command_mapping()
        self.conf_p = ConfigParser(dir_path,
                                   config_file=config_file,
                                   logger=logger)
        self.conf_rw = ConfigReadWrite()
        self.dependency_checker = DependencyChecker()
        self.dependency_checker.check_dependencies()

        self.dir_path = dir_path
        self.nano_nodes_path = self.conf_p.nano_nodes_path
        self.compose_yml_path = self.conf_p.compose_out_path
        self.compose_env_path = os.path.join(self.nano_nodes_path,
                                             "dc_nano_local_env")
        self.project_name = project_name
        self.services_dir = self.conf_p.services_dir
        self.nodes_data_path = f"{self.nano_nodes_path}/{{node_name}}/NanoTest"
        self.config_node_path = f"{self.nano_nodes_path}/{{node_name}}/NanoTest/config-node.toml"
        self.config_rpc_path = f"{self.nano_nodes_path}/{{node_name}}/NanoTest/config-rpc.toml"
        self.config_log_path = f"{self.nano_nodes_path}/{{node_name}}/NanoTest/config-log.toml"

        os.makedirs(self.nano_nodes_path, exist_ok=True)

        self.docker_interface = create_docker_interface(
            self.compose_yml_path, self.project_name)

    def _initialize_command_mapping(self):
        # (command_method , validation_method)
        return {
            'create': (self.init_containers, None),
            'start': (self.start_containers, None),
            'start_nodes': (self.start_all_nodes, None),
            'status': (self.network_status, None),
            'restart': (self.restart_containers, None),
            'reset': (self.reset_nodes_data, None),
            'init': (self.init_nodes, None),
            'init_wallets': (self.init_wallets, None),
            'beta_create': (self.beta_create, None),
            'beta_init': (self.beta_init, None),
            'stop': (self.stop_containers, None),
            'stop_nodes': (self.stop_all_nodes, None),
            'remove': (self.remove_containers, None),
            'down': (self.remove_containers, None),
            'destroy': (lambda: self.destroy(remove_files=True), None),
            'rpc': (self.run_rpc, self._validator_rpc),
            'conf_edit': (self.conf_edit, self._validator_conf_edit)
        }

    def _get_default(self, config_name):
        # Mapping of config names to their respective default file names
        default_paths = {
            "config_node": "default_config-node.toml",
            "config_rpc": "default_config-rpc.toml",
            "config_log": "default_config-log.toml"
        }

        # Get the default path if the config name is valid
        default_file = default_paths.get(config_name)

        if default_file:
            default_path = os.path.join(self.services_dir, default_file)
            return self.conf_rw.read_toml(default_path, is_packaged=True)

        return {}

    def _generate_docker_compose_env_file(self):
        env_variables = self.conf_p.get_docker_compose_env_variables()
        self.conf_rw.write_list(f'{self.compose_env_path}', env_variables)

    def _generate_docker_compose_yml_file(self):
        self.conf_p.set_docker_compose()
        self.conf_p.write_docker_compose()

    def _set_config_log_file(self, node_name):
        config_log = self.conf_p.get_config_from_path(node_name, "config_log_path")
        if config_log is None:
            logger.debug( "No config-log.toml found. minimal version was created")
            config_log = self._get_default("config_log")
        config_log["log"]["default_level"] = self.conf_p.get_log_level(node_name)
        return config_log

    def _generate_config_log_file(self, node_name):
        config_log = self._set_config_log_file(node_name)
        self.conf_rw.write_toml(
            self.config_log_path.format(node_name=node_name), config_log)

    def _set_config_node_file(self, node_name):
        config_node = self.conf_p.get_config_from_path(node_name, "config_node_path")
        if config_node is None:
            logger.debug( "No config-node.toml found. minimal version was created")
            config_node = self._get_default("config_node")

        config_node["node"][
            "preconfigured_peers"] = self.conf_p.get_connected_peers(node_name)
        config_node["node"]["enable_voting"] = self.conf_p.is_voting_enabled(
            node_name)
        return config_node

    def _generate_config_node_file(self, node_name):
        config_node = self._set_config_node_file(node_name)
        self.conf_rw.write_toml(
            self.config_node_path.format(node_name=node_name), config_node)

    def _generate_config_rpc_file(self, node_name):
        config_rpc = self.conf_p.get_config_from_path(node_name, "config_rpc_path")
        if config_rpc is None:
            logger.debug( "No config-rpc.toml found. minimal version was created")
            config_rpc = self._get_default("config_rpc")

        self.conf_rw.write_toml(
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

    def _prepare_nodes(self, genesis_only=False):
        # prepare genesis
        nodes = self.conf_p.get_nodes_name()
        if genesis_only:
            nodes = [nodes[0]]
            logger.info("Only genesis node will be created")
        for node_name in self.conf_p.get_nodes_name():
            self._prepare_node_env(node_name)

    def _prepare_node_env(self, node_name):
        node_name = node_name.lower(
        )  # docker-compose requires lower case names
        self._create_node_folders(node_name)
        self._generate_config_node_file(node_name)
        self._generate_config_rpc_file(node_name)
        self._generate_config_log_file(node_name)
        self._generate_nanomonitor_config_file(node_name)

    def _online_containers(self, node_names: List[str]) -> List[str]:
        online_containers = []
        for container in node_names:
            cmd = f"docker ps |grep {container}$ | wc -l"
            res = subprocess_run_capture_output(cmd)
            online = int(res.stdout.strip())

            if online == 1:
                online_containers.append(container)

        return online_containers

    def _count_online_containers(self, node_names: List[str]) -> int:
        online_containers = self._online_containers(node_names)
        online_count = len(online_containers)
        return online_count

    async def _get_nodes_block_counts(self, nodes_name: List[str]) -> List[Dict[str, Union[str, int]]]:
        nodes_block_count = []

        nodes_rpc = ([
            NanoRpc(self.conf_p.get_node_rpc(node)) for node in nodes_name
        ] if nodes_name is not None else self._get_all_rpc())

        async def get_block_count_for_node(node_rpc):
            try:
                block_count = await asyncio.wait_for(node_rpc.block_count(), timeout=2.0)
                version_rpc_call = await asyncio.wait_for(node_rpc.version(), timeout=2.0)
                if not (block_count or version_rpc_call):
                    return None
                node_name = self.conf_p.get_node_name_from_rpc(node_rpc)
                count = int(block_count["count"])
                return {
                    "node_name": node_name,
                    "count": count,
                    "cemented": block_count["cemented"],
                    "version": version_rpc_call
                }
            except (asyncio.TimeoutError, Exception):
                return None

        results = await asyncio.gather(*(get_block_count_for_node(node_rpc) for node_rpc in nodes_rpc))
        nodes_block_count = [result for result in results if result is not None]
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

    async def _is_rpc_available(self,
                                container: str,
                                timeout: int = 3) -> Tuple[str, bool]:
        rpc_url = self.conf_p.get_node_rpc(container)
        try:
            nano_rpc = NanoRpc(rpc_url)
            block_count = await nano_rpc.block_count()
            if block_count:
                return container, True
        except Exception as e:
            logger.warning(
                f"RPC {rpc_url} not yet reachable for node {container}: {str(e)}"
            )

        return container, False

    async def _wait_for_rpc_availability(self,
                                         nodes_name: List[str] = None,
                                         wait: bool = True,
                                         timeout: int = 10,
                                         max_timeout_s: int = 45) -> None:
        start_time = time.time()
        nodes_name = nodes_name or self.conf_p.get_nodes_name()
        logger.warning(nodes_name)

        async def get_unavailable_nodes(nodes: List[str], timeout: int) -> List[str]:
            results = await asyncio.gather(*(self._is_rpc_available(node, timeout) for node in nodes))
            unavailable_nodes = [node for node, (node_name, available) in zip(
                nodes, results) if not available]
            return unavailable_nodes

        nodes_to_check = nodes_name.copy()

        while len(nodes_to_check) > 0:
            if not wait:
                break
            nodes_to_check = await get_unavailable_nodes(nodes_to_check, timeout)
            if time.time() - start_time > max_timeout_s:
                raise ValueError(
                    f"TIMEOUT: RPCs not reachable for nodes {nodes_to_check}")
            if len(nodes_to_check) > 0:
                await asyncio.sleep(1)  # Asynchronous sleep

        logger.info("Nodes %s reachable", nodes_name)

    def online_containers_status(self, online_containers: List[str],
                                 total_nodes) -> str:

        online_count = len(online_containers)
        if online_count == total_nodes:
            return f"All {online_count} containers online"
        else:
            return f"{online_count}/{total_nodes} containers online"

    async def conf_edit(self, payload):
        self.conf_p.modify_nanolocal_config(payload["path"], payload["value"])
        return True

    @log_on_success
    async def network_status(self, nodes_name: Optional[List[str]] = None) -> str:
        if nodes_name == []:
            return ""

        nodes_name = self.conf_p.get_nodes_name()
        online_containers = self._online_containers(nodes_name)
        status_msg = self.online_containers_status(online_containers,
                                                   len(nodes_name))
        # if "All" not in status_msg:
        #     return status_msg

        nodes_block_count = await self._get_nodes_block_counts(online_containers)
        return status_msg + self._generate_network_status_report(
            nodes_name, nodes_block_count)

    async def _create_docker_compose_file(self, genesis_only=False):
        extract_packaged_services_to_disk(self.nano_nodes_path)
        if genesis_only:
            genesis_name = self.conf_p.get_nodes_name()[0]
            self.conf_p.keep_nodes_by_name([genesis_name])
        self._prepare_nodes(genesis_only=genesis_only)
        self._generate_docker_compose_env_file()
        self._generate_docker_compose_yml_file()
        self.docker_interface.create_network(self.conf_p.get_network_name())
        self._initilaise_services_configs(self.conf_p)

        logger.success(
            f"Docker Compose file created at {self.compose_yml_path}")
        return None, "\n".join(self.conf_p.get_enabled_services())

    def _initilaise_services_configs(self, config: ConfigParser):
        if bool(config.get_config_value("nanocap_enable")):
            network_name = config.get_network_name()
            device_ip = self.docker_interface.get_network_gateway(network_name)
            config.set_nanocap_device_ip(device_ip)

    def _validator_rpc(self, nodes=None, payload=None):
        if not payload:
            raise ValueError(
                "The --payload argument is required for the 'rpc' command.")
        return nodes, payload

    def _validator_conf_edit(self, nodes=None, payload=None):
        if payload is None:
            raise ValueError(
                "payload must be provided '{\"path\" : ... , \"value\": ...}'")
        if "path" not in payload:
            raise ValueError("key \"path\" must be provided")
        if "value" not in payload:
            raise ValueError("key \"value\" must be provided")

        return nodes, payload

    @log_on_success
    async def run_rpc(self, payload=None, nodes=None):
        if nodes is None:
            nodes = self.conf_p.get_nodes_name()

        tasks = []
        for node in nodes:
            node_rpc = NanoRpc(self.conf_p.get_node_rpc(node))
            task = node_rpc.nanorpc.rpc.process_payloads([payload])
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return None, json.dumps(responses, indent=2)


    @log_on_success
    async def init_wallets(self):
        init_blocks = InitialBlocks(self.conf_p,
                                    self.conf_p.get_nodes_rpc()[0])

        async def process_node(node_name):
            await self._wait_for_rpc_availability([node_name])

            if node_name == self.conf_p.get_genesis_node_name():
                await init_blocks.create_node_wallet(
                    self.conf_p.get_node_config(
                        self.conf_p.get_genesis_node_name())["rpc_url"],
                    self.conf_p.get_genesis_node_name(),
                    private_key=self.conf_p.config_dict["genesis_key"])
            else:
                await init_blocks.create_node_wallet(
                    self.conf_p.get_node_config(node_name)["rpc_url"],
                    node_name,
                    seed=self.conf_p.get_node_config(node_name)["seed"])

        node_names = self.conf_p.get_nodes_name()
        await asyncio.gather(*(process_node(node_name) for node_name in node_names))

        # return without logging for unit tests
        return init_blocks.logger.pop("InitialBlocks")

    async def _create_wallet(self, node_name, init_blocks):
        # Extract wallet creation logic into a separate coroutine
        if node_name == self.conf_p.get_genesis_node_name():
            await init_blocks.create_node_wallet(
                self.conf_p.get_node_config(self.conf_p.get_genesis_node_name())["rpc_url"],
                self.conf_p.get_genesis_node_name(),
                private_key=self.conf_p.config_dict["genesis_key"])
        else:
            await init_blocks.create_node_wallet(
                self.conf_p.get_node_config(node_name)["rpc_url"],
                node_name,
                seed=self.conf_p.get_node_config(node_name)["seed"])

    @log_on_success
    async def init_nodes(self):
        await self.init_wallets()
        init_blocks = InitialBlocks(self.conf_p,
                                    self.conf_p.get_nodes_rpc()[0])
        return await init_blocks.publish_initial_blocks()

    @log_on_success
    async def beta_create(self):
        await self.init_containers(genesis_only=True)

    @log_on_success
    async def beta_init(self):
        genesis_name = self.conf_p.get_nodes_name()[0]
        self.start_containers([genesis_name])
        init_blocks = InitialBlocks(self.conf_p,
                                    self.conf_p.get_nodes_rpc()[0])
        return init_blocks.publish_initial_blocks(move_weight=False)

    @log_on_success
    async def reset_nodes_data(self, nodes: Optional[List[str]] = None):
        await self.stop_containers(nodes)
        nodes_to_process = nodes or ['.']

        for node in nodes_to_process:
            node_path = Path(self.nano_nodes_path) / node if nodes else Path(
                self.nano_nodes_path)
            files_to_remove = ['data.ldb', 'wallets.ldb', 'rocksdb']

            for file_pattern in files_to_remove:
                for file_path in node_path.rglob(file_pattern):
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()

    @log_on_success
    async def init_containers(self, genesis_only=False):
        await self._create_docker_compose_file(genesis_only=genesis_only)
        await self.build_containers()

    @log_on_success
    async def restart_containers(self, nodes: Optional[List[str]] = None):
        return None, self.docker_interface.compose_restart(nodes)

    @log_on_success
    async def build_containers(self):
        return None, self.docker_interface.compose_build()

    @log_on_success
    async def start_containers(self, nodes: Optional[List[str]] = None):
        self.docker_interface.compose_start(nodes)
        await self._wait_for_rpc_availability(nodes)

    @log_on_success
    async def start_all_nodes(self):
        nodes = self.conf_p.get_nodes_name()
        self.docker_interface.compose_start(nodes)
        await self._wait_for_rpc_availability(nodes)

    @log_on_success
    async def stop_containers(self, nodes: Optional[List[str]] = None):
        # by default, stops all containers (also services like nanolooker, monitor or prom-exporter)
        self.docker_interface.compose_stop(nodes)

    @log_on_success
    async def stop_all_nodes(self):
        # stops all nodes but leaves services running
        nodes = self.conf_p.get_nodes_name()
        self.docker_interface.compose_stop(nodes)

    @log_on_success
    async def remove_containers(self):
        containers = self.conf_p.get_containers_name()
        if containers:
            self.docker_interface.compose_down()
        started_count = self.docker_interface.container_count(containers)
        removed_count = len(containers) - started_count
        return f"{removed_count} containers have been removed"

    @log_on_success
    async def destroy(self, remove_files=False):
        # Stop and remove containers
        await self.remove_containers()

        # Remove the created files and folders if remove_files is True
        if remove_files:
            return None, shutil_rmtree(self.nano_nodes_path)

    @log_on_success
    async def update(self):
        self.docker_interface.compose_pull()
        # Remove containers and networks
        await self.remove_containers()
        await self.build_containers()

    def _filter_args(self, func, **kwargs):
        sig = inspect.signature(func)
        filtered_args = {
            k: v
            for k, v in kwargs.items() if k in sig.parameters
        }
        return filtered_args

    async def execute_command(self, command, nodes=None, payload=None):
        if command not in self.command_mapping:
            raise ValueError(f"Invalid command: {command}")

        command_func, validator_func = self.command_mapping[command]

        if validator_func is not None:
            filtered_validator_args = self._filter_args(validator_func,
                                                        nodes=nodes,
                                                        payload=payload)
            validated_nodes, validated_payload = validator_func(
                **filtered_validator_args)
        else:
            validated_nodes, validated_payload = nodes, payload

        filtered_command_args = self._filter_args(command_func,
                                                  nodes=validated_nodes,
                                                  payload=validated_payload)
        await command_func(**filtered_command_args)


if __name__ == "__main__":
    pass
