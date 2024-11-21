import unittest
import json
from nanomock.modules.nl_parse_config import ConfigParser
import platform
import time

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
        self._load_modify_conf_edit(nested_path, "")

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
        self._load_modify_conf_edit(nested_path, "")

    def test_conf_edit_modify_wildcard(self):
        nested_path = "representatives.nodes.*.vote_weight_percent"
        nested_value = 33
        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        for node in loaded_config["representatives"]["nodes"]:
            node["vote_weight_percent"] = nested_value

        assert loaded_config == modified_config
        self._load_modify_conf_edit(nested_path, "")

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
        self._load_modify_conf_edit(nested_path, "")

    def test_conf_edit_delete_nested_key(self):
        nested_path = "representatives.docker_tag"
        nested_value = None

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config["representatives"].pop("docker_tag")

        assert loaded_config == modified_config
        self._load_modify_conf_edit(nested_path, "")

    def test_conf_edit_insert_flat(self):
        nested_path = "new_key"
        nested_value = "some_value/with_sp@cial_cHars"

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config["new_key"] = nested_value

        assert loaded_config == modified_config
        self._load_modify_conf_edit(nested_path, "")

    def test_conf_edit_modify_flat(self):
        nested_path = "nanolooker_enable"
        nested_value = True

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config["nanolooker_enable"] = nested_value

        assert loaded_config == modified_config
        self._load_modify_conf_edit(nested_path, "")

    def test_conf_edit_delete_flat(self):
        nested_path = "nanolooker_enable"
        nested_value = None

        loaded_config, modified_config = self._load_modify_conf_edit(
            nested_path, nested_value)

        # Add the new key-value pair to each node in the loaded_config
        loaded_config.pop(nested_path)

        assert loaded_config == modified_config
        self._load_modify_conf_edit(nested_path, "")

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
        self._load_modify_conf_edit(nested_path, "")

    def test_add_container_node_flags(self):
        config_parser = ConfigParser(
            "unit_tests/configs/mock_nl_config", "node_flags.toml")
        config_parser.set_docker_compose()

        commands = []
        for service_name, service_config in config_parser.compose_dict["services"].items():
            commands.append(service_config.get("command"))

        # Use container type and path from config
        user_id = config_parser.get_user_id()
        container_type = config_parser.get_container_type(user_id)
        docker_compose_file = config_parser._get_compose_dict()
        default_service = docker_compose_file["services"][container_type]
        data_path = default_service["command"].split(
            "--data_path=")[1].split()[0].rstrip(" -l")
        expected_commands = [
            f"nano_node daemon --network=test --data_path={data_path} --flag_1 --flag_2 ",
            f"nano_node daemon --network=test --data_path={data_path} --flag_1 ",
            f"nano_node daemon --network=test --data_path={data_path} --flag_3 "
        ]

        self.assertEqual(len(commands), len(expected_commands))
        for expected, actual in zip(expected_commands, commands):
            self.assertEqual(expected, actual)

    def test_performance(self):
        start_time = time.time()
        config_parser, conf_file = self._get_config_parser(
            conf_name="connected_peers.toml")

        # Call your function here with appropriate arguments
        # Example:
        config_parser.modify_nanolocal_config(
            'representatives.new_key', 'some_value/with_sp@cial_cHars')
        end_time = time.time()
        execution_time = end_time - start_time
        assert execution_time < 0.1, f"Function took too long: {execution_time} seconds"

    def test_yaml_boolean_handling(self):
        config_parser = ConfigParser(
            "unit_tests/configs/mock_nl_config", "conf_edit_config.toml")
        test_dict = {'version': '2.4', 'services': {'nl_genesis': {'build': {'context': '.', 'dockerfile': './services/custom_Dockerfile', 'args': ['NANO_IMAGE=rsnano:v1', 'UID=501']}, 'user': '501', 'container_name': 'nl_genesis', 'command': 'nano_node daemon --network=test --data_path=/home/nanocurrency/NanoTest  ', 'restart': 'unless-stopped', 'cap_add': ['NET_ADMIN'], 'ports': ['44100:17075', '45100:17076', '47100:17078'], 'volumes': ['./nl_genesis:/home/nanocurrency'], 'env_file': ['./dc_nano_local_env'], 'networks': ['nano-local']}, 'nl_pr1': {'build': {'context': '.', 'dockerfile': './services/custom_Dockerfile', 'args': ['NANO_IMAGE=rsnano:v1', 'UID=501']}, 'user': '501', 'container_name': 'nl_pr1', 'command': 'nano_node daemon --network=test --data_path=/home/nanocurrency/NanoTest  ', 'restart': 'unless-stopped', 'cap_add': ['NET_ADMIN'], 'ports': ['44101:17075', '45101:17076', '47101:17078'], 'volumes': ['./nl_pr1:/home/nanocurrency'], 'env_file': ['./dc_nano_local_env'], 'networks': ['nano-local']}, 'nl_pr2': {'build': {'context': '.', 'dockerfile': './services/custom_Dockerfile', 'args': ['NANO_IMAGE=rsnano:v1', 'UID=501']}, 'user': '501', 'container_name': 'nl_pr2', 'command': 'nano_node daemon --network=test --data_path=/home/nanocurrency/NanoTest  ', 'restart': 'unless-stopped', 'cap_add': ['NET_ADMIN'], 'ports': ['44102:17075', '45102:17076', '47102:17078'], 'volumes': ['./nl_pr2:/home/nanocurrency'], 'env_file': ['./dc_nano_local_env'], 'networks': ['nano-local']}, 'nl_pr3': {'build': {'context': '.', 'dockerfile': './services/custom_Dockerfile', 'args': ['NANO_IMAGE=rsnano:v1', 'UID=501']}, 'user': '501', 'container_name': 'nl_pr3', 'command': 'nano_node daemon --network=test --data_path=/home/nanocurrency/NanoTest  ', 'restart': 'unless-stopped', 'cap_add': ['NET_ADMIN'], 'ports': ['44103:17075', '45103:17076', '47103:17078'], 'volumes': ['./nl_pr3:/home/nanocurrency'], 'env_file': ['./dc_nano_local_env'], 'networks': ['nano-local']}, 'nl_pr4': {'build': {'context': '.', 'dockerfile': './services/custom_Dockerfile', 'args': ['NANO_IMAGE=rsnano:v1', 'UID=501']}, 'user': '501', 'container_name': 'nl_pr4', 'command': 'nano_node daemon --network=test --data_path=/home/nanocurrency/NanoTest  ', 'restart': 'unless-stopped', 'cap_add': ['NET_ADMIN'], 'ports': [
            '44104:17075', '45104:17076', '47104:17078'], 'volumes': ['./nl_pr4:/home/nanocurrency'], 'env_file': ['./dc_nano_local_env'], 'networks': ['nano-local']}, 'nl_genesis_exporter': {'image': 'gr0v1ty/nano-prom-exporter:853a6c2f0934c99fe5a388994ddf2f3176139716', 'container_name': 'nl_genesis_exporter', 'restart': 'unless-stopped', 'environment': ['NANO_PROM_DEBUG=0'], 'networks': ['nano-local'], 'command': '--host 192.168.178.42 --port 45100 --push_gateway https://nl-exporter.bnano.info --hostname nl_genesis --runid nanolab_c92552dc --interval 2', 'pid': 'service:nl_genesis'}, 'nl_pr1_exporter': {'image': 'gr0v1ty/nano-prom-exporter:853a6c2f0934c99fe5a388994ddf2f3176139716', 'container_name': 'nl_pr1_exporter', 'restart': 'unless-stopped', 'environment': ['NANO_PROM_DEBUG=0'], 'networks': ['nano-local'], 'command': '--host 192.168.178.42 --port 45101 --push_gateway https://nl-exporter.bnano.info --hostname nl_pr1 --runid nanolab_c92552dc --interval 2', 'pid': 'service:nl_pr1'}, 'nl_pr2_exporter': {'image': 'gr0v1ty/nano-prom-exporter:853a6c2f0934c99fe5a388994ddf2f3176139716', 'container_name': 'nl_pr2_exporter', 'restart': 'unless-stopped', 'environment': ['NANO_PROM_DEBUG=0'], 'networks': ['nano-local'], 'command': '--host 192.168.178.42 --port 45102 --push_gateway https://nl-exporter.bnano.info --hostname nl_pr2 --runid nanolab_c92552dc --interval 2', 'pid': 'service:nl_pr2'}, 'nl_pr3_exporter': {'image': 'gr0v1ty/nano-prom-exporter:853a6c2f0934c99fe5a388994ddf2f3176139716', 'container_name': 'nl_pr3_exporter', 'restart': 'unless-stopped', 'environment': ['NANO_PROM_DEBUG=0'], 'networks': ['nano-local'], 'command': '--host 192.168.178.42 --port 45103 --push_gateway https://nl-exporter.bnano.info --hostname nl_pr3 --runid nanolab_c92552dc --interval 2', 'pid': 'service:nl_pr3'}, 'nl_pr4_exporter': {'image': 'gr0v1ty/nano-prom-exporter:853a6c2f0934c99fe5a388994ddf2f3176139716', 'container_name': 'nl_pr4_exporter', 'restart': 'unless-stopped', 'environment': ['NANO_PROM_DEBUG=0'], 'networks': ['nano-local'], 'command': '--host 192.168.178.42 --port 45104 --push_gateway https://nl-exporter.bnano.info --hostname nl_pr4 --runid nanolab_c92552dc --interval 2', 'pid': 'service:nl_pr4'}}, 'networks': {'nano-local': {'name': 'nl_nano-local', 'driver': 'bridge', 'external': True}}, 'volumes': {'nl_default_volume': {}}}

        # Write the test dictionary to a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
            config_parser.conf_rw.write_yaml(tf.name, test_dict)

            # Read back and verify boolean value is preserved
            with open(tf.name, 'r') as f:
                content = f.read()
                self.assertIn("external: true", content.lower())
                self.assertNotIn("external: 'true'", content.lower())

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
