import subprocess
import functools
import logging
from typing import Callable, List


class NanoMeshLogger(logging.Logger):

    SUCCESS_LEVEL_NUM = 25
    logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

    def success(self, message, *args, **kws):
        self.log(self.SUCCESS_LEVEL_NUM, message, *args, **kws)

    @staticmethod
    def get_logger(name: str):
        logger = NanoMeshLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)
        return logger

    def dynamic(self, log_level, message):
        log_level = getattr(logger, log_level, logging.INFO)
        logger.log(log_level, message)


logger = NanoMeshLogger.get_logger(__name__)


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


def auto_retry_on_error(func: Callable) -> Callable:

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        while True:
            try:
                result = func(*args, **kwargs)
                return result
            except subprocess.CalledProcessError as e:
                do_auto_heal = kwargs.pop('auto_heal', True)
                print(do_auto_heal)

                # Check if the object has the auto_heal method
                if not hasattr(args[0], "auto_heal"):
                    raise TypeError(
                        f"{args[0].__class__.__name__} must have an auto_heal method"
                    )

                if do_auto_heal:
                    logger.warn(
                        f"{func.__name__} failed with {e.stderr}. Retrying")
                    auto_heal_result = args[0].auto_heal(e.stderr)
                    do_auto_heal = False

                    if not auto_heal_result:
                        raise e
                else:
                    raise e

    return wrapper


# def log_and_auto_retry_on_error(func: Callable) -> Callable:

#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         auto_heal_called = False

#         while True:
#             try:
#                 result = func(*args, **kwargs)
#                 logger.success(f"{func.__name__}")
#                 return result
#             except subprocess.CalledProcessError as e:

#                 # Check if the object has the auto_heal method
#                 if not hasattr(args[0], "auto_heal"):
#                     raise TypeError(
#                         f"{args[0].__class__.__name__} must have an auto_heal method"
#                     )

#                 if not auto_heal_called:
#                     logger.warn(
#                         f"{func.__name__} failed with {e.stderr}. Retrying")
#                     auto_heal_result = args[0].auto_heal(e)
#                     auto_heal_called = True

#                     if not auto_heal_result:
#                         raise e
#                 else:
#                     raise e

#     return wrapper
