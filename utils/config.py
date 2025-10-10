import yaml
from typing import Dict, Any

def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """Carrega e valida o arquivo de configuração YAML."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        # Adicionar validações básicas aqui se necessário
        return config
    except FileNotFoundError:
        print(f"Erro: Arquivo de configuração '{path}' não encontrado.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Erro ao analisar o arquivo YAML: {e}")
        exit(1)