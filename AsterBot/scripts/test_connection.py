#!/usr/bin/env python3
"""
Script de teste para verificar a conectividade com a API Aster Dex
"""

import sys
import os
import json
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asterbot.api.client import AsterDexClient


def test_api_connection(config_path: str):
    """Testa a conexão com a API Aster Dex"""

    print("Testando conexao com Aster Dex API...")
    print("=" * 50)

    try:
        # Carregar configuração
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Criar cliente
        client = AsterDexClient(
            api_key=config['api_key'],
            secret_key=config['secret_key'],
            base_url=config.get('base_url', 'https://fapi.asterdex.com')
        )

        print("Cliente criado com sucesso")

        # Teste 1: Horário do servidor
        print("\nTestando horario do servidor...")
        server_time = client.get_server_time()
        print(f"   Horario: {server_time}")

        # Teste 2: Informações da exchange
        print("\nTestando informacoes da exchange...")
        exchange_info = client.get_exchange_info()
        print(f"   Simbolos disponiveis: {len(exchange_info.get('symbols', []))}")

        # Teste 3: Dados de mercado
        symbol = config.get('symbol', 'BTCUSDT')
        print(f"\nTestando dados de mercado para {symbol}...")

        ticker = client.get_24hr_ticker(symbol)
        if isinstance(ticker, list):
            ticker = ticker[0]
        print(f"   Preco atual: {ticker.get('lastPrice', 'N/A')}")
        print(f"   Volume 24h: {ticker.get('volume', 'N/A')}")

        # Teste 4: Orderbook
        print(f"\nTestando orderbook para {symbol}...")
        orderbook = client.get_orderbook(symbol, 5)
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])
        print(f"   Melhor bid: {bids[0][0] if bids else 'N/A'}")
        print(f"   Melhor ask: {asks[0][0] if asks else 'N/A'}")

        # Teste 5: Informações da conta (autenticado)
        print("\nTestando informacoes da conta...")
        try:
            account_info = client.get_account_info()
            print(f"   Conta ativa: OK")
            print(f"   Assets: {len(account_info.get('assets', []))}")
        except Exception as e:
            print(f"   ERRO na autenticacao: {e}")
            return False

        print("\nTodos os testes passaram com sucesso!")
        print("Bot esta pronto para operar")
        return True

    except FileNotFoundError:
        print(f"ERRO: Arquivo de configuracao nao encontrado: {config_path}")
        return False
    except json.JSONDecodeError:
        print(f"ERRO: Erro ao ler arquivo de configuracao (JSON invalido)")
        return False
    except Exception as e:
        print(f"ERRO: Erro durante o teste: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("ERRO: Uso: python test_connection.py <caminho_config>")
        print("   Exemplo: python test_connection.py config/config.json")
        return

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"ERRO: Arquivo nao encontrado: {config_path}")
        return

    success = test_api_connection(config_path)

    if success:
        print("\nProximos passos:")
        print("   1. Execute o bot: python main.py config/config.json")
        print("   2. Monitore os logs em logs/")
        print("   3. Ajuste configuracoes conforme necessario")
    else:
        print("\nVerifique:")
        print("   1. Suas credenciais da API")
        print("   2. Conexao com a internet")
        print("   3. Configuracoes no arquivo de config")


if __name__ == "__main__":
    main()