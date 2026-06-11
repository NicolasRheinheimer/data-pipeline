# ### Bloco 1: Importações e Definição das Funções de Limpeza

import pandas as pd
import numpy as np
import pandas as pd
from datetime import datetime
from src.extract import extract_vendas, extract_produtos, extract_clientes, extract_contas_receber

def transformar_vendas():
    df_vendas = extract_vendas()
    df_produtos = extract_produtos()
    df_clientes = extract_clientes()

    # Seleciona as colunas e renomeia 'nome' para 'nome_produto'
    df_consolidado = pd.merge(df_vendas, df_produtos[['produto_id', 'nome', 'custo_unitario_medio']], on="produto_id", how="left"
    ).rename(columns={"nome": "nome_produto"})
    
    # Seleciona apenas o necessário e renomeia 'nome' para 'nome_cliente'
    df_clientes_selecionado = df_clientes[['cliente_id', 'nome', 'dias_pagamento']].rename(columns={"nome": "nome_cliente"})

    df_consolidado = pd.merge(df_consolidado, df_clientes_selecionado, on="cliente_id", how="left")
    
    # Renomeia a coluna de dias de pagamento para o padrão do projeto
    df_consolidado = df_consolidado.rename(columns={"dias_pagamento": "dias_pagamento_cliente"})
    
    # 3. TRANSFORMAÇÕES: Cria as colunas calculadas de lucro
    df_consolidado['margem'] = df_consolidado['valor_total'] - (df_consolidado['quantidade'] * df_consolidado['custo_unitario_medio'])
    df_consolidado['margem_percentual'] = (df_consolidado['margem'] / df_consolidado['valor_total']) * 100
    
    # 4. LIMPEZA: Organiza na ordem exata do plano
    colunas_ordenadas = [
        'venda_id', 'data', 'cliente_id', 'nome_cliente', 'dias_pagamento_cliente',
        'produto_id', 'nome_produto', 'quantidade', 'valor_unitario', 'valor_total',
        'data_vencimento', 'margem', 'margem_percentual'
    ]
    return df_consolidado[colunas_ordenadas]


def transformar_contas_receber():
    df_contas = extract_contas_receber()
    df_clientes = extract_clientes()
    
    # CORREÇÃO AQUI: Renomeia 'nome' para 'nome_cliente' logo no merge do financeiro também
    df_clientes_selecionado = df_clientes[['cliente_id', 'nome']].rename(columns={"nome": "nome_cliente"})
    df_consolidado = pd.merge(df_contas, df_clientes_selecionado, on="cliente_id", how="left")
    
    # PREPARAÇÃO: Datas reais
    df_consolidado['data_vencimento'] = pd.to_datetime(df_consolidado['data_vencimento'])
    df_consolidado['data_pagamento'] = pd.to_datetime(df_consolidado['data_pagamento'])
    
    # 1. Garante que as colunas sejam tratadas como Data pelo Pandas
    df_consolidado['data_vencimento'] = pd.to_datetime(df_consolidado['data_vencimento'])
    df_consolidado['data_pagamento'] = pd.to_datetime(df_consolidado['data_pagamento'])
    
    # Data de hoje para as contas que ainda estão abertas
    data_hoje = pd.to_datetime(pd.Timestamp.now().date())
    
    # 2. Define qual data usar no cálculo: data de pagamento (se houver) ou data de hoje
    data_final_calculo = np.where(
        df_consolidado['data_pagamento'].notna(), 
        df_consolidado['data_pagamento'], 
        data_hoje
    )
    
    # 3. Calcula a diferença bruta de dias tratando como uma Série limpa do Pandas
    dias_diferenca = (pd.Series(data_final_calculo) - df_consolidado['data_vencimento'].reset_index(drop=True)).dt.days
    dias_diferenca.index = df_consolidado.index # Sincroniza os índices

    # 4. Cria as colunas comerciais usando o .clip() para evitar erros de matriz
    df_consolidado['dias_atraso'] = dias_diferenca.clip(lower=0)
    df_consolidado['dias_anticipacao'] = (dias_diferenca * -1).clip(lower=0)
    
    # 5. Define o Status Comercial Inteligente
    df_consolidado['status_comercial'] = np.where(
        df_consolidado['data_pagamento'].notna(), 
        "Pago", 
        np.where(dias_diferenca > 0, "Atrasado", "Em Aberto")
    )
    
    colunas_ordenadas = [
        'recebimento_id', 'venda_id', 'cliente_id', 'nome_cliente', 'valor',
        'data_vencimento', 'data_pagamento', 'dias_atraso', 'dias_anticipacao', 
        'status_comercial'
    ]

    return df_consolidado[colunas_ordenadas]


def situacao_clientes():
    df_vendas = transformar_vendas()
    df_contas = transformar_contas_receber()
    
    # PIVOT DE VENDAS
    resumo_vendas = df_vendas.groupby(['cliente_id', 'nome_cliente']).agg(
        faturamento_total_cliente=('valor_total', 'sum'),
        margem_total_cliente=('margem', 'sum')
    ).reset_index()
    
    # PIVOT DO FINANCEIRO
    resumo_financeiro = df_contas.groupby('cliente_id').agg(
        valor_a_receber=('valor', lambda x: x[df_contas.loc[x.index, 'status_comercial'] == 'Em Aberto'].sum()),
        valor_atrasado=('valor', lambda x: x[df_contas.loc[x.index, 'status_comercial'] == 'Atrasado'].sum()),
        dias_medio_recebimento=('dias_atraso', lambda x: x[df_contas.loc[x.index, 'status_comercial'] == 'Pago'].mean())
    ).reset_index()
    
    resumo_financeiro['dias_medio_recebimento'] = resumo_financeiro['dias_medio_recebimento'].fillna(0).astype(int)
    
    # UNIR OS DOIS LADOS
    df_clientes_final = pd.merge(resumo_vendas, resumo_financeiro, on="cliente_id", how="left")
    df_clientes_final[['valor_a_receber', 'valor_atrasado']] = df_clientes_final[['valor_a_receber', 'valor_atrasado']].fillna(0)
    
    # CÁLCULO ESTRATÉGICO
    df_clientes_final['percentual_atraso'] = (df_clientes_final['valor_atrasado'] / df_clientes_final['faturamento_total_cliente']) * 100
    df_clientes_final['percentual_atraso'] = df_clientes_final['percentual_atraso'].fillna(0).round(1)
    
    colunas_ordenadas = [
        'cliente_id', 'nome_cliente', 'faturamento_total_cliente', 'margem_total_cliente',
        'valor_a_receber', 'valor_atrasado', 'percentual_atraso', 'dias_medio_recebimento'
    ]
    return df_clientes_final[colunas_ordenadas]


# %%
# ### Bloco 3: Execução do Teste Principal
if __name__ == "__main__":
    import sys, os
    sys.path.append(os.getcwd())

    df_totalvendas = transformar_vendas()
    print(df_totalvendas.head(1))

    df_financeiro = transformar_contas_receber()
    print(df_financeiro.head(1))
    
    df_situacao = situacao_clientes()
    print(df_situacao.head(1))

