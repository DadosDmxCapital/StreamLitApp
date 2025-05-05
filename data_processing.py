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

# Filtros via Streamlit
def process_data(df):
    if 'gerente' in df.columns:
        df['gerente'] = df['gerente'].apply(rename_gerente)

    df_filtered = df

    if 'data' in df.columns:
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
            df_filtered = df.loc[mask]
    else:
        st.sidebar.warning("A coluna 'DATA' não foi encontrada na tabela")

    if 'cedente' in df.columns:
        st.sidebar.subheader("Filtro por Cedente")
        cedentes = sorted(df['cedente'].dropna().unique())
        selected_cedentes = st.sidebar.multiselect("Selecione os cedentes", cedentes)
        if selected_cedentes:
            df_filtered = df_filtered[df_filtered['cedente'].isin(selected_cedentes)]

    if 'gerente' in df.columns:
        st.sidebar.subheader("Filtro por Gerente")
        gerentes = sorted(df['gerente'].dropna().unique())
        selected_gerentes = st.sidebar.multiselect("Selecione os gerentes", gerentes)
        if selected_gerentes:
            df_filtered = df_filtered[df_filtered['gerente'].isin(selected_gerentes)]
    else:
        st.sidebar.warning("A coluna 'GERENTE' não foi encontrada na tabela")

    if 'etapa' in df.columns:
        st.sidebar.subheader("Filtro por Etapa")
        etapas = sorted(df['etapa'].dropna().unique())
        selected_etapas = st.sidebar.multiselect("Selecione as etapas", etapas)
        if selected_etapas:
            df_filtered = df_filtered[df_filtered['etapa'].isin(selected_etapas)]
    else:
        st.sidebar.warning("A coluna 'ETAPA' não foi encontrada na tabela")

    return df_filtered

# Agrupamento, cálculo e formatação
def format_dataframes(df_filtered):
    has_captador = 'captador' in df_filtered.columns
    has_prazo_medio = 'prazo_medio' in df_filtered.columns

    group_cols = ['cedente', 'gerente', 'etapa']
    if has_captador:
        group_cols = ['captador'] + group_cols

    agg_dict = {
        'data': ('data', 'max'),
        'valor_desagio': ('valor_desagio', 'sum'),
        'valor_bruto': ('valor_bruto', 'sum')
    }

    if has_prazo_medio:
        agg_dict['prazo_medio'] = ('prazo_medio', 'mean')

    df_grouped = df_filtered.groupby(group_cols).agg(**agg_dict).reset_index()

    df_grouped = df_grouped.rename(columns={
        'data': 'data',
        'prazo_medio': 'PRAZO MEDIO',
        'valor_desagio': 'DESAGIO',
        'valor_bruto': 'VALOR OPERADO'
    })

    df_grouped['data'] = df_grouped['data'].apply(format_short_date)
    if has_prazo_medio:
        df_grouped['PRAZO MEDIO'] = df_grouped['PRAZO MEDIO'].apply(lambda x: format_decimal(x, 2))
    df_grouped['DESAGIO'] = df_grouped['DESAGIO'].apply(format_currency)
    df_grouped['VALOR OPERADO'] = df_grouped['VALOR OPERADO'].apply(format_currency)

    total_desagio = df_filtered['valor_desagio'].sum()
    total_valor_operado = df_filtered['valor_bruto'].sum()

    prazo_medio_geral = 0
    if has_prazo_medio and total_valor_operado > 0:
        prazo_medio_geral = (
            (df_filtered['prazo_medio'] * df_filtered['valor_bruto']).sum() / total_valor_operado
        )

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

    totals_row = pd.DataFrame(totals_data)
    df_grouped_with_totals = pd.concat([df_grouped, totals_row], ignore_index=True)

    summary_stats = {
        'total_desagio': total_desagio,
        'total_valor_operado': total_valor_operado,
        'prazo_medio_geral': prazo_medio_geral if has_prazo_medio else None
    }

    return df_grouped, df_grouped_with_totals, summary_stats
