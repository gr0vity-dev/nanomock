import unittest
import json
from nanolocal.modules.nl_parse_config import ConfigParser


class TestConfigParser(unittest.TestCase):

    def setUp(self):
        self.config_parser = ConfigParser("unit_tests/configs")

    def test_parse_default_path(self):
        self.config_parser.config_dict.pop("tcpdump_filename")
        with open('unit_tests/data/expected_nl_config.json', 'r') as f:
            expected_dict = json.load(f)

        self.assertDictEqual(expected_dict, self.config_parser.config_dict)


if __name__ == '__main__':
    unittest.main()
