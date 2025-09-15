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
from modules.plots.heatmap_plot import heatmap_by_century_country, geographic_heatmap
from modules.plots.timeline_plot import timeline_plot
from modules.utils import clear_console, write_to_csv, calcula_seculo
from modules.wiki_functions import sparql_query_wikidata
from modules.webscraping_functions import extract_full_name

alphabet_detector = AlphabetDetector()

FILE_NAME = ""


# Função que gera a visualização com as informações salvas no arquivo csv.
def generate_visualization(browser_history=False, custom_file_path=None):

    # Busca dados diretamente do SQLite ou memória via data_adapter
    from modules.data_adapter import data_adapter
    if custom_file_path:
        # Se custom_file_path for passado, tenta carregar sessão específica
        session_name = os.path.basename(custom_file_path).replace('.csv', '')
        session_data = data_adapter.db.get_session_personalities(session_name)
    else:
        # NOVA LÓGICA: Prioriza sessão em memória
        if data_adapter._is_memory_session_active():
            session_data = data_adapter._get_memory_session_personalities()
            print(f"🧠 Gerando visualização da sessão em memória: {len(session_data)} personalidade(s)")
        else:
            # Busca dados da sessão ativa (salva ou temporária)
            active_session = data_adapter.active_saved_session or data_adapter.current_session
            session_data = data_adapter.db.get_session_personalities(active_session)
            
            # Debug info
            if data_adapter.active_saved_session:
                print(f"🔍 Gerando visualização para sessão ativa: '{data_adapter.active_saved_session}'")
            else:
                print(f"🔍 Gerando visualização para sessão temporária")

    if not session_data or len(session_data) == 0:
        print("Nenhum dado encontrado na sessão selecionada.")
        time.sleep(2)
        return

    # Converte para DataFrame no formato esperado
    df_data = []
    for p in session_data:
        full_name = p.get('full_name', '').strip()
        if full_name:
            df_data.append({
                'Termo Buscado': p.get('search_term', ''),
                'Nome Completo': full_name,
                'Origem/Nacionalidade': p.get('country', ''),
                'Data de Nascimento': p.get('birth_date', ''),
                'Local de Nascimento': p.get('birth_place', ''),
                'Data de Falecimento': p.get('death_date', ''),
                'Local de Falecimento': p.get('death_place', ''),
                'Século': p.get('century', ''),
                'Latitude': p.get('latitude', None),
                'Longitude': p.get('longitude', None),
                'Url': p.get('url', ''),
                'Imagem': p.get('image_url', '')
            })

    if not df_data:
        print("Dados insuficientes para visualização.")
        time.sleep(2)
        return

    df = pd.DataFrame(df_data)

    # Configurar logging para evitar mensagens desnecessárias
    app = dash.Dash(__name__)
    
    # Desabilitar logs do werkzeug e dash
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("dash").setLevel(logging.ERROR)
    
    # Configurar para não mostrar mensagens de debug
    app.logger.disabled = True

    # Calcula centro do mapa a partir das coordenadas válidas
    latitudes = df["Latitude"].dropna()
    longitudes = df["Longitude"].dropna()
    
    # Converte para float apenas valores não nulos
    valid_latitudes = []
    valid_longitudes = []
    
    for lat in latitudes:
        try:
            if lat is not None and lat != '':
                valid_latitudes.append(float(lat))
        except (ValueError, TypeError):
            continue
    
    for lon in longitudes:
        try:
            if lon is not None and lon != '':
                valid_longitudes.append(float(lon))
        except (ValueError, TypeError):
            continue
    
    if valid_latitudes and valid_longitudes:
        center_lat = sum(valid_latitudes) / len(valid_latitudes)
        center_lon = sum(valid_longitudes) / len(valid_longitudes)
        map_center = [float(center_lat), float(center_lon)]
    else:
        map_center = [0.0, 0.0]

    app.layout = html.Div([
            html.H1("Mapa de Pessoas", style=dict(fontFamily="Fira Sans")),
            html.Div(
                dropdown_component(df),
                style=dict(
                    width="100%",
                    verticalAlign="middle",
                    padding="0px 0px 15px 0px",
                    display="inline-block",
                    fontSize=15,
                    fontFamily="Fira Sans",
                    fontWeight="bold",
                    backgroundColor="white",
                    margin="0px 0px 0px 0px",
                ),
            ),
            dl.Map(
                style={
                    "width": "100%",
                    "height": "60em",
                    "margin": "auto",
                    "display": "block",
                },
                center=map_center,  # type: ignore
                zoom=2,
                children=[
                    dl.TileLayer(),
                    dl.MeasureControl(
                        position="bottomright",
                        primaryLengthUnit="kilometers",
                        primaryAreaUnit="hectares",
                        activeColor="#db4a29",
                        completedColor="#9b2d14",
                    ),
                    dl.LayerGroup(id="map"),
                ],
            ),
            html.Div(
                range_slide_component(df),
                style=dict(
                    width="100%",
                    verticalAlign="middle",
                    padding="10px 0px 0px 0px",
                    display="inline-block",
                    textAlign="center",
                    fontSize=20,
                    fontFamily="Fira Sans",
                    fontWeight="bold",
                    color="black",
                    backgroundColor="white",
                    border="1px solid black",
                    borderRadius="5px",
                    margin="10px 0px 0px 0px",
                ),
            ),
            html.Div(
                style={"textAlign": "center"},
                children=[
                    dcc.Graph(
                        figure=stacked_bar_plot(df),
                        style={
                            "display": "inline-block",
                            "verticalAlign": "middle",
                            "margin": "50px 0px 0px 0px",
                        },
                    )
                ],
            ),
            html.Div(
                style={"textAlign": "center"},
                children=[
                    dcc.Graph(
                        figure=scatter_plot_chart(df),
                        style={
                            "display": "inline-block",
                            "verticalAlign": "middle",
                            "margin": "70px 0px 0px 0px",
                        },
                    )
                ],
            ),
            html.Div(
                style={"textAlign": "center"},
                children=[
                    dcc.Graph(
                        figure=heatmap_by_century_country(df),
                        style={
                            "display": "inline-block",
                            "verticalAlign": "middle",
                            "margin": "70px 0px 0px 0px",
                        },
                    )
                ],
            ),
            html.Div(
                style={"textAlign": "center"},
                children=[
                    dcc.Graph(
                        figure=timeline_plot(df),
                        style={
                            "display": "inline-block",
                            "verticalAlign": "middle",
                            "margin": "70px 0px 0px 0px",
                        },
                    )
                ],
            ),
        ]
    )  # <-- Colchete e parêntese fechados corretamente

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
        Input("name-dropdown", "value"),
    )
    def update_layer(layer_id, seculo, name):
        def valid_coords(row):
            try:
                lat = float(row["Latitude"])
                lon = float(row["Longitude"])
                if lat is None or lon is None:
                    return False
                return -90 <= lat <= 90 and -180 <= lon <= 180
            except (ValueError, TypeError):
                return False

        seculo_min = int(seculo[0])
        seculo_max = int(seculo[1])
        markers = []
        for idx, row in df.iterrows():
            if not valid_coords(row):
                continue
            if name is None or len(name) == 0:
                if seculo_min <= parse_seculo(row["Século"]) <= seculo_max:
                    lat = float(row["Latitude"]) if row["Latitude"] is not None else 0.0
                    lon = float(row["Longitude"]) if row["Longitude"] is not None else 0.0
                    markers.append(
                        dl.Marker(
                            position=[lat, lon],  # type: ignore
                            children=[dl.Tooltip(row["Nome Completo"]), popup_html(row)],
                        )
                    )
            else:
                if row["Nome Completo"] in name and seculo_min <= parse_seculo(row["Século"]) <= seculo_max:
                    lat = float(row["Latitude"]) if row["Latitude"] is not None else 0.0
                    lon = float(row["Longitude"]) if row["Longitude"] is not None else 0.0
                    markers.append(
                        dl.Marker(
                            position=[lat, lon],  # type: ignore
                            children=[dl.Tooltip(row["Nome Completo"]), popup_html(row)],
                        )
                    )
        return markers

    def parse_seculo(valor):
        if "a.C." in str(valor):
            return -int(valor.replace(" a.C.", ""))
        else:
            return int(valor)

    # Removido código de manipulação de arquivos CSV, pois agora tudo é via SQLite

    # run server and wait for execution and hide messages
    print("Abrindo visualização no navegador...")
    print("Pressione Ctrl+C para encerrar o servidor")
    webbrowser.open("http://127.0.0.1:8050/")
    
    try:
        app.run(debug=False, host='127.0.0.1', port=8050, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário")
    except Exception as e:
        print(f"Erro no servidor: {e}")
    finally:
        print("Visualização encerrada")


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

    for hist in browser_history.histories:
        # Ajusta para tupla de 2 ou 3 elementos
        if isinstance(hist, tuple) and len(hist) >= 2:
            url = hist[1] if len(hist) == 3 else hist[1]
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
        if get_wikidata is None or not hasattr(get_wikidata, "data"):
            continue
        data_dict = getattr(get_wikidata, "data", {})
        wikidata_labels = data_dict["labels"] if "labels" in data_dict else {}
        if "Q5" not in wikidata_labels:
            continue
        else:
            wikipedia_search.append(entry)
            get_rest_base = wiki_page.get_restbase() if hasattr(wiki_page, "get_restbase") else None
            page_url = ""
            if get_rest_base and hasattr(get_rest_base, "data"):
                rest_data = getattr(get_rest_base, "data", {})
                if rest_data and isinstance(rest_data, dict) and "url" in rest_data:
                    page_url = rest_data["url"]
            wiki_data = data_dict["wikidata"] if "wikidata" in data_dict else {}

            try:
                full_name = wiki_data.get("nome de nascimento (P1477)", "")
                if not alphabet_detector.is_latin(full_name):
                    full_name = extract_full_name(page_url)
                if type(full_name) is list:
                    full_name = ",".join(full_name).replace(",", ", ")
            except Exception:
                full_name = extract_full_name(page_url)

            sparql_query_data = sparql_query_wikidata(entry)
            if sparql_query_data is None:
                continue

            imagem = sparql_query_data.get("Imagem", "")
            origem = sparql_query_data.get("País", "")
            data_nascimento = sparql_query_data.get("Data de Nascimento", "")
            local_nascimento = sparql_query_data.get("Local de Nascimento", "")
            data_falecimento = sparql_query_data.get("Data de Falecimento", "")
            local_falecimento = sparql_query_data.get("Local de Falecimento", "")
            latitude = sparql_query_data.get("Latitude", None)
            longitude = sparql_query_data.get("Longitude", None)
            seculo = calcula_seculo(data_nascimento)

            person_info.append(
                {
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
                }
            )

    # remove duplicates from person_info
    person_info = [dict(t) for t in {tuple(d.items()) for d in person_info}]
    
    # Salvar dados no banco de dados SQLite via data_adapter
    from modules.data_adapter import data_adapter
    
    if len(wikipedia_search) == 0:
        print("Nenhum registro de busca na Wikipedia encontrado")
        time.sleep(3)
        return
    
    print(f"Salvando {len(person_info)} personalidades no banco de dados...")
    saved_count = 0
    
    # Salva cada personalidade no banco de dados
    for person in person_info:
        try:
            success = data_adapter.write_to_csv_compatible(person, FILE_NAME)
            if success:
                saved_count += 1
        except Exception as e:
            print(f"Erro ao salvar {person.get('Nome Completo', 'N/A')}: {e}")
            continue
    
    print(f"✅ {saved_count} personalidades salvas no banco de dados")

    print("Buscas na Wikipedia: " + str(len(list(dict.fromkeys(wikipedia_search)))))
    time.sleep(3)
    print()
    print("Gerando visualização dos dados salvos no banco...")
    # Gera visualização dos dados que foram salvos no banco de dados
    generate_visualization(browser_history=False)  # Usa dados da sessão atual do banco
