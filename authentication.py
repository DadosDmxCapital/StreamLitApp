import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def setup_authentication():
    import yaml
    from yaml.loader import SafeLoader
    import streamlit_authenticator as stauth

    # Carregar configurações de autenticação
    with open("config.yaml", "r") as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    try:
        authenticator.login()
    except Exception as e:
        st.error(e)

    auth_status = st.session_state.get("authentication_status", False)
    name = st.session_state.get("name", "")
    username = st.session_state.get("username", "")

    # Recuperar grupo do usuário ou definir um padrão
    user_data = config["credentials"]["usernames"].get(username, {})
    user_group = user_data.get("group", "SEM_GRUPO")  # Garante que sempre retorna algo

    if auth_status:
        st.sidebar.success(f"Bem-vindo, {name}!")
        authenticator.logout("Sair", "sidebar")

    return auth_status, name, username, user_group
