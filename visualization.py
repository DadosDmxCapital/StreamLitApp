import streamlit as st
import pandas as pd

def create_visualizations(df_filtered):
    """
    Cria visualizações gráficas baseadas nos dados filtrados
    
    Args:
        df_filtered (pandas.DataFrame): DataFrame com filtros aplicados
    """
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