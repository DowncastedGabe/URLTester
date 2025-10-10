import logging
from rich.logging import RichHandler

def setup_logger():
    """Configura o logger para usar o Rich para uma saída bonita."""
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    return logging.getLogger("rich")