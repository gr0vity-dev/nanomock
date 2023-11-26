from .interface import DockerInterface
from .mixin import DockerMixin
import subprocess


class MacDockerInterface(DockerMixin,DockerInterface):

    @classmethod
    def get_docker_gateway_ip(cls) -> str:
        interfaces = ["docker", "en0", "eth0"]
        ipv4_address = "127.0.0.1"  # Default address

        for interface in interfaces:
            try:
                command = f"ifconfig | grep -A1 '{interface}' | grep inet | awk '{{print $2}}' | grep -v -E '^[a-f0-9:]+%'"
                output = subprocess.check_output(command, shell=True, text=True).strip()
                # Split the output by newlines and take the first non-empty line which should be the IPv4 address.
                ipv4_address_list = [ip for ip in output.split('\n') if ip]
                if ipv4_address_list:
                    ipv4_address = ipv4_address_list[0]  # Use the first found IPv4 address
                    break  # Exit the loop if an address is found
            except subprocess.CalledProcessError:
                # This exception is raised if the subprocess exits with a non-zero status (interface not found or other issues)
                continue

        return ipv4_address
