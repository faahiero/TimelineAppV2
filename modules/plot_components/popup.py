import dash_leaflet as dl
from dash import dcc, html, Input, Output

def popup_html(row):
    return dl.Popup([
        html.Div([
            html.H2(row["Nome Completo"], style=dict(textAlign='center', fontSize=24)),
        ]),

        html.Div([
            html.P("Dados Biográficos", style={"fontWeight": "bold", "fontSize": "16px"}),
        ]),

        #check if row["Imagem"] is "Sem Imagem". If it is, create a div with the text "Sem Imagem"
        html.Div([
            html.Img(src=row["Imagem"], style=dict(width="100%", height="100%")),
        ]) if row["Imagem"] != "Sem Imagem" else html.Div([
            html.P("Sem Imagem", style=dict(textAlign='center', fontSize=18, fontWeight="bold", color="red"))
        ]),

        html.Div([
            html.Ul([
                html.Li("Data de Nascimento: " + row["Data de Nascimento"]),
                html.Li("Local de Nascimento: " + row["Local de Nascimento"]),
                html.Li("Data de Falecimento: " + row["Data de Falecimento"]),
                html.Li("Local de Falecimento: " + row["Local de Falecimento"]),
                html.Li("Século: " + str(row["Século"]))
            ], style=dict(paddingLeft="30px", fontWeight="bold"))
        ]),

        # link to the wikipedia page of the person
        html.Div([
            html.A("Wikipedia", href=row["Url"], target="_blank")
        ], style=dict(textAlign='center', fontSize=18))
    ])