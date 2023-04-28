#!./venv_py/bin/python
import unittest
from unittest.mock import MagicMock
from app.internal.nl_block_tools import BlockReadWrite


class TestRefactoredCode(unittest.TestCase):

    def setUp(self):
        self.example_instance = BlockReadWrite(
        )  # Replace this with the actual class name
        self.example_instance.ba = MagicMock()
        self.example_instance.ba.assert_blockgen_succeeded = MagicMock()
        self.example_instance.conf_rw = MagicMock()
        self.example_instance.conf_rw.write_json = MagicMock()

    def test_write_blocks_to_disk_nested_list(self):
        nested_rpc_block_list = [[
            {
                "success": True,
                "hash": "hash1",
                "block": "block1",
                "account_data": {
                    "source_seed": "seed1"
                }
            },
            {
                "success": True,
                "hash": "hash2",
                "block": "block2",
                "account_data": {
                    "source_seed": "seed2"
                }
            },
        ],
                                 [
                                     {
                                         "success": True,
                                         "hash": "hash3",
                                         "block": "block3",
                                         "account_data": {
                                             "source_seed": None
                                         }
                                     },
                                     {
                                         "success": True,
                                         "hash": "hash4",
                                         "block": "block4",
                                         "account_data": {
                                             "source_seed": "seed4"
                                         }
                                     },
                                 ]]
        expected_output = {
            "h": [["hash1", "hash2"], ["hash3", "hash4"]],
            "s": [["seed1", "seed2"], ["seed4"]],
            "b": [["block1", "block2"], ["block3", "block4"]],
        }
        self.example_instance.write_blocks_to_disk(nested_rpc_block_list,
                                                   "output_path")
        self.example_instance.conf_rw.write_json.assert_called_with(
            "output_path", expected_output)

    def test_write_blocks_to_disk_dict(self):
        dict_rpc_block_list = [
            {
                "success": True,
                "hash": "hash1",
                "block": "block1",
                "account_data": {
                    "source_seed": "seed1"
                }
            },
            {
                "success": True,
                "hash": "hash2",
                "block": "block2",
                "account_data": {
                    "source_seed": "seed2"
                }
            },
            {
                "success": True,
                "hash": "hash3",
                "block": "block3",
                "account_data": {
                    "source_seed": None
                }
            },
            {
                "success": True,
                "hash": "hash4",
                "block": "block4",
                "account_data": {
                    "source_seed": "seed4"
                }
            },
        ]
        expected_output = {
            "h": [["hash1", "hash2", "hash3", "hash4"]],
            "s": [["seed1", "seed2", "seed4"]],
            "b": [["block1", "block2", "block3", "block4"]],
        }
        self.example_instance.write_blocks_to_disk(dict_rpc_block_list,
                                                   "output_path")
        self.example_instance.conf_rw.write_json.assert_called_with(
            "output_path", expected_output)


if __name__ == '__main__':
    unittest.main()
