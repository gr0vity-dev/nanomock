import unittest
from unittest.mock import MagicMock
from nanolocal.internal.nl_block_tools import BlockReadWrite
import json


class TestRefactoredCode(unittest.TestCase):

    def setUp(self):
        self.block_rw = BlockReadWrite(
            "unit_tests/configs/nl_config.toml"
        )  # Replace this with the actual class name
        self.block_rw.ba = MagicMock()
        self.block_rw.ba.assert_blockgen_succeeded = MagicMock()
        self.block_rw.conf_rw = MagicMock()
        self.block_rw.conf_rw.write_json = MagicMock()

    def test_write_blocks_to_disk_nested_list(self):
        with open('unit_tests/data/read_write_blocks.json', 'r') as f:
            test_data = json.load(f)
        self.block_rw.write_blocks_to_disk(
            test_data["nested_rpc_block_list_in"], "output_path")
        self.block_rw.conf_rw.write_json.assert_called_with(
            "output_path", test_data["nested_rpc_block_list_expected_output"])

    def test_write_blocks_to_disk_dict(self):
        with open('unit_tests/data/read_write_blocks.json', 'r') as f:
            test_data = json.load(f)
        self.block_rw.write_blocks_to_disk(test_data["dict_rpc_block_list_in"],
                                           "output_path")
        self.block_rw.conf_rw.write_json.assert_called_with(
            "output_path", test_data["dict_rpc_block_list_expected_output"])


if __name__ == '__main__':
    unittest.main()
