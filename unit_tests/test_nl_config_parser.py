import unittest
import json
from nanomock.modules.nl_parse_config import ConfigParser
import platform

os_name = platform.system()


class TestConfigParser(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None  # Allows unlimited diff output in assertion failures

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

    def _get_config_parser(self, conf_dir="unit_tests/configs/mock_nl_config", conf_name="conf_edit_config.toml"):
        config_parser = ConfigParser(conf_dir, conf_name)
        conf_file = config_parser.conf_rw.read_toml(f"{conf_dir}/{conf_name}")
        return config_parser, conf_file
    
       

    def _load_modify_conf_edit(self, nested_path, nested_value):
        conf_dir = "unit_tests/configs/mock_nl_config"
        conf_name = "conf_edit_config.toml"

        config_parser = ConfigParser(conf_dir, conf_name)
        modified_config = config_parser.modify_nanolocal_config(nested_path,
                                                                nested_value,
                                                                save=False)
        conf_file = config_parser.conf_rw.read_toml(f"{conf_dir}/{conf_name}")

        return conf_file, modified_config.data

    def test_parse_default_path(self):
        config_parser = ConfigParser("unit_tests/configs", "nl_config.toml")
        config_parser.config_dict.pop("tcpdump_filename")
        with open('unit_tests/data/expected_nl_config.json', 'r') as f:
            expected_dict = json.load(f)

        self.assertDictEqual(expected_dict, config_parser.config_dict)

    def test_mock_conf_blkio_disk_cpu_mem(self):
        # This will test that "disk"
        config_parser = ConfigParser("unit_tests/configs/mock_nl_config",
                                     "blkio_disk_cpu_mem.toml")
        config_parser.set_docker_compose()
        extracted_values = self._extract_blkio_config_from_compose_dict(
            config_parser.compose_dict)
        if os_name == "Darwin":
            expected_file_path = "unit_tests/data/expected_nl_config_blkio_disk_mem_cpu_darwin.json"
        else:
            expected_file_path = "unit_tests/data/expected_nl_config_blkio_disk_mem_cpu.json"
        with open(expected_file_path, 'r') as f:
            expected_dict = json.load(f)

        self.assertDictEqual(expected_dict, extracted_values)

    def test_mock_bitmath_conversion(self):
        # This will test that "disk"
        config_parser = ConfigParser("unit_tests/configs/mock_nl_config",
                                     "bitmath_conversion.toml")
        config_parser.set_docker_compose()
        extracted_values = self._extract_blkio_config_from_compose_dict(
            config_parser.compose_dict)

        if os_name == "Darwin":
            expected_file_path = "unit_tests/data/expected_nl_config_bitmath_conversion_darwin.json"
        else:
            expected_file_path = "unit_tests/data/expected_nl_config_bitmath_conversion.json"
        with open(expected_file_path, 'r') as f:
            expected_dict = json.load(f)

        self.assertDictEqual(expected_dict, extracted_values)

    def test_conf_edit_insert_wildcard(self):
        nested_path = "representatives.nodes.*.new_key"
        nested_value = "some_value/with_sp@cial_cHars"

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        for node in loaded_config["representatives"]["nodes"]:
            node["new_key"] = nested_value

        assert loaded_config == modified_config

    def test_conf_edit_delete_wildcard(self):
        nested_path = "representatives.nodes.*.vote_weight_percent"
        nested_value = None

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        for node in loaded_config["representatives"]["nodes"]:
            node.pop("vote_weight_percent"
                     ) if "vote_weight_percent" in node else None

        assert loaded_config == modified_config

    def test_conf_edit_modify_wildcard(self):
        nested_path = "representatives.nodes.*.vote_weight_percent"
        nested_value = 33
        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        for node in loaded_config["representatives"]["nodes"]:
            node["vote_weight_percent"] = nested_value

        assert loaded_config == modified_config

    def test_conf_edit_insert_nested_key(self):
        nested_path = "representatives.ney_key"
        nested_value = "some_value/with_sp@cial_cHars"

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config["representatives"]["ney_key"] = nested_value

        assert loaded_config == modified_config

    def test_conf_edit_modify_nested_key(self):
        nested_path = "representatives.docker_tag"
        nested_value = "ok"

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config["representatives"]["docker_tag"] = nested_value

        assert loaded_config == modified_config

    def test_conf_edit_delete_nested_key(self):
        nested_path = "representatives.docker_tag"
        nested_value = None

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config["representatives"].pop("docker_tag")

        assert loaded_config == modified_config

    def test_conf_edit_insert_flat(self):
        nested_path = "new_key"
        nested_value = "some_value/with_sp@cial_cHars"

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config["new_key"] = nested_value

        assert loaded_config == modified_config

    def test_conf_edit_modify_flat(self):
        nested_path = "nanolooker_enable"
        nested_value = True

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config["nanolooker_enable"] = nested_value

        assert loaded_config == modified_config

    def test_conf_edit_delete_flat(self):
        nested_path = "nanolooker_enable"
        nested_value = None

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config.pop(nested_path)

        assert loaded_config == modified_config

    def test_connected_peers(self):
        config_parser, _ = self._get_config_parser(
            conf_name="connected_peers.toml")

        assert config_parser.get_connected_peers(
            "unittest_genesis") == ["unittest_pr1"]
        assert config_parser.get_connected_peers(
            "unittest_pr1") == ["unittest_pr2"]
        assert config_parser.get_connected_peers(
            "unittest_pr2") == ["unittest_pr1", "unittest_genesis"]

    def test_connected_peers_2(self):
        config_parser, conf_file = self._get_config_parser(
            conf_name="connected_peers.toml")

        nested_path = "nanolooker_enable"
        nested_value = False

        modified_config = config_parser.modify_nanolocal_config(
            nested_path, nested_value, save=False)

        assert conf_file == modified_config
    
    def test_add_container_node_flags(self):
        
        config_parser = ConfigParser("unit_tests/configs/mock_nl_config",
                                     "node_flags.toml")
        config_parser.set_docker_compose()
        
        commands = []
        for service_name, service_config in config_parser.compose_dict["services"].items():
            commands.append(service_config.get("command"))
            
        # Expected command after appending node_flags
        expected_command_0 = "nano_node daemon --network=test --data_path=/root/NanoTest --flag_1 --flag_2 -l"
        expected_command_1 = "nano_node daemon --network=test --data_path=/root/NanoTest --flag_1 -l"
        expected_command_2 = "nano_node daemon --network=test --data_path=/root/NanoTest --flag_3 -l"
       
            
        # Assert to check if the command in the container is as expected
        self.assertEqual(expected_command_0, commands[0])
        self.assertEqual(expected_command_1, commands[1])
        self.assertEqual(expected_command_2, commands[2])
        self.assertEqual(len(commands), 3)
    
    # def test_key_in_compose__log_level(self):
        
    #     conf_dir = "unit_tests/configs/mock_nl_config"
    #     conf_name = "conf_edit_config_test.toml"        
    #     config_parser = ConfigParser(conf_dir, conf_name)
        
        
    #     # nested_path = "representatives.log_level"
    #     # nested_value = "trace"

    #     # config_parser.modify_nanolocal_config(nested_path,nested_value)        
    #     config_parser.set_docker_compose()
        
        
    #     log_levels = []
    #     for service_name, service_config in config_parser.compose_dict["services"].items():           
    #         log_levels.append(service_config.get("log_level"))        

    #     expected_log_level = "trace"
    #     self.assertEqual(expected_log_level, log_levels[0])
        


if __name__ == '__main__':
    unittest.main()
