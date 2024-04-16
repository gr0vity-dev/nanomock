import traceback
import secrets
import json
import time
import logging
from nanomock.modules.nl_nanolib import NanoLibTools, get_account_public_key
from nanorpc.client import NanoRpcTyped
from nanomock.modules.nl_rpc_utils import *
import asyncio

# for block_creation, we store local frontier info, so that subsequant calls know about the most recent frontier without needing to publish the block to the ledger.
_FRONTIER_INFO = {}


class NanoRpc:
    def __init__(self, url, username=None, password=None, wrap_json=False):
        self.url = url
        self.nano_lib = NanoLibTools()
        self.nanorpc = NanoRpcTyped(
            url=url, username=username, password=password, )

    def get_url(self):
        return self.url

    def account_balance(self, account, include_only_confirmed):
        return asyncio.run(self.nanorpc.account_balance(account, include_only_confirmed=include_only_confirmed))

    def account_info(self, account, representative=True, weight=None, receivable=True, pending=None, include_confirmed=True):
        return asyncio.run(self.nanorpc.account_info(account, representative=representative, weight=weight, receivable=receivable, pending=pending, include_confirmed=include_confirmed))

    def account_get(self, key):
        return asyncio.run(self.nanorpc.account_get(key))

    def account_history(self, account, count=None, raw=None, head=None, offset=None, reverse=None, account_filter=None):
        return asyncio.run(self.nanorpc.account_history(account, count=count, raw=raw, head=head, offset=offset, reverse=reverse, account_filter=account_filter))

    def account_key(self, account):
        return asyncio.run(self.nanorpc.account_key(account))

    def account_representative(self, account):
        return asyncio.run(self.nanorpc.account_representative(account))

    def account_weight(self, account):
        return asyncio.run(self.nanorpc.account_weight(account))

    def accounts_balances(self, accounts, include_only_confirmed=None):
        return asyncio.run(self.nanorpc.accounts_balances(accounts, include_only_confirmed=include_only_confirmed))

    def accounts_frontiers(self, accounts):
        return asyncio.run(self.nanorpc.accounts_frontiers(accounts))

    def accounts_representatives(self, accounts):
        return asyncio.run(self.nanorpc.accounts_representatives(accounts))

    def available_supply(self, ):
        return asyncio.run(self.nanorpc.available_supply())

    def block_account(self, hash):
        return asyncio.run(self.nanorpc.block_account(hash))

    def block_confirm(self, hash):
        return asyncio.run(self.nanorpc.block_confirm(hash))

    def block_count(self, include_cemented=None):
        return asyncio.run(self.nanorpc.block_count(include_cemented=include_cemented))

    def block_create(self, type, balance, key, representative, link, previous, work=None, version=None, difficulty=None, json_block=None):
        return asyncio.run(self.nanorpc.block_create(type, balance, key, representative, link, previous, work=work, version=version, difficulty=difficulty, json_block=json_block))

    def block_hash(self, block, json_block=None):
        return asyncio.run(self.nanorpc.block_hash(block, json_block=json_block))

    def block_info(self, hash, json_block=None):
        return asyncio.run(self.nanorpc.block_info(hash, json_block=json_block))

    def blocks(self, hashes, json_block=None):
        return asyncio.run(self.nanorpc.blocks(hashes, json_block=json_block))

    def blocks_info(self, hashes, json_block=None, receivable=None, pending=None, source=None, receive_hash=None, include_not_found=None):
        return asyncio.run(self.nanorpc.blocks_info(hashes, json_block=json_block, receivable=receivable, pending=pending, source=source, receive_hash=receive_hash, include_not_found=include_not_found))

    def bootstrap(self, address, port, bypass_frontier_confirmation=None, id=None):
        return asyncio.run(self.nanorpc.bootstrap(address, port, bypass_frontier_confirmation=bypass_frontier_confirmation, id=id))

    def bootstrap_any(self, force=None, id=None, account=None):
        return asyncio.run(self.nanorpc.bootstrap_any(force=force, id=id, account=account))

    def bootstrap_lazy(self, hash, force=None, id=None):
        return asyncio.run(self.nanorpc.bootstrap_lazy(hash, force=force, id=id))

    def bootstrap_status(self, ):
        return asyncio.run(self.nanorpc.bootstrap_status())

    def chain(self, block, count, offset=None, reverse=None):
        return asyncio.run(self.nanorpc.chain(block, count, offset=offset, reverse=reverse))

    def confirmation_active(self, announcements=None):
        return asyncio.run(self.nanorpc.confirmation_active(announcements=announcements))

    def confirmation_height_currently_processing(self, ):
        return asyncio.run(self.nanorpc.confirmation_height_currently_processing())

    def confirmation_history(self, hash=None):
        return asyncio.run(self.nanorpc.confirmation_history(hash=hash))

    def confirmation_info(self, root, contents=None, json_block=None, representatives=None):
        return asyncio.run(self.nanorpc.confirmation_info(root, contents=contents, json_block=json_block, representatives=representatives))

    def confirmation_quorum(self, peer_details=None):
        return asyncio.run(self.nanorpc.confirmation_quorum(peer_details=peer_details))

    def database_txn_tracker(self, min_read_time, min_write_time):
        return asyncio.run(self.nanorpc.database_txn_tracker(min_read_time, min_write_time))

    def delegators(self, account, threshold=None, count=None, start=None):
        return asyncio.run(self.nanorpc.delegators(account, threshold=threshold, count=count, start=start))

    def delegators_count(self, account):
        return asyncio.run(self.nanorpc.delegators_count(account))

    def deterministic_key(self, seed, index):
        return asyncio.run(self.nanorpc.deterministic_key(seed, index))

    def epoch_upgrade(self, epoch, key, count=None, threads=None):
        return asyncio.run(self.nanorpc.epoch_upgrade(epoch, key, count=count, threads=threads))

    def frontier_count(self, ):
        return asyncio.run(self.nanorpc.frontier_count())

    def frontiers(self, account, count=None):
        return asyncio.run(self.nanorpc.frontiers(account, count=count))

    def keepalive(self, address, port):
        return asyncio.run(self.nanorpc.keepalive(address, port))

    def key_create(self, ):
        return asyncio.run(self.nanorpc.key_create())

    def key_expand(self, key):
        return asyncio.run(self.nanorpc.key_expand(key))

    def ledger(self, account, count, representative=None, weight=None, receivable=None, pending=None, modified_since=None, sorting=None, threshold=None):
        return asyncio.run(self.nanorpc.ledger(account, count, representative=representative, weight=weight, receivable=receivable, pending=pending, modified_since=modified_since, sorting=sorting, threshold=threshold))

    def node_id(self, ):
        return asyncio.run(self.nanorpc.node_id())

    def node_id_delete(self, ):
        return asyncio.run(self.nanorpc.node_id_delete())

    def peers(self, peer_details=None):
        return asyncio.run(self.nanorpc.peers(peer_details=peer_details))

    def process(self, block, force=None, subtype=None, json_block=None, async_=None):
        return asyncio.run(self.nanorpc.process(block, force=force, subtype=subtype, json_block=json_block, async_=async_))

    def representatives(self, count=None, sorting=None):
        return asyncio.run(self.nanorpc.representatives(count=count, sorting=sorting))

    def representatives_online(self, weight=None, accounts=None):
        return asyncio.run(self.nanorpc.representatives_online(weight=weight, accounts=accounts))

    def republish(self, hash, sources=None, destinations=None):
        return asyncio.run(self.nanorpc.republish(hash, sources=sources, destinations=destinations))

    def sign_hash(self, hash):
        return asyncio.run(self._sign(hash=hash))

    def sign_block_with_key(self, block, private_key, json_block=False):
        return asyncio.run(self._sign(key=private_key, block=block, json_block=json_block))

    def sign_block_with_wallet(self, block, wallet, json_block=False):
        return asyncio.run(self._sign(wallet=wallet, block=block, json_block=json_block))

    def _sign(self, key=None, wallet=None, block=None, hash=None, json_block=False):
        # Note: This method requires either 'block' or 'hash'. Either 'key' or 'wallet'. Don't use directly.
        return asyncio.run(self.nanorpc._sign(key=key, wallet=wallet, block=block, hash=hash, json_block=json_block))

    def stats(self, type):
        return asyncio.run(self.nanorpc.stats(type))

    def stats_clear(self, ):
        return asyncio.run(self.nanorpc.stats_clear())

    def stop(self, ):
        return asyncio.run(self.nanorpc.stop())

    def successors(self, block, count, offset=None, reverse=None):
        return asyncio.run(self.nanorpc.successors(block, count, offset=offset, reverse=reverse))

    def telemetry(self, raw=None, address=None, port=None):
        return asyncio.run(self.nanorpc.telemetry(raw=raw, address=address, port=port))

    def validate_account_number(self, account):
        return asyncio.run(self.nanorpc.validate_account_number(account))

    def version(self, ):
        return asyncio.run(self.nanorpc.version())

    def unchecked(self, count, json_block=None):
        return asyncio.run(self.nanorpc.unchecked(count, json_block=json_block))

    def unchecked_clear(self, ):
        return asyncio.run(self.nanorpc.unchecked_clear())

    def unchecked_get(self, hash, json_block=None):
        return asyncio.run(self.nanorpc.unchecked_get(hash, json_block=json_block))

    def unchecked_keys(self, key, count, json_block=None):
        return asyncio.run(self.nanorpc.unchecked_keys(key, count, json_block=json_block))

    def unopened(self, account, count, threshold=None):
        return asyncio.run(self.nanorpc.unopened(account, count, threshold=threshold))

    def uptime(self, ):
        return asyncio.run(self.nanorpc.uptime())

    def work_cancel(self, hash):
        return asyncio.run(self.nanorpc.work_cancel(hash))

    def work_generate(self, hash, use_peers=None, difficulty=None, multiplier=None, account=None, version=None, block=None, json_block=None):
        return asyncio.run(self.nanorpc.work_generate(hash, use_peers=use_peers, difficulty=difficulty, multiplier=multiplier, account=account, version=version, block=block, json_block=json_block))

    def work_peer_add(self, address, port):
        return asyncio.run(self.nanorpc.work_peer_add(address, port))

    def work_peers(self, ):
        return asyncio.run(self.nanorpc.work_peers())

    def work_peers_clear(self, ):
        return asyncio.run(self.nanorpc.work_peers_clear())

    def work_validate(self, work, hash, difficulty=None, multiplier=None, version=None):
        return asyncio.run(self.nanorpc.work_validate(work, hash, difficulty=difficulty, multiplier=multiplier, version=version))

    def account_create(self, wallet, index=None, work=None):
        return asyncio.run(self.nanorpc.account_create(wallet, index=index, work=work))

    def account_list(self, wallet):
        return asyncio.run(self.nanorpc.account_list(wallet))

    def account_move(self, wallet, source, accounts):
        return asyncio.run(self.nanorpc.account_move(wallet, source, accounts))

    def account_remove(self, wallet, account):
        return asyncio.run(self.nanorpc.account_remove(wallet, account))

    def account_representative_set(self, wallet, account, representative, work=None):
        return asyncio.run(self.nanorpc.account_representative_set(wallet, account, representative, work=work))

    def accounts_create(self, wallet, count, work=None):
        return asyncio.run(self.nanorpc.accounts_create(wallet, count, work=work))

    def password_change(self, wallet, password):
        return asyncio.run(self.nanorpc.password_change(wallet, password))

    def password_enter(self, wallet, password):
        return asyncio.run(self.nanorpc.password_enter(wallet, password))

    def password_valid(self, wallet):
        return asyncio.run(self.nanorpc.password_valid(wallet))

    def receive(self, wallet, account, block):
        return asyncio.run(self.nanorpc.receive(wallet, account, block))

    def receive_minimum(self, ):
        return asyncio.run(self.nanorpc.receive_minimum())

    def receive_minimum_set(self, amount):
        return asyncio.run(self.nanorpc.receive_minimum_set(amount))

    def send(self, wallet, source, destination, amount, id=None, work=None):
        return asyncio.run(self.nanorpc.send(wallet, source, destination, amount, id=id, work=work))

    def wallet_add(self, wallet, key, work=None):
        return asyncio.run(self.nanorpc.wallet_add(wallet, key, work=work))

    def wallet_add_watch(self, wallet, accounts):
        return asyncio.run(self.nanorpc.wallet_add_watch(wallet, accounts))

    def wallet_balances(self, wallet, threshold=None):
        return asyncio.run(self.nanorpc.wallet_balances(wallet, threshold=threshold))

    def wallet_change_seed(self, wallet, seed, count=None):
        return asyncio.run(self.nanorpc.wallet_change_seed(wallet, seed, count=count))

    def wallet_contains(self, wallet, account):
        return asyncio.run(self.nanorpc.wallet_contains(wallet, account))

    def wallet_create(self, seed=None):
        return asyncio.run(self.nanorpc.wallet_create(seed=seed))

    def wallet_destroy(self, wallet):
        return asyncio.run(self.nanorpc.wallet_destroy(wallet))

    def wallet_export(self, wallet):
        return asyncio.run(self.nanorpc.wallet_export(wallet))

    def wallet_frontiers(self, wallet):
        return asyncio.run(self.nanorpc.wallet_frontiers(wallet))

    def wallet_history(self, wallet, modified_since=None):
        return asyncio.run(self.nanorpc.wallet_history(wallet, modified_since=modified_since))

    def wallet_info(self, wallet):
        return asyncio.run(self.nanorpc.wallet_info(wallet))

    def wallet_ledger(self, wallet, representative=None, weight=None, receivable=None, pending=None):
        return asyncio.run(self.nanorpc.wallet_ledger(wallet, representative=representative, weight=weight, receivable=receivable, pending=pending))

    def wallet_lock(self, wallet):
        return asyncio.run(self.nanorpc.wallet_lock(wallet))

    def wallet_representative(self, wallet):
        return asyncio.run(self.nanorpc.wallet_representative(wallet))

    def wallet_representative_set(self, wallet, representative, work=None):
        return asyncio.run(self.nanorpc.wallet_representative_set(wallet, representative, work=work))

    def wallet_republish(self, wallet, count=None):
        return asyncio.run(self.nanorpc.wallet_republish(wallet, count=count))

    def wallet_work_get(self, wallet):
        return asyncio.run(self.nanorpc.wallet_work_get(wallet))

    def work_get(self, wallet):
        return asyncio.run(self.nanorpc.work_get(wallet))

    def work_set(self, wallet, account, work):
        return asyncio.run(self.nanorpc.work_set(wallet, account, work))

    def nano_to_raw(self, amount):
        return asyncio.run(self.nanorpc.nano_to_raw(amount))

    def raw_to_nano(self, amount):
        return asyncio.run(self.nanorpc.raw_to_nano(amount))

    def accounts_receivable(self, accounts, count, threshold=None, source=None, include_active=None, sorting=None, include_only_confirmed=None):
        return asyncio.run(self.nanorpc.accounts_receivable(accounts, count, threshold=threshold, source=source, include_active=include_active, sorting=sorting, include_only_confirmed=include_only_confirmed))

    def populate_backlog(self, ):
        return asyncio.run(self.nanorpc.populate_backlog())

    def receivable(self, account, count=None, threshold=None, source=None, include_active=None, min_version=None, sorting=None, include_only_confirmed=None, offset=None):
        return asyncio.run(self.nanorpc.receivable(account, count=count, threshold=threshold, source=source, include_active=include_active, min_version=min_version, sorting=sorting, include_only_confirmed=include_only_confirmed, offset=offset))

    def receivable_exists(self, hash, include_active=None, include_only_confirmed=None):
        return asyncio.run(self.nanorpc.receivable_exists(hash, include_active=include_active, include_only_confirmed=include_only_confirmed))

    def search_receivable(self, wallet):
        return asyncio.run(self.nanorpc.search_receivable(wallet))

    def search_receivable_all(self, ):
        return asyncio.run(self.nanorpc.search_receivable_all())

    def wallet_receivable(self, wallet, count=None, threshold=None, source=None):
        return asyncio.run(self.nanorpc.wallet_receivable(wallet, count=count, threshold=threshold, source=source))

    def active_difficulty(self):
        return asyncio.run(self.nanorpc.active_difficulty())

    def generate_seed(self):
        return secrets.token_hex(32)

    def check_balances(self, seed, start_index=0, end_index=50):
        result = []
        for index in range(start_index, end_index + 1):
            nano_account = self.generate_account(seed, index)
            result.append(self.check_balance(nano_account["account"]))
        return result

    def generate_account(self, seed, index):
        try:
            response = self.deterministic_key(seed, index)
        except Exception as e:
            print(f"Error generating account from deterministic key: {e}")
            return None

        return format_account_data(response, seed, index)

    def check_balance(self, account, include_only_confirmed=True):
        try:
            response = self.account_balance(
                account, include_only_confirmed=include_only_confirmed)
        except Exception as e:
            print(f"Error fetching account balance: {e}")
            return None

        return format_balance_data(response, account)

    def block_confirmed(self, json_block=None, block_hash=None):
        if json_block:
            block_hash = self.block_hash(json_block)["hash"]
        if not block_hash:
            return False

        response = self.block_info(block_hash)
        if response is None:
            return False
        if "error" in response:
            return False
        return True if response["confirmed"] == "true" else False

    def create_block(self,
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
                    source_account_info = self.account_info(
                        source_account_data["account"])
            else:
                source_account_info = self.account_info(
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
                    link = link
                else:
                    sub_type = "receive"
                    previous = source_account_info["frontier"]
                    balance = int(
                        source_account_info["balance"]) + int(amount_raw)
                    link = link

            elif sub_type == "send":
                link = get_account_public_key(account_id=destination_account)
                balance = int(source_account_info["balance"]) - int(amount_raw)
                previous = source_account_info["frontier"]

            elif sub_type == "change":
                amount_raw = "0"
                destination_account = source_account_data["account"]
                link = link

            elif sub_type == "epoch":
                if use_rpc:
                    pass
                else:
                    balance = int(source_account_info["balance"])

            if use_rpc:
                block = self.block_create("state",
                                          balance,
                                          source_account_data["private"],
                                          representative,
                                          link,
                                          previous,
                                          json_block=True)
            else:
                lib_block = self.nano_lib.create_state_block(
                    source_account_data["account"],
                    representative,
                    previous,
                    balance,
                    link,
                    source_account_data["private"],
                    difficulty=self.active_difficulty()["network_minimum"])

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

    def create_open_block(self,
                          destination_account,
                          open_private_key,
                          amount_per_chunk_raw,
                          rep_account,
                          send_block_hash,
                          broadcast=True):
        block = self.create_block("receive",
                                  source_private_key=open_private_key,
                                  destination_account=destination_account,
                                  representative=rep_account,
                                  amount_raw=amount_per_chunk_raw,
                                  link=send_block_hash,
                                  in_memory=not broadcast)

        return self.get_block_result(block, broadcast)

    def create_send_block(self,
                          source_seed,
                          source_index,
                          destination_account,
                          amount_per_chunk_raw,
                          broadcast=True):
        block = self.create_block("send",
                                  source_seed=source_seed,
                                  source_index=source_index,
                                  destination_account=destination_account,
                                  amount_raw=amount_per_chunk_raw,
                                  in_memory=not broadcast)
        return self.get_block_result(block,
                                     broadcast,
                                     source_seed=source_seed,
                                     source_index=source_index)

    def create_change_block(self,
                            source_seed,
                            source_index,
                            new_rep,
                            broadcast=True):
        block = self.create_block("change",
                                  source_seed=source_seed,
                                  source_index=source_index,
                                  link="0" * 64,
                                  representative=new_rep,
                                  in_memory=not broadcast)

        return self.get_block_result(block,
                                     broadcast,
                                     source_seed=source_seed,
                                     source_index=source_index)

    def create_change_block_pkey(self,
                                 source_private_key,
                                 new_rep,
                                 broadcast=True):
        block = self.create_block("change",
                                  source_private_key=source_private_key,
                                  link="0" * 64,
                                  representative=new_rep,
                                  in_memory=not broadcast)
        return self.get_block_result(block, broadcast)

    def create_send_block_pkey(self,
                               private_key,
                               destination_account,
                               amount_per_chunk_raw,
                               broadcast=True):

        block = self.create_block("send",
                                  source_private_key=private_key,
                                  destination_account=destination_account,
                                  amount_raw=amount_per_chunk_raw,
                                  in_memory=not broadcast)
        return self.get_block_result(block, broadcast)

    def create_epoch_block(self,
                           epoch_link,
                           genesis_private_key,
                           genesis_account,
                           broadcast=True):

        block = self.create_block("epoch",
                                  source_private_key=genesis_private_key,
                                  destination_account=genesis_account,
                                  link=epoch_link,
                                  in_memory=not broadcast)

        return self.get_block_result(block, broadcast)

    def get_block_result(self, block, broadcast, source_seed=None, source_index=None, exit_after_s=2):
        start_time = time.time()

        # Log an error immediately if the block was unsuccessful
        if not block.get("success", False):
            logging.warning(block.get("error", "Unknown error"))

        # Handle broadcast if needed
        if broadcast:
            publish = self._try_publish_block(block, start_time, exit_after_s)
            broadcast = publish is not None and "hash" in publish
            if not broadcast:
                logging.error(
                    f'Block not published: {block.get("hash", "Unknown hash")}')

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
            logging.error(result)

        return result

    def _try_publish_block(self, block, start_time, exit_after_s):
        while True:
            if time.time() - start_time > exit_after_s:
                return None
            publish = self.process(block["block"], json_block=True)
            if publish is not None:
                return publish
            time.sleep(0.5)  # Sleep briefly before trying again
