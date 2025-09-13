"""
Mapa de calor mostrando concentração de personalidades por região e século
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def heatmap_by_century_country(dataframe):
    """Cria um mapa de calor de personalidades por país e século"""
    
    # Prepara os dados
    df_heatmap = dataframe.copy()
    
    # Agrupa por país e século
    heatmap_data = df_heatmap.groupby(['Origem/Nacionalidade', 'Século']).size().reset_index(name='Contagem')
    
    # Cria uma matriz pivot
    pivot_data = heatmap_data.pivot(
        index='Origem/Nacionalidade', 
        columns='Século', 
        values='Contagem'
    ).fillna(0)
    
    # Ordena os séculos corretamente
    centuries = sorted(pivot_data.columns, key=lambda x: parse_century(x))
    pivot_data = pivot_data[centuries]
    
    # Cria o heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Viridis',
        hoverongaps=False,
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Século: %{x}<br>'
            'Personalidades: %{z}<br>'
            '<extra></extra>'
        )
    ))
    
    fig.update_layout(
        title={
            'text': '<b>Mapa de Calor: Personalidades por País e Século</b>',
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        xaxis=dict(
            title='Século',
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            title='País/Nacionalidade',
            tickfont=dict(size=12)
        ),
        width=1200,
        height=600
    )
    
    return fig

def geographic_heatmap(dataframe):
    """Cria um mapa de calor geográfico baseado em coordenadas"""
    
    # Filtra dados com coordenadas válidas
    df_geo = dataframe.copy()
    df_geo = df_geo[
        (df_geo['Latitude'] != 'Não Informado') & 
        (df_geo['Longitude'] != 'Não Informado')
    ]
    
    if df_geo.empty:
        return go.Figure().add_annotation(
            text="Não há dados geográficos suficientes para o mapa de calor",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
    
    # Converte coordenadas para float
    df_geo['Latitude'] = pd.to_numeric(df_geo['Latitude'], errors='coerce')
    df_geo['Longitude'] = pd.to_numeric(df_geo['Longitude'], errors='coerce')
    
    # Remove valores inválidos
    df_geo = df_geo.dropna(subset=['Latitude', 'Longitude'])
    
    # Cria o mapa de densidade
    fig = px.density_mapbox(
        df_geo,
        lat='Latitude',
        lon='Longitude',
        hover_name='Nome Completo',
        hover_data={
            'Século': True,
            'Origem/Nacionalidade': True,
            'Data de Nascimento': True
        },
        mapbox_style='open-street-map',
        zoom=2,
        center=dict(lat=0, lon=0),
        opacity=0.7
    )
    
    fig.update_layout(
        title={
            'text': '<b>Mapa de Densidade Geográfica das Personalidades</b>',
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        width=1400,
        height=700,
        margin=dict(t=60, b=0, l=0, r=0)
    )
    
    return fig

def parse_century(century_str):
    """Converte string de século para número para ordenação"""
    if 'a.C.' in str(century_str):
        return -int(str(century_str).replace(' a.C.', ''))
    else:
        return int(century_str)