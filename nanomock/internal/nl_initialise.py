from nanomock.modules.nl_rpc import NanoRpc
from nanomock.modules.nl_nanolib import raw_high_precision_percent
from nanomock.modules.nl_parse_config import ConfigParser
from nanomock.internal.utils import get_mock_logger


class InitialBlocks:

    def __init__(self, config_parser: ConfigParser, rpc_url, logger=None):
        logger = logger or get_mock_logger()
        self.logger = logger
        self.api = NanoRpc(rpc_url)
        self.conf_p = config_parser

    def __epoch_link(self, epoch: int):
        message = f"epoch v{epoch} block"
        as_hex = bytearray(message, "ascii").hex()
        link = as_hex.upper().ljust(64, '0')
        return link

    def __publish_epochs(self):
        e = 1
        self.__log_active_difficulty()
        while e <= self.conf_p.get_all()["epoch_count"]:
            link = self.__epoch_link(e)
            epoch_block = self.api.create_epoch_block(
                link,
                self.conf_p.get_genesis_account_data()["private"],
                self.conf_p.get_genesis_account_data()["account"],
            )
            self.logger.append_log(
                "InitialBlocks", "INFO",
                "EPOCH {} sent by genesis : HASH {}".format(
                    e, epoch_block["hash"]))
            self.__log_active_difficulty()
            e += 1
        pass

    def __log_active_difficulty(self):
        diff = self.api.get_active_difficulty()
        self.logger.append_log(
            "InitialBlocks", "INFO",
            f'current_diff : [{diff["network_current"]}]  current_receive_diff: [{diff["network_receive_current"]}]'
        )

    def __publish_canary(self):
        fv_canary_send_block = self.api.create_send_block_pkey(
            self.conf_p.get_genesis_account_data()["private"],
            self.conf_p.get_canary_account_data()["account"], 1)
        self.logger.append_log(
            "InitialBlocks", "INFO",
            "SEND FINAL VOTES CANARY BLOCK FROM {} To {} : HASH {}".format(
                self.conf_p.get_genesis_account_data()["account"],
                self.conf_p.get_canary_account_data()["account"],
                fv_canary_send_block["hash"]))

        fv_canary_open_block = self.api.create_open_block(
            self.conf_p.get_canary_account_data()["account"],
            self.conf_p.get_canary_account_data()["private"], 1,
            self.conf_p.get_genesis_account_data()["account"],
            fv_canary_send_block["hash"])
        self.logger.append_log(
            "InitialBlocks", "INFO",
            "OPENED CANARY ACCOUNT {} : HASH {}".format(
                self.conf_p.get_canary_account_data()["account"],
                fv_canary_open_block["hash"]))

    def __send_to_burn(self):
        if "burn_amount" not in self.conf_p.get_all():
            self.logger.debug("[burn_amount] is not set. exit send_to_burn()")
            return False

        genesis_balance = int(
            self.api.check_balance(self.conf_p.get_genesis_account_data()
                                   ["account"])["balance_raw"])
        if int(self.conf_p.get_all()["burn_amount"]) > genesis_balance:
            self.logger.append_log(
                "InitialBlocks", "WARNING",
                "[burn_amount] exceeds genesis balance. exit send_to_burn()")
            return False

        send_block = self.api.create_send_block_pkey(
            self.conf_p.get_genesis_account_data()["private"],
            self.conf_p.get_burn_account_data()["account"],
            self.conf_p.get_all()["burn_amount"])

        self.logger.append_log(
            "InitialBlocks", "INFO",
            "SENT {:>40} FROM {} To {} : HASH {}".format(
                send_block["amount_raw"],
                self.conf_p.get_genesis_account_data()["account"],
                self.conf_p.get_burn_account_data()["account"],
                send_block["hash"]))

    def __convert_weight_percentage_to_balance(self):
        genesis_balance = int(
            self.api.check_balance(
                self.conf_p.get_genesis_account_data()["account"],
                include_only_confirmed=False)["balance_raw"])
        genesis_remaing = genesis_balance

        for node_conf in self.conf_p.get_nodes_config():

            if "vote_weight_percent" not in node_conf and "balance" not in node_conf:
                continue  #skip genesis that was added as node
            if "vote_weight_percent" in node_conf:
                node_conf["balance"] = raw_high_precision_percent(
                    genesis_balance, node_conf["vote_weight_percent"])
            node_conf["balance"] = int(node_conf["balance"])

            if genesis_remaing <= 0:
                self.logger.append_log(
                    "InitialBlocks", "WARNING",
                    f'No Genesis funds remaining! Account [{node_conf["account_data"]["account"]}] will not be opened!'
                )
                #self.conf_p["node_account_data"].remove(node_account_data)
                continue
            if genesis_remaing < node_conf["balance"]:
                self.logger.append_log(
                    "InitialBlocks", "WARNING",
                    f'Genesis remaining balance is too small! Send {genesis_remaing} instead of {node_conf["balance"]}.'
                )

            self.conf_p.set_node_balance(
                node_conf["name"], min(node_conf["balance"], genesis_remaing))
            genesis_remaing = max(0, genesis_remaing - node_conf["balance"])

    def __send_vote_weigh(self):

        for node_conf in self.conf_p.get_nodes_config():

            if "balance" not in node_conf:

                continue  #skip genesis that was added as node
            node_account_data = node_conf["account_data"]

            send_block = self.api.create_send_block_pkey(
                self.conf_p.get_genesis_account_data()["private"],
                node_account_data["account"], node_conf["balance"])

            self.logger.append_log(
                "InitialBlocks", "INFO",
                "SENT {:>40} FROM {} To {} : HASH {}".format(
                    send_block["amount_raw"],
                    self.conf_p.get_genesis_account_data()["account"],
                    node_account_data["account"], send_block["hash"]))

            open_block = self.api.create_open_block(
                node_account_data["account"], node_account_data["private"],
                node_conf["balance"], node_account_data["account"],
                send_block["hash"])

            self.logger.append_log(
                "InitialBlocks", "INFO",
                "OPENED PR ACCOUNT {} : HASH {}".format(
                    node_account_data["account"], open_block["hash"]))

    def create_node_wallet(self,
                           rpc_url,
                           node_name,
                           private_key=None,
                           seed=None):
        api = NanoRpc(rpc_url)

        if private_key != None:
            wallet = api.wallet_create(None)["wallet"]
            account = api.wallet_add(wallet, private_key)["account"]
        if seed != None:
            wallet = api.wallet_create(seed)["wallet"]
            account = api.get_account_data(seed, 0)["account"]
        self.logger.append_log(
            "InitialBlocks", "INFO",
            f"WALLET {wallet} CREATED FOR {node_name} WITH ACCOUNT {account}")

    def publish_initial_blocks(self):
        self.__publish_epochs()
        self.__publish_canary()
        self.__send_to_burn()
        self.__convert_weight_percentage_to_balance()
        self.__send_vote_weigh()
        return self.logger.pop("InitialBlocks")
