from .interface import DockerInterface
from .mixin import DockerMixin
import subprocess
import socket


class MacDockerInterface(DockerMixin, DockerInterface):

    @classmethod
    def get_docker_gateway_ip(cls) -> str:
        """Get the local IP address using multiple fallback methods."""
        # Method 1: Using socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            pass

        # Method 2: Using networksetup
        try:
            # Get active network service
            service = subprocess.check_output(
                ["networksetup", "-listnetworkserviceorder"],
                text=True
            )
            # Look for "Wi-Fi" or "Ethernet" in the active services
            for line in service.split('\n'):
                if "Wi-Fi" in line or "Ethernet" in line:
                    service_name = line.split(')')[1].strip()
                    ip = subprocess.check_output(
                        ["networksetup", "-getinfo", service_name],
                        text=True
                    )
                    for info_line in ip.split('\n'):
                        if "IP address" in info_line:
                            return info_line.split(': ')[1].strip()
        except:
            pass

        # Method 3: Using ifconfig as last resort
        try:
            ifconfig = subprocess.check_output(["ifconfig"], text=True)
            for line in ifconfig.split('\n'):
                if "inet " in line and "127.0.0.1" not in line:
                    return line.split("inet ")[1].split(" ")[0]
        except:
            pass

        raise ConnectionError("Could not determine local IP address")
