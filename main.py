import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
from typing import List, Tuple
from urllib.parse import urljoin
import time


class URLTester:
    """Classe para testar URLs com suporte a threading e controle de taxa"""
    
    def __init__(self, base_url: str, timeout: int = 5, max_workers: int = 10):
        """
        Inicializa o testador de URLs
        
        Args:
            base_url: A URL base do alvo
            timeout: Timeout para cada requisição em segundos
            max_workers: Número máximo de threads paralelas
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.found_urls = []
        self.tested_count = 0
        self.error_count = 0
    
    def load_wordlist(self, wordlist_path: str) -> List[str]:
        """
        Carrega a wordlist do arquivo
        
        Args:
            wordlist_path: Caminho para o arquivo de wordlist
            
        Returns:
            Lista de palavras limpas
        """
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                words = [line.strip() for line in f if line.strip()]
            print(f"[*] Wordlist carregada: {len(words)} entradas")
            return words
        except FileNotFoundError:
            print(f"[!] Erro: O arquivo '{wordlist_path}' não foi encontrado")
            sys.exit(1)
        except Exception as e:
            print(f"[!] Erro ao ler wordlist: {e}")
            sys.exit(1)
    
    def test_single_url(self, word: str) -> Tuple[str, int, bool]:
        """
        Testa uma única URL
        
        Args:
            word: Palavra para testar
            
        Returns:
            Tupla (url, status_code, sucesso)
        """
        full_url = urljoin(self.base_url + '/', word)
        
        try:
            response = self.session.get(
                full_url,
                timeout=self.timeout,
                allow_redirects=False
            )
            return (full_url, response.status_code, True)
        except requests.exceptions.Timeout:
            return (full_url, 0, False)
        except requests.exceptions.RequestException:
            return (full_url, 0, False)
    
    def test_urls(self, wordlist_path: str, show_errors: bool = False) -> None:
        """
        Testa URLs usando threading
        
        Args:
            wordlist_path: Caminho para o arquivo de wordlist
            show_errors: Se deve mostrar erros de conexão
        """
        print("=" * 60)
        print(f"[*] Alvo: {self.base_url}")
        print(f"[*] Threads: {self.max_workers}")
        print(f"[*] Timeout: {self.timeout}s")
        print("=" * 60)
        
        words = self.load_wordlist(wordlist_path)
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_word = {
                executor.submit(self.test_single_url, word): word 
                for word in words
            }
            
            for future in as_completed(future_to_word):
                self.tested_count += 1
                full_url, status_code, success = future.result()
                
                if success and status_code != 404:
                    status_color = self._get_status_color(status_code)
                    print(f"[+] {status_color}[{status_code}]{self._reset_color()} {full_url}")
                    self.found_urls.append((full_url, status_code))
                elif not success:
                    self.error_count += 1
                    if show_errors:
                        print(f"[!] Erro de conexão: {full_url}")
                
                # Progress indicator
                if self.tested_count % 100 == 0:
                    print(f"[*] Progresso: {self.tested_count}/{len(words)} testadas", end='\r')
        
        elapsed_time = time.time() - start_time
        self._print_summary(len(words), elapsed_time)
    
    def _get_status_color(self, status_code: int) -> str:
        """Retorna código de cor ANSI baseado no status HTTP"""
        if 200 <= status_code < 300:
            return '\033[92m'  # Verde
        elif 300 <= status_code < 400:
            return '\033[93m'  # Amarelo
        elif 400 <= status_code < 500:
            return '\033[91m'  # Vermelho
        else:
            return '\033[94m'  # Azul
    
    def _reset_color(self) -> str:
        """Reseta a cor do terminal"""
        return '\033[0m'
    
    def _print_summary(self, total: int, elapsed: float) -> None:
        """Imprime resumo dos resultados"""
        print("\n" + "=" * 60)
        print("[*] RESUMO")
        print("=" * 60)
        print(f"[*] URLs testadas: {total}")
        print(f"[+] URLs encontradas: {len(self.found_urls)}")
        print(f"[!] Erros de conexão: {self.error_count}")
        print(f"[*] Tempo decorrido: {elapsed:.2f}s")
        print(f"[*] Requisições/segundo: {total/elapsed:.2f}")
        print("=" * 60)
        
        if self.found_urls:
            print("\n[*] URLs encontradas:")
            for url, status in sorted(self.found_urls, key=lambda x: x[1]):
                print(f"  [{status}] {url}")


def main():
    """Função principal"""
    if len(sys.argv) < 3:
        print("Uso: python url_tester.py <url_base> <wordlist> [opções]")
        print("\nOpções:")
        print("  --timeout <segundos>    Timeout por requisição (padrão: 5)")
        print("  --threads <número>      Número de threads (padrão: 10)")
        print("  --show-errors           Mostrar erros de conexão")
        print("\nExemplo:")
        print("  python url_tester.py http://example.com wordlist.txt --threads 20")
        sys.exit(1)
    
    target_url = sys.argv[1]
    wordlist_file = sys.argv[2]
    
    # Parse opções
    timeout = 5
    threads = 10
    show_errors = False
    
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--timeout' and i + 1 < len(sys.argv):
            timeout = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--threads' and i + 1 < len(sys.argv):
            threads = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--show-errors':
            show_errors = True
            i += 1
        else:
            i += 1
    
    try:
        tester = URLTester(target_url, timeout=timeout, max_workers=threads)
        tester.test_urls(wordlist_file, show_errors=show_errors)
    except KeyboardInterrupt:
        print("\n\n[!] Interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()