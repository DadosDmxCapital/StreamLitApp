# Codigo para subir dados para o App StreamLit
# Relatório de Comissionamento

Este projeto é uma aplicação web desenvolvida com Streamlit para gerar relatórios de comissionamento, oferecendo visualização interativa e exportação de dados em PDF.

## Tecnologias Utilizadas
- Python
- Streamlit
- Pandas
- PostgreSQL (ou outro banco de dados suportado)
- ReportLab (para geração de PDF)

## Estrutura do Projeto
```
/
|-- authentication.py         # Gerenciamento de autenticação
|-- database.py               # Conexão e consulta ao banco de dados
|-- data_processing.py        # Processamento e formatação dos dados
|-- pdf_generator.py          # Geração de relatórios em PDF
|-- visualizations.py         # Criação de gráficos e visualizações
|-- app.py                    # Arquivo principal da aplicação
|-- requirements.txt          # Dependências do projeto
|-- README.md                 # Documentação do projeto
```

## Como Executar o Projeto

### 1. Instalar dependências
Certifique-se de ter o Python instalado e execute:
```sh
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados
Defina as configurações de conexão ao banco de dados no arquivo `database.py`.

### 3. Executar a aplicação
```sh
streamlit run app.py
```

## Funcionalidades
- **Autenticação**: Verificação de usuário e permissões.
- **Consulta ao Banco de Dados**: Busca e filtra dados automaticamente.
- **Processamento de Dados**: Aplica formatação e renomeia campos relevantes.
- **Visualização Interativa**: Exibição de tabelas e gráficos.
- **Geração de PDF**: Permite download do relatório.

## Possíveis Erros e Soluções
- **Erro de Autenticação (18456)**:
  - Verifique credenciais.
  - Confirme permissões de acesso ao banco.
  - Ajuste o tipo de autenticação.

## Contribuição
Sugestões e melhorias são bem-vindas! Fique à vontade para abrir uma issue ou enviar um pull request.

## Licença
Este projeto está sob a licença MIT.