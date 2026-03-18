import logging


def get_logger():

    logger = logging.getLogger("automation_logger")

    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("test_execution.log")

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger