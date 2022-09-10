#!/usr/bin/python3
import sys
import webbrowser
import wptools
import wikipedia as wiki
import urllib
import time
from SPARQLWrapper import SPARQLWrapper, JSON
import shutil
import requests
import pandas as pd
import os
import locale
import folium
from datetime import datetime
import csv
from bs4 import BeautifulSoup
import art
from alphabet_detector import AlphabetDetector

WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIPEDIA_URL = "https://pt.wikipedia.org/"

alphabet_detector = AlphabetDetector()

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

wiki.set_lang('pt')

attempts = 0


# Limpar o console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


# Arte do cabeçalho do programa
def header():
    banner = art.text2art("Wikipedia GeoHist", font="small")
    print(banner)


# Menu do programa
def menu():
    print("[1] - Buscar (Ex.: 'Machado de Assis')")
    print("[2] - Gerar visualização")
    print("[0] - Encerrar")
    print()


# Função que utiliza wptools para fazer uma busca na wikidata por um termo.
# Ela retorna uma instância na wikidata do item buscado caso ele exista,
# e com essa informação extraio a propriedade "nome de nascimento (P1477)"
# em funções mais abaixo.
# Caso não haja registro dessa propriedade, utilizo Webscraping tradicional (BeautifulSoup, etc.) para obter o dado.
def search(search_term):
    return wptools.page(search_term, lang='pt', silent=True, verbose=False)


# Função principal da aplicação, responsável por obter os dados solicitados. Ela chama as outras funções.
# Ao final da execução, gera um arquivo csv que será utilizado para gerar a visualização.
def get_info_person(search_term, is_correct_term):
    global attempts
    if not is_correct_term:
        search_term = input(
            "Digite o nome da personalidade (0 para encerrar): ")
        if search_term == '0':
            clear_console()
            print("Obrigado por usar o software!!")
            sys.exit()

    clear_console()

    # Chamada da função que tenta corrigir o termo de busca, para garantir que o termo exista na wikipedia.
    correct_search_term = get_correct_search_term(search_term)
    print("Termo buscado: " + search_term)

    # Pesquisa o termo, após corrigodo, na lib wptools.
    page = search(correct_search_term)
    get_wiki_data = page.get_wikidata()

    # Verifica se a instância da wikidata referente ao termo buscado possui a propriedade 'Q5',
    # que representa um ser humano, logo entende-se que é uma pessoa.
    wikidata_labels = get_wiki_data.data['labels']
    if 'Q5' not in wikidata_labels:
        print("Termo buscado não é uma pessoa. Tente novamente.")
        attempts += 1
        if attempts < 3:
            get_info_person(search_term, False)
        else:
            print("Refine sua busca e tente novamente")
            print("Obrigado por usar o software!!")
            sys.exit()

    print("Obtendo informações...")

    # Aqui utilizo uma biblioteca auxiliar chamada wikipedia(importada como wiki),
    # apenas para obter algumas linhas do sumário do artigo encontrado e mostrar
    # na tela para confirmar a busca.
    summary = wiki.summary(correct_search_term, sentences=2)
    clear_console()
    print(summary)
    while True:
        print()
        user_option = input("A informação está correta? (s/n): ")
        answer = user_option.lower()
        if user_option == '' or answer not in ['s', 'n']:
            print("Responda com s ou n!")
        else:
            break
    if answer == 's':
        time.sleep(5)
        wiki_data = get_wiki_data.data['wikidata']

        # URL da página, utilizado para fazer Webscraping diretamente na página do artigo e obter o nome completo,
        # caso não seja possível obter pela wptools, e também para compor o arquivo csv.
        get_rest_base = page.get_restbase()
        page_url = get_rest_base.data['url']

        # NOME COMPLETO
        # Trecho que utilizo para obter o nome completo da pessoa.
        # Tento pela wptools, caso não consiga, utilizo Webscraping.
        try:
            full_name = wiki_data['nome de nascimento (P1477)']
            if not alphabet_detector.is_latin(full_name):
                full_name = extract_full_name(page_url)
            if type(full_name) == list:
                full_name = ','.join(full_name).replace(',', ', ')
        except KeyError:
            full_name = extract_full_name(page_url)

        # Após conseguir o nome completo, começo a utilizar a biblioteca SPARQLWrapper para obter os demais dados.
        # A função query_wikidata retorna um objeto JSON com as informações necessárias.
        sparql_query_data = query_wikidata(correct_search_term)

        # A partir daqui monto um dicionário com todas as informações que eu preciso e crio um arquivo csv.
        imagem = sparql_query_data['Imagem']
        origem = sparql_query_data['País']
        data_nascimento = sparql_query_data['Data de Nascimento']
        local_nascimento = sparql_query_data['Local de Nascimento']
        data_falecimento = sparql_query_data['Data de Falecimento']
        local_falecimento = sparql_query_data['Local de Falecimento']
        latitude = sparql_query_data['Latitude']
        longitude = sparql_query_data['Longitude']

        person_info = {
            "Termo Buscado": search_term,
            "Nome Completo": full_name,
            "Origem/Nacionalidade": origem,
            "Data de Nascimento": data_nascimento,
            "Local de Nascimento": local_nascimento,
            "Data de Falecimento": data_falecimento,
            "Local de Falecimento": local_falecimento,
            "Latitude": latitude,
            "Longitude": longitude,
            "Url": page_url,
            "Imagem": imagem
        }

        if not os.path.isfile("person_info.csv"):
            with open('person_info.csv', 'a', newline='') as csvfile:
                fieldnames = person_info.keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(person_info)
        else:
            with open('person_info.csv', 'a', newline='') as csvfile:
                fieldnames = person_info.keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(person_info)

        clear_console()
        print()
        print("Nome Completo: " + full_name)
        if origem != "Não Informado":
            print("Origem/Nacionalidade: " + origem)
        print("Data de Nascimento: " + data_nascimento)
        print("Local de Nascimento: " + local_nascimento)
        print("Data de Falecimento: " + data_falecimento)
        print("Local de Falecimento: " + local_falecimento)
        print("Finalizando...")

        time.sleep(5)
        clear_console()
    else:
        clear_console()
        attempts += 1
        if attempts <= 3:
            get_info_person(search_term, False)
        else:
            print("Refine sua busca e tente novamente")
            print("Obrigado por usar o software!!")
            sys.exit()


# Função para corrigir o termo buscado.
def get_correct_search_term(search_term):
    corrected_search_term = None
    encoded_search_term = urllib.parse.quote_plus(search_term)
    base_wikipedia_url = WIKIPEDIA_URL
    wikipedia_search_url = base_wikipedia_url+"w/index.php?search={}&title=Especial:Pesquisar&profile=advanced&" \
        "fulltext=1&ns0=1".format(encoded_search_term)
    page = requests.get(wikipedia_search_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # correção palavra errada (você quis dizer)
    if soup.find_all('div', class_='searchdidyoumean'):
        for data in soup.find_all('div', class_='searchdidyoumean'):
            for a in data.find_all('a'):
                link = a.get('href')
                corrected_search = requests.get(base_wikipedia_url + link)
                soup_correct_search = BeautifulSoup(
                    corrected_search.content, 'html.parser')
                corrected_search_term = soup_correct_search.find('div', class_='mw-search-result-heading').find(
                    'a').text
                break
            break
        return corrected_search_term

    # palavra certa
    elif soup.find('div', class_='mw-search-result-heading'):
        corrected_search_term = soup.find(
            'div', class_='mw-search-result-heading').text.strip()
        return corrected_search_term

    # termo não encontrado na wikipedia, logo, artigo não existe
    else:
        print("Artigo não encontrado na wikipedia")
    get_info_person(corrected_search_term, False)


# Função para obter o nome completo, caso não consiga utilizar a wptools.
def extract_full_name(page_url):
    request_page = requests.get(page_url)
    soup = BeautifulSoup(request_page.text, 'html.parser')

    for table in soup.find_all('table'):
        table.decompose()

    if soup.find('div', class_='hatnote'):
        soup.find('div', class_='hatnote').decompose()

    if soup.find('p', class_='mw-empty-elt'):
        soup.find('p', class_='mw-empty-elt').decompose()

    full_name = soup.find(
        'div', attrs={'class': 'mw-parser-output'}).p.b.text.replace(",", "").strip()
    return full_name


# Função que utiliza a biblioteca SPARQLWrapper para fazer a consulta no wikidata. Ao final da execução,
# ela monta um objeto, que é retornado para a função get_info_person sendo utilizado gerar um arquivo csv.
def query_wikidata(term_to_query):
    endpoint_url = WIKIDATA_SPARQL_ENDPOINT

    query = """
    SELECT ?item ?itemLabel ?imagem ?dataNascimento ?localNascimento ?localNascimentoLabel ?dataFalecimento ?localFalecimento 
           ?localFalecimentoLabel ?pais ?paisLabel ?geo
      WHERE {{
        ?item wdt:P31 wd:Q5 .
        ?item ?label "{term_to_query}"@pt .
        ?item wdt:P18 ?imagem .
        ?item wdt:P569 ?dataNascimento .
        ?item wdt:P19 ?localNascimento .
        ?localNascimento wdt:P17 ?pais .
        ?localNascimento wdt:P625 ?geo .
        OPTIONAL {{ ?item wdt:P570 ?dataFalecimento . }}
        OPTIONAL {{ ?item wdt:P20 ?localFalecimento . }}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "pt,en" }}
    }} ORDER BY DESC(?item) LIMIT 1

    """.format(term_to_query=term_to_query)
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 " \
                 "Safari/537.36 "

    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    query_results = sparql.query().convert()['results']['bindings']

    imagem = query_results[0]['imagem']['value']
    pais = (query_results[0]["paisLabel"]["value"])
    data_nascimento = (query_results[0]["dataNascimento"]["value"])
    if data_nascimento[0] == '-':
        data_nascimento = data_nascimento[1:]
    data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%dT%H:%M:%SZ')
    data_nascimento = data_nascimento.strftime('%d de %B de %Y')

    if 'dataFalecimento' in query_results[0]:
        data_falecimento = (query_results[0]["dataFalecimento"]["value"])
        if data_falecimento[0] == '-':
            data_falecimento = data_falecimento[1:]
        data_falecimento = datetime.strptime(
            data_falecimento, '%Y-%m-%dT%H:%M:%SZ')
        data_falecimento = data_falecimento.strftime('%d de %B de %Y')
    else:
        data_falecimento = '-'

    local_nascimento = (query_results[0]["localNascimentoLabel"]["value"])

    if 'localFalecimento' in query_results[0]:
        local_falecimento = (
            query_results[0]["localFalecimentoLabel"]["value"])
    else:
        local_falecimento = '-'

    coordinates = (query_results[0]["geo"]["value"])
    coordinates = coordinates[6:-1]
    coordinates = coordinates.split(' ')
    coordinates.reverse()
    coordinates = ', '.join(coordinates)

    latitude = coordinates.split(',')[0]
    longitude = coordinates.split(',')[1]

    query_results = {
        'Imagem': imagem,
        'País': pais,
        'Data de Nascimento': data_nascimento,
        'Local de Nascimento': local_nascimento,
        'Data de Falecimento': data_falecimento,
        'Local de Falecimento': local_falecimento,
        'Latitude': latitude,
        'Longitude': longitude
    }

    return query_results


# Função que gera a visualização com as informações salvas no arquivo csv.
def generate_visualization():
    timestamp_fname = time.strftime("%Y%m%d-%H%M%S") + "_"
    df = pd.read_csv("person_info.csv")
    df.to_csv("person_info.csv", index=False)
    folium_map = folium.Map()

    for index, linha in df.iterrows():
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
    webbrowser.open('file://' + os.path.realpath('data/' +
                    timestamp_fname + 'map.html'))
