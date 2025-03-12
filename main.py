import os
import pyodbc
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime
from dotenv import load_dotenv
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import locale
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="Relatório de Comissionamento", layout="wide")

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

# Verifica status de autenticação
if st.session_state["authentication_status"]:
    name = st.session_state["name"]
    username = st.session_state["username"]
    st.sidebar.success(f"Bem-vindo, {name}!")
    authenticator.logout("Sair", "sidebar")
else:
    st.warning("⚠️ Por favor, faça login para acessar o relatório.")
    st.stop()  # Interrompe a execução se o usuário não estiver autenticado

# Configuração da página Streamlit
st.title("Comissão de Operações")

# Configurar locale para formatação de números com vírgula para decimais
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass  # Se ambos falharem, usaremos formatação manual

# Carregar as variáveis do .env
load_dotenv(".env")

# Pegar as credenciais
server = os.getenv("FABRIC_SERVER")
database = os.getenv("FABRIC_DATABASE")
username = os.getenv("FABRIC_USERNAME")
password = os.getenv("FABRIC_PASSWORD")

# Verificar se as variáveis essenciais foram carregadas
if not all([server, database, username, password]):
    st.error("⚠️ Uma ou mais variáveis de ambiente estão ausentes. Verifique o seu arquivo .env!")
    st.stop()

# Construir a string de conexão para pyodbc
conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Authentication=ActiveDirectoryPassword"

# Função para formatar valores monetários com vírgula como separador decimal
def format_currency(value):
    # Formatar com ponto para milhares e vírgula para decimais
    # Ex: 1.234,56
    return f"R$ {value:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")

# Função para formatar números decimais com vírgula como separador decimal
def format_decimal(value, digits=2):
    # Formatar com vírgula para decimais
    # Ex: 12,34
    return f"{value:.{digits}f}".replace(".", ",")

# Função para formatar data no formato curto (dd/mm/aaaa)
def format_short_date(date):
    if pd.isna(date):
        return ""
    return date.strftime('%d/%m/%Y')

# Função para renomear captadores
def rename_gerente(gerente):
    if pd.isna(gerente):
        return gerente
    
    mapping = {
        "*COMERCIAL - RFA - ADITAR ***": "RFA",
        "*COMERCIAL - ALX": "ALX",
        "*COMERCIAL - ANDRE TAVARES ***": "ANDRE TAVARES",
        "*COMERCIAL - LEANDRO APARECIDO VIEIRA DE SOUSA": "LEANDRO APARECIDO",
        "*COMERCIAL - LUIS FERNANDO DE JESUS LOMBELLO": "LUIS FERNANDO",
        "*COMERCIAL - MANUEL SANJI GOMES KOMIYAMA": "MANUEL",
        "*COMERCIAL - ROLAN GABRIEL SYLVESTRE MARINO": "ROLAN",
        "*COMERCIAL RODRIGO WEISSINGER CARVALHO***": "RODRIGO",
        "Setor de Novos Negócios - DMX Capital": "DMX Capital"
    }
    
    return mapping.get(gerente, gerente)

# Função para gerar PDF
def generate_pdf(df, filtered=False):
    buffer = BytesIO()
    
    # Usar orientação paisagem para ter mais espaço horizontal
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    
    # Título
    title = "Relatório de Comissionamento por Cedente"
    if filtered:
        title += " (Filtrado)"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))
    
    # Data do relatório
    date_style = styles['Normal']
    date_text = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    elements.append(Paragraph(date_text, date_style))
    elements.append(Spacer(1, 12))
    
    # Preparar dados para tabela
    # Limitar a 20 primeiras linhas para o PDF não ficar muito grande
    pdf_data = [df.columns.tolist()] + df.head(20).values.tolist()
    
    # Adicionar linha para totais (se o DataFrame tiver linhas)
    if len(df) > 0:
        totals_row = ["TOTAL"] + [""] * (len(df.columns) - 4) + [
            df["DESAGIO"].iloc[-1] if df.index[-1] == "TOTAL" else "",
            df["VALOR OPERADO"].iloc[-1] if df.index[-1] == "TOTAL" else ""
        ]
        pdf_data.append(totals_row)
    
    # Calcular larguras das colunas automaticamente baseado no conteúdo
    col_widths = [None] * len(df.columns)
    
    # Definindo larguras específicas para colunas que sabemos que precisam de mais espaço
    col_indices = {col: i for i, col in enumerate(df.columns)}
    
    # Ajustar larguras baseadas no tipo de dados
    if 'CEDENTE' in col_indices:
        col_widths[col_indices['CEDENTE']] = 3.5*inch
    if 'GERENTE' in col_indices:
        col_widths[col_indices['GERENTE']] = 1.0*inch
    if 'ETAPA' in col_indices:
        col_widths[col_indices['ETAPA']] = 1.0*inch
    if 'DATA' in col_indices:
        col_widths[col_indices['DATA']] = 1.0*inch
    if 'PRAZO MEDIO' in col_indices:
        col_widths[col_indices['PRAZO MEDIO']] = 1.2*inch
    if 'DESAGIO' in col_indices:
        col_widths[col_indices['DESAGIO']] = 1.5*inch
    if 'VALOR OPERADO' in col_indices:
        col_widths[col_indices['VALOR OPERADO']] = 1.5*inch
    
    # Criar tabela com larguras específicas
    table = Table(pdf_data, colWidths=col_widths, repeatRows=1)
    
    # Estilo da tabela - ajustado para melhor legibilidade
    style = TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Corpo da tabela
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (3, -1), 'LEFT'),  # Alinhar texto à esquerda (ajustado para incluir GERENTE)
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Alinhar números à direita (ajustado para incluir GERENTE)
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        
        # Grade
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        
        # Linhas alternadas para melhor leitura
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        
        # Estilo para linha de total
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ])
    
    # Adicionar estilo específico para reduzir a fonte da coluna CEDENTE
    if 'CEDENTE' in col_indices:
        cedente_idx = col_indices['CEDENTE']
        style.add('FONTSIZE', (cedente_idx, 1), (cedente_idx, -2), 7)  # Tamanho de fonte menor para a coluna Cedente
    
    table.setStyle(style)
    elements.append(table)
    
    # Adicionar nota de rodapé
    elements.append(Spacer(1, 20))
    footer_text = "Nota: Este relatório contém informações confidenciais."
    if len(df) > 20:
        footer_text += f" Apenas as primeiras 20 de {len(df)} linhas são mostradas no PDF."
    elements.append(Paragraph(footer_text, styles['Italic']))
    
    # Construir PDF
    doc.build(elements)
    
    return buffer

# Container para exibir status da conexão
connection_status = st.empty()

# Testar a conexão
try:
    connection_status.info("Conectando ao banco de dados...")
    conn = pyodbc.connect(conn_str)
    connection_status.success("✅ Conexão bem-sucedida!")
    
    # Query modificada para incluir a coluna GERENTE da tabela dbo.d_cedentes
    # usando JOIN pela coluna CPF_CNPJ
    query = """
SELECT 
    f.CEDENTE,
    d.GERENTE,  -- Nova coluna adicionada
    f.ETAPA, 
    f.DATA, 
    f.PRAZO_MEDIO, 
    f.VALOR_DESAGIO, 
    f.VALOR_BRUTO 
FROM dbo.f_operacao f
LEFT JOIN dbo.d_Cedentes d ON f.CPF_CNPJ_CEDENTE = d.CPF_CNPJ
    """
    
    # Mostrar progresso
    with st.spinner('Carregando dados...'):
        # Ler os dados no Pandas
        df = pd.read_sql(query, conn)
    
    # Fechar conexão
    conn.close()
    
    # Aplicar a função de renomeação aos captadores
    if 'CAPTADOR' in df.columns:
        df['CAPTADOR'] = df['CAPTADOR'].apply(rename_captador)
    
    # Converter a coluna DATA para datetime se não for
    if 'DATA' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['DATA']):
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    
    # Criar sidebar para filtros
    st.sidebar.header("Filtros")
    
    # Verificar se as colunas especificadas existem
    if 'DATA' in df.columns:
        # Extrair datas mínima e máxima
        min_date = df['DATA'].min().date()
        max_date = df['DATA'].max().date()
        
        # Filtro de período
        st.sidebar.subheader("Filtro por Período")
        date_range = st.sidebar.date_input(
            "Selecione o período",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        
        # Aplicar filtro de data
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df['DATA'].dt.date >= start_date) & (df['DATA'].dt.date <= end_date)
            df_filtered = df.loc[mask]
        else:
            df_filtered = df
    else:
        st.sidebar.warning("A coluna 'DATA' não foi encontrada na tabela")
        df_filtered = df
    
    # Filtro de cedentes
    if 'CEDENTE' in df.columns:
        st.sidebar.subheader("Filtro por Cedente")
        cedentes = sorted(df['CEDENTE'].dropna().unique())
        selected_cedentes = st.sidebar.multiselect("Selecione os cedentes", cedentes)
        
        # Aplicar filtro de cedentes
        if selected_cedentes:
            df_filtered = df_filtered[df_filtered['CEDENTE'].isin(selected_cedentes)]
    
    # Filtro de GERENTES
    if 'GERENTE' in df.columns:
        st.sidebar.subheader("Filtro por Gerente")
        gerentes = sorted(df['GERENTE'].dropna().unique())
        selected_gerentes = st.sidebar.multiselect("Selecione os gerentes", gerentes)
        
        # Aplicar filtro de gerentes
        if selected_gerentes:
            df_filtered = df_filtered[df_filtered['GERENTE'].isin(selected_gerentes)]
    else:
        st.sidebar.warning("A coluna 'GERENTE' não foi encontrada na tabela")
            
    # Filtro de ETAPAS
    if 'ETAPA' in df.columns:
        st.sidebar.subheader("Filtro por ETAPA")
        etapa = sorted(df['ETAPA'].dropna().unique())
        selected_etapa = st.sidebar.multiselect("Selecione a Etapa", etapa)
        
        # Aplicar filtro de etapas
        if selected_etapa:
            df_filtered = df_filtered[df_filtered['ETAPA'].isin(selected_etapa)] 
    else:
        st.sidebar.warning("A coluna 'ETAPA' não foi encontrada na tabela")               
    
    # Agrupar por cedente e calcular as métricas necessárias
    # Incluímos GERENTE e ETAPA no agrupamento
    if 'CAPTADOR' in df.columns:
        df_grouped = df_filtered.groupby(['CAPTADOR', 'CEDENTE', 'GERENTE', 'ETAPA']).agg(
            DATA_MAIS_RECENTE=('DATA', 'max'),
            PRAZO_MEDIO=('PRAZO_MEDIO', 'mean'),
            DESAGIO=('VALOR_DESAGIO', 'sum'),
            VALOR_OPERADO=('VALOR_BRUTO', 'sum')
        ).reset_index()
    else:
        df_grouped = df_filtered.groupby(['CEDENTE', 'GERENTE', 'ETAPA']).agg(
            DATA_MAIS_RECENTE=('DATA', 'max'),
            PRAZO_MEDIO=('PRAZO_MEDIO', 'mean'),
            DESAGIO=('VALOR_DESAGIO', 'sum'),
            VALOR_OPERADO=('VALOR_BRUTO', 'sum')
        ).reset_index()
    
    # Renomear colunas
    df_grouped = df_grouped.rename(columns={
        'DATA_MAIS_RECENTE': 'DATA',
        'PRAZO_MEDIO': 'PRAZO MEDIO',
        'DESAGIO': 'DESAGIO',
        'VALOR_OPERADO': 'VALOR OPERADO'
    })
    
    # Formatar a coluna DATA para formato curto (dd/mm/aaaa)
    df_grouped['DATA'] = df_grouped['DATA'].apply(format_short_date)
    
    # Calcular os totais de DESAGIO e VALOR OPERADO
    total_desagio = df_filtered['VALOR_DESAGIO'].sum()
    total_valor_operado = df_filtered['VALOR_BRUTO'].sum()
    
    # Calcular o PRAZO MEDIO geral (média ponderada pelo valor operado)
    prazo_medio_geral = (df_filtered['PRAZO_MEDIO'] * df_filtered['VALOR_BRUTO']).sum() / df_filtered['VALOR_BRUTO'].sum() if df_filtered['VALOR_BRUTO'].sum() > 0 else 0
    
    # Formatar as colunas numéricas para melhor visualização
    df_grouped['PRAZO MEDIO'] = df_grouped['PRAZO MEDIO'].apply(lambda x: format_decimal(x, 2))
    df_grouped['DESAGIO'] = df_grouped['DESAGIO'].apply(format_currency)
    df_grouped['VALOR OPERADO'] = df_grouped['VALOR OPERADO'].apply(format_currency)
    
    # Criar uma linha de totais para adicionar ao final do dataframe
    if 'CAPTADOR' in df_grouped.columns:
        totals_row = pd.DataFrame({
            'CAPTADOR': ['TOTAL'],
            'CEDENTE': [''],
            'GERENTE': [''],
            'ETAPA': [''],
            'DATA': [''],
            'PRAZO MEDIO': [format_decimal(prazo_medio_geral, 2)],  # Prazo médio geral
            'DESAGIO': [format_currency(total_desagio)],
            'VALOR OPERADO': [format_currency(total_valor_operado)]
        })
    else:
        totals_row = pd.DataFrame({
            'CEDENTE': ['TOTAL'],
            'GERENTE': [''],
            'ETAPA': [''],
            'DATA': [''],
            'PRAZO MEDIO': [format_decimal(prazo_medio_geral, 2)],  # Prazo médio geral
            'DESAGIO': [format_currency(total_desagio)],
            'VALOR OPERADO': [format_currency(total_valor_operado)]
        })
    
    # Adicionar linha de totais ao DataFrame
    df_grouped_with_totals = pd.concat([df_grouped, totals_row], ignore_index=True)
    
    # Exibir informações do DataFrame agrupado
    st.write(f"Total de cedentes: {len(df_grouped)} (de {df_filtered['CEDENTE'].nunique()} cedentes filtrados)")
    
    # Exibir o DataFrame agrupado com totais
    st.dataframe(df_grouped_with_totals)
    
    # Botão para exportar para PDF
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Exportar para PDF"):
            pdf_buffer = generate_pdf(df_grouped_with_totals, filtered=(len(df_filtered) != len(df)))
            
            # Preparar download
            pdf_data = pdf_buffer.getvalue()
            b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
            
            # Criar link de download
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="relatorio_comissao_cedentes_{current_date}.pdf">Clique aqui para baixar o PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            st.success("PDF gerado com sucesso!")
    
    # Adicionar gráfico de barras para visualizar valores por cedente
    st.subheader("Valor Operado por Cedente")
    
    # Criar uma cópia para o gráfico com valores numéricos
    df_chart = df_filtered.groupby('CEDENTE')['VALOR_BRUTO'].sum().reset_index()
    df_chart = df_chart.rename(columns={'VALOR_BRUTO': 'VALOR OPERADO'})
    
    # Ordenar por valor operado
    df_chart = df_chart.sort_values('VALOR OPERADO', ascending=False).head(10)
    
    # Criar gráfico
    st.bar_chart(df_chart.set_index('CEDENTE')['VALOR OPERADO'])
    
    # Adicionar gráfico de barras para visualizar valores por gerente
    if 'GERENTE' in df_filtered.columns:
        st.subheader("Valor Operado por Gerente")
        
        # Criar uma cópia para o gráfico com valores numéricos
        df_gerente_chart = df_filtered.groupby('GERENTE')['VALOR_BRUTO'].sum().reset_index()
        df_gerente_chart = df_gerente_chart.rename(columns={'VALOR_BRUTO': 'VALOR OPERADO'})
        
        # Ordenar por valor operado
        df_gerente_chart = df_gerente_chart.sort_values('VALOR OPERADO', ascending=False).head(10)
        
        # Criar gráfico
        st.bar_chart(df_gerente_chart.set_index('GERENTE')['VALOR OPERADO'])
    
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