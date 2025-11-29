import locale
import wptools
import wikipedia as wiki
from datetime import datetime
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import unquote

wiki.set_lang('pt')
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


# Função que utiliza a biblioteca SPARQLWrapper para fazer a consulta no wikidata. Ao final da execução,
# ela monta um objeto, retornado para a função get_info_person sendo utilizado gerar um arquivo csv.
def sparql_query_wikidata(term_to_query, wikidata_id=None):
    import time
    endpoint_url = WIKIDATA_SPARQL_ENDPOINT

    # Se tivermos o ID, a busca é direta e instantânea
    if wikidata_id:
        query_filter = f"BIND(wd:{wikidata_id} AS ?item)"
    else:
        # Fallback para busca por nome (mais lenta e sujeita a timeout)
        query_filter = """
        {{ ?item rdfs:label ?label . FILTER(LCASE(STR(?label)) = LCASE("{term_to_query}")) }}
        UNION
        {{ ?item skos:altLabel ?alias . FILTER(LCASE(STR(?alias)) = LCASE("{term_to_query}")) }}
        """.format(term_to_query=term_to_query)

    # Query otimizada com OPTIONALs
    query = """
    SELECT DISTINCT ?item ?itemLabel ?imagem ?dataNascimento ?localNascimento ?localNascimentoLabel ?dataFalecimento ?localFalecimento 
           ?localFalecimentoLabel ?pais ?paisLabel ?geo
      WHERE {{
        {query_filter}
        ?item wdt:P31 wd:Q5 .
        
        OPTIONAL {{ ?item wdt:P569 ?dataNascimento . }}
        OPTIONAL {{ ?item wdt:P19 ?localNascimento . 
            OPTIONAL {{ ?localNascimento wdt:P17 ?pais . }}
            OPTIONAL {{ ?localNascimento wdt:P625 ?geo . }}
        }}
        OPTIONAL {{ ?item wdt:P18 ?imagem . }}
        OPTIONAL {{ ?item wdt:P570 ?dataFalecimento . }}
        OPTIONAL {{ ?item wdt:P20 ?localFalecimento . }}
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "pt,en" }}
    }} LIMIT 1
    """.format(query_filter=query_filter)
    
    # User-Agent em conformidade com a política da Wikimedia
    user_agent = "TimelineApp/1.0 (fabriciosilvalp@outlook.com) based on SPARQLWrapper"

    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    query_results = None
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            results_raw = sparql.query().convert()
            query_results = results_raw['results']['bindings']
            break # Sucesso
        except Exception as e:
            error_msg = str(e)
            if '429' in error_msg:
                print(f"Rate limit (429) atingido. Aguardando 2s... (Tentativa {attempt+1}/{max_retries})")
                time.sleep(2)
            elif '504' in error_msg:
                print(f"Gateway Timeout (504). Tentando novamente em 5s... (Tentativa {attempt+1}/{max_retries})")
                time.sleep(5)
            else:
                print(f"Erro na consulta SPARQL: {e}")
                return None

    if not query_results:
        return None

    result = query_results[0]
    
    # Helper para extrair valor com segurança
    def get_val(key):
        return result[key]["value"] if key in result else None

    # Imagem
    imagem = get_val("imagem") or 'Sem Imagem'

    # País
    pais = get_val("paisLabel") or '-'

    # Data de Nascimento
    raw_nascimento = get_val("dataNascimento")
    if raw_nascimento:
        if raw_nascimento.startswith('-'):
            # Tratamento AC
            try:
                ano_ac = int(raw_nascimento[1:5])
                data_nascimento = "{} a.C.".format(ano_ac)
            except:
                data_nascimento = raw_nascimento
        else:
            try:
                dt_obj = datetime.strptime(raw_nascimento, '%Y-%m-%dT%H:%M:%SZ')
                data_nascimento = dt_obj.strftime('%d de %B de %Y')
            except ValueError:
                data_nascimento = raw_nascimento
    else:
        data_nascimento = '-'

    # Data de Falecimento
    raw_falecimento = get_val("dataFalecimento")
    if raw_falecimento:
        if raw_falecimento.startswith('-'):
            try:
                ano_ac = int(raw_falecimento[1:5])
                data_falecimento = "{} a.C.".format(ano_ac)
            except:
                data_falecimento = raw_falecimento
        else:
            try:
                dt_obj = datetime.strptime(raw_falecimento, '%Y-%m-%dT%H:%M:%SZ')
                data_falecimento = dt_obj.strftime('%d de %B de %Y')
            except ValueError:
                data_falecimento = '-'
    else:
        data_falecimento = '-'

    # Locais
    local_nascimento = get_val("localNascimentoLabel") or '-'
    local_falecimento = get_val("localFalecimentoLabel") or '-'

    # Coordenadas
    raw_geo = get_val("geo")
    latitude = '0'
    longitude = '0'
    
    if raw_geo:
        # Formato Point(-46.6333 23.5505) -> remove "Point(" e ")"
        try:
            clean_geo = raw_geo.replace("Point(", "").replace(")", "")
            parts = clean_geo.split(' ')
            if len(parts) >= 2:
                # Wikidata retorna "LONG LAT" no WKT
                longitude = parts[0]
                latitude = parts[1]
        except:
            pass

    parsed_results = {
        'Imagem': imagem,
        'País': pais,
        'Data de Nascimento': data_nascimento,
        'Local de Nascimento': local_nascimento,
        'Data de Falecimento': data_falecimento,
        'Local de Falecimento': local_falecimento,
        'Latitude': latitude,
        'Longitude': longitude
    }

    return parsed_results


# Função que utiliza wptools para fazer uma busca na wikidata por um termo.
# Ela retorna uma instância na wikidata do item buscado caso ele exista,
# e com essa informação extraio a propriedade "nome de nascimento (P1477)"
# em funções mais abaixo. Caso não haja registro dessa propriedade, utilizo 
# Webscraping tradicional (BeautifulSoup, etc.) para obter o dado.
def search_wikidata(search_term):
    return wptools.page(search_term, lang='pt', silent=True, verbose=False)


# Aqui utilizo uma biblioteca auxiliar chamada wikipedia(importada como wiki),
# apenas para obter algumas linhas do sumário do artigo encontrado e mostrar
# na tela para confirmar a busca.
def get_summary(correct_search_term, sentences=2):
    return wiki.summary(correct_search_term, sentences=sentences)


def get_wikipedia_history(histories):
    wikipedia_history = []
    for dt, url in histories:
        if "wikipedia.org/wiki" in url:
            wikipedia_history.append(unquote(url.split("/")[-1]).replace("_", " "))
    return wikipedia_history
