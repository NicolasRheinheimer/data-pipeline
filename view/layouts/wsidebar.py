import streamlit as st
import plotly.express as px

# Paleta de cores fixas do layout
COR_VERDE = "#2CA02C"
COR_VERMELHO = "#D62728"

def aplicar_estilo_dark(grafico):
    grafico.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        title_font=dict(size=15, color="#f8f9fa", family="sans-serif"),
        legend=dict(font=dict(color="#f8f9fa")),
        xaxis=dict(tickfont=dict(color="#f8f9fa"), showgrid=False),
        yaxis=dict(tickfont=dict(color="#f8f9fa"), showgrid=False)
    )
    return grafico

def renderizar_layout_financeiro(titulo, valor_caixa, valor_entradas, valor_saidas, df_historico, df_ralo, produtos_disponiveis):
    """
    CONSTRUTOR VISUAL PURO: 
    Recebe os dados mastigados e transforma em componentes visuais do Streamlit e Plotly.
    """
    
    # 3 Métricas no Topo
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.metric(label="💰 Sobra de Caixa Real (Lucro)", value=valor_caixa)
    with col_k2:
        st.metric(label="📈 Faturamento Total (Entradas)", value=valor_entradas)
    with col_k3:
        st.metric(label="📉 Custo Operacional (Saídas/CMV)", value=valor_saidas)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráfico da Esquerda: Evolução do Faturamento
    g_historico = px.area(
        df_historico, x="mes_nome", y="faturamento",
        title="Evolução do Faturamento Mensal",
        color_discrete_sequence=[COR_VERDE],
        labels={"mes_nome": "Mês", "faturamento": "Faturamento (R$)"}
    )
    g_historico.update_traces(line=dict(width=3))
    aplicar_estilo_dark(g_historico)
    
    # Gráfico da Direita: Ralo do Dinheiro
    df_ralo_ordenado = df_ralo.sort_values(by="custo", ascending=True)
    g_ralo = px.bar(
        df_ralo_ordenado, x="custo", y="item",
        orientation="h",
        title="Ralo do Dinheiro: Maiores Custos por Item",
        color_discrete_sequence=[COR_VERMELHO],
        labels={"custo": "Custo Total (R$)", "item": "Item/Produto"}
    )
    aplicar_estilo_dark(g_ralo)
    
    # Desenha a divisão de colunas na tela central (Proporção 2 por 1)
    col_esq, col_dir = st.columns([2, 1])
    with col_esq:
        st.plotly_chart(g_historico, use_container_width=True)
    with col_dir:
        st.plotly_chart(g_ralo, use_container_width=True)
        
    # Criação dos Filtros de Controle na Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Filtros do Caixa")
        

        opcoes_periodo = ["Todo o Período", "2026/1", "2025/2", "2025/1", "2024/2", "2024/1"]
        periodo_selecionado = st.selectbox(
            "Selecione o Período", 
            opcoes_periodo, 
            index=0,  # 0 indica que "Todo o Período" é o padrão
            key="filtro_periodo_fin"
        )
        
        # Filtro de Produto recebendo a lista dinâmica que vem do banco
        lista_produtos = ["Todos"] + list(produtos_disponiveis) 
        produto_selecionado = st.selectbox(
            "Selecione o Produto", 
            lista_produtos, 
            index=0, 
            key="filtro_produto_fin"
        )
        
    return periodo_selecionado, produto_selecionado