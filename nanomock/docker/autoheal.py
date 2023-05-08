import re
from nanomock.internal.utils import subprocess_run_capture_output, get_mock_logger
from subprocess import CalledProcessError


class DockerAutoHeal():

    logger = get_mock_logger()

    def __init__(self, max_heal_attampts=10):
        self.max_heal_attemps = max_heal_attampts

    def _get_error_mapping(self):
        error_mapping = {
            "address_in_use": {
                "error_msg": "programming external connectivity on endpoint",
                "heal_method": self._heal_address_in_use
            },
            "docker_in_use": {
                "error_msg":
                "Error response from daemon: Conflict. The container name",
                "heal_method": self._heal_docker_in_use
            }
        }
        return error_mapping

    def is_healable(self, stderr: str):
        error_mapping = self._get_error_mapping()

        matching_errors = [
            error_data for error_data in error_mapping.values()
            if error_data["error_msg"] in stderr
        ]

        if matching_errors:
            error_msg = matching_errors[0]["error_msg"]
            healing_method = matching_errors[0]["heal_method"]
            healing_method(error_msg, stderr)
            return True

        return False

    def _heal_address_in_use(self, error_msg, stderr):
        error_msg = "programming external connectivity on endpoint"

        container_name = re.search(r"{} (\w+)".format(error_msg),
                                   stderr).group(1)
        subprocess_run_capture_output(
            f"docker stop -t 0 {container_name} && sleep 5 && docker start {container_name}",
            shell=True)
        return True

    def _heal_docker_in_use(self, error_msg, stderr):
        pattern = r'{} "/([^"]+)"'.format(error_msg)
        match = re.search(pattern, stderr)
        if match:
            container_name = match.group(1)
            subprocess_run_capture_output(
                f"docker stop -t 0 {container_name} && docker rm {container_name} && sleep 5",
                shell=True)
            return True
        return False

    def try_heal(self, error: CalledProcessError, cmd_shell, cmd_cwd):
        stderr = error.stderr
        attempt = 1
        if self.is_healable(stderr):
            while attempt <= self.max_heal_attemps:
                self.logger.warning("Retry attempt %s\n%s", attempt, stderr)
                try:
                    return subprocess_run_capture_output(
                        error.cmd, cmd_shell, cmd_cwd)
                except CalledProcessError as heal_error:
                    self.logger.error("Attempt %s failed\n%s", attempt,
                                      heal_error.stderr)
                    attempt += 1
        raise ValueError(error.stderr)
