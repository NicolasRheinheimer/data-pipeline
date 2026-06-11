import streamlit as st

def renderizar_template(titulo_aba, kpis, lista_clientes, fig_esquerda, fig_direita, fig_fundo_longo):
    
    st.markdown("""
        <style>
            header[data-testid="stHeader"] {
                display: block !important;
                height: 2.5rem !important;
            }
            .main .block-container {
                padding-top: 1rem !important;
                padding-bottom: 0.5rem !important;
            }
            
            /* 🎯 CENTRALIZAÇÃO TOTAL DO KPI */
            div[data-testid="stMetric"] {
                min-height: 90px !important;
                max-height: 90px !important;
                display: flex;
                flex-direction: column;
                justify-content: center;
                text-align: center !important; 
                align-items: center !important; 
            }
            
            div[data-testid="stMetricValue"], 
            div[data-testid="stMetricLabel"], 
            div[data-testid="stMetricDelta"] {
                display: flex;
                justify-content: center;
                width: 100%;
            }
            
            /* Ajuste para o multiselect e selectbox conversarem bem no espaço */
            div[data-testid="stMultiSelect"], div[data-testid="stSelectbox"] {
                margin-bottom: -5px !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Linha do topo com 3 colunas
    col1, col2, col3 = st.columns([1, 1, 1.2])
    
    # KPI 1
    if len(kpis) > 0:
        with col1:
            with st.container(border=True):
                st.metric(label=kpis[0].get("label"), value=kpis[0].get("value"), delta=kpis[0].get("delta"))
                
    # KPI 2
    if len(kpis) > 1:
        with col2:
            with st.container(border=True):
                st.metric(label=kpis[1].get("label"), value=kpis[1].get("value"), delta=kpis[1].get("delta"))
                
    # 🎛️ COLUNA DE FILTROS EVOLUÍDOS
    with col3:
        with st.container(border=True):
            # Filtro 1: st.multiselect para permitir selecionar 1, 2 ou vários clientes.
            # Se deixar vazio, representará "Todos os Clientes"
            filtros_clientes_selecionados = st.multiselect(
                "Selecionar Clientes",
                options=list(lista_clientes),
                default=st.session_state.get("filtro_clientes", []),
                placeholder="Todos os Clientes (Nenhum filtrado)",
                label_visibility="collapsed"
            )
            
            # Filtro 2: Período de Data com "Todo o Histórico" como primeira opção
            filtro_data = st.selectbox(
                "Período",
                options=["Todo o Histórico", "Ano Atual", "Último Mês", "Última Semana"],
                index=["Todo o Histórico", "Ano Atual", "Último Mês", "Última Semana"].index(st.session_state.get("filtro_data", "Todo o Histórico")),
                label_visibility="collapsed"
            )
                
    # Linha do Meio
    col_esq, col_dir = st.columns(2)
    with col_esq:
        with st.container(border=True):
            st.plotly_chart(fig_esquerda, use_container_width=True)
        
    with col_dir:
        with st.container(border=True):
            st.plotly_chart(fig_direita, use_container_width=True)
        
    # Linha de Baixo (Gráfico Longo)
    with st.container(border=True):
        st.plotly_chart(fig_fundo_longo, use_container_width=True)
        
    return filtros_clientes_selecionados, filtro_data