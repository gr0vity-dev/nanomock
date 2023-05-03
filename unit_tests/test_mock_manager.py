from nanomock.nanomock_manager import NanoLocalManager
from nanomock.modules.nl_rpc import NanoRpc
import json
import pytest
from typing import Tuple
from subprocess import CalledProcessError


@pytest.fixture(scope="class", autouse=True)
def local_fixture(request) -> Tuple[NanoLocalManager, NanoRpc]:
    # Setup code here
    manager = NanoLocalManager("unit_tests/configs", "unittest")
    nano_rpc = NanoRpc("http://127.0.0.1:45900")

    request.cls.manager, request.cls.nano_rpc = manager, nano_rpc

    yield manager, nano_rpc

    # Teardown code here
    manager.execute_command("destroy")


class TestLocal:

    @classmethod
    def setup_class(cls):
        cls.manager: NanoLocalManager
        cls.nano_rpc: NanoRpc
        cls.manager.execute_command("down")
        cls.manager.execute_command("create")
        cls.manager.execute_command("start")

    def test_genesis_account(self):
        genesis_account_data = self.nano_rpc.account_info(
            "xrb_1fzwxb8tkmrp8o66xz7tcx65rm57bxdmpitw39ecomiwpjh89zxj33juzt6p")
        genesis_account_data.pop("modified_timestamp")
        with open('unit_tests/data/expected_genesis_account.json', 'r') as f:
            genesis_account_expected = json.load(f)
        assert genesis_account_data == genesis_account_expected

    def test_network_status(self):
        status = self.manager.network_status()
        with open('unit_tests/data/expected_network_status.txt', 'r') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    def test_network_stop(self):
        self.manager.stop_containers(["unittest_pr1"])
        status = self.manager.network_status()
        with open('unit_tests/data/expected_network_status_down.txt',
                  'r') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    def test_network_start(self):
        self.manager.start_containers(["unittest_pr1"])
        status = self.manager.network_status()
        with open('unit_tests/data/expected_network_status.txt', 'r') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    def test_network_stop_cmd(self):
        self.manager.execute_command("stop", nodes=["unittest_pr1"])
        status = self.manager.network_status()
        with open('unit_tests/data/expected_network_status_down.txt',
                  'r') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    def test_network_start_cmd(self):
        self.manager.execute_command("start", nodes=["unittest_pr1"])
        status = self.manager.network_status()
        with open('unit_tests/data/expected_network_status.txt', 'r') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    def test_auto_heal_external_connectivity(self):
        #adds 10s to teh test

        cmd = "echo Hello World!"
        error = CalledProcessError(
            90,
            cmd,
            stderr=
            "Error response from daemon: driver failed programming external connectivity on endpoint unittest_pr1 (b1eba3d3066aad6cab7cd85fc0f78936c994ce872d3d08d7f2fb8552fa8768a2): Bind for 0.0.0.0:17078 failed: port is already allocated"
        )
        result = self.manager.auto_heal(error, True, None)
        assert result.args == cmd

    def test_network_init(self):

        log_output = "\n".join(self.manager.init_nodes()[3::])
        with open('unit_tests/data/expected_init_log.txt', 'r') as f:
            expected_output = f.read()

        assert log_output == expected_output, f"Log output '{log_output}' does not match expected output '{expected_output}'"

    # def test_network_init(self):
    #     self.manager.init_nodes()
    #     status = self.manager.network_status()
    #     with open('unit_tests/data/expected_network_status_init.txt',
    #               'r') as f:
    #         expected_network_status = f.read()
    #     assert status == expected_network_status


# def test_network_status_2(manager: NanoLocalManager, nano_rpc: NanoRpc):
#     manager.stop_containers(["unittest_pr2"])
#     status = manager.network_status()
#     with open('unit_tests/data/expected_network_status_2.txt', 'r') as f:
#         expected_network_status = f.read()
#     assert status == expected_network_status