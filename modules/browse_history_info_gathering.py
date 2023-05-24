import wptools
from alphabet_detector import AlphabetDetector

alphabet_detector = AlphabetDetector()

from modules.webscraping_functions import extract_full_name
from modules.utils import calcula_seculo
from modules.wiki_functions import sparql_query_wikidata


def get_browse_history_person_info(wikipedia_history):
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

    # remove duplicates from person_info
    person_info = [dict(t) for t in {tuple(d.items()) for d in person_info}]
    return person_info
