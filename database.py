import os
import pyodbc
import pandas as pd
from dotenv import load_dotenv

def connect_to_database():
    """
    Estabelece a conexão com o banco de dados SQL Server.
    
    Returns:
        pyodbc.Connection: Objeto de conexão com o banco de dados
    
    Raises:
        ValueError: Se as variáveis de ambiente estiverem faltando
        Exception: Para outros erros de conexão
    """
    # Carregar as variáveis do .env
    load_dotenv(".env")

    # Pegar as credenciais
    server = os.getenv("FABRIC_SERVER")
    database = os.getenv("FABRIC_DATABASE")
    username = os.getenv("FABRIC_USERNAME")
    password = os.getenv("FABRIC_PASSWORD")

    # Verificar se as variáveis essenciais foram carregadas
    if not all([server, database, username, password]):
        raise ValueError("Uma ou mais variáveis de ambiente estão ausentes. Verifique o seu arquivo .env!")

    # Construir a string de conexão para pyodbc
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Authentication=ActiveDirectoryPassword"
    
    # Conectar ao banco de dados
    conn = pyodbc.connect(conn_str)
    return conn

def fetch_data(conn):
    """
    Executa a consulta SQL e retorna os dados em um DataFrame
    
    Args:
        conn (pyodbc.Connection): Conexão com o banco de dados
        
    Returns:
        pandas.DataFrame: DataFrame com os dados da consulta
    """
    # Query para recuperar os dados incluindo a coluna GERENTE
    query = """
    SELECT 
        f.CEDENTE,
        d.GERENTE,
        f.ETAPA, 
        f.DATA, 
        f.PRAZO_MEDIO, 
        f.VALOR_DESAGIO, 
        f.VALOR_BRUTO 
    FROM dbo.f_operacao f
    LEFT JOIN dbo.d_Cedentes d ON f.CPF_CNPJ_CEDENTE = d.CPF_CNPJ
    """
    
    # Ler os dados no Pandas
    df = pd.read_sql(query, conn)
    
    # Fechar conexão
    conn.close()
    
    # Converter a coluna DATA para datetime se não for
    if 'DATA' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['DATA']):
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    
    return df