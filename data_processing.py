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

# Formatação de valores
def format_currency(value):
    return f"R$ {value:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")

def format_decimal(value, digits=2):
    return f"{value:.{digits}f}".replace(".", ",")

def format_short_date(date):
    if pd.isna(date):
        return ""
    return date.strftime('%d/%m/%Y')

# Renomear gerentes
def rename_gerente(gerente):
    if pd.isna(gerente):
        return gerente

    mapping = {
        "*COMERCIAL - RFA - ADITAR ***": "RFA",
        "*COMERCIAL - ALX": "ALX",
        "*COMERCIAL - ANDRE TAVARES ***": "ANDRE TAVARES",
        "LEANDRO APARECIDO": "LEANDRO AP",
        "*COMERCIAL - LUIS FERNANDO DE JESUS LOMBELLO": "LUIS FERNANDO",
        "*COMERCIAL - MANUEL SANJI GOMES KOMIYAMA": "MANUEL",
        "*COMERCIAL - ROLAN GABRIEL SYLVESTRE MARINO": "ROLAN",
        "*COMERCIAL RODRIGO WEISSINGER CARVALHO***": "RODRIGO",
        "DMX FUNDO DE INVESTIMENTO EM DIREITOS CREDITORIOS": "DMX Capital"
    }

    gerente_normalizado = gerente.strip().upper()
    return mapping.get(gerente_normalizado, gerente)

# Funções auxiliares para filtros
def apply_date_filter(df, df_filtered):
    """Aplica filtro de data ao DataFrame."""
    if 'data' not in df.columns:
        st.sidebar.warning("A coluna 'DATA' não foi encontrada na tabela")
        return df_filtered

    min_date = df['data'].min().date()
    max_date = df['data'].max().date()

    st.sidebar.subheader("Filtro por Período")
    date_range = st.sidebar.date_input(
        "Selecione o período",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df['data'].dt.date >= start_date) & (df['data'].dt.date <= end_date)
        return df.loc[mask]

    return df_filtered

def apply_column_filter(df_filtered, column_name, title):
    """Aplica filtro genérico por coluna ao DataFrame."""
    if column_name not in df_filtered.columns:
        st.sidebar.warning(f"A coluna '{title}' não foi encontrada na tabela")
        return df_filtered

    st.sidebar.subheader(f"Filtro por {title}")
    values = sorted(df_filtered[column_name].dropna().unique())
    selected_values = st.sidebar.multiselect(f"Selecione os {title.lower()}s", values)

    if selected_values:
        return df_filtered[df_filtered[column_name].isin(selected_values)]

    return df_filtered

# Filtros via Streamlit
def process_data(df):
    """Processa e filtra os dados com base nas seleções do usuário."""
    # Normalizar nomes de gerentes
    if 'gerente' in df.columns:
        df['gerente'] = df['gerente'].apply(rename_gerente)

    # Aplicar filtros em sequência
    df_filtered = df
    df_filtered = apply_date_filter(df, df_filtered)
    df_filtered = apply_column_filter(df_filtered, 'cedente', 'Cedente')
    df_filtered = apply_column_filter(df_filtered, 'gerente', 'Gerente')
    df_filtered = apply_column_filter(df_filtered, 'etapa', 'Etapa')

    return df_filtered

# Funções auxiliares para agrupamento e formatação
def get_grouping_columns(df):
    """Define as colunas para agrupamento."""
    group_cols = ['cedente', 'gerente', 'etapa']
    if 'captador' in df.columns:
        group_cols = ['captador'] + group_cols
    return group_cols

def get_aggregation_dict(df):
    """Define o dicionário de agregação para o groupby."""
    agg_dict = {
        'data': ('data', 'max'),
        'valor_desagio': ('valor_desagio', 'sum'),
        'valor_bruto': ('valor_bruto', 'sum')
    }

    if 'prazo_medio' in df.columns:
        agg_dict['prazo_medio'] = ('prazo_medio', 'mean')

    return agg_dict

def format_grouped_data(df_grouped, has_prazo_medio):
    """Formata os dados agrupados."""
    # Renomear colunas
    df_grouped = df_grouped.rename(columns={
        'data': 'data',
        'prazo_medio': 'PRAZO MEDIO',
        'valor_desagio': 'DESAGIO',
        'valor_bruto': 'VALOR OPERADO'
    })

    # Aplicar formatação
    df_grouped['data'] = df_grouped['data'].apply(format_short_date)
    if has_prazo_medio:
        df_grouped['PRAZO MEDIO'] = df_grouped['PRAZO MEDIO'].apply(lambda x: format_decimal(x, 2))
    df_grouped['DESAGIO'] = df_grouped['DESAGIO'].apply(format_currency)
    df_grouped['VALOR OPERADO'] = df_grouped['VALOR OPERADO'].apply(format_currency)

    return df_grouped

def calculate_totals(df_filtered, has_prazo_medio):
    """Calcula os totais para o relatório."""
    total_desagio = df_filtered['valor_desagio'].sum()
    total_valor_operado = df_filtered['valor_bruto'].sum()

    prazo_medio_geral = 0
    if has_prazo_medio and total_valor_operado > 0:
        prazo_medio_geral = (
            (df_filtered['prazo_medio'] * df_filtered['valor_bruto']).sum() / total_valor_operado
        )

    return total_desagio, total_valor_operado, prazo_medio_geral

def create_totals_row(df_grouped, total_desagio, total_valor_operado, prazo_medio_geral, has_captador, has_prazo_medio):
    """Cria a linha de totais para o DataFrame."""
    totals_data = {
        'cedente': ['TOTAL'],
        'gerente': [''],
        'etapa': [''],
        'data': [''],
        'DESAGIO': [format_currency(total_desagio)],
        'VALOR OPERADO': [format_currency(total_valor_operado)]
    }

    if has_prazo_medio:
        totals_data['PRAZO MEDIO'] = [format_decimal(prazo_medio_geral, 2)]

    if has_captador:
        totals_data['captador'] = ['TOTAL']
        for col in df_grouped.columns:
            if col not in totals_data:
                totals_data[col] = ['']

    return pd.DataFrame(totals_data)

# Agrupamento, cálculo e formatação
def format_dataframes(df_filtered):
    """
    Agrupa, calcula e formata os dados para exibição.

    Args:
        df_filtered (pandas.DataFrame): DataFrame filtrado

    Returns:
        tuple: (df_grouped, df_grouped_with_totals, summary_stats)
    """
    # Verificar colunas disponíveis
    has_captador = 'captador' in df_filtered.columns
    has_prazo_medio = 'prazo_medio' in df_filtered.columns

    # Definir colunas para agrupamento
    group_cols = get_grouping_columns(df_filtered)

    # Definir dicionário de agregação
    agg_dict = get_aggregation_dict(df_filtered)

    # Agrupar dados
    df_grouped = df_filtered.groupby(group_cols).agg(**agg_dict).reset_index()

    # Formatar dados agrupados
    df_grouped = format_grouped_data(df_grouped, has_prazo_medio)

    # Calcular totais
    total_desagio, total_valor_operado, prazo_medio_geral = calculate_totals(
        df_filtered, has_prazo_medio
    )

    # Criar linha de totais
    totals_row = create_totals_row(
        df_grouped, total_desagio, total_valor_operado, prazo_medio_geral,
        has_captador, has_prazo_medio
    )

    # Concatenar com o DataFrame agrupado
    df_grouped_with_totals = pd.concat([df_grouped, totals_row], ignore_index=True)

    # Criar estatísticas resumidas
    summary_stats = {
        'total_desagio': total_desagio,
        'total_valor_operado': total_valor_operado,
        'prazo_medio_geral': prazo_medio_geral if has_prazo_medio else None
    }

    return df_grouped, df_grouped_with_totals, summary_stats
