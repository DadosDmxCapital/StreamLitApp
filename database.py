import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def connect_to_database():
    """
    Estabelece a conexão com o banco de dados PostgreSQL.
    """
    # Carregar variáveis do .env
    load_dotenv(".env")

    # Obter as credenciais do ambiente
    server = os.getenv("POSTGRES_SERVER")
    database = os.getenv("POSTGRES_DB")
    username = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    port = os.getenv("POSTGRES_PORT", "5432")  # padrão PostgreSQL

    # Verificar se tudo foi carregado corretamente
    if not all([server, database, username, password]):
        raise ValueError("Uma ou mais variáveis de ambiente estão ausentes. Verifique o arquivo .env!")

    # Criar a URL de conexão para SQLAlchemy
    conn_url = f"postgresql+psycopg2://{username}:{password}@{server}:{port}/{database}"

    # Criar engine de conexão
    engine = create_engine(conn_url)
    return engine

def fetch_data(engine):
    """
    Executa a consulta SQL e retorna os dados em um DataFrame.
    """
    query = """
    SELECT 
        f.cedente,
        d.gerente,
        f.etapa, 
        f.data, 
        f.prazo_medio, 
        f.valor_desagio, 
        f.valor_bruto 
    FROM fato_operacoes f
    LEFT JOIN dimcedentesconsolidado d 
        ON f.cpf_cnpj_cedente = d.cpf_cnpj
    """

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    # Conversão de data
    if 'data' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['data']):
        df['data'] = pd.to_datetime(df['data'], errors='coerce')

    return df

if __name__ == "__main__":
    engine = connect_to_database()
    df = fetch_data(engine)
    print(df.head())
