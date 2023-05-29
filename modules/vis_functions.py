import logging
import os
import shutil
import time
import webbrowser
from datetime import datetime
from urllib.parse import unquote

import dash
import dash_leaflet as dl
import pandas as pd
import wptools
from alphabet_detector import AlphabetDetector
from browser_history import get_history
from dash import dcc, html, Input, Output

from modules.browse_history_info_gathering import get_browse_history_person_info
from modules.plot_components.dropdown_menu import dropdown_component
from modules.plot_components.popup import popup_html
from modules.plot_components.range_slider import range_slide_component
from modules.plots.bar_plot import stacked_bar_plot
from modules.plots.scatter_plot import scatter_plot_chart
from modules.utils import clear_console, write_to_csv, calcula_seculo
from modules.wiki_functions import sparql_query_wikidata
from modules.webscraping_functions import extract_full_name

alphabet_detector = AlphabetDetector()

FILE_NAME = ""


# Função que gera a visualização com as informações salvas no arquivo csv.
def generate_visualization(browser_history=False):
    timestamp_fname = datetime.now().strftime("%Y%m%d-%H%M%S") + "_"
    FILE_NAME = "browser_history_person_info.csv" if browser_history else "person_info.csv"

    if not os.path.exists(FILE_NAME):
        print("Arquivo não encontrado")
        time.sleep(2)
        return

    df = pd.read_csv(FILE_NAME)

    app = dash.Dash(__name__)
    log = logging.getLogger('werkzeug')
    log.disabled = True

    app.layout = html.Div([
        html.H1("Mapa de Pessoas", style=dict(
            fontFamily='Fira Sans')
        ),

        html.Div(dropdown_component(df), style=dict(
            width='100%',
            verticalAlign="middle",
            padding="0px 0px 15px 0px",
            display='inline-block',
            fontSize=15,
            fontFamily='Fira Sans',
            fontWeight='bold',
            backgroundColor='white',
            margin='0px 0px 0px 0px',
        )),

        dl.Map(style={'width': '100%', 'height': '60em', 'margin': "auto", "display": "block"}, center=[0, 0], zoom=2,
               children=[
                   dl.TileLayer(),
                   dl.MeasureControl(position='bottomright', primaryLengthUnit='kilometers', primaryAreaUnit='hectares',
                                     activeColor='#db4a29', completedColor='#9b2d14'),
                   dl.LayerGroup(id="map")
               ]),

        html.Div(range_slide_component(df), style=dict(
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

        html.Div(
            style={'textAlign': 'center'},
            children=[
                dcc.Graph(
                    figure=stacked_bar_plot(df),
                    style={'display': 'inline-block', 'verticalAlign': 'middle', 'margin': '50px 0px 0px 0px'}
                )
            ]
        ),

        html.Div(
            style={'textAlign': 'center'},
            children=[
                dcc.Graph(
                    figure=scatter_plot_chart(df),
                    style={'display': 'inline-block', 'verticalAlign': 'middle', 'margin': '70px 0px 0px 0px'}
                )
            ]
        )
    ])

    # @app.callback(
    #     Output("map", "children"),
    #     [Input("map", "id")], Input("seculo-slider", "value"), Input("name-dropdown", "value")
    # )
    # def update_layer(layer_id, seculo, name):
    #     if name is None or len(name) == 0:
    #         return [dl.Marker(position=[row["Latitude"], row["Longitude"]], children=[
    #             dl.Tooltip(row["Nome Completo"]),
    #             popup_html(row)
    #         ]) for idx, row in df.iterrows() if seculo[0] <= row["Século"] <= seculo[1]]
    #     else:
    #         return [dl.Marker(position=[row["Latitude"], row["Longitude"]], children=[
    #             dl.Tooltip(row["Nome Completo"]),
    #             popup_html(row)
    #         ]) for idx, row in df.iterrows() if
    #                 row["Nome Completo"] in name and seculo[0] <= row["Século"] <= seculo[1]]

    @app.callback(
        Output("map", "children"),
        [Input("map", "id")],
        Input("seculo-slider", "value"),
        Input("name-dropdown", "value")
    )
    def update_layer(layer_id, seculo, name):
        if name is None or len(name) == 0:
            seculo_min = int(seculo[0])
            seculo_max = int(seculo[1])
            return [dl.Marker(position=[row["Latitude"], row["Longitude"]], children=[
                dl.Tooltip(row["Nome Completo"]),
                popup_html(row)
            ]) for idx, row in df.iterrows() if seculo_min <= parse_seculo(row["Século"]) <= seculo_max]
        else:
            seculo_min = int(seculo[0])
            seculo_max = int(seculo[1])
            return [dl.Marker(position=[row["Latitude"], row["Longitude"]], children=[
                dl.Tooltip(row["Nome Completo"]),
                popup_html(row)
            ]) for idx, row in df.iterrows() if
                    row["Nome Completo"] in name and seculo_min <= parse_seculo(row["Século"]) <= seculo_max]


    def parse_seculo(valor):
        if "a.C." in str(valor):
            return -int(valor.replace(" a.C.", ""))
        else:
            return int(valor)

    if not os.path.exists("data/"):
        os.makedirs("data/")
    shutil.move(FILE_NAME, "data/" + timestamp_fname + FILE_NAME)

    # run server and wait for execution and hide messages
    webbrowser.open("http://127.0.0.1:8050/")
    app.run(use_reloader=False, debug=True)


def generate_visualization_history():
    FILE_NAME = "browser_history_person_info.csv"
    clear_console()
    print("Obtendo histórico dos navagadores instalados")
    print("Isso pode demorar alguns minutos")
    time.sleep(3)
    print()
    wikipedia_history = []
    browser_history = get_history()

    print()

    if len(browser_history.histories) == 0:
        print("Nenhum histórico encontrado")
        time.sleep(3)
        return

    time.sleep(3)

    print("Registros totais: " + str(len(browser_history.histories)))

    for dt, url in browser_history.histories:
        if "wikipedia.org/wiki" in url:
            wikipedia_history.append(unquote(url.split("/")[-1]).replace("_", " "))

    # print(wikipedia_search)
    # time.sleep(2)
    # print()

    wikipedia_search = []
    person_info = []

    for entry in wikipedia_history:
        wiki_page = wptools.page(entry, lang="pt", silent=True, verbose=False)
        try:
            get_wikidata = wiki_page.get_wikidata()
        except LookupError:
            continue
        wikidata_labels = get_wikidata.data["labels"]
        if "Q5" not in wikidata_labels:
            continue
        else:
            wikipedia_search.append(entry)
            get_rest_base = wiki_page.get_restbase()
            page_url = get_rest_base.data["url"]
            wiki_data = get_wikidata.data["wikidata"]

            try:
                full_name = wiki_data["nome de nascimento (P1477)"]
                if not alphabet_detector.is_latin(full_name):
                    full_name = extract_full_name(page_url)
                if type(full_name) is list:
                    full_name = ",".join(full_name).replace(",", ", ")
            except KeyError:
                full_name = extract_full_name(page_url)

            sparql_query_data = sparql_query_wikidata(entry)
            if sparql_query_data is None:
                continue

            imagem = sparql_query_data["Imagem"]
            origem = sparql_query_data["País"]
            data_nascimento = sparql_query_data["Data de Nascimento"]
            local_nascimento = sparql_query_data["Local de Nascimento"]
            data_falecimento = sparql_query_data["Data de Falecimento"]
            local_falecimento = sparql_query_data["Local de Falecimento"]
            latitude = sparql_query_data["Latitude"]
            longitude = sparql_query_data["Longitude"]
            seculo = calcula_seculo(data_nascimento)

            person_info.append({
                "Termo Buscado": entry,
                "Nome Completo": full_name,
                "Origem/Nacionalidade": origem,
                "Data de Nascimento": data_nascimento,
                "Local de Nascimento": local_nascimento,
                "Data de Falecimento": data_falecimento,
                "Local de Falecimento": local_falecimento,
                "Século": seculo,
                "Latitude": latitude,
                "Longitude": longitude,
                "Url": page_url,
                "Imagem": imagem,
            })

    #remove duplicates from person_info
    person_info = [dict(t) for t in {tuple(d.items()) for d in person_info}]
    # loop through each dictionary in the list and pass as argument to write_to_csv function
    for person in person_info:
        write_to_csv(person, FILE_NAME)


    if len(wikipedia_search) == 0:
        print("Nenhum registro de busca na Wikipedia encontrado")
        time.sleep(3)
        return

    print("Buscas na Wikipedia: " + str(len(list(dict.fromkeys(wikipedia_search)))))
    # print("Buscas na Wikipedia: " + str(len(wikipedia_search)))
    time.sleep(3)
    print()
    print("Gerando visualização")
    generate_visualization(browser_history=True)
