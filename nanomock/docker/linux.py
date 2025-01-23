from .interface import DockerInterface
from .mixin import DockerMixin
import subprocess


class LinuxDockerInterface(DockerMixin, DockerInterface):

    @classmethod
    def get_docker_gateway_ip(cls) -> str:
        # Try ip address first
        ip_cmd = (
            "ip address show docker0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1"
        )
        try:
            output = subprocess.check_output(ip_cmd, shell=True, text=True).strip()
            if output:
                return output
        except subprocess.CalledProcessError:
            pass

        # Fallback to ifconfig if available
        ifconfig_cmd = "ifconfig docker0 2>/dev/null | grep 'inet ' | awk '{print $2}'"
        try:
            output = subprocess.check_output(
                ifconfig_cmd, shell=True, text=True
            ).strip()
            if output:
                return output
        except subprocess.CalledProcessError:
            pass

        # Last resort - try docker network inspect
        docker_cmd = (
            "docker network inspect bridge | grep Gateway | awk -F'\"' '{print $4}'"
        )
        try:
            output = subprocess.check_output(docker_cmd, shell=True, text=True).strip()
            if output:
                return output
        except subprocess.CalledProcessError:
            pass

        raise RuntimeError("Could not determine Docker gateway IP")
