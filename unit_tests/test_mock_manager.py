from nanomock.nanomock_manager import NanoLocalManager
from nanomock.modules.nl_parse_config import ConfigParser


class TestManager:

    def setup_method(self, method):
        self.manager = NanoLocalManager(
            "unit_tests/configs/mock_nl_config",
            "unittest",
            config_file="enable_voting_config.toml")

    def test_enable_voting_false(self):
        config = self.manager._set_config_node_file("unittest_genesis")
        assert config["node"]["enable_voting"] == False

    def test_enable_voting_empty(self):
        config = self.manager._set_config_node_file("unittest_pr1")
        assert config["node"]["enable_voting"] == True

    def test_enable_voting_true(self):
        config = self.manager._set_config_node_file("unittest_pr2")
        assert config["node"]["enable_voting"] == True