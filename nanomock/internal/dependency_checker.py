import os
import json
import subprocess
from typing import List


class DependencyChecker:

    def __init__(self):
        self.dependencies = self._load_dependencies_config()

    @staticmethod
    def _load_dependencies_config():
        return {
            "docker": ["docker", "--version"],
            "docker-compose": ["docker-compose", "--version"]
        }

        # config_file = "dependencies_config.json"
        # with open(config_file, "r") as f:
        #     return json.load(f)

    def check_dependencies(self):
        missing_dependencies = []
        for dep, command in self.dependencies.items():
            if not self._is_dependency_installed(command):
                missing_dependencies.append(dep)

        if missing_dependencies:
            self._display_missing_dependencies_instructions(
                missing_dependencies)
            return False
        return True

    @staticmethod
    def _is_dependency_installed(command: str) -> bool:
        try:
            subprocess.run(command,
                           check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def _display_missing_dependencies_instructions(
            missing_dependencies: List[str]):
        print("The following dependencies are missing:")
        for dep in missing_dependencies:
            print(f"- {dep}")

        print("\nPlease install the missing dependencies and try again.")


if __name__ == "__main__":
    checker = DependencyChecker()
    checker.check_dependencies()
