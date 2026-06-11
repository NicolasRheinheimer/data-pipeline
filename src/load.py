import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import DATABASE_URL, RAW_DATA_DIR

engine = create_engine(DATABASE_URL)

ARQUIVOS = {
    "dim_clientes": ("clientes.csv", None),
    "dim_produtos": ("produtos.csv", None),
    "fato_vendas": (
        "vendas.csv",
        lambda df: df.assign(
            data=pd.to_datetime(df["data"]).dt.date,
            data_vencimento=pd.to_datetime(df["data_vencimento"]).dt.date,
        ),
    ),
    "fato_contas_receber": (
        "contas_receber.csv",
        lambda df: df.assign(
            data_vencimento=pd.to_datetime(df["data_vencimento"]).dt.date,
            data_pagamento=pd.to_datetime(df["data_pagamento"]).dt.date,
        ),
    ),
}


def carregar_tabela(nome_tabela: str, arquivo: str, transformar=None) -> int:
    caminho = RAW_DATA_DIR / arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho}")

    print(f"\n--- CARREGANDO {nome_tabela} ---")
    df = pd.read_csv(caminho)
    if transformar:
        df = transformar(df)

    print(f"{len(df)} registros lidos de {arquivo}")
    print(df.head())
    df.to_sql(nome_tabela, con=engine, if_exists="replace", index=False)
    print(f"OK {nome_tabela} carregada com sucesso!")
    return len(df)


def main():
    print("OK Motor SQLAlchemy configurado!")
    resumo = {}
    for tabela, (arquivo, transformar) in ARQUIVOS.items():
        resumo[tabela] = carregar_tabela(tabela, arquivo, transformar)

    print("\n" + "=" * 50)
    print("CARGA CONCLUIDA COM SUCESSO!")
    print("=" * 50)
    for tabela, total in resumo.items():
        print(f"{tabela}: {total} registros")
    print("=" * 50)


if __name__ == "__main__":
    main()
