# main.py
import typer
from typing_extensions import Annotated
import asyncio

from utils.logger import setup_logger
from utils.config import load_config
from core.scanner import URLScanner

app = typer.Typer()
log = setup_logger()

@app.command()
def scan(
    config_path: Annotated[str, typer.Option(help="Caminho para o arquivo de configuração.")] = "config.yaml",
    url: Annotated[str, typer.Option(help="Sobrescreve a URL base do arquivo de configuração.")] = None,
    wordlist: Annotated[str, typer.Option(help="Sobrescreve o caminho da wordlist.")] = None
):
    """
    Inicia um scanner de URLs assíncrono baseado em um arquivo de configuração.
    """
    log.info("======================================")
    log.info("=     Advanced URL Scanner v1.0      =")
    log.info("======================================")

    config = load_config(config_path)

    # Sobrescreve a configuração com argumentos da linha de comando, se fornecidos
    if url:
        config['base_url'] = url
    if wordlist:
        config['wordlist_path'] = wordlist

    scanner = URLScanner(config)
    asyncio.run(scanner.run())

if __name__ == "__main__":
    app()