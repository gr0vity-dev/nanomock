import unittest
import json
from nanomock.modules.nl_parse_config import ConfigParser


class TestConfigParser(unittest.TestCase):

    def _extract_blkio_config_from_compose_dict(self, config):
        extracted_values = {}
        for service_name, service_config in config["services"].items():
            blkio_config = service_config.get("blkio_config")
            if blkio_config:
                for key in blkio_config:
                    for item in blkio_config[key]:
                        item.pop("path", None)
            extracted_values[service_name] = {
                "blkio_config": blkio_config,
                "cpus": service_config.get("cpus"),
                "mem_limit": service_config.get("mem_limit")
            }
        return extracted_values

    def test_parse_default_path(self):
        config_parser = ConfigParser("unit_tests/configs")
        config_parser.config_dict.pop("tcpdump_filename")
        with open('unit_tests/data/expected_nl_config.json', 'r') as f:
            expected_dict = json.load(f)

        self.assertDictEqual(expected_dict, config_parser.config_dict)

    def test_mock_conf_blkio_disk_cpu_mem(self):
        #This will test that "disk"
        config_parser = ConfigParser("unit_tests/configs/mock_nl_config",
                                     config_file="blkio_disk_cpu_mem.toml")
        config_parser.set_docker_compose()
        extracted_values = self._extract_blkio_config_from_compose_dict(
            config_parser.compose_dict)
        with open('unit_tests/data/expected_nl_config_blkio_disk_mem_cpu.json',
                  'r') as f:
            expected_dict = json.load(f)

        self.assertDictEqual(expected_dict, extracted_values)

    def test_mock_bitmath_conversion(self):
        #This will test that "disk"
        config_parser = ConfigParser("unit_tests/configs/mock_nl_config",
                                     config_file="bitmath_conversion.toml")
        config_parser.set_docker_compose()
        extracted_values = self._extract_blkio_config_from_compose_dict(
            config_parser.compose_dict)
        with open('unit_tests/data/expected_nl_config_bitmath_conversion.json',
                  'r') as f:
            expected_dict = json.load(f)

        self.assertDictEqual(expected_dict, extracted_values)


if __name__ == '__main__':
    unittest.main()
