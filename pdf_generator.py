import pandas as pd
import locale
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# Configura o locale para o Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass  # Se ambos falharem, usaremos formatação manual

def format_currency(value):
    """Formata o valor monetário para o formato de moeda brasileira."""
    if pd.isna(value):
        return "R$ 0,00"
    return locale.currency(value, grouping=True)

def create_document(buffer):
    """Cria o documento PDF com configurações padrão."""
    return SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

def add_header(elements, filtered=False):
    """Adiciona o cabeçalho do relatório."""
    styles = getSampleStyleSheet()

    # Título
    title = "Relatório de Comissionamento por Cedente"
    if filtered:
        title += " (Filtrado)"
    elements.append(Paragraph(title, styles['Heading1']))
    elements.append(Spacer(1, 12))

    # Data do relatório
    date_text = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    elements.append(Paragraph(date_text, styles['Normal']))
    elements.append(Spacer(1, 12))

    return elements

def format_table_data(df):
    """Formata os dados da tabela para o PDF."""
    # Limitar a 20 primeiras linhas para o PDF não ficar muito grande
    pdf_data = [df.columns.tolist()] + df.head(20).values.tolist()

    # Aplicando formatação para os valores monetários e data
    for i, row in enumerate(pdf_data[1:]):  # pular o cabeçalho
        for j, value in enumerate(row):
            if isinstance(value, (int, float)):
                pdf_data[i + 1][j] = format_currency(value)
            elif isinstance(value, datetime):
                pdf_data[i + 1][j] = value.strftime('%d/%m/%Y')

    # Adicionar linha para totais (se o DataFrame tiver linhas)
    if len(df) > 0:
        totals_row = ["TOTAL"] + [""] * (len(df.columns) - 4) + [
            format_currency(df["DESAGIO"].iloc[-1]) if df.index[-1] == "TOTAL" else "",
            format_currency(df["VALOR OPERADO"].iloc[-1]) if df.index[-1] == "TOTAL" else ""
        ]
        pdf_data.append(totals_row)

    return pdf_data

def get_column_widths(df):
    """Define as larguras das colunas para a tabela."""
    col_widths = [None] * len(df.columns)
    col_indices = {col.lower(): i for i, col in enumerate(df.columns)}

    # Mapeamento de colunas para larguras
    width_mapping = {
        'cedente': 3.0*inch,
        'gerente': 1.2*inch,
        'etapa': 1.6*inch,
        'data': 1.0*inch,
        'prazo medio': 1.0*inch,
        'desagio': 1.0*inch,
        'valor operado': 1.0*inch
    }

    # Aplicar larguras específicas
    for col_name, width in width_mapping.items():
        if col_name in col_indices:
            col_widths[col_indices[col_name]] = width

    return col_widths, col_indices

def create_table_style(col_indices):
    """Cria o estilo da tabela."""
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
        ('ALIGN', (0, 1), (3, -1), 'LEFT'),  # Alinhar texto à esquerda
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Alinhar números à direita
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
    if 'cedente' in col_indices:
        cedente_idx = col_indices['cedente']
        style.add('FONTSIZE', (cedente_idx, 1), (cedente_idx, -2), 7)

    return style

def add_footer(elements, df):
    """Adiciona o rodapé ao relatório."""
    styles = getSampleStyleSheet()
    elements.append(Spacer(1, 20))

    footer_text = "Nota: Este relatório contém informações confidenciais."
    if len(df) > 20:
        footer_text += f" Apenas as primeiras 20 de {len(df)} linhas são mostradas no PDF."

    elements.append(Paragraph(footer_text, styles['Italic']))
    return elements

def generate_pdf_report(df, filtered=False):
    """
    Gera um relatório PDF a partir de um DataFrame

    Args:
        df (pandas.DataFrame): DataFrame a ser incluído no PDF
        filtered (bool, optional): Indica se os dados estão filtrados. Defaults to False.

    Returns:
        BytesIO: Buffer contendo o documento PDF
    """
    buffer = BytesIO()
    doc = create_document(buffer)
    elements = []

    # Adicionar cabeçalho
    elements = add_header(elements, filtered)

    # Formatar dados da tabela
    pdf_data = format_table_data(df)

    # Definir larguras das colunas
    col_widths, col_indices = get_column_widths(df)

    # Criar tabela
    table = Table(pdf_data, colWidths=col_widths, repeatRows=1)

    # Aplicar estilo à tabela
    style = create_table_style(col_indices)
    table.setStyle(style)
    elements.append(table)

    # Adicionar rodapé
    elements = add_footer(elements, df)

    # Construir PDF
    doc.build(elements)

    return buffer
