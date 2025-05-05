import streamlit as st
from authentication import setup_authentication

# ⚠️ DEVE SER A PRIMEIRA CHAMADA DO STREAMLIT
st.set_page_config(page_title="Dashboard Principal", layout="centered")

# Agora sim pode autenticar
auth_status, name, username, user_group = setup_authentication()

# Bloqueia acesso se não estiver autenticado
if not auth_status:
    st.warning("⚠️ Por favor, faça login para acessar o painel.")
    st.stop()

# Conteúdo da página
st.title("📊 Painel de Relatórios")
st.page_link("pages/Comissionamento.py", label="➡️ Acessar Relatório de Comissão")
