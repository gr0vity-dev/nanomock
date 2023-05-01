import subprocess
import functools
import logging
from typing import Callable, List
from importlib.metadata import version, PackageNotFoundError
from importlib import resources
from pathlib import Path
from typing import Tuple
import tomli
import oyaml as yaml
import json


class NanoLocalLogger(logging.Logger):

    SUCCESS_LEVEL_NUM = 25
    logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

    def success(self, message, *args, **kws):
        self.log(self.SUCCESS_LEVEL_NUM, message, *args, **kws)

    @staticmethod
    def get_logger(name: str):
        logger = NanoLocalLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)
        return logger

    def dynamic(self, log_level, message):
        log_level = getattr(logger, log_level, logging.INFO)
        logger.log(log_level, message)


logger = NanoLocalLogger.get_logger(__name__)


def log_on_success(func: Callable) -> Callable:

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if result is None:
            log_message = func.__name__
        else:
            log_message = result

        logger.success(log_message)
        return result

    return wrapper


def is_packaged_version():
    is_packaged = None
    try:
        _ = version('nanomock')
        is_packaged = True
    except PackageNotFoundError:
        is_packaged = False

    return is_packaged


def _convert_to_dotted_str(path: str) -> str:
    return path.replace("/", ".")


def _convert_to_dotted_path(path: Path, base_dir: str,
                            replacement: str) -> Tuple[str, str]:
    parts = path.parts
    new_parts = [replacement if p == base_dir else p for p in parts[:-1]]
    dot_separated_file_path = '.'.join(new_parts)
    file_name = parts[-1]
    return dot_separated_file_path, file_name


def _split_file_from_path(path: str) -> Tuple[str, str]:
    parts = path.split(".")
    file_name = '.'.join(parts[-2::])
    dot_separated_file_path = '.'.join(parts[0:-2])

    return dot_separated_file_path, file_name


def _read_data(dotted_path: str, file_name: str):

    with resources.open_text(dotted_path, file_name) as file:
        data = file.read()
    return data


def read_from_package_if_needed(read_method):

    @functools.wraps(read_method)
    def wrapper(self, path, *args, is_packaged=False, **kwargs):
        if is_packaged_version() and is_packaged:
            # Convert path to dotted path and read data using read_data method
            dotted_path = _convert_to_dotted_str(path)
            file_path, file_name = _split_file_from_path(dotted_path)
            data = _read_data(file_path, file_name)

            # If the read method is expected to return a different data format,
            # you can add the conversion logic here based on the read_method.__name__
            if read_method.__name__ == "read_json":
                return json.loads(data)
            elif read_method.__name__ == "read_toml":
                return tomli.loads(data)
            elif read_method.__name__ == "read_yaml":
                return yaml.safe_load(data)
            else:
                # For read_file, the data is already in the correct format (list of lines)
                return data.splitlines()
        else:
            # If not a packaged version, call the original read_method
            return read_method(self, path, *args, is_packaged=False, **kwargs)

    return wrapper