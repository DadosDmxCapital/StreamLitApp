import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def setup_authentication():
    """
    Configura a autenticação usando streamlit_authenticator
    
    Returns:
        tuple: Status de autenticação, nome e username
    """
    # Carregar configurações de autenticação
    with open("config.yaml", "r") as file:
        config = yaml.load(file, Loader=SafeLoader)
        
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # Autenticação
    try:
        authenticator.login()
    except Exception as e:
        st.error(e)

    # Status de autenticação
    auth_status = st.session_state.get("authentication_status", False)
    name = st.session_state.get("name", "")
    username = st.session_state.get("username", "")
    
    # Mostrar informação de login na sidebar
    if auth_status:
        st.sidebar.success(f"Bem-vindo, {name}!")
        authenticator.logout("Sair", "sidebar")
        
    return auth_status, name, username