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

    print(f"Termo buscado: {search_term}")

    page = _get_wikidata_page(correct_search_term)
    if page is None:
        return

    if not _is_person(page):
        print("Termo buscado não é uma pessoa. Tente novamente.")
        time.sleep(4)
        return

    print("Obtendo informações...")
    sparql_query_data = sparql_query_wikidata(correct_search_term)
    if sparql_query_data is None:
        print("Não foi possível obter informações sobre a personalidade pesquisada.")
        time.sleep(4)
        return

    summary = get_summary(correct_search_term)
    clear_console()
    print(summary)

    if not _confirm_information():
        _handle_incorrect_information(search_term)
        return

    person_data = _extract_person_data(page, sparql_query_data, search_term)
    write_to_csv(person_data, FILE_NAME)
    _display_person_info(person_data)

    time.sleep(4)
    clear_console()


def _get_wikidata_page(search_term):
    """Busca o termo na Wikidata e retorna a página."""
    try:
        page = search_wikidata(search_term)
        if page and hasattr(page, 'data') and page.data.get('requests'): # Verifica se houve requisição
            return page
        else:
            print(f"Nenhuma página encontrada ou dados insuficientes para '{search_term}' na Wikidata.")
            return None
    except Exception as e:
        print(f"Erro ao buscar '{search_term}' na Wikidata: {e}")
        return None


def _is_person(page):
    """Verifica se a página da Wikidata se refere a uma pessoa."""
    if not page:
        return False
    try:
        get_wiki_data = page.get_wikidata()
        if not get_wiki_data or not hasattr(get_wiki_data, 'data') or 'labels' not in get_wiki_data.data:
            print(f"Não foi possível obter dados da Wikidata ou labels para a página.")
            return False
        wikidata_labels = get_wiki_data.data["labels"]
        return "Q5" in wikidata_labels  # Q5 é o item do Wikidata para "ser humano"
    except Exception as e:
        print(f"Erro ao verificar se a página é de uma pessoa: {e}")
        return False


def _confirm_information():
    """Pergunta ao usuário se a informação está correta."""
    while True:
        print()
        user_option = input("A informação está correta? (s/n): ")
        answer = user_option.lower()
        if user_option == "" or answer not in ["s", "n"]:
            print("Responda com s ou n!")
        else:
            return answer == "s"


def _handle_incorrect_information(search_term):
    """Lida com a situação em que o usuário indica que a informação está incorreta."""
    global attempts
    clear_console()
    attempts += 1
    if attempts <= 3:
        fetch_data(search_term, False)
    else:
        print("Refine sua busca e tente novamente")
        print("Obrigado por usar o software!!")
        sys.exit()


def _extract_person_data(page, sparql_query_data, search_term):
    """Extrai os dados da pessoa da página da Wikidata e dos dados SPARQL."""
    try:
        get_wiki_data = page.get_wikidata()
        wiki_data = get_wiki_data.data.get("wikidata", {})
        get_rest_base = page.get_restbase()
        page_url = get_rest_base.data.get("url", f"https://pt.wikipedia.org/wiki/{search_term.replace(' ', '_')}")

        full_name = _get_full_name(wiki_data, page_url, search_term)

        data_nascimento = sparql_query_data.get("Data de Nascimento", "Não Informado")
        seculo = calcula_seculo(data_nascimento) if data_nascimento != "Não Informado" else "Não Informado"

        return {
            "Termo Buscado": search_term,
            "Nome Completo": full_name,
            "Origem/Nacionalidade": sparql_query_data.get("País", "Não Informado"),
            "Data de Nascimento": data_nascimento,
            "Local de Nascimento": sparql_query_data.get("Local de Nascimento", "Não Informado"),
            "Data de Falecimento": sparql_query_data.get("Data de Falecimento", "Não Informado"),
            "Local de Falecimento": sparql_query_data.get("Local de Falecimento", "Não Informado"),
            "Século": seculo,
            "Latitude": sparql_query_data.get("Latitude", "Não Informado"),
            "Longitude": sparql_query_data.get("Longitude", "Não Informado"),
            "Url": page_url,
            "Imagem": sparql_query_data.get("Imagem", "Não Informado"),
        }
    except Exception as e:
        print(f"Erro ao extrair dados da pessoa para '{search_term}': {e}")
        # Retorna um dicionário com valores padrão em caso de erro, para manter a estrutura
        return {
            "Termo Buscado": search_term,
            "Nome Completo": search_term, # Fallback para o termo de busca
            "Origem/Nacionalidade": "Não Informado",
            "Data de Nascimento": "Não Informado",
            "Local de Nascimento": "Não Informado",
            "Data de Falecimento": "Não Informado",
            "Local de Falecimento": "Não Informado",
            "Século": "Não Informado",
            "Latitude": "Não Informado",
            "Longitude": "Não Informado",
            "Url": f"https://pt.wikipedia.org/wiki/{search_term.replace(' ', '_')}",
            "Imagem": "Não Informado",
        }


def _get_full_name(wiki_data, page_url, search_term):
    """Obtém o nome completo da pessoa, com fallbacks."""
    full_name = None
    try:
        # Tenta obter o nome de nascimento (P1477)
        full_name = wiki_data.get("nome de nascimento (P1477)")
        if isinstance(full_name, list):
            full_name = ", ".join(full_name) # Concatena se for uma lista

        # Se o nome não for latino ou não for encontrado, tenta extrair da URL da página
        if not full_name or (full_name and not alphabet_detector.is_latin(str(full_name))):
            if page_url:
                extracted_name = webscraping.extract_full_name(page_url)
                if extracted_name: # Usa o nome extraído se a extração for bem-sucedida
                    full_name = extracted_name
    except Exception as e:
        print(f"Erro ao obter nome completo para '{search_term}': {e}")
        # Não define full_name aqui para que o fallback abaixo seja usado

    # Fallback final para o termo de busca se nenhum nome foi encontrado
    if not full_name:
        full_name = search_term

    return full_name


def _display_person_info(person_data):
    """Exibe as informações da pessoa no console."""
    clear_console()
    print()
    print(f"Nome Completo: {person_data['Nome Completo']}")
    if person_data["Origem/Nacionalidade"] != "Não Informado":
        print(f"Origem/Nacionalidade: {person_data['Origem/Nacionalidade']}")
    print(f"Data de Nascimento: {person_data['Data de Nascimento']}")
    print(f"Local de Nascimento: {person_data['Local de Nascimento']}")
    print(f"Data de Falecimento: {person_data['Data de Falecimento']}")
    print(f"Local de Falecimento: {person_data['Local de Falecimento']}")
    print(f"Século: {person_data['Século']}")
    print("Finalizando...")
