import os
import sys

import streamlit as st
from sqlalchemy import create_engine

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from view import financeiro, comercial, clientes

@st.cache_resource
def conectar_banco():
    try:
        from config.settings import DATABASE_URL
    except Exception as exc:
        st.error(f"Nao foi possivel ler a configuracao do banco: {exc}")
        return None

    try:
        return create_engine(DATABASE_URL)
    except Exception as exc:
        st.error(f"Nao foi possivel criar a conexao com o banco: {exc}")
        return None


st.set_page_config(
    page_title="Dashboard da Empresa",
    layout="wide",
    initial_sidebar_state="collapsed",
)

conn = conectar_banco()

tab_financeiro, tab_clientes, tab_comercial = st.tabs(
    [
        "Saude do Caixa",
        "Visao Clientes",
        "Visao Comercial",
    ]
)

with tab_financeiro:
    financeiro.render(conn)

with tab_clientes:
    clientes.render(conn)

with tab_comercial:
    comercial.render(conn)


