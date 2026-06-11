import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
from google import genai
import time

from view.layouts.grade_3kpis import renderizar_template

# PALETA DE CORES DEFINIDA
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

@st.cache_data(ttl=3600)
def gerar_insights_gemini(df_kpis, df_eficiencia, df_recencia):
    resumo_kpis = df_kpis.to_string(index=False)
    resumo_clientes = df_eficiencia[["cliente", "faturamento_k", "margem_pct"]].to_string(index=False)
    resumo_alertas = df_recencia.to_string(index=False)
    
    prompt = f"""
    Você é um conselheiro comercial experiente, prático e direto. Analise os dados reais da nossa carteira de clientes abaixo e gere EXATAMENTE 3 dicas de negócios muito simples, fáceis de entender e rápidas (máximo 2 linhas por dica).
    
    ATENÇÃO ÀS REGRAS DE LINGUAGEM:
    1. NÃO use termos técnicos de análise ou palavras em inglês (como Churn, KPI, Recência, Share, BI, Overlap).
    2. Use palavras simples do dia a dia do comércio, como: "clientes sumidos", "tempo sem comprar", "lucro", "vendas" e "faturamento".
    3. Imagine que você está explicando a situação da empresa para um comerciante tradicional que quer saber direto ao ponto onde agir hoje.
    4. Aponte os nomes dos clientes reais que aparecem nos dados para sugerir ações (ex: "Ligue para o Cliente X que está há muitos dias sem comprar").

    Dados das Vendas do Período:
    {resumo_kpis}
    
    Principais Clientes por Vendas (em milhares k) e Margem de Lucro (%):
    {resumo_clientes}
    
    Lista de Clientes Sumidos e Dias Sem Comprar:
    {resumo_alertas}
    """
    
    # 🛡️ Mecanismo de Retentativa (Retry Logic) para evitar o erro 503
    tentativas = 3
    for i in range(tentativas):
        try:
            chave_api = st.secrets["api"].get("GEMINI_API_KEY", None)
            if not chave_api:
                return "⚠️ **Erro de Configuração:** A chave não foi encontrada no seu secrets.toml."
            
            client = genai.Client(api_key=str(chave_api).strip())
            resposta = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return resposta.text
            
        except Exception as e:
            # Se for a última tentativa e falhar, exibe o erro tratável
            if i == tentativas - 1:
                return f"🤖 Os insights automáticos de IA estão temporariamente indisponíveis (Servidor Ocupado). Por favor, mude um filtro para tentar novamente."
            # Se não for a última, espera 1.5 segundos e tenta de novo o loop
            time.sleep(1.5)

# --- QUERIES SQL ---

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


# --- MONTAGEM DO DASHBOARD ---

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

    # 🍕 Gráfico 1: Pizza
    g_esq = px.pie(
        df_pizza, names="cliente", values="margem_lucro",
        title="Participação na Margem de Lucro por Cliente",
        height=230,
        color_discrete_sequence=["#2CA02C", "#1F77B4", "#4FACFE", "#00F2FE", "#52B788"]
    )
    g_esq.update_traces(textposition='inside', textinfo='percent')
    g_esq.update_layout(showlegend=True)

    # 📊 Gráfico 2: Eficiência Comercial
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

    # 📈 Gráfico 3 (Longo): Termômetro de Recência
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

    # 💡 3. CONTEXTO DA INTELIGÊNCIA ARTIFICIAL: Adicionado na base do painel
    st.markdown("---")
    with st.container(border=True):
        st.markdown("### 🤖 Insights Consultivos da Carteira (Google Gemini)")
        with st.spinner("O Gemini está analisando o comportamento dos seus clientes..."):
            # Dispara a função enviando as tabelas ativas e capturando os insights reais
            texto_insights = gerar_insights_gemini(df_kpis, df_eficiencia, df_recencia)
            st.markdown(texto_insights)

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