from enum import Enum


class BalanceFormat(Enum):
    RAW = 1
    NANO = 10**30


def _truncate(number):
    # Improved to handle edge cases and ensure consistent output format
    return '{:.8f}'.format(number if number > 0 else 0.00)


def format_account_data(response, seed, index):
    return {
        "seed": seed,
        "index": index,
        "private": response["private"],
        "public": response["public"],
        "account": response["account"],
        "nano_prefix": response["account"][0:11],
        "nano_center": response["account"][11:59],
        "nano_suffix": response["account"][-6:]
    }


def format_balance_data(response, account):
    balance_format = BalanceFormat.NANO
    balance_raw = int(response["balance"])
    pending_raw = int(response["pending"])

    # Apply the multiplier based on the chosen format
    multiplier = balance_format.value
    balance = balance_raw / multiplier
    pending = pending_raw / multiplier
    total = (balance_raw + pending_raw) / multiplier

    # Format and return the results
    return {
        "account": account,
        "balance_raw": balance_raw,
        "balance": _truncate(balance),
        "pending": _truncate(pending),
        "total": _truncate(total)
    }
