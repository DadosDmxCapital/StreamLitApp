import streamlit as st

def create_bar_chart(df, group_column, value_column='valor_bruto', title=None, limit=10):
    """
    Cria um gráfico de barras para visualizar valores agrupados por uma coluna.

    Args:
        df (pandas.DataFrame): DataFrame com os dados
        group_column (str): Nome da coluna para agrupar
        value_column (str): Nome da coluna com os valores a serem somados
        title (str, optional): Título do gráfico. Se None, usa o nome da coluna.
        limit (int, optional): Limite de itens a mostrar. Padrão é 10.
    """
    if group_column not in df.columns:
        return

    # Definir título
    chart_title = title if title else f"Valor Operado por {group_column.title()}"
    st.subheader(chart_title)

    # Criar uma cópia para o gráfico com valores numéricos
    df_chart = df.groupby(group_column)[value_column].sum().reset_index()
    df_chart = df_chart.rename(columns={value_column: 'VALOR OPERADO'})

    # Ordenar por valor operado e limitar
    df_chart = df_chart.sort_values('VALOR OPERADO', ascending=False).head(limit)

    # Criar gráfico
    st.bar_chart(df_chart.set_index(group_column)['VALOR OPERADO'])

def create_visualizations(df_filtered):
    """
    Cria visualizações gráficas baseadas nos dados filtrados

    Args:
        df_filtered (pandas.DataFrame): DataFrame com filtros aplicados
    """
    # Criar gráfico para cedentes
    create_bar_chart(df_filtered, 'cedente', title="Valor Operado por Cedente")

    # Criar gráfico para gerentes
    create_bar_chart(df_filtered, 'gerente', title="Valor Operado por Gerente")

    # Podemos adicionar facilmente mais visualizações
    if 'etapa' in df_filtered.columns:
        create_bar_chart(df_filtered, 'etapa', title="Valor Operado por Etapa")