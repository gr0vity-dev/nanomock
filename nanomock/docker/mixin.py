from .interface import DockerInterface
import subprocess
import json

from typing import List, Optional
from nanomock.internal.utils import subprocess_run_capture_output


# Holds all the shared os independant implementations
class DockerMixin(DockerInterface):

    def __init__(self, compose_path: str, project_name: str):
        self.compose_path = compose_path
        self.project_name = project_name

    @staticmethod
    def _get_stop_flag(force_stop: bool) -> str:
        return "-t 0" if force_stop else ""

    def _get_docker_compose_command(self,
                                    command,
                                    nodes: Optional[List[str]] = None):
        base_command = [
            "docker-compose", "-f",
            str(self.compose_path), "-p", self.project_name
        ]
        base_command.extend(command)
        if nodes:
            base_command.extend(nodes)
        return " ".join(base_command)

    def _run_command(self, base_command):
        subprocess_run_capture_output(base_command)

    def restart_container(self,
                          container_name: str,
                          command_interval: int = 0,
                          force_stop=True) -> bool:
        stop_flag = self._get_stop_flag(force_stop)
        subprocess_run_capture_output(
            f"docker stop {stop_flag} {container_name} && sleep {command_interval} && docker start {container_name}")
        return True

    def stop_and_remove_container(self, container_name: str, force_stop=True):
        stop_flag = self._get_stop_flag(force_stop)
        subprocess_run_capture_output(
            f"docker stop {stop_flag} {container_name} && docker rm {container_name}")

    def check_container_running(self, container_name: str):
        cmd = f"docker ps |grep {container_name}$ | wc -l"
        res = subprocess_run_capture_output(cmd)
        return res

    def compose_start(self, nodes: Optional[List[str]] = None):
        cmd = self._get_docker_compose_command(["up", "-d"], nodes)
        return self._run_command(cmd)

    def compose_restart(self, nodes: Optional[List[str]] = None):
        cmd = self._get_docker_compose_command(["restart"], nodes)
        return self._run_command(cmd)

    def compose_stop(self, nodes: Optional[List[str]] = None):
        cmd = self._get_docker_compose_command(["stop"], nodes)
        return self._run_command(cmd)

    def compose_down(self, nodes: Optional[List[str]] = None):
        cmd = self._get_docker_compose_command(["down"], nodes)
        return self._run_command(cmd)

    def compose_build(self):
        cmd = self._get_docker_compose_command(["build"])
        return self._run_command(cmd)

    def compose_pull(self):
        cmd = self._get_docker_compose_command(["pull"])
        return self._run_command(cmd)

    def container_count(self, container_names):
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            text=True,
        )

        existing_container_names = result.stdout.strip().split("\n")

        count = 0
        for name in container_names:
            if name in existing_container_names:
                count += 1

        return count

    def create_network(self, network_name):
        try:
            subprocess.run(["docker", "network", "create", network_name],
                           check=True,
                           capture_output=True)
        except subprocess.CalledProcessError as exc:
            output = exc.stderr.decode()
            if exc.returncode == 1 and "already exists" in output:
                print(f"The network '{network_name}' already exists.")
            else:
                raise Exception(f"Error creating network: {exc}") from exc

    def get_network_gateway(self, network_name):
        try:
            completed_process = subprocess.run(
                ["docker", "network", "inspect", network_name],
                capture_output=True,
                check=True)
            output = completed_process.stdout.decode()
            data = json.loads(output)
            gateway = data[0]['IPAM']['Config'][0]['Gateway']
            return gateway
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error inspecting network: {e}") from e
        except KeyError:
            raise Exception(
                "Unable to find the Gateway in the network's IPAM Config.")
