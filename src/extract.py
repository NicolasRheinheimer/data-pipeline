
import pandas as pd

def extract_clientes():
    df = pd.read_csv("data/01_raw/clientes.csv")
    return df

df_clientes = extract_clientes()
print(f"Clientes: {len(df_clientes)} registros")
df_clientes.head()


def extract_produtos():
    df = pd.read_csv("data/01_raw/produtos.csv")
    return df

df_produtos = extract_produtos()
print(f" Produtos: {len(df_produtos)} registros")
df_produtos.head()


def extract_vendas():
    df = pd.read_csv("data/01_raw/vendas.csv")
    return df

df_vendas = extract_vendas()
print(f" Vendas: {len(df_vendas)} registros")
df_vendas.head()


def extract_contas_receber():
    df = pd.read_csv("data/01_raw/contas_receber.csv")
    return df

df_contas = extract_contas_receber()
print(f" Contas a Receber: {len(df_contas)} registros")
df_contas.head()




































""" import pandas as pd

DATA_DIR = "data/01_raw"

def extract_clientes():
    return pd.read_csv(f"{DATA_DIR}/clientes.csv")

def extract_contas_receber():
    return pd.read_csv(f"{DATA_DIR}/contas_receber.csv")

def extract_produtos():
    return pd.read_csv(f"{DATA_DIR}/produtos.csv")

def extract_vendas():
    return pd.read_csv(f"{DATA_DIR}/vendas.csv")


# PARA VISUALIZAR TABELAS COLE ISSO NO TERMINAL ---> $env:PYTHONPATH="."; python src/extract.py
if __name__ == "__main__":
    
    print("\n\n=============================================================")
    print("1. ESPIANDO: TABELA DE CLIENTES")
    print("=============================================================")
    print(extract_clientes().head(3))
    
    print("\n\n=============================================================")
    print("2. ESPIANDO: TABELA DE PRODUTOS")
    print("=============================================================")
    print(extract_produtos().head(3))
    
    print("\n\n=============================================================")
    print("3. ESPIANDO: TABELA DE VENDAS")
    print("=============================================================")
    print(extract_vendas().head(3))
    
    print("\n\n=============================================================")
    print("4. ESPIANDO: TABELA DE CONTAS A RECEBER")
    print("=============================================================")
    print(extract_contas_receber().head(3)) """
