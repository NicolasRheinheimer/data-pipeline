import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import time

from view.layouts.grade_3kpis import renderizar_template

COR_FATURAMENTO = "#1F77B4"  
COR_MARGEM = "#2CA02C"       
COR_RECENCIA = "#FF7F0E"     

def formatar_moeda(valor):
    valor = float(valor or 0)
    if abs(valor) >= 1_000_000:
        return f"R$ {valor / 1_000_000:.1f}M".replace(".", ",")
    if abs(valor) >= 1_000:
        return f"R$ {valor / 1_000:.1f}k".replace(".", ",")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_percentual(valor):
    return f"{float(valor or 0):.1f}%".replace(".", ",")


def carregar_lista_clientes_unicos(conn):
    df = pd.read_sql("SELECT DISTINCT COALESCE(nome_cliente, 'Sem cadastro') AS cliente FROM public.f_vendas ORDER BY cliente", conn)
    return df["cliente"].tolist()

def carregar_dados_dashboard(conn, clientes_filtrados, periodo_filtrado):
    clausula_data = "1=1"
    if periodo_filtrado == "Último Mês":
        clausula_data = "v.data::date >= CURRENT_DATE - INTERVAL '30 days'"
    elif periodo_filtrado == "Última Semana":
        clausula_data = "v.data::date >= CURRENT_DATE - INTERVAL '7 days'"
    elif periodo_filtrado == "Ano Atual":
        clausula_data = "EXTRACT(YEAR FROM v.data::date) = EXTRACT(YEAR FROM CURRENT_DATE)"

    clausula_cliente = "1=1"
    if clientes_filtrados and len(clientes_filtrados) > 0:
        formatado = ", ".join([f"'{c}'" for c in clientes_filtrados])
        clausula_cliente = f"v.nome_cliente IN ({formatado})"

    filtro_final = f"WHERE {clausula_data} AND {clausula_cliente}"

    df_kpis = pd.read_sql(f"""
        SELECT 
            COALESCE(SUM(v.valor_total), 0) AS faturamento_total, 
            COALESCE((SUM(v.margem) / NULLIF(SUM(v.valor_total), 0)) * 100, 0) AS margem_media_percentual
        FROM public.f_vendas v
        {filtro_final}
    """, conn)

    df_pizza = pd.read_sql(f"""
        SELECT 
            COALESCE(v.nome_cliente, 'Sem cadastro') AS cliente,
            SUM(v.margem) AS margem_lucro
        FROM public.f_vendas v
        {filtro_final}
        GROUP BY 1
        ORDER BY margem_lucro DESC
    """, conn)

    df_eficiencia = pd.read_sql(f"""
        SELECT 
            COALESCE(v.nome_cliente, 'Sem cadastro') AS cliente, 
            SUM(v.valor_total) / 1000.0 AS faturamento_k, 
            SUM(v.margem) / 1000.0 AS margem_k,
            COALESCE((SUM(v.margem) / NULLIF(SUM(v.valor_total), 0)) * 100, 0) AS margem_pct
        FROM public.f_vendas v 
        {filtro_final}
        GROUP BY 1 
        ORDER BY faturamento_k DESC 
        LIMIT 7
    """, conn)

    df_recencia = pd.read_sql(f"""
        SELECT 
            COALESCE(v.nome_cliente, 'Sem cadastro') AS cliente,
            CURRENT_DATE - MAX(v.data::date) AS dias_sem_comprar
        FROM public.f_vendas v
        {filtro_final}
        GROUP BY 1
        ORDER BY dias_sem_comprar DESC
        LIMIT 15
    """, conn)

    return df_kpis, df_pizza, df_eficiencia, df_recencia


def aplicar_estilo(grafico):
    grafico.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=35, r=25, t=35, b=25),
        xaxis_title=None, yaxis_title=None, legend_title_text=None,
        title_font=dict(size=14, color="#f8f9fa", family="sans-serif"),
    )
    grafico.update_xaxes(showgrid=False)
    grafico.update_yaxes=False
    return grafico


# view

def montar_dashboard(conn):
    if "filtro_clientes" not in st.session_state:
        st.session_state.filtro_clientes = []
    if "filtro_data" not in st.session_state:
        st.session_state.filtro_data = "Todo o Histórico"

    lista_clientes = carregar_lista_clientes_unicos(conn)
    
    df_kpis, df_pizza, df_eficiencia, df_recencia = carregar_dados_dashboard(
        conn, st.session_state.filtro_clientes, st.session_state.filtro_data
    )

    kpis = df_kpis.iloc[0] if not df_kpis.empty else {"faturamento_total": 0, "margem_media_percentual": 0}
    
    meus_kpis = [
        {"label": "Faturamento Total", "value": formatar_moeda(kpis["faturamento_total"])},
        {"label": "Margem de Lucro Real", "value": formatar_percentual(kpis["margem_media_percentual"])},
    ]

    # 1st chart 
    g_esq = px.pie(
        df_pizza, names="cliente", values="margem_lucro",
        title="Participação na Margem de Lucro por Cliente",
        height=230,
        color_discrete_sequence=["#2CA02C", "#1F77B4", "#4FACFE", "#00F2FE", "#52B788"]
    )
    g_esq.update_traces(textposition='inside', textinfo='percent')
    g_esq.update_layout(showlegend=True)

    # 2nd chart
    g_dir = go.Figure()
    g_dir.add_trace(go.Bar(
        x=df_eficiencia["cliente"], y=df_eficiencia["faturamento_k"],
        name="Faturamento", marker_color=COR_FATURAMENTO
    ))
    g_dir.add_trace(go.Bar(
        x=df_eficiencia["cliente"], y=df_eficiencia["margem_k"],
        name="Margem", marker_color=COR_MARGEM,
        text=df_eficiencia["margem_pct"].apply(lambda x: f"{x:.1f}%"),
        textposition='inside',
        textfont=dict(color="#ffffff", size=11)
    ))
    g_dir.update_layout(
        barmode="group", 
        title="Eficiência Comercial: Valor Total vs Margem (em Milhares)", 
        height=230,
        yaxis=dict(ticksuffix="k")
    )

    # 3rd chart
    g_longo = px.line(
        df_recencia, x="cliente", y="dias_sem_comprar",
        title="Termômetro de Recência: Dias desde a última compra por Cliente",
        height=240, color_discrete_sequence=[COR_RECENCIA]
    )

    for grafico in [g_esq, g_dir, g_longo]:
        aplicar_estilo(grafico)

    g_longo.update_traces(line=dict(width=4), mode="lines+markers")

    # Renderiza o grid de gráficos estruturado do template
    res_clientes, res_data = renderizar_template(
        "Análise Estratégica de Clientes", meus_kpis, lista_clientes, g_esq, g_dir, g_longo
    )

    if res_clientes != st.session_state.filtro_clientes or res_data != st.session_state.filtro_data:
        st.session_state.filtro_clientes = res_clientes
        st.session_state.filtro_data = res_data
        st.rerun()

def render(conn):
    if conn is None:
        st.warning("Conexão com o banco indisponível.")
        return
    try:
        montar_dashboard(conn)
    except Exception as exc:
        st.error(f"Erro ao carregar dados dinâmicos: {exc}")