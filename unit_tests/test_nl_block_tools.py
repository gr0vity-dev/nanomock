#!./venv_py/bin/python
import unittest
from unittest.mock import MagicMock
from app.internal.nl_block_tools import BlockReadWrite
import json


class TestRefactoredCode(unittest.TestCase):

    def setUp(self):
        self.example_instance = BlockReadWrite(
        )  # Replace this with the actual class name
        self.example_instance.ba = MagicMock()
        self.example_instance.ba.assert_blockgen_succeeded = MagicMock()
        self.example_instance.conf_rw = MagicMock()
        self.example_instance.conf_rw.write_json = MagicMock()

    def test_write_blocks_to_disk_nested_list(self):
        with open('unit_tests/data/read_write_blocks.json', 'r') as f:
            test_data = json.load(f)
        self.example_instance.write_blocks_to_disk(
            test_data["nested_rpc_block_list_in"], "output_path")
        self.example_instance.conf_rw.write_json.assert_called_with(
            "output_path", test_data["nested_rpc_block_list_expected_output"])

    def test_write_blocks_to_disk_dict(self):
        with open('unit_tests/data/read_write_blocks.json', 'r') as f:
            test_data = json.load(f)
        self.example_instance.write_blocks_to_disk(
            test_data["dict_rpc_block_list_in"], "output_path")
        self.example_instance.conf_rw.write_json.assert_called_with(
            "output_path", test_data["dict_rpc_block_list_expected_output"])


if __name__ == '__main__':
    unittest.main()
