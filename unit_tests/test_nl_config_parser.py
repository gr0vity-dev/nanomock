#!./venv_py/bin/python
import unittest
import json
from app.modules.nl_parse_config import ConfigParser


class TestConfigParser(unittest.TestCase):

    def setUp(self):
        self.example_instance = ConfigParser(
            "unit_tests/configs")  # Replace this with the actual class name

    def test_parse_default_path(self):
        self.example_instance.config_dict.pop("tcpdump_filename")
        with open('unit_tests/data/expected_nl_config.json', 'r') as f:
            expected_dict = json.load(f)

        self.assertDictEqual(expected_dict, self.example_instance.config_dict)


if __name__ == '__main__':
    unittest.main()
