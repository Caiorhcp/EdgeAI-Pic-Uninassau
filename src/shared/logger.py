# src/shared/logger.py
# Logger padronizado para o projeto

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado para o módulo solicitado.

    Uso:
        from src.shared.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Modelo carregado com sucesso.")
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
