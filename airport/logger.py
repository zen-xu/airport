import datetime
import logging


class LoggingFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = datetime.datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.strftime("%Y-%m-%d %H:%M:%S.%f")
        return s


def _create_logger():
    logger = logging.getLogger("airport")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    formatter = LoggingFormatter(
        "%(levelname).1s%(asctime)s [%(module)s.%(funcName)s:%(lineno)s] %(message)s",
        datefmt="%m%d %H:%M:%S.%f",
    )
    handler.setFormatter(formatter)
    return logger


logger = _create_logger()
