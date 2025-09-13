"""
Gráfico de linha do tempo interativo
"""
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd

def timeline_plot(dataframe):
    """Cria um gráfico de linha do tempo das personalidades"""
    
    # Prepara os dados
    df_timeline = dataframe.copy()
    
    # Converte datas para formato numérico para plotagem
    df_timeline['Ano_Nascimento'] = df_timeline['Data de Nascimento'].apply(extract_year)
    df_timeline['Ano_Falecimento'] = df_timeline['Data de Falecimento'].apply(extract_year)
    
    # Remove entradas sem data válida
    df_timeline = df_timeline.dropna(subset=['Ano_Nascimento'])
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona barras horizontais para cada pessoa (vida)
    for idx, row in df_timeline.iterrows():
        ano_nasc = row['Ano_Nascimento']
        ano_morte = row['Ano_Falecimento'] if pd.notna(row['Ano_Falecimento']) else datetime.now().year
        
        # Barra representando a vida da pessoa
        fig.add_trace(go.Scatter(
            x=[ano_nasc, ano_morte],
            y=[idx, idx],
            mode='lines+markers',
            name=row['Nome Completo'],
            line=dict(width=8),
            marker=dict(size=10),
            hovertemplate=(
                f"<b>{row['Nome Completo']}</b><br>"
                f"Nascimento: {row['Data de Nascimento']}<br>"
                f"Falecimento: {row['Data de Falecimento']}<br>"
                f"Nacionalidade: {row['Origem/Nacionalidade']}<br>"
                f"Século: {row['Século']}<br>"
                "<extra></extra>"
            )
        ))
    
    # Configurações do layout
    fig.update_layout(
        title={
            'text': '<b>Linha do Tempo das Personalidades</b>',
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        xaxis=dict(
            title='Ano',
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Personalidades',
            tickfont=dict(size=10),
            tickmode='array',
            tickvals=list(range(len(df_timeline))),
            ticktext=[name[:30] + '...' if len(name) > 30 else name 
                     for name in df_timeline['Nome Completo']],
            showgrid=True,
            gridcolor='lightgray'
        ),
        height=max(600, len(df_timeline) * 40),
        width=1400,
        showlegend=False,
        hovermode='closest'
    )
    
    return fig

def extract_year(date_str):
    """Extrai o ano de uma string de data"""
    if not date_str or date_str == "Não Informado":
        return None
    
    import re
    
    # Para datas ISO
    if re.match(r'^\d{4}-\d{2}-\d{2}$', str(date_str)):
        return int(str(date_str)[:4])
    
    # Para anos simples
    if re.match(r'^\d{4}$', str(date_str)):
        return int(str(date_str))
    
    # Para datas a.C.
    if 'a.C.' in str(date_str):
        year_match = re.search(r'(\d+)', str(date_str))
        if year_match:
            return -int(year_match.group(1))
    
    # Busca por ano de 4 dígitos
    year_match = re.search(r'\b(\d{4})\b', str(date_str))
    if year_match:
        return int(year_match.group(1))
    
    return None