import traceback
import secrets
import json
import time
from nanomock.internal.utils import logger
from nanomock.modules.nl_nanolib import NanoLibTools, get_account_public_key
from nanorpc.client import NanoRpcTyped
from nanomock.modules.nl_rpc_utils import format_account_data, format_balance_data

# for block_creation, we store local frontier info, so that subsequant calls know about the most recent frontier without needing to publish the block to the ledger.
_FRONTIER_INFO = {}


class NanoRpc:
    def __init__(self, url, username=None, password=None, wrap_json=False):
        self.url = url
        self.nano_lib = NanoLibTools()
        self.nanorpc = NanoRpcTyped(
            url=url, username=username, password=password, wrap_json=wrap_json)

    def get_url(self):
        return self.url

    async def account_balance(self, account, include_only_confirmed):
        return await self.nanorpc.account_balance(account, include_only_confirmed=include_only_confirmed)

    async def account_info(self, account, representative=True, weight=None, receivable=True, pending=None, include_confirmed=True):
        return await self.nanorpc.account_info(account, representative=representative, weight=weight, receivable=receivable, pending=pending, include_confirmed=include_confirmed)

    async def accounts_balances(self, accounts, include_only_confirmed=None):
        return await self.nanorpc.accounts_balances(accounts, include_only_confirmed=include_only_confirmed)

    async def available_supply(self, ):
        return await self.nanorpc.available_supply()

    async def block_count(self, include_cemented=None):
        return await self.nanorpc.block_count(include_cemented=include_cemented)

    async def block_hash(self, block, json_block=True):
        return await self.nanorpc.block_hash(block, json_block=json_block)

    async def block_create(self, type_a, balance, key, representative, link, previous, work=None, version=None, difficulty=None, json_block=True):
        return await self.nanorpc.block_create(type_a, balance, key, representative, link, previous, work=work, version=version, difficulty=difficulty, json_block=json_block)

    async def block_info(self, block_hash, json_block=True):
        return await self.nanorpc.block_info(block_hash, json_block=json_block)

    async def deterministic_key(self, seed, index):
        return await self.nanorpc.deterministic_key(seed, index)

    async def key_create(self, ):
        return await self.nanorpc.key_create()

    async def key_expand(self, key):
        return await self.nanorpc.key_expand(key)

    async def process(self, block, force=None, subtype=None, json_block=True, async_=None):
        return await self.nanorpc.process(block, force=force, subtype=subtype, json_block=json_block, async_=async_)

    async def work_generate(self, block_hash, use_peers=None, difficulty=None, multiplier=None, account=None, version=None, block=None, json_block=True):
        return await self.nanorpc.work_generate(block_hash, use_peers=use_peers, difficulty=difficulty, multiplier=multiplier, account=account, version=version, block=block, json_block=json_block)

    async def account_create(self, wallet, index=None, work=None):
        return await self.nanorpc.account_create(wallet, index=index, work=work)

    async def account_list(self, wallet):
        return await self.nanorpc.account_list(wallet)

    async def receive(self, wallet, account, block):
        return await self.nanorpc.receive(wallet, account, block)

    async def wallet_create(self, seed=None):
        return await self.nanorpc.wallet_create(seed=seed)

    async def wallet_add(self, wallet, key, work=None):
        return await self.nanorpc.wallet_add(wallet, key, work=work)

    async def active_difficulty(self):
        return await self.nanorpc.active_difficulty()

    async def version(self):
        return await self.nanorpc.version()

    def generate_seed(self):
        return secrets.token_hex(32)

    async def check_balances(self, seed, start_index=0, end_index=50):
        result = []
        for index in range(start_index, end_index + 1):
            nano_account = await self.generate_account(seed, index)
            result.append(self.check_balance(nano_account["account"]))
        return result

    async def generate_account(self, seed, index):
        try:
            response = await self.deterministic_key(seed, index)
        except Exception as e:
            print(f"Error generating account from deterministic key: {e}")
            return None

        return format_account_data(response, seed, index)

    async def check_balance(self, account, include_only_confirmed=True):
        try:
            response = await self.account_balance(
                account, include_only_confirmed=include_only_confirmed)
        except Exception as e:
            print(f"Error fetching account balance: {e}")
            return None

        return format_balance_data(response, account)

    async def block_confirmed(self, json_block=True, block_hash=None):
        if json_block:
            block_hash = await self.block_hash(json_block)["hash"]
        if not block_hash:
            return False

        response = await self.block_info(block_hash)
        if response is None:
            return False
        if "error" in response:
            return False
        return True if response["confirmed"] == "true" else False

    async def create_open_block(self,
                                destination_account,
                                open_private_key,
                                amount_per_chunk_raw,
                                rep_account,
                                send_block_hash,
                                broadcast=True):
        block = await self.create_block("receive",
                                        source_private_key=open_private_key,
                                        destination_account=destination_account,
                                        representative=rep_account,
                                        amount_raw=amount_per_chunk_raw,
                                        link=send_block_hash,
                                        in_memory=not broadcast)

        return await self.get_block_result(block, broadcast)

    async def create_send_block(self,
                                source_seed,
                                source_index,
                                destination_account,
                                amount_per_chunk_raw,
                                broadcast=True):
        block = await self.create_block("send",
                                        source_seed=source_seed,
                                        source_index=source_index,
                                        destination_account=destination_account,
                                        amount_raw=amount_per_chunk_raw,
                                        in_memory=not broadcast)
        return await self.get_block_result(block,
                                           broadcast,
                                           source_seed=source_seed,
                                           source_index=source_index)

    async def create_change_block(self,
                                  source_seed,
                                  source_index,
                                  new_rep,
                                  broadcast=True):
        block = await self.create_block("change",
                                        source_seed=source_seed,
                                        source_index=source_index,
                                        link="0" * 64,
                                        representative=new_rep,
                                        in_memory=not broadcast)

        return await self.get_block_result(block,
                                           broadcast,
                                           source_seed=source_seed,
                                           source_index=source_index)

    async def create_change_block_pkey(self,
                                       source_private_key,
                                       new_rep,
                                       broadcast=True):
        block = await self.create_block("change",
                                        source_private_key=source_private_key,
                                        link="0" * 64,
                                        representative=new_rep,
                                        in_memory=not broadcast)
        return await self.get_block_result(block, broadcast)

    async def create_send_block_pkey(self,
                                     private_key,
                                     destination_account,
                                     amount_per_chunk_raw,
                                     broadcast=True):

        block = await self.create_block("send",
                                        source_private_key=private_key,
                                        destination_account=destination_account,
                                        amount_raw=amount_per_chunk_raw,
                                        in_memory=not broadcast)
        return await self.get_block_result(block, broadcast)

    async def create_epoch_block(self,
                                 epoch_link,
                                 genesis_private_key,
                                 genesis_account,
                                 broadcast=True):

        block = await self.create_block("epoch",
                                        source_private_key=genesis_private_key,
                                        destination_account=genesis_account,
                                        link=epoch_link,
                                        in_memory=not broadcast)

        return await self.get_block_result(block, broadcast)

    async def create_block(self,
                           sub_type,
                           link=None,
                           destination_account=None,
                           representative=None,
                           source_seed=None,
                           source_index=None,
                           source_private_key=None,
                           amount_raw=None,
                           in_memory=False,
                           add_in_memory=False,
                           read_in_memory=False,
                           use_rpc=True):
        try:
            if in_memory:
                add_in_memory = True
                read_in_memory = True
            if source_private_key is not None:
                source_account_data = self.nano_lib.nanolib_account_data(
                    private_key=source_private_key)
            elif source_seed is not None and source_index is not None:
                source_account_data = self.nano_lib.nanolib_account_data(
                    seed=source_seed, index=source_index)

            if read_in_memory:
                if source_account_data["account"] in _FRONTIER_INFO:
                    source_account_info = _FRONTIER_INFO[
                        source_account_data["account"]]
                else:
                    source_account_info = await self.account_info(
                        source_account_data["account"])
            else:
                source_account_info = await self.account_info(
                    source_account_data["account"])

            if representative is None:
                representative = source_account_info["representative"]
            if "balance" in source_account_info:
                balance = source_account_info["balance"]
            if "frontier" in source_account_info:
                previous = source_account_info["frontier"]

            if sub_type == "open" or sub_type == "receive":
                # destination_account = source_account_data["account"]
                if "error" in source_account_info:
                    sub_type = "open"
                    if use_rpc:
                        previous = "0" * 64
                    else:
                        previous = None
                    balance = amount_raw
                    # link = link
                else:
                    sub_type = "receive"
                    previous = source_account_info["frontier"]
                    balance = int(
                        source_account_info["balance"]) + int(amount_raw)
                    # link = link

            elif sub_type == "send":
                link = get_account_public_key(account_id=destination_account)
                balance = int(source_account_info["balance"]) - int(amount_raw)
                previous = source_account_info["frontier"]

            elif sub_type == "change":
                amount_raw = "0"
                destination_account = source_account_data["account"]
                # link = link

            elif sub_type == "epoch":
                if use_rpc:
                    pass
                else:
                    balance = int(source_account_info["balance"])

            if use_rpc:
                block = await self.block_create("state",
                                                balance,
                                                source_account_data["private"],
                                                representative,
                                                link,
                                                previous,
                                                json_block=True)
            else:
                active_difficulty = await self.active_difficulty()
                lib_block = self.nano_lib.create_state_block(
                    source_account_data["account"],
                    representative,
                    previous,
                    balance,
                    link,
                    source_account_data["private"],
                    difficulty=active_difficulty["network_minimum"])

                block = {
                    "hash": lib_block.block_hash,
                    "difficulty": lib_block.difficulty,
                    "block": json.loads(lib_block.json())
                }

            block["private"] = source_account_data["private"]
            block["subtype"] = sub_type
            block["amount_raw"] = amount_raw

            if "error" in block:
                block["success"] = False
                block["block"] = {}
                block["hash"] = None
            else:
                block["success"] = True
                block["error"] = None
                if add_in_memory:
                    _FRONTIER_INFO[source_account_data["account"]] = {
                        "frontier": block["hash"],
                        "balance": balance,
                        "representative": representative
                    }
            block["block"]["subtype"] = sub_type

        except Exception as e:
            traceback.print_exc()
            block = {
                "success": False,
                "block": {},
                "hash": None,
                "subtype": sub_type,
                "error": str(e)
            }
        return block

    async def get_block_result(self, block, broadcast, source_seed=None, source_index=None, exit_after_s=2):
        start_time = time.time()

        # Log an error immediately if the block was unsuccessful
        if not block.get("success", False):
            logger.warning(block.get("error", "Unknown error"))

        # Handle broadcast if needed
        if broadcast:
            publish = await self._try_publish_block(block, start_time, exit_after_s)
            broadcast = publish is not None and "hash" in publish
            if not broadcast:
                logger.error(
                    'Block not published: %s', block.get("hash", "Unknown hash"))

        # Construct the result dictionary
        result = {
            "success": block.get("success", False),
            "published": broadcast,
            "balance_raw": block["block"].get("balance", ""),
            "amount_raw": block.get("amount_raw", "0"),
            "hash": block.get("hash", ""),
            "block": block.get("block", {}),
            "subtype": block.get("subtype", ""),
            "account_data": {
                "account": block["block"].get("account", ""),
                "private": block.get("private", ""),
                "source_seed": source_seed,
                "source_index": source_index
            },
            "error": block.get("error", "")
        }

        # Log the entire result if the block was not successful
        if not result["success"]:
            logger.error(result)

        return result

    async def _try_publish_block(self, block, start_time, exit_after_s):
        while True:
            if time.time() - start_time > exit_after_s:
                return None
            publish = await self.process(block["block"], json_block=True)
            if publish is not None:
                return publish
            time.sleep(0.5)  # Sleep briefly before trying again
