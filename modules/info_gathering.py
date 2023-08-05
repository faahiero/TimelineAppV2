import sys
import time

from alphabet_detector import AlphabetDetector

import modules.webscraping_functions as webscraping
from modules.utils import calcula_seculo, clear_console, write_to_csv
from modules.wiki_functions import get_summary, search_wikidata, sparql_query_wikidata

alphabet_detector = AlphabetDetector()

attempts = 0


# Função principal da aplicação, responsável por obter os dados solicitados.
# Ela chama as outras funções. Ao final da execução, gera um arquivo csv que
# será utilizado para gerar a visualização.
def fetch_data(search_term, is_correct_term):
    FILE_NAME = "person_info.csv"
    global attempts
    if not is_correct_term:
        search_term = input("Digite o nome da personalidade (0 para encerrar): ")
        if search_term == "0":
            clear_console()
            print("Obrigado por usar o software!!")
            sys.exit()

    clear_console()

    # Chamada da função que tenta corrigir o termo de busca,
    # para garantir que o termo exista na wikipedia.
    correct_search_term = webscraping.get_correct_search_term(search_term)
    if correct_search_term is None:
        time.sleep(4)
        return
    print("Termo buscado: " + search_term)

    # Pesquisa o termo, após corrigido, na lib wptools.
    page = search_wikidata(correct_search_term)
    get_wiki_data = page.get_wikidata()

    # Verifica se a instância da wikidata referente ao termo buscado possui a
    # propriedade 'Q5', que representa um ser humano, logo entende-se que é uma pessoa.
    wikidata_labels = get_wiki_data.data["labels"]
    if "Q5" not in wikidata_labels:
        print("Termo buscado não é uma pessoa. Tente novamente.")
        time.sleep(4)
        return
        # attempts += 1
        # if attempts < 3:
        #     retrieve_information(search_term, False)
        # else:
        #     print("Refine sua busca e tente novamente")
        #     print("Obrigado por usar o software!!")
        #     sys.exit()

    print("Obtendo informações...")

    # Após conseguir o nome completo, começo a utilizar a biblioteca SPARQLWrapper para obter os demais dados.
    # A biblioteca realiza consultas diretamente na wikidata, e retorna um objeto JSON com as informações.
    # A função query_wikidata retorna um objeto JSON com as informações necessárias.
    sparql_query_data = sparql_query_wikidata(correct_search_term)

    if sparql_query_data is None:
        print("Não foi possível obter informações sobre a personalidade pesquisada.")
        time.sleep(4)
        return

    # Aqui utilizo uma biblioteca auxiliar chamada wikipedia(importada como wiki),
    # apenas para obter algumas linhas do sumário do artigo encontrado e mostrar
    # na tela para confirmar a busca.
    summary = get_summary(correct_search_term)

    clear_console()
    print(summary)

    while True:
        print()
        user_option = input("A informação está correta? (s/n): ")
        answer = user_option.lower()
        if user_option == "" or answer not in ["s", "n"]:
            print("Responda com s ou n!")
        else:
            break
    if answer == "s":
        time.sleep(4)
        wiki_data = get_wiki_data.data["wikidata"]

        # URL do artigo na wikipedia, utilizado para fazer Webscraping diretamente na página
        # do artigo e obter o nome completo, caso não seja possível obter pela wptools, e
        # também para compor o arquivo csv.
        get_rest_base = page.get_restbase()
        page_url = get_rest_base.data["url"]

        # NOME COMPLETO
        # Trecho que utilizo para obter o nome completo da pessoa.
        # Tento pela wptools, caso não consiga, utilizo Webscraping.
        try:
            full_name = wiki_data["nome de nascimento (P1477)"]
            if not alphabet_detector.is_latin(full_name):
                full_name = webscraping.extract_full_name(page_url)
            if type(full_name) is list:
                full_name = ",".join(full_name).replace(",", ", ")
        except KeyError:
            full_name = webscraping.extract_full_name(page_url)

        # # Após conseguir o nome completo, começo a utilizar a biblioteca SPARQLWrapper para obter os demais dados.
        # # A biblioteca realiza consultas diretamente na wikidata, e retorna um objeto JSON com as informações.
        # # A função query_wikidata retorna um objeto JSON com as informações necessárias.
        # sparql_query_data = sparql_query_wikidata(correct_search_term)

        # A partir daqui monto um dicionário com todas as informações que eu preciso e crio um arquivo csv.
        imagem = sparql_query_data["Imagem"]
        origem = sparql_query_data["País"]
        data_nascimento = sparql_query_data["Data de Nascimento"]
        local_nascimento = sparql_query_data["Local de Nascimento"]
        data_falecimento = sparql_query_data["Data de Falecimento"]
        local_falecimento = sparql_query_data["Local de Falecimento"]
        latitude = sparql_query_data["Latitude"]
        longitude = sparql_query_data["Longitude"]
        seculo = calcula_seculo(data_nascimento)

        # ano = int(data_nascimento.split()[-1])
        # if ano % 100 == 0:
        #     ano -= 1
        # seculo = (ano // 100) + 1

        person_info = {
            "Termo Buscado": search_term,
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

        write_to_csv(person_info, FILE_NAME)

        clear_console()
        print()
        print("Nome Completo: " + full_name)
        if origem != "Não Informado":
            print("Origem/Nacionalidade: " + origem)
        print("Data de Nascimento: " + data_nascimento)
        print("Local de Nascimento: " + local_nascimento)
        print("Data de Falecimento: " + data_falecimento)
        print("Local de Falecimento: " + local_falecimento)
        print("Século: " + str(seculo))
        print("Finalizando...")

        time.sleep(4)
        clear_console()
    else:
        clear_console()
        attempts += 1
        if attempts <= 3:
            fetch_data(search_term, False)
        else:
            print("Refine sua busca e tente novamente")
            print("Obrigado por usar o software!!")
            sys.exit()
