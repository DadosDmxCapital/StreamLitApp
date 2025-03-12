import pandas as pd
import streamlit as st
import locale

# Configurar locale para formatação de números com vírgula para decimais
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass  # Se ambos falharem, usaremos formatação manual

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

# Função para renomear gerentes
def rename_gerente(gerente):
    if pd.isna(gerente):
        return gerente
    
    mapping = {
        "*COMERCIAL - RFA - ADITAR ***": "RFA",
        "*COMERCIAL - ALX": "ALX",
        "*COMERCIAL - ANDRE TAVARES ***": "ANDRE TAVARES",
        "*COMERCIAL - LEANDRO APARECIDO VIEIRA DE SOUSA": "LEANDRO AP",
        "*COMERCIAL - LUIS FERNANDO DE JESUS LOMBELLO": "LUIS FERNANDO",
        "*COMERCIAL - MANUEL SANJI GOMES KOMIYAMA": "MANUEL",
        "*COMERCIAL - ROLAN GABRIEL SYLVESTRE MARINO": "ROLAN",
        "*COMERCIAL RODRIGO WEISSINGER CARVALHO***": "RODRIGO",
        "Setor de Novos Negócios - DMX Capital": "DMX Capital"
    }
    
    return mapping.get(gerente, gerente)

def process_data(df):
    """
    Aplica filtros do Streamlit e retorna os dados filtrados.
    
    Args:
        df (pandas.DataFrame): DataFrame original
        
    Returns:
        pandas.DataFrame: DataFrame com filtros aplicados
    """
    # Aplicar rename ao gerente se necessário
    if 'GERENTE' in df.columns:
        df['GERENTE'] = df['GERENTE'].apply(rename_gerente)
    
    # Inicializar df_filtered com o dataframe original
    df_filtered = df
    
    # Filtro de período
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
        st.sidebar.warning("A coluna 'DATA' não foi encontrada na tabela")
    
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
        
    return df_filtered

def format_dataframes(df_filtered):
    """
    Processa os dados filtrados, agrupa por cedente/gerente e formata os valores
    
    Args:
        df_filtered (pandas.DataFrame): DataFrame com filtros aplicados
    
    Returns:
        tuple: (df_grouped, df_grouped_with_totals, summary_stats)
    """
    # Agrupar por cedente e calcular as métricas necessárias
    if 'CAPTADOR' in df_filtered.columns:
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
    
    # Resumo estatístico para uso em outras funções
    summary_stats = {
        'total_desagio': total_desagio,
        'total_valor_operado': total_valor_operado,
        'prazo_medio_geral': prazo_medio_geral
    }
    
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
    
    return df_grouped, df_grouped_with_totals, summary_stats