from importlib.metadata import version, PackageNotFoundError
from importlib import resources

import subprocess
import functools
import logging
import shutil
import json
import asyncio
from typing import Tuple
from pathlib import Path
import tomli
import oyaml as yaml
import bitmath


def get_mock_logger():
    logger_l = logging.getLogger(__name__)
    logger_l.setLevel(logging.INFO)
    if not logger_l.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger_l.addHandler(handler)
    return logger_l


class NanoMockLogger(logging.Logger):
    LOG_STORE = {}
    SUCCESS_LEVEL_NUM = 25
    logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

    def success(self, message, *args, **kws):
        self.log(self.SUCCESS_LEVEL_NUM, message, *args, **kws)

    def dynamic(self, log_level, message):
        log_level = getattr(logger, log_level, logging.INFO)
        logger.log(log_level, message)

    def append_log(self, log_key, log_level, message):
        self.LOG_STORE.setdefault(log_key, [])
        self.LOG_STORE[log_key].append(message)
        self.dynamic(log_level, message)

    def pop(self, log_key):
        return self.LOG_STORE.pop(log_key)


# Set the custom logger as the root logger
logging.setLoggerClass(NanoMockLogger)
logger = get_mock_logger()


def log_on_success(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Await the result of the async function
        result = await func(*args, **kwargs)
        if isinstance(result, tuple) and len(result) == 2:
            value, log_message = result
            logger.success(log_message)
            return value
        elif result is None:
            logger.success(f"{func.__name__} completed with None result.")
            return None
        else:
            logger.success(result)
            return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)  # Execute the sync function normally
        if isinstance(result, tuple) and len(result) == 2:
            value, log_message = result
            logger.success(log_message)
            return value
        elif result is None:
            logger.success(f"{func.__name__} completed with None result.")
            return None
        else:
            logger.success(result)
            return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


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


# def _convert_to_dotted_path(path: Path, base_dir: str,
#                             replacement: str) -> Tuple[str, str]:
#     parts = path.parts
#     new_parts = [replacement if p == base_dir else p for p in parts[:-1]]
#     dot_separated_file_path = '.'.join(new_parts)
#     file_name = parts[-1]
#     return dot_separated_file_path, file_name


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


def find_device_for_path(path: str) -> str:
    path = Path(path).resolve()
    df_output = subprocess.check_output(['df', path],
                                        universal_newlines=True).splitlines()

    # The first line is the header, and the second line contains the information we need
    device = df_output[1].split()[0]

    return device


def convert_to_bytes(size_string) -> int:
    if str(size_string).isnumeric():
        return int(size_string)

    size = bitmath.parse_string(size_string)
    return int(size.to_Byte())


def extract_packaged_services_to_disk(destination_path: Path):
    with resources.path("nanomock", "__init__.py") as src_dir:
        src_dir = src_dir.parent / "internal" / "data" / "services"
        dest_dir = destination_path / "services"

        if src_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
            logger.info(
                "nanomock data has been copied to your current working directory."
            )
        else:
            logger.error("Error: nanomock data not found.")


def shutil_rmtree(path: Path):
    shutil.rmtree(path)
    return f"Removed directory: {path}"


def subprocess_run_capture_output(cmd, shell=True, cwd=None):

    try:
        result = subprocess.run(cmd,
                                shell=shell,
                                check=True,
                                capture_output=True,
                                text=True,
                                cwd=cwd)
    except subprocess.CalledProcessError as exc:
        # Log the error and the command
        logger.error("Command failed: %s", cmd)
        logger.error("Error output: %s", exc.stderr)
        logger.error("Return code: %s", exc.returncode)
        raise subprocess.CalledProcessError(
            "Command '%s' failed with return code %s: %s", cmd, exc.returncode, exc.stderr)

    return result
