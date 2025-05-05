import streamlit as st
from authentication import setup_authentication
from database import connect_to_database, fetch_data
from data_processing import process_data, format_dataframes, rename_gerente
from pdf_generator import generate_pdf_report
from visualizations import create_visualizations
import base64
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Relatório de Comissionamento", layout="wide")

# Setup de autenticação
auth_status, name, username, user_group = setup_authentication()

# Verifica status de autenticação
if not auth_status:
    st.warning("⚠️ Por favor, faça login para acessar o relatório.")
    st.stop()

st.title("Comissão de Operações")

# Conectar ao banco de dados
connection_status = st.empty()

try:
    connection_status.info("Conectando ao banco de dados...")
    conn = connect_to_database()
    connection_status.success("✅ Conexão bem-sucedida!")

    with st.spinner('Carregando dados...'):
        df = fetch_data(conn)

    # Aplicar renomeação dos gerentes antes de qualquer filtragem
    if 'gerente' in df.columns:
        df['gerente'] = df['gerente'].apply(rename_gerente)

    # Aplicar os filtros laterais primeiro
    df_filtered = process_data(df)

    # Filtrar dados pelo gerente logado
    if user_group != "ADM":
        df_filtered = df_filtered[df_filtered["gerente"] == user_group]  # Apenas dados do próprio gerente

    # Processar e formatar dados usando a função de data_processing.py
    df_grouped, df_grouped_with_totals, summary_stats = format_dataframes(df_filtered)

    st.write(f"Total de cedentes: {len(df_grouped)} (de {df_filtered['cedente'].nunique()} cedentes filtrados)")

    # Exibir a tabela
    st.dataframe(df_grouped_with_totals)

    # Gerar PDF utilizando a função do pdf_generator.py
    pdf_buffer = generate_pdf_report(df_filtered)

    # Adicionar um botão para download do PDF
    pdf_file = pdf_buffer.getvalue()

    st.download_button(
        label="Baixar Relatório PDF",
        data=pdf_file,
        file_name="relatorio_comissionamento.pdf",
        mime="application/pdf"
    )

    # Criar visualizações usando a função do visualizations.py
    create_visualizations(df_filtered)

except Exception as e:
    error_message = str(e)
    connection_status.error(f"❌ Erro ao conectar: {error_message}")

    # Oferecer dicas baseadas no erro
    if "18456" in error_message:
        st.warning("""        
        **Erro de autenticação detectado!** Verifique:
        - Se o nome de usuário e senha estão corretos
        - Se a conta possui acesso ao banco de dados
        - Se o tipo de autenticação (ActiveDirectoryPassword) é apropriado para sua conta
        """)
