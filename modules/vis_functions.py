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
# Modificada para aceitar um custom_file_path
def generate_visualization(browser_history=False, custom_file_path=None):
    timestamp_fname = datetime.now().strftime("%Y%m%d-%H%M%S") + "_"

    current_file_to_process = ""
    is_session_load = False

    if custom_file_path:
        current_file_to_process = custom_file_path
        is_session_load = True
        print(f"Carregando dados da sessão: {custom_file_path}")
    elif browser_history:
        current_file_to_process = "browser_history_person_info.csv"
    else:
        current_file_to_process = "person_info.csv"

    if not os.path.exists(current_file_to_process):
        print(f"Arquivo '{current_file_to_process}' não encontrado. Não é possível gerar a visualização.")
        time.sleep(2)
        return

    try:
        # Determina o tipo de arquivo e lê os dados
        if current_file_to_process.endswith(".csv"):
            df = pd.read_csv(current_file_to_process)
        elif current_file_to_process.endswith(".json"):
            df = pd.read_json(current_file_to_process)
        else:
            print(f"Formato de arquivo não suportado: {current_file_to_process}. Use .csv ou .json.")
            return

        if df.empty:
            print(f"O arquivo '{current_file_to_process}' está vazio. Não há dados para visualizar.")
            time.sleep(2)
            return

    except pd.errors.EmptyDataError:
        print(f"O arquivo '{current_file_to_process}' está vazio ou corrompido (EmptyDataError).")
        time.sleep(2)
        return
    except ValueError as ve: # Especificamente para erros de parsing de JSON
        print(f"Erro ao processar o arquivo JSON '{current_file_to_process}': {ve}")
        time.sleep(2)
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo '{current_file_to_process}': {e}")
        time.sleep(2)
        return

    required_columns = ["Latitude", "Longitude", "Nome Completo", "Século"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Colunas essenciais ausentes no arquivo '{current_file_to_process}': {', '.join(missing_columns)}. Não é possível gerar a visualização.")
        time.sleep(2)
        return

    app = dash.Dash(__name__)
    log = logging.getLogger("werkzeug")
    log.disabled = True

    # Título dinâmico baseado na origem dos dados
    data_source_title = os.path.basename(current_file_to_process) if is_session_load else \
                        ("Histórico de Navegação" if browser_history else "Busca Atual")

    app.layout = html.Div(
        [
            html.H1(f"Mapa de Pessoas - {data_source_title}", style=dict(fontFamily="Fira Sans", textAlign="center")),
            html.Div(
                dropdown_component(df), # Assume que df tem as colunas necessárias
                style=dict(
                    width="100%", verticalAlign="middle", padding="0px 0px 15px 0px",
                    display="inline-block", fontSize=15, fontFamily="Fira Sans",
                    fontWeight="bold", backgroundColor="white", margin="0px 0px 0px 0px",
                ),
            ),
            dl.Map(
                style={"width": "100%", "height": "60em", "margin": "auto", "display": "block"},
                center=[0, 0], zoom=2,
                children=[
                    dl.TileLayer(),
                    dl.MeasureControl(
                        position="bottomright", primaryLengthUnit="kilometers",
                        primaryAreaUnit="hectares", activeColor="#db4a29", completedColor="#9b2d14",
                    ),
                    dl.LayerGroup(id="map"),
                ],
            ),
            html.Div(
                range_slide_component(df), # Assume que df tem as colunas necessárias
                style=dict(
                    width="100%", verticalAlign="middle", padding="10px 0px 0px 0px",
                    display="inline-block", textAlign="center", fontSize=20,
                    fontFamily="Fira Sans", fontWeight="bold", color="black",
                    backgroundColor="white", border="1px solid black",
                    borderRadius="5px", margin="10px 0px 0px 0px",
                ),
            ),
            html.Div(
                style={"textAlign": "center"},
                children=[dcc.Graph(figure=stacked_bar_plot(df), style={"display": "inline-block", "verticalAlign": "middle", "margin": "50px 0px 0px 0px"})],
            ),
            html.Div(
                style={"textAlign": "center"},
                children=[dcc.Graph(figure=scatter_plot_chart(df), style={"display": "inline-block", "verticalAlign": "middle", "margin": "70px 0px 0px 0px"})],
            ),
        ]
    )

    @app.callback(
        Output("map", "children"),
        [Input("map", "id")],
        Input("seculo-slider", "value"),
        Input("name-dropdown", "value"),
    )
    def update_map_callback(layer_id, seculo_range, selected_names):
        # Passa o DataFrame (df) que foi lido do arquivo correto para a função de callback
        return _update_map_layer(df, seculo_range, selected_names)

    # Apenas move para 'data/' se não for um carregamento de sessão,
    # pois os arquivos de sessão já estão em 'data/sessions/'.
    # Os arquivos temporários 'person_info.csv' e 'browser_history_person_info.csv'
    # ainda são movidos para 'data/' para arquivamento.
    if not is_session_load:
        _prepare_data_directory(current_file_to_process, timestamp_fname)

    _launch_dash_app(app)


def _update_map_layer(df, seculo_range, selected_names):
    """Atualiza a camada do mapa com base nos filtros selecionados."""
    try:
        seculo_min, seculo_max = map(int, seculo_range)

        # Assegura que o DataFrame não seja modificado inplace desnecessariamente
        df_copy = df.copy()

        # Converte 'Século' para numérico para filtro, tratando erros.
        # Extrai apenas a parte numérica antes de "a.C." ou o número em si.
        df_copy['Século_Num'] = df_copy['Século'].astype(str).str.extract(r'(-?\d+)', expand=False)
        df_copy['Século_Num'] = pd.to_numeric(df_copy['Século_Num'], errors='coerce')

        # Aplica a função parse_seculo para converter corretamente para o filtro
        # parse_seculo já lida com "a.C." e retorna int
        df_copy['Século_Parsed'] = df_copy['Século'].apply(parse_seculo)

        # Filtra por século
        df_filtered_seculo = df_copy[
            df_copy['Século_Parsed'].between(seculo_min, seculo_max, inclusive='both')
        ]

        # Filtra por nome, se houver nomes selecionados
        if selected_names:
            # Garante que selected_names seja uma lista, mesmo que seja uma string única do dropdown
            names_to_filter = selected_names if isinstance(selected_names, list) else [selected_names]
            df_filtered_final = df_filtered_seculo[df_filtered_seculo["Nome Completo"].isin(names_to_filter)]
        else:
            df_filtered_final = df_filtered_seculo

        # Converte colunas de Latitude e Longitude para numérico, tratando erros
        df_filtered_final.loc[:, "Latitude"] = pd.to_numeric(df_filtered_final["Latitude"], errors='coerce')
        df_filtered_final.loc[:, "Longitude"] = pd.to_numeric(df_filtered_final["Longitude"], errors='coerce')

        # Remove linhas onde Latitude ou Longitude são NaN
        df_filtered_final.dropna(subset=["Latitude", "Longitude"], inplace=True)

        markers = [
            dl.Marker(
                position=[row["Latitude"], row["Longitude"]],
                children=[dl.Tooltip(row["Nome Completo"]), popup_html(row)],
            )
            for _, row in df_filtered_final.iterrows()
        ]
        return markers
    except Exception as e:
        print(f"Erro ao atualizar camada do mapa: {e}")
        return []


def parse_seculo(valor):
    """Converte o valor do século para um inteiro (negativo para a.C.)."""
    text = str(valor).strip().lower() # Normaliza para minúsculas
    if not text or text == "não informado":
        return -9999 # Um valor que provavelmente estará fora do range do slider

    is_ac = "a.c." in text or "ac" in text or "bc" in text # Verifica todas as variações comuns

    # Extrai o número do século
    num_str = "".join(filter(str.isdigit, text))
    if not num_str:
        return -9999

    try:
        seculo_num = int(num_str)
        if is_ac:
            return -seculo_num
        return seculo_num
    except ValueError:
        return -9999


def _prepare_data_directory(file_name_to_move, timestamp_prefix):
    """Cria o diretório 'data/' se não existir e move o arquivo especificado para lá, com timestamp."""
    data_dir = "data/"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Garante que estamos movendo apenas arquivos da raiz do projeto (não de data/sessions)
    if os.path.dirname(file_name_to_move) == "": # Arquivo está na raiz
        base_name = os.path.basename(file_name_to_move)
        destination_path = os.path.join(data_dir, timestamp_prefix + base_name)
        try:
            shutil.move(file_name_to_move, destination_path)
            print(f"Arquivo '{base_name}' movido para '{destination_path}'")
        except FileNotFoundError:
            print(f"Arquivo '{file_name_to_move}' não encontrado para mover.")
        except Exception as e:
            print(f"Erro ao mover '{file_name_to_move}' para '{destination_path}': {e}")
    # else:
        # print(f"Arquivo '{file_name_to_move}' não está na raiz, não será movido para o arquivamento geral.")


def _launch_dash_app(app):
    """Inicia o servidor Dash."""
    webbrowser.open("http://127.0.0.1:8050/")
    app.run_server(use_reloader=False, debug=True)


def generate_visualization_history():
    """Gera a visualização a partir do histórico de navegação."""
    FILE_NAME = "browser_history_person_info.csv"
    clear_console()
    print("Obtendo histórico dos navegadores instalados...")
    print("Isso pode demorar alguns minutos.")
    time.sleep(3)

    browser_hist = get_history()
    if not browser_hist.histories:
        print("\nNenhum histórico encontrado.")
        time.sleep(3)
        return

    print(f"\nRegistros totais: {len(browser_hist.histories)}")
    time.sleep(1)

    wikipedia_urls = _extract_wikipedia_urls(browser_hist.histories)
    if not wikipedia_urls:
        print("Nenhum registro de busca na Wikipedia encontrado no histórico.")
        time.sleep(3)
        return

    print(f"Buscas na Wikipedia encontradas: {len(wikipedia_urls)}")
    time.sleep(1)
    print("Processando entradas da Wikipedia...")

    person_info_list = _fetch_person_info_from_history(wikipedia_urls)

    if not person_info_list:
        print("Não foi possível obter informações de nenhuma entrada da Wikipedia no histórico.")
        time.sleep(3)
        return

    _save_person_info_to_csv(person_info_list, FILE_NAME)

    print("\nGerando visualização do histórico...")
    generate_visualization(browser_history=True)


def _extract_wikipedia_urls(histories):
    """Extrai URLs da Wikipedia do histórico de navegação."""
    urls = []
    for _, url in histories:
        if "wikipedia.org/wiki" in url:
            term = unquote(url.split("/")[-1]).replace("_", " ")
            urls.append(term)
    return list(dict.fromkeys(urls)) # Remove duplicates while preserving order


from concurrent.futures import ThreadPoolExecutor, as_completed

# ... (outras importações)

MAX_WORKERS = 10 # Ajuste conforme necessário para otimizar I/O bound tasks

def _fetch_single_person_info(entry):
    """Função wrapper para processar uma única entrada para ThreadPoolExecutor."""
    # print(f"Processando: {entry}") # Movido para dentro do loop de progresso
    return get_browse_history_person_info(entry)

def _fetch_person_info_from_history(wikipedia_urls):
    """Busca informações de pessoas a partir de uma lista de URLs da Wikipedia usando ThreadPoolExecutor."""
    person_info_list = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_entry = {executor.submit(_fetch_single_person_info, entry): entry for entry in wikipedia_urls}

        processed_count = 0
        total_entries = len(wikipedia_urls)

        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            processed_count += 1
            try:
                info = future.result()
                if info:
                    person_info_list.append(info)
                # Imprime o progresso aqui para refletir a conclusão real
                print(f"Processado: {entry} ({processed_count}/{total_entries}) - {'Sucesso' if info else 'Falha/Não é pessoa'}")
            except Exception as exc:
                print(f"'{entry}' gerou uma exceção: {exc}")

    return person_info_list


def _save_person_info_to_csv(person_info_list, file_name):
    """Salva a lista de informações de pessoas em um arquivo CSV."""
    # Remove duplicates from person_info_list before saving
    unique_person_info = [dict(t) for t in {tuple(d.items()) for d in person_info_list}]
    for person_data in unique_person_info:
        write_to_csv(person_data, file_name)
    print(f"\n{len(unique_person_info)} registros únicos salvos em {file_name}")

# Note: The function `get_browse_history_person_info` is assumed to be similar to
# the logic previously in `generate_visualization_history` for fetching data for a single entry.
# It would involve:
# 1. wptools.page to get page info
# 2. Check if it's a person (Q5)
# 3. Extract full name
# 4. sparql_query_wikidata
# 5. Construct and return the person_info dictionary
# This function would need to be created in `browse_history_info_gathering.py` or similar.
