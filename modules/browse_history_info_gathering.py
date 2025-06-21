from alphabet_detector import AlphabetDetector
import wptools

from modules.utils import calcula_seculo
from modules.wiki_functions import sparql_query_wikidata
from modules.webscraping_functions import extract_full_name

alphabet_detector = AlphabetDetector()

def get_browse_history_person_info(entry):
    """
    Obtém informações de uma pessoa a partir de uma entrada do histórico de navegação (termo de busca da Wikipedia).
    Retorna um dicionário com as informações da pessoa ou None se não for uma pessoa ou se ocorrer um erro.
    """
    try:
        wiki_page = wptools.page(entry, lang="pt", silent=True, verbose=False)
        get_wikidata = wiki_page.get_wikidata()
    except LookupError:
        # print(f"Erro de lookup ao processar '{entry}'. Pulando.")
        return None
    except Exception as e:
        # print(f"Erro inesperado ao processar '{entry}' com wptools: {e}. Pulando.")
        return None

    wikidata_labels = get_wikidata.data.get("labels", {})
    if "Q5" not in wikidata_labels: # Q5 é o item do Wikidata para "ser humano"
        # print(f"'{entry}' não é uma pessoa. Pulando.")
        return None

    # print(f"'{entry}' é uma pessoa. Coletando dados...")
    page_url = get_wikidata.data.get("url")
    wiki_data = get_wikidata.data.get("wikidata", {})

    try:
        full_name = wiki_data.get("nome de nascimento (P1477)")
        if isinstance(full_name, list):
            full_name = ", ".join(full_name)

        # Se o nome não for latino (ex: russo, japonês), tenta extrair do HTML
        if full_name and not alphabet_detector.is_latin(str(full_name)):
            if page_url:
                extracted_name = extract_full_name(page_url)
                if extracted_name: # Usa o nome extraído se a extração for bem-sucedida
                    full_name = extracted_name
            # else: se não houver URL, não podemos extrair, então mantemos o nome não latino
                 # pass # full_name = full_name # (no change)
        elif not full_name and page_url: # Se não houver nome de nascimento e houver URL
             full_name = extract_full_name(page_url)

    except KeyError: # Caso P1477 não exista
        if page_url:
            full_name = extract_full_name(page_url)
        else:
            full_name = entry # Usa o termo de busca como fallback
    except Exception as e:
        # print(f"Erro ao processar nome para '{entry}': {e}")
        full_name = entry # Fallback em caso de outros erros

    if not full_name: # Garante que full_name não seja None ou vazio
        full_name = entry


    sparql_data = sparql_query_wikidata(entry)
    if not sparql_data:
        # print(f"Não foi possível obter dados SPARQL para '{entry}'. Pulando.")
        return None

    data_nascimento = sparql_data.get("Data de Nascimento", "Não Informado")
    seculo = calcula_seculo(data_nascimento) if data_nascimento != "Não Informado" else "Não Informado"

    return {
        "Termo Buscado": entry,
        "Nome Completo": full_name,
        "Origem/Nacionalidade": sparql_data.get("País", "Não Informado"),
        "Data de Nascimento": data_nascimento,
        "Local de Nascimento": sparql_data.get("Local de Nascimento", "Não Informado"),
        "Data de Falecimento": sparql_data.get("Data de Falecimento", "Não Informado"),
        "Local de Falecimento": sparql_data.get("Local de Falecimento", "Não Informado"),
        "Século": seculo,
        "Latitude": sparql_data.get("Latitude", "Não Informado"),
        "Longitude": sparql_data.get("Longitude", "Não Informado"),
        "Url": page_url if page_url else f"https://pt.wikipedia.org/wiki/{entry.replace(' ', '_')}",
        "Imagem": sparql_data.get("Imagem", "Não Informado"),
    }
