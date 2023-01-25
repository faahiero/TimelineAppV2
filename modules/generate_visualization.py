import os
import shutil
import time
import webbrowser

import dash
from dash import Input, Output, dcc, html
import plotly.graph_objects as go
import pandas as pd
import folium


# Função que gera a visualização com as informações salvas no arquivo csv.
def generate_visualization():
    timestamp_fname = time.strftime("%Y%m%d-%H%M%S") + "_"
    df = pd.read_csv("person_info.csv")

    df["Século"] = ""

    for i in range(len(df)):
        year = int(df.loc[i, "Data de Nascimento"].split()[-1])
        if year % 100 == 0:
            year -= 1
        century = (year // 100) + 1
        df.loc[i, "Século"] = century

    folium_map = folium.Map()

    for idx, linha in df.iterrows():
        html = f"""
        <div id="dados" style='border:solid; border-radius:10px; width: 700px;height: 300px'>
            <div style="padding: 10px;margin-top:7px;float: right">
                <img src="{linha['Imagem']}"
                width="189" height="266"/>
            </div>
            <h2 style="text-align: center">{linha['Nome Completo']}</h2>
                <p style="font-weight: bold;margin-left: 20px">Dados Biográficos</p>
                    <ul style="margin-left: 20px">
                        <li>Origem/Nacionalidade: {linha['Origem/Nacionalidade']}</li>    
                        <li>Data de Nascimento: {linha['Data de Nascimento']}</li>
                        <li>Local de Nascimento: {linha['Local de Nascimento']}</li>
                        <li>Data de Falecimento: {linha['Data de Falecimento']}</li>
                        <li>Local de Falecimento: {linha['Local de Falecimento']}</li>
                    </ul>
                </p>
            <p style="margin-left: 20px">Link para artigo completo na  <a href="{linha['Url']}" 
            target="_blank">Wikipedia</a></p>
        </div>
        """
        iframe = folium.IFrame(html=html, width=730, height=330)
        popup = folium.Popup(iframe, max_width=2650)
        folium.Marker(
            [linha['Latitude'], linha['Longitude']],
            popup=popup,
            tooltip=linha['Nome Completo']
        ).add_to(folium_map)

        if not os.path.exists("data"):
            os.makedirs("data")
        folium_map.save("data/" + timestamp_fname + 'map.html')

    shutil.move('person_info.csv', 'data/' +
                timestamp_fname + 'person_info.csv')

    app = dash.Dash(__name__)

    data = [go.Scattermapbox(
        lat=df['Latitude'],
        lon=df['Longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=17,
            color=df['Século'],
            colorscale='Viridis',
            showscale=True
        ),
    )]

    layout = go.Layout(
        autosize=True,
        hovermode='closest',
        mapbox=go.layout.Mapbox(
            accesstoken='pk.eyJ1IjoiZmFhaGllcm8iLCJhIjoiY2txc3lnazRiMXNvNTJvcjFvMnp0aGd4NyJ9.fPzGgM_mC-xJnx56RQ_y8Q',
            zoom=2
        ),
        height=800,
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
    )

    app.layout = dash.html.Div([

        # iframe
        dash.html.Iframe(
            id='map',
            srcDoc=open('data/' + timestamp_fname + 'map.html', 'r').read(),
            width='100%',
            height='100%'
        ),

        dcc.Graph(id='dash-map', figure={'data': data, 'layout': layout}),

        dash.html.Div(dcc.RangeSlider(
            id='seculo-slider',
            min=df['Século'].min(),
            max=df['Século'].max(),
            value=[df['Século'].min(), df['Século'].max()],
            marks={str(seculo): str(seculo) for seculo in df['Século'].unique()},
            step=None
        ), style=dict(
            width='100%',
            verticalAlign="middle",
            padding="10px 0px 0px 0px",
            display='inline-block',
            textAlign='center',
            fontSize=20,
            fontFamily='Fira Sans',
            fontWeight='bold',
            color='black',
            backgroundColor='white',
            border='1px solid black',
            borderRadius='5px',
            margin='10px 0px 0px 0px',
        )),
    ])

    @app.callback(
        Output('dash-map', 'figure'),
        [Input('seculo-slider', 'value')])
    def update_figure(selected_seculo):
        filtered_df = df[df['Século'].between(selected_seculo[0], selected_seculo[1])]

        traces = []
        traces.append(go.Scattermapbox(
            lat=filtered_df['Latitude'],
            lon=filtered_df['Longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=17,
                symbol='circle',
            ),

            hoverlabel=dict(
                bgcolor="blue",
                font_size=16,
                font_family="Fira Sans"
            ),
            text="<b>Nome: </b>" + filtered_df['Nome Completo'] + "<br>" +
                 "<b>Data de Nascimento: </b>" + filtered_df['Data de Nascimento'] + "<br>" +
                 "<b>Local de Nascimento: </b>" + filtered_df['Local de Nascimento'] + "<br>" +
                 "<b>Local de Falecimento: </b>" + filtered_df['Local de Falecimento'] + "<br>" +
                 "<b>Latitude: </b>" + filtered_df['Latitude'].astype(str) + "<br>" +
                 "<b>Longitude: </b>" + filtered_df['Longitude'].astype(str) + "<br>" +
                 "<b>Século: </b>" + filtered_df['Século'].astype(str),
        ))
        return {
            'data': traces,
            'layout': layout
        }

    app.run_server()

    # webbrowser.open('file://' + os.path.realpath('data/' +
    #                 timestamp_fname + 'map.html'))
