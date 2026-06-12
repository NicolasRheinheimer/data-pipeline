import pandas as pd
import streamlit as st
from view.layouts.wsidebar import renderizar_layout_financeiro

def formatar_moeda(valor):
    valor = float(valor or 0)
    if abs(valor) >= 1_000_000:
        return f"R$ {valor / 1_000_000:.1f}M".replace(".", ",")
    if abs(valor) >= 1_000:
        return f"R$ {valor / 1_000:.1f}k".replace(".", ",")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_dados_do_banco(conn, periodo, produto):

    clausulas = ["1=1"] # Base para concatenar com AND facilmente
    
    # Tratamento do Semestre
    if periodo != "Todo o Período":
        ano, semestre = periodo.split("/")
        clausulas.append(f"EXTRACT(YEAR FROM data::date) = {ano}")
        if semestre == "1":
            clausulas.append("EXTRACT(MONTH FROM data::date) BETWEEN 1 AND 6")
        elif semestre == "2":
            clausulas.append("EXTRACT(MONTH FROM data::date) BETWEEN 7 AND 12")
            
    # Tratamento do Produto
    if produto != "Todos":
        # Evita quebra de aspas simples no SQL caso o nome do produto tenha caracteres especiais
        produto_limpo = produto.replace("'", "''")
        clausulas.append(f"nome_produto = '{produto_limpo}'")
        
    where_condicao = " AND ".join(clausulas)

    # Busca lista única de produtos para alimentar o filtro da sidebar
    df_lista_prod = pd.read_sql("SELECT DISTINCT nome_produto FROM public.f_vendas WHERE nome_produto IS NOT NULL ORDER BY nome_produto", conn)
    produtos_lista = df_lista_prod["nome_produto"].tolist()

    # Query KPIs
    df_kpis = pd.read_sql(f"""
        SELECT 
            COALESCE(SUM(margem), 0) AS disponibilidade_caixa,
            COALESCE(SUM(valor_total), 0) AS total_entradas,
            COALESCE(SUM(valor_total - margem), 0) AS total_saidas
        FROM public.f_vendas WHERE {where_condicao}
    """, conn)

    if periodo == "Todo o Período":
        formato_data = "YYYY/MM"
        ordem_data = "TO_CHAR(data::date, 'YYYY/MM')"
    else:
        formato_data = "Mon"
        ordem_data = "EXTRACT(MONTH FROM data::date)"
    
    df_historico = pd.read_sql(f"""
        SELECT 
            TO_CHAR(data::date, '{formato_data}') AS mes_nome, 
            SUM(valor_total) AS faturamento
        FROM public.f_vendas 
        WHERE {where_condicao}
        GROUP BY mes_nome, {ordem_data}
        ORDER BY {ordem_data}
    """, conn)

    # Query Ralo do Dinheiro
    df_ralo = pd.read_sql(f"""
        SELECT COALESCE(nome_produto, 'Outros') AS item, SUM(valor_total - margem) AS custo
        FROM public.f_vendas WHERE {where_condicao}
        GROUP BY item ORDER BY custo DESC LIMIT 5
    """, conn)

    return df_kpis, df_historico, df_ralo, produtos_lista

def render(conn):
    # Recupera ou inicializa os estados dos novos filtros na sessão
    periodo_ativo = st.session_state.get("filtro_periodo_fin", "Todo o Período")
    produto_ativo = st.session_state.get("filtro_produto_fin", "Todos")
    
    # 1. Puxa os dados estruturados do banco com os filtros dinâmicos
    df_kpis, df_historico, df_ralo, lista_produtos = carregar_dados_do_banco(conn, periodo_ativo, produto_ativo)
    
    # 2. Formata os KPIs
    if not df_kpis.empty:
        dados = df_kpis.iloc[0]
        caixa_fmt = formatar_moeda(dados["disponibilidade_caixa"])
        entradas_fmt = formatar_moeda(dados["total_entradas"])
        saidas_fmt = formatar_moeda(dados["total_saidas"])
    else:
        caixa_fmt, entradas_fmt, saidas_fmt = "R$ 0,00", "R$ 0,00", "R$ 0,00"
    
    # 3. Choca os dados direto no layout maestro wsidebar
    periodo_upd, produto_upd = renderizar_layout_financeiro(
        titulo="📊 Visão Financeira",
        valor_caixa=caixa_fmt,
        valor_entradas=entradas_fmt,
        valor_saidas=saidas_fmt,
        df_historico=df_historico,
        df_ralo=df_ralo,
        produtos_disponiveis=lista_produtos
    )
    
    # Se o usuário mexer em qualquer um dos dois filtros, atualiza e recarrega a tela
    if periodo_upd != periodo_ativo or produto_upd != produto_ativo:
        st.session_state.filtro_periodo_fin = periodo_upd
        st.session_state.filtro_produto_fin = produto_upd # 👈 Linha corrigida com '='
        st.rerun()