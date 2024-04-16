import time
import unittest
from itertools import islice
from math import ceil, floor

from nanomock.modules.nl_rpc import NanoRpc
from nanomock.modules.nl_parse_config import ConfigParser, ConfigReadWrite
from nanomock.modules.nl_nanolib import NanoLibTools, raw_high_precision_multiply


class BlockGenerator():

    single_change_rep = None

    def __init__(self,
                 rpc_url,
                 broadcast_blocks=False,
                 rpc_user=None,
                 rpc_password=None,
                 log_to_console=False):

        self.conf_p = ConfigParser()
        rpc_url = self.conf_p.get_nodes_rpc(
        )[0] if rpc_url is None else rpc_url

        self.broadcast = broadcast_blocks
        self.log_to_console = log_to_console
        self.single_account_open_counter = 0
        self.nano_lib = NanoLibTools()
        self.nano_rpc_default = NanoRpc(rpc_url,
                                        username=rpc_user,
                                        password=rpc_password)

    def get_nano_rpc_default(self):
        return self.nano_rpc_default

    def blockgen_single_account_opener(
            self,
            representative=None,
            source_key=None,  #
            source_seed=None,
            source_index=None,
            destination_key=None,  #
            destination_seed=None,
            destination_index=None,
            send_amount=1,
            number_of_accounts=1000,
            nano_rpc=None,
            accounts_keep_track=False,
            increment_index=False):
        nano_rpc = self.get_nano_rpc_default()
        if accounts_keep_track:
            if self.single_account_open_counter >= number_of_accounts:
                return []
            if increment_index:
                destination_index = self.single_account_open_counter
        self.single_account_open_counter = self.single_account_open_counter + 1

        destination = self.nano_lib.nanolib_account_data(
            private_key=destination_key,
            seed=destination_seed,
            index=destination_index)
        source = self.nano_lib.nanolib_account_data(private_key=source_key,
                                                    seed=source_seed,
                                                    index=source_index)

        send_block = nano_rpc.create_send_block_pkey(source["private"],
                                                     destination["account"],
                                                     send_amount,
                                                     broadcast=self.broadcast)

        open_block = nano_rpc.create_open_block(destination["account"],
                                                destination["private"],
                                                send_amount,
                                                representative,
                                                send_block["hash"],
                                                broadcast=self.broadcast)
        open_block["account_data"]["source_seed"] = destination_seed
        open_block["account_data"]["source_index"] = destination_index

        res = [send_block, open_block]
        if self.log_to_console:
            print("accounts opened:  {:>6}".format(
                self.single_account_open_counter),
                end='\r')
        return res

    def set_single_change_rep(self, rep=None, nano_rpc: NanoRpc = None):
        # returns random rep if rep is not specified
        if rep is not None:
            self.single_change_rep = rep
        elif rep is None and nano_rpc is not None:
            self.single_change_rep = nano_rpc.generate_account(
                nano_rpc.generate_seed(), 0)["account"]
        else:
            nano_rpc = self.get_nano_rpc_default()
            self.single_change_rep = nano_rpc.generate_account(
                nano_rpc.generate_seed(), 0)["account"]
        return self.single_change_rep

    def blockgen_single_change(self,
                               source_seed=None,
                               source_index=None,
                               source_private_key=None,
                               rep=None,
                               nano_rpc=None):
        nano_rpc = self.get_nano_rpc_default()
        if rep is None:
            rep = self.single_change_rep
        if rep is None:
            rep = nano_rpc.generate_account(nano_rpc.generate_seed(),
                                            0)["account"]

        if source_private_key is not None:
            return nano_rpc.create_change_block_pkey(source_private_key,
                                                     rep,
                                                     broadcast=self.broadcast)
        elif source_seed is not None and source_index is not None:
            return nano_rpc.create_change_block(source_seed,
                                                source_index,
                                                rep,
                                                broadcast=self.broadcast)
        else:
            raise ValueError(
                f"Either source_private_key({source_private_key})   OR   source_seed({source_seed}) and source_index({source_index}) must not be None"
            )

    def recursive_split(self, source_account_data, destination_seed,
                        representative, number_of_accounts, splitting_depth,
                        current_depth, final_account_balance_raw, split_count):

        blocks_current_depth = self.blockgen_single_account_opener(
            representative=representative,
            source_key=source_account_data["private"],
            destination_seed=destination_seed,
            # destination_index=source_dest_account_data["index"] + 1,
            accounts_keep_track=True,
            increment_index=True,
            number_of_accounts=number_of_accounts,
            send_amount=int(
                raw_high_precision_multiply(
                    (split_count**(splitting_depth - current_depth + 1) -
                     split_count) + 1, final_account_balance_raw)))

        if len(blocks_current_depth) == 0:
            return blocks_current_depth

        blocks_next_depth = self.blockgen_account_splitter(
            number_of_accounts=number_of_accounts,
            destination_seed=destination_seed,
            current_depth=current_depth + 1,
            representative=representative,
            source_private_key=blocks_current_depth[1]["account_data"]
            ["private"],
            final_account_balance_raw=final_account_balance_raw,
            split_count=split_count)
        # blocks_current_depth.extends(blocks_next_depth)
        return blocks_current_depth + blocks_next_depth

    def get_spliting_depth(self, number_of_accounts, split_count):
        sum_l = 0
        for exponent in range(1, 128):
            sum_l = sum_l + (split_count**exponent)
            if sum_l >= number_of_accounts:
                break
        return exponent

    def get_accounts_for_depth(self, split_count, splitting_depth):
        accounts = 0
        for i in range(1, splitting_depth + 1):
            accounts = accounts + (split_count**i)
        return accounts

    def blockgen_account_splitter(self,
                                  source_private_key=None,
                                  source_seed=None,
                                  source_index=0,
                                  destination_seed=None,
                                  number_of_accounts=1000,
                                  current_depth=1,
                                  split_count=2,
                                  representative=None,
                                  final_account_balance_raw=10**30,
                                  nano_rpc=None):
        '''create {split_count} new accounts from 1 account recursively until {number_of_accounts} is reached.
           each account sends its funds to {split_count}  other accounts and keeps a minimum balance of {final_account_balance_raw}
           returns 2 * {number_of_accounts} blocks
           '''

        splitting_depth = self.get_spliting_depth(number_of_accounts,
                                                  split_count)

        if current_depth > splitting_depth:
            return []  # end of recursion is reached
        nano_rpc = self.get_nano_rpc_default()

        source_account_data = self.nano_lib.nanolib_account_data(
            private_key=source_private_key,
            seed=source_seed,
            index=source_index)
        if current_depth == 1:
            max_accounts_for_depth = self.get_accounts_for_depth(
                split_count, splitting_depth)
            print(
                f"Creating {number_of_accounts} of {max_accounts_for_depth} possible accounts for current splitting_depth : {splitting_depth} and split_count {split_count}"
            )
            # reset variable when multiple tests run successively
            self.single_account_open_counter = 0
            unittest.TestCase().assertGreater(
                int(
                    nano_rpc.check_balance(
                        source_account_data["account"])["balance_raw"]),
                int(
                    raw_high_precision_multiply(number_of_accounts,
                                                final_account_balance_raw)))
            if representative is None:  # keep the same representative for all blocks
                representative = nano_rpc.account_info(
                    source_account_data["account"]
                )["representative"]  # keep the same representative for all opened accounts

        all_blocks = []
        for _ in range(0, split_count):
            all_blocks.extend(
                self.recursive_split(source_account_data, destination_seed,
                                     representative, number_of_accounts,
                                     splitting_depth, current_depth,
                                     final_account_balance_raw, split_count))

        if current_depth == 1:
            self.single_account_open_counter = 0  # reset counter for next call
        return all_blocks

    def get_hashes_from_blocks(self, blocks):
        if isinstance(blocks, list):
            block_hashes = [x["hash"] for x in blocks]
            return block_hashes
        elif isinstance(blocks, dict):
            return blocks.get("hash", "")

    def make_deep_forks(self,
                        source_seed,
                        source_index,
                        dest_seed,
                        amount_raw,
                        peer_count,
                        forks_per_peer=1,
                        max_depth=5,
                        current_depth=0):
        fork_blocks = {"gap": [], "forks": []}
        nano_rpc = self.get_nano_rpc_default()
        send_block = nano_rpc.create_block(
            "send",
            source_seed=source_seed,
            source_index=source_index,
            destination_account=nano_rpc.generate_account(
                source_seed, source_index)["account"],
            amount_raw=amount_raw,
            read_in_memory=False,
            add_in_memory=True)

        fork_blocks["gap"].append(nano_rpc.get_block_result(send_block, False))

        fork_blocks["forks"] = self.recursive_fork_depth(
            source_seed,
            source_index,
            dest_seed,
            amount_raw,
            peer_count,
            forks_per_peer=forks_per_peer,
            max_depth=max_depth,
            current_depth=current_depth)

        return fork_blocks

    def recursive_fork_depth(self,
                             source_seed,
                             source_index,
                             dest_seed,
                             amount_raw,
                             peer_count,
                             forks_per_peer=1,
                             max_depth=5,
                             current_depth=0):
        res = []
        if current_depth >= max_depth:
            return res

        nano_rpc = self.get_nano_rpc_default()
        next_depth = current_depth + 1
        current_dest_start_index = (forks_per_peer * peer_count *
                                    next_depth) + next_depth
        previous_dest_start_index = (forks_per_peer * peer_count *
                                     current_depth) + current_depth

        # current_dest_start_index = (100 ** next_depth)
        # previous_dest_start_index = 100 ** current_depth

        for i in range(0, forks_per_peer * peer_count):
            dest_index = current_dest_start_index + i
            dest_account = nano_rpc.generate_account(dest_seed,
                                                     dest_index)["account"]
            send_block = nano_rpc.create_block(
                "send",
                source_seed=source_seed,
                # source_index=source_index if current_depth == 0 else 100 ** current_depth,
                source_index=source_index
                if current_depth == 0 else previous_dest_start_index,
                destination_account=dest_account,
                amount_raw=amount_raw,
                read_in_memory=True,
                add_in_memory=False)

            receive_block = nano_rpc.create_block(
                "receive",
                source_seed=dest_seed,
                source_index=dest_index,
                destination_account=dest_account,
                representative=dest_account,
                amount_raw=amount_raw,
                link=send_block["hash"],
                read_in_memory=False,
                add_in_memory=True,
            )
            res.append(nano_rpc.get_block_result(send_block, False))
            res.append(nano_rpc.get_block_result(receive_block, False))

            next_res = self.recursive_fork_depth(dest_seed,
                                                 dest_index,
                                                 dest_seed,
                                                 amount_raw,
                                                 peer_count,
                                                 max_depth=max_depth,
                                                 current_depth=next_depth)
            res.extend(next_res)
        # print(
        #     ">>>>DEBUG", "Current_depth : {:>2}  results {:>6}".format(
        #         current_depth, len(res)))
        return res


class BlockReadWrite():

    def __init__(self):
        self.conf_rw = ConfigReadWrite()

    def read_blocks_from_disk(self,
                              path,
                              seeds=False,
                              hashes=False,
                              blocks=False):
        res = self.conf_rw.read_json(path)
        if seeds:
            return res["s"]
        if hashes:
            return res["h"]
        if blocks:
            return res["b"]
        return res

    def write_blocks_to_disk(self, rpc_block_list, path):
        hash_list = []
        seed_list = []
        block_list = []

        if self.is_nested_list(rpc_block_list):
            for block_list_i in rpc_block_list:
                result = self.process_rpc_block_list(block_list_i)
                hash_list.append(result["hash_list"])
                seed_list.append(result["seed_list"])
                block_list.append(result["block_list"])
        else:
            result = self.process_rpc_block_list(rpc_block_list)
            hash_list.append(result["hash_list"])
            seed_list.append(result["seed_list"])
            block_list.append(result["block_list"])

        res = {"h": hash_list, "s": seed_list, "b": block_list}
        self.conf_rw.write_json(path, res)

    def extract_hashes(self, rpc_block_list):
        return list(map(lambda x: x["hash"], rpc_block_list))

    def extract_unique_seeds(self, rpc_block_list):
        unique_seeds = {
            x["account_data"]["source_seed"]
            for x in rpc_block_list
            if x["account_data"]["source_seed"] is not None
        }
        return sorted(unique_seeds)

    def extract_blocks(self, rpc_block_list):
        return list(map(lambda x: x["block"], rpc_block_list))

    def process_rpc_block_list(self, rpc_block_list):
        self._assert_blockgen_succeeded(rpc_block_list)
        return {
            "hash_list": self.extract_hashes(rpc_block_list),
            "seed_list": self.extract_unique_seeds(rpc_block_list),
            "block_list": self.extract_blocks(rpc_block_list)
        }

    def is_nested_list(self, rpc_block_list):
        return any(isinstance(i, list) for i in rpc_block_list[:2])

    def _assert_blockgen_succeeded(self, blocks):
        tc = unittest.TestCase()
        if isinstance(blocks, list):
            tc.assertEqual(len(list(filter(lambda x: x["success"], blocks))),
                           len(blocks))
        elif isinstance(blocks, dict):
            tc.assertTrue(blocks["success"])
        else:
            tc.fail("Blocks must be of list or dict type")
