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
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def format_currency(value):
    """Formata o valor monetário para o formato de moeda brasileira."""
    if pd.isna(value):
        return "R$ 0,00"
    return locale.currency(value, grouping=True)

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
    
    # Aplicando formatação para os valores monetários e data
    for i, row in enumerate(pdf_data[1:]):  # pular o cabeçalho
        for j, value in enumerate(row):
            if isinstance(value, (int, float)):
                # Formatar valores monetários
                pdf_data[i + 1][j] = format_currency(value)
            elif isinstance(value, datetime):
                # Formatar data como shortdate
                pdf_data[i + 1][j] = value.strftime('%d/%m/%Y')
    
    # Adicionar linha para totais (se o DataFrame tiver linhas)
    if len(df) > 0:
        totals_row = ["TOTAL"] + [""] * (len(df.columns) - 4) + [
            format_currency(df["DESAGIO"].iloc[-1]) if df.index[-1] == "TOTAL" else "",
            format_currency(df["VALOR OPERADO"].iloc[-1]) if df.index[-1] == "TOTAL" else ""
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
