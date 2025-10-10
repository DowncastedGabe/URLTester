# core/scanner.py
import asyncio
import aiohttp
import csv
from typing import Dict, Any, List
from tqdm.asyncio import tqdm
import logging

log = logging.getLogger("rich")

class URLScanner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config['target']['base_url']
        self.wordlist_path = config['target']['wordlist_path']
        self.output_file = config['reporting']['output_file']
        self.results = []

    async def _fetch(self, session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore):
        """Realiza uma única requisição HTTP de forma assíncrona."""
        headers = {'User-Agent': self.config['scanner']['user_agent']}
        async with semaphore:
            try:
                async with session.get(url, headers=headers, timeout=self.config['scanner']['timeout'], allow_redirects=False) as response:
                    content = await response.read()
                    return {
                        "url": url,
                        "status": response.status,
                        "content_length": len(content),
                        "content": content.lower() # para busca de keywords
                    }
            except asyncio.TimeoutError:
                return {"url": url, "status": "TIMEOUT", "content_length": 0}
            except aiohttp.ClientError:
                return {"url": url, "status": "ERROR", "content_length": 0}

    def _is_valid_result(self, result: Dict[str, Any]) -> bool:
        """Aplica as regras de filtro do arquivo de configuração."""
        status = result['status']
        if not isinstance(status, int):
            return False

        filters = self.config['filters']
        
        if filters['include_status_codes'] and status not in filters['include_status_codes']:
            return False
        
        if status in filters['exclude_status_codes']:
            return False
            
        if result['content_length'] <= filters['min_content_length']:
            return False
            
        for keyword in filters['exclude_keywords']:
            if keyword.encode('utf-8').lower() in result['content']:
                return False
                
        return True

    def _save_report(self):
        """Salva os resultados encontrados em um arquivo CSV."""
        if not self.results:
            log.info("Nenhum resultado válido encontrado para salvar.")
            return

        log.info(f"Salvando {len(self.results)} resultados em '{self.output_file}'...")
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "Status Code", "Content Length"])
            for result in self.results:
                writer.writerow([result['url'], result['status'], result['content_length']])
        log.info("Relatório salvo com sucesso!")

    async def run(self):
        """Orquestra todo o processo de escaneamento."""
        try:
            with open(self.wordlist_path, 'r') as f:
                words = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            log.error(f"Wordlist não encontrada em '{self.wordlist_path}'")
            return

        semaphore = asyncio.Semaphore(self.config['scanner']['concurrency'])
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for word in words:
                url = f"{self.base_url}/{word}"
                tasks.append(self._fetch(session, url, semaphore))

            log.info(f"Iniciando scan em '{self.base_url}' com {len(tasks)} URLs...")
            
            for f in tqdm.as_completed(tasks, total=len(tasks), desc="Escaneando"):
                result = await f
                if self._is_valid_result(result):
                    log.info(f"[+] Encontrado: {result['url']} [Status: {result['status']}, Tamanho: {result['content_length']}]")
                    self.results.append(result)

        self._save_report()