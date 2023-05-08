from nanomock.nanomock_manager import NanoLocalManager
from nanomock.modules.nl_parse_config import ConfigParser
from nanomock import main as mock
from argparse import Namespace
from os import environ
import pytest
import logging
from unittest.mock import patch


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

    def test_path_flag(self):
        args = Namespace(command="status",
                         path="unit_tests/configs/mock_nl_config",
                         project_name="test_path")

        with pytest.raises(FileNotFoundError,
                           match="No such file or directory"):
            mock.main(args)

    def test_path_flag_os_env(self, caplog):
        environ["NL_CONF_FILE"] = "path_env.toml"
        args = Namespace(command="status",
                         path="unit_tests/configs/mock_nl_config",
                         project_name="test_path",
                         nodes=None,
                         payload=None)
        with caplog.at_level(logging.INFO):
            mock.main(args)

        success_record_found = any(
            record.levelname == "SUCCESS"
            and record.message == "0/2 containers online"
            for record in caplog.records)

        assert success_record_found, "Expected log record not found"