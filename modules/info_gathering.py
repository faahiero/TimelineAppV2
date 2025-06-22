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
def fetch_data(search_term): # Removido is_correct_term
    FILE_NAME = "person_info.csv"
    # A variável global attempts e a lógica de input foram removidas daqui.
    # A responsabilidade de pedir o search_term e de novas tentativas (se houver)
    # agora é da função chamadora (em main.py).

    if not search_term or search_term.strip() == "":
        print("Termo de busca não pode ser vazio.")
        return

    clear_console()
    print(f"Processando busca por: {search_term}...") # Mensagem inicial

    # Chamada da função que tenta corrigir o termo de busca,
    # para garantir que o termo exista na wikipedia.
    # A função get_correct_search_term já imprime "Buscando termo..." etc.
    corrected_search_term = webscraping.get_correct_search_term(search_term)
    if not corrected_search_term: # Se for None ou vazio
        # A função get_correct_search_term já deve ter informado o usuário sobre a falha.
        # Adiciona uma pequena pausa se a função interna não o fizer.
        # time.sleep(2)
        return

    # Usa o termo original para feedback ao usuário, mas o corrigido para buscas.
    print(f"Termo original: {search_term} | Termo corrigido para busca: {corrected_search_term}")

    page = _get_wikidata_page(corrected_search_term)
    if page is None:
        # _get_wikidata_page já imprime o erro.
        return

    if not _is_person(page):
        print(f"'{corrected_search_term}' não parece ser uma pessoa. Tente novamente com um nome diferente ou mais específico.")
        # time.sleep(3) # Pausa para o usuário ler
        return

    print(f"Obtendo informações detalhadas para: {corrected_search_term}...")
    sparql_query_data = sparql_query_wikidata(corrected_search_term)
    if sparql_query_data is None:
        print(f"Não foi possível obter informações detalhadas (SPARQL) para '{corrected_search_term}'.")
        # time.sleep(3)
        return

    summary = get_summary(corrected_search_term) # Usar termo corrigido para resumo também
    clear_console()
    print(f"--- Resumo para: {corrected_search_term} ---")
    print(summary if summary else "Nenhum resumo disponível.")
    print("------------------------------------")

    # A lógica de confirmação e _handle_incorrect_information foi simplificada.
    # Se a busca chegou até aqui, assume-se que o usuário quer os dados.
    # Confirmações mais complexas ou novas tentativas seriam melhor gerenciadas no main loop.
    if not _confirm_information(f"Os dados encontrados para '{corrected_search_term}' parecem corretos?"):
        print("Busca cancelada pelo usuário ou informação considerada incorreta.")
        # Não chama _handle_incorrect_information para evitar recursão complexa aqui.
        # O usuário pode simplesmente tentar uma nova busca no menu principal.
        # global attempts # Se attempts for removido, esta linha também.
        # attempts = 0 # Reseta tentativas se for mantido para outros propósitos.
        return

    # Passa o termo de busca original para _extract_person_data para que seja salvo no CSV.
    person_data = _extract_person_data(page, sparql_query_data, search_term, corrected_search_term)
    if person_data: # Verifica se a extração foi bem-sucedida
        write_to_csv(person_data, FILE_NAME) # write_to_csv lida com duplicatas
        _display_person_info(person_data)
        print(f"\nDados para '{person_data['Nome Completo']}' salvos em '{FILE_NAME}'.")
    else:
        print(f"Não foi possível extrair e salvar dados para '{search_term}'.")


    # time.sleep(4) # Pausa antes de limpar o console é agora gerenciada no main.py
    # clear_console()


def _get_wikidata_page(search_term):
    """Busca o termo na Wikidata e retorna a página."""
    # search_wikidata já tem tratamento de erro e cache.
    return search_wikidata(search_term)


def _is_person(page):
    """Verifica se a página da Wikidata se refere a uma pessoa."""
    if not page:
        return False
    try:
        get_wiki_data = page.get_wikidata() # Isso pode fazer uma chamada de rede se não estiver em cache
        if not get_wiki_data or not hasattr(get_wiki_data, 'data') or 'labels' not in get_wiki_data.data:
            # print(f"Não foi possível obter dados da Wikidata ou labels para a página.") # Log interno
            return False
        wikidata_labels = get_wiki_data.data["labels"]
        return "Q5" in wikidata_labels  # Q5 é o item do Wikidata para "ser humano"
    except Exception as e:
        print(f"Erro ao verificar se a página é de uma pessoa: {e}")
        return False


def _confirm_information(prompt_message="A informação está correta? (s/n): "):
    """Pergunta ao usuário se a informação está correta com uma mensagem customizável."""
    while True:
        print()
        user_option = input(f"{prompt_message} ").strip().lower()
        if user_option in ["s", "sim"]:
            return True
        elif user_option in ["n", "nao", "não"]:
            return False
        else:
            print("Resposta inválida. Por favor, responda com 's' (sim) ou 'n' (não).")


# _handle_incorrect_information foi removido pois sua lógica de repetição de fetch_data
# não se encaixa bem com a remoção do input de dentro de fetch_data.
# A repetição de busca deve ser gerenciada no loop principal.
# global attempts # Removido, pois era usado principalmente por _handle_incorrect_information
# attempts = 0


def _extract_person_data(page, sparql_query_data, original_search_term, corrected_search_term):
    """Extrai os dados da pessoa da página da Wikidata e dos dados SPARQL."""
    try:
        get_wiki_data = page.get_wikidata() # Pode ser repetido se _is_person não cacheou, mas wptools pode ter cache interno.
        wiki_data = get_wiki_data.data.get("wikidata", {})

        # Tenta obter a URL da página do objeto page, se não, constrói a partir do termo corrigido.
        page_url_from_restbase = page.get_restbase().data.get("url") if hasattr(page, 'get_restbase') else None
        page_url = page_url_from_restbase if page_url_from_restbase else f"https://pt.wikipedia.org/wiki/{corrected_search_term.replace(' ', '_')}"

        # Usa o termo corrigido para buscar o nome completo, mas o original para o campo "Termo Buscado"
        full_name = _get_full_name(wiki_data, page_url, corrected_search_term)

        data_nascimento = sparql_query_data.get("Data de Nascimento", "Não Informado")
        seculo = calcula_seculo(data_nascimento) if data_nascimento != "Não Informado" else "Não Informado"

        return {
            "Termo Buscado": original_search_term, # Salva o termo original do usuário
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
        print(f"Erro ao extrair dados da pessoa para '{original_search_term}': {e}")
        return None # Retorna None para indicar falha na extração


def _get_full_name(wiki_data, page_url, search_term_for_extraction): # Mudado para search_term_for_extraction
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
