from nanomock.nanomock_manager import NanoLocalManager
from nanomock.modules.nl_rpc import NanoRpc
from nanomock.docker.autoheal import DockerAutoHeal
import json
import pytest
from typing import Tuple
from subprocess import CalledProcessError
import re
from pathlib import Path


@pytest.fixture(scope="class", autouse=True)
def local_fixture(request) -> Tuple[NanoLocalManager, NanoRpc]:
    # Setup code here
    manager = NanoLocalManager("unit_tests/configs", "unittest")
    nano_rpc = NanoRpc("http://127.0.0.1:45900")

    request.cls.manager, request.cls.nano_rpc = manager, nano_rpc

    yield manager, nano_rpc

    # Teardown code here
    manager.execute_command("destroy")


class TestMockNetwork:

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
        healer = DockerAutoHeal(3)
        result = healer.try_heal(error, True, None)
        assert result.args == cmd

    def test_network_init(self):

        log_output = "\n".join(self.manager.init_nodes())
        with open('unit_tests/data/expected_init_log.txt', 'r') as f:
            expected_output = f.read()

        assert log_output == expected_output, f"Log output '{log_output}' does not match expected output '{expected_output}'"

    def test_network_init_wallets(self):
        log_output = "\n".join(self.manager.init_wallets())

        # Define the pattern for the expected log output
        pattern = (
            r"(WALLET [A-F0-9]{64} CREATED FOR unittest_genesis WITH ACCOUNT nano_1fzwxb8tkmrp8o66xz7tcx65rm57bxdmpitw39ecomiwpjh89zxj33juzt6p)\n"
            r"(WALLET [A-F0-9]{64} CREATED FOR unittest_pr1 WITH ACCOUNT nano_1ge7edbt774uw7z8exomwiu19rd14io1nocyin5jwpiit3133p9eaaxn74ub)\n"
            r"(WALLET [A-F0-9]{64} CREATED FOR unittest_pr2 WITH ACCOUNT nano_3sz3bi6mpeg5jipr1up3hotxde6gxum8jotr55rzbu9run8e3wxjq1rod9a6)"
        )

        assert re.fullmatch(
            pattern, log_output
        ), f"Log output '{log_output}' does not match the expected pattern"

    def test_network_ldb_exists(self):
        nano_nodes_path = Path("unit_tests/configs/nano_nodes")

        keep_file_path = nano_nodes_path / "keep.ldb"
        keep_file_path.touch()
        data_files = list(nano_nodes_path.glob('**/data.ldb'))
        wallet_files = list(nano_nodes_path.glob('**/wallets.ldb'))
        assert data_files
        assert wallet_files
        assert keep_file_path.exists()

    def test_network_reset(self):
        nano_nodes_path = Path("unit_tests/configs/nano_nodes")
        self.manager.reset_nodes_data()

        keep_file_path = nano_nodes_path / "keep.ldb"
        data_files = list(nano_nodes_path.glob('**/data.ldb'))
        wallet_files = list(nano_nodes_path.glob('**/wallets.ldb'))

        # Assert keep.ldb is still there
        assert keep_file_path.exists()
        assert not data_files
        assert not wallet_files
