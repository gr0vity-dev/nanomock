from nanomock.nanomock_manager import NanoLocalManager
from nanomock.modules.nl_rpc import NanoRpc
import json
import pytest
from typing import Tuple
from subprocess import CalledProcessError
import re
from pathlib import Path
import asyncio


@pytest.fixture(scope="class", autouse=True)
def local_fixture(request) -> Tuple[NanoLocalManager, NanoRpc]:
    # Setup code here
    manager = NanoLocalManager("unit_tests/configs", "unittest")
    nano_rpc = NanoRpc("http://127.0.0.1:45900")

    request.cls.manager, request.cls.nano_rpc = manager, nano_rpc

    yield manager, nano_rpc

    # Teardown code here
    asyncio.run(manager.execute_command("destroy"))


class TestMockNetwork:

    @classmethod
    def setup_class(cls):
        cls.manager: NanoLocalManager
        cls.nano_rpc: NanoRpc

        async def setup_network(cls):
            await cls.manager.execute_command("destroy")
            await cls.manager.execute_command("create")
            await cls.manager.execute_command("start")
            await cls.manager.execute_command("status")

        asyncio.run(setup_network(cls))

    @ pytest.mark.asyncio
    async def test_genesis_account(self):
        genesis_account_data = await self.nano_rpc.account_info(
            "xrb_1fzwxb8tkmrp8o66xz7tcx65rm57bxdmpitw39ecomiwpjh89zxj33juzt6p")
        genesis_account_data.pop("modified_timestamp")
        with open('unit_tests/data/expected_genesis_account.json', 'r', encoding='utf-8') as f:
            genesis_account_expected = json.load(f)
        assert genesis_account_data == genesis_account_expected

    @ pytest.mark.asyncio
    async def test_network_status(self):
        status = await self.manager.network_status()
        with open('unit_tests/data/expected_network_status.txt', 'r', encoding='utf-8') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    @ pytest.mark.asyncio
    async def test_network_stop(self):
        await self.manager.stop_containers(["unittest_pr1"])
        status = await self.manager.network_status()
        with open('unit_tests/data/expected_network_status_down.txt',
                  'r', encoding='utf-8') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    @ pytest.mark.asyncio
    async def test_network_start(self):
        await self.manager.start_containers(["unittest_pr1"])
        status = await self.manager.network_status()
        with open('unit_tests/data/expected_network_status.txt', 'r', encoding='utf-8') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    @ pytest.mark.asyncio
    async def test_network_stop_cmd(self):
        await self.manager.execute_command("stop", nodes=["unittest_pr1"])
        status = await self.manager.network_status()
        with open('unit_tests/data/expected_network_status_down.txt',
                  'r', encoding='utf-8') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    @ pytest.mark.asyncio
    async def test_network_start_cmd(self):
        await self.manager.execute_command("start", nodes=["unittest_pr1"])
        status = await self.manager.network_status()
        with open('unit_tests/data/expected_network_status.txt', 'r', encoding='utf-8') as f:
            expected_network_status = f.read()
        assert status == expected_network_status

    @ pytest.mark.asyncio
    async def test_network_init(self):
        log = await self.manager.init_nodes()
        log_output = "\n".join(log)
        with open('unit_tests/data/expected_init_log.txt', 'r', encoding='utf-8') as f:
            expected_output = f.read()

        assert log_output == expected_output, f"Log output '{log_output}' does not match expected output '{expected_output}'"

    @ pytest.mark.asyncio
    async def test_network_init_wallets(self):
        log_string = await self.manager.init_wallets()
        log_output = "\n".join(log_string)

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

    @ pytest.mark.asyncio
    async def test_network_reset(self):
        nano_nodes_path = Path("unit_tests/configs/nano_nodes")
        await self.manager.reset_nodes_data()

        keep_file_path = nano_nodes_path / "keep.ldb"
        data_files = list(nano_nodes_path.glob('**/data.ldb'))
        wallet_files = list(nano_nodes_path.glob('**/wallets.ldb'))

        # Assert keep.ldb is still there
        assert keep_file_path.exists()
        assert not data_files
        assert not wallet_files
