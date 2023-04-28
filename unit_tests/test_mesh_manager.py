#!./venv_py/bin/python
import unittest
from app.mesh_manager import NanoMeshManager
from app.modules.nl_rpc import NanoRpc
import time
import pytest
from typing import Tuple


@pytest.fixture
def nanomesh_fixture() -> Tuple[NanoMeshManager, NanoRpc]:
    # Setup code here
    manager = NanoMeshManager("unit_tests/configs", "unittest")
    nano_rpc = NanoRpc("http://127.0.0.1:45000")

    yield manager, nano_rpc

    # Teardown code here
    manager.destroy()


def test_start_command(nanomesh_fixture):
    manager, nano_rpc = nanomesh_fixture
    manager.create_docker_compose_file()
    manager.start_containers()
    genesis_account_data = nano_rpc.account_info(
        "xrb_1fzwxb8tkmrp8o66xz7tcx65rm57bxdmpitw39ecomiwpjh89zxj33juzt6p")
    genesis_account_expected = {
        "frontier":
        "E670DF81878460B76B3425EC399800E1219A4387B11A4841B16CE260A9F36917",
        "open_block":
        "E670DF81878460B76B3425EC399800E1219A4387B11A4841B16CE260A9F36917",
        "representative_block":
        "E670DF81878460B76B3425EC399800E1219A4387B11A4841B16CE260A9F36917",
        "balance": "340282366920938463463374607431768211455",
        "confirmed_balance": "340282366920938463463374607431768211455",
        "modified_timestamp": "1682720362",
        "block_count": "1",
        "account_version": "0",
        "confirmed_height": "1",
        "confirmed_frontier":
        "E670DF81878460B76B3425EC399800E1219A4387B11A4841B16CE260A9F36917",
        "representative":
        "nano_1fzwxb8tkmrp8o66xz7tcx65rm57bxdmpitw39ecomiwpjh89zxj33juzt6p",
        "confirmed_representative":
        "nano_1fzwxb8tkmrp8o66xz7tcx65rm57bxdmpitw39ecomiwpjh89zxj33juzt6p",
        "pending": "0",
        "receivable": "0",
        "confirmed_pending": "0",
        "confirmed_receivable": "0"
    }
    assert genesis_account_data == genesis_account_expected
