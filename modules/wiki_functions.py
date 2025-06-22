import wptools
import wikipedia
from SPARQLWrapper import SPARQLWrapper, JSON, XML, POST, GET # Import POST and GET
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json # Para json.JSONDecodeError

# Configurações globais
SPARQL_USER_AGENT = "GeoHistWikipediaApp/1.0 (https://github.com/CainaDRP/GeoHist-Wikipedia; cainademorais@gmail.com)"
WIKIPEDIA_API_USER_AGENT = {"User-Agent": SPARQL_USER_AGENT}
WIKIPEDIA_LANG = "pt"

_wikidata_cache = {}
_summary_cache = {}
_sparql_cache = {}

def _requests_session_with_retries(retries=3, backoff_factor=0.5, status_forcelist=(500, 502, 503, 504)):
    session = requests.Session()
    retry_strategy = Retry(
        total=retries, read=retries, connect=retries,
        backoff_factor=backoff_factor, status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(WIKIPEDIA_API_USER_AGENT)
    return session

global_session = _requests_session_with_retries()

wikipedia.set_lang(WIKIPEDIA_LANG)
wikipedia.set_user_agent(SPARQL_USER_AGENT)


def search_wikidata(search_term):
    if search_term in _wikidata_cache:
        return _wikidata_cache[search_term]
    try:
        page = wptools.page(search_term, lang=WIKIPEDIA_LANG, silent=True, verbose=False, session=global_session)
        page.get_wikidata()
        _wikidata_cache[search_term] = page
        return page
    except LookupError:
        _wikidata_cache[search_term] = None
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro de rede ao buscar '{search_term}' com wptools: {e}")
        _wikidata_cache[search_term] = None
        return None
    except Exception as e:
        print(f"Erro inesperado ao buscar '{search_term}' com wptools: {e}")
        _wikidata_cache[search_term] = None
        return None

def get_summary(search_term, sentences=5):
    cache_key = (search_term, sentences)
    if cache_key in _summary_cache:
        return _summary_cache[cache_key]
    try:
        summary = wikipedia.summary(search_term, sentences=sentences)
        _summary_cache[cache_key] = summary
        return summary
    except wikipedia.exceptions.PageError:
        _summary_cache[cache_key] = "Resumo não disponível (página não encontrada)."
        return _summary_cache[cache_key]
    except wikipedia.exceptions.DisambiguationError as e:
        summary_text = f"Termo ambíguo. Opções: {', '.join(e.options[:3])}..." if e.options else "Termo ambíguo, resumo não disponível."
        _summary_cache[cache_key] = summary_text
        return summary_text
    except requests.exceptions.RequestException as e:
        print(f"Erro de rede ao obter resumo para '{search_term}': {e}")
        _summary_cache[cache_key] = "Resumo não disponível (erro de rede)."
        return _summary_cache[cache_key]
    except Exception as e:
        print(f"Erro inesperado ao obter resumo para '{search_term}': {e}")
        _summary_cache[cache_key] = "Resumo não disponível (erro inesperado)."
        return _summary_cache[cache_key]

def sparql_query_wikidata(person_name, retries=2, delay_base=1, timeout=20):
    if person_name in _sparql_cache:
        return _sparql_cache[person_name]

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent=SPARQL_USER_AGENT)
    sparql.setTimeout(timeout)
    sparql.setReturnFormat(JSON)
    sparql.setMethod(POST)

    # Query SPARQL original restaurada
    query = """
    SELECT ?personLabel ?birthDate ?birthPlaceLabel ?deathDate ?deathPlaceLabel ?countryLabel ?image ?coord WHERE {
      ?person rdfs:label "%s"@pt. # Busca pelo nome em português
      ?person wdt:P31 wd:Q5. # Garante que é uma instância de ser humano (Q5)
      OPTIONAL { ?person wdt:P569 ?birthDate. } # Data de nascimento
      OPTIONAL {
          ?person wdt:P19 ?birthPlace. # Local de nascimento (entidade)
          OPTIONAL {?birthPlace rdfs:label ?birthPlaceLabel. FILTER(LANG(?birthPlaceLabel) = "pt") } # Label em PT
      }
      OPTIONAL { ?person wdt:P570 ?deathDate. } # Data de falecimento
      OPTIONAL {
          ?person wdt:P20 ?deathPlace. # Local de falecimento (entidade)
          OPTIONAL {?deathPlace rdfs:label ?deathPlaceLabel. FILTER(LANG(?deathPlaceLabel) = "pt") }
      }
      OPTIONAL {
          ?person wdt:P27 ?country. # País de cidadania (entidade)
          OPTIONAL {?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "pt") }
      }
      OPTIONAL { ?person wdt:P18 ?image. } # Imagem
      OPTIONAL { ?birthPlace wdt:P625 ?coord. } # Coordenadas do local de nascimento
    }
    LIMIT 1
    """ % person_name.replace('"', '\\"')

    sparql.setQuery(query)
    # print(f"DEBUG: Executando query SPARQL para '{person_name}' (Query Restaurada)")

    for attempt in range(retries):
        try:
            # print(f"DEBUG: Tentativa {attempt + 1} para '{person_name}'")
            results = sparql.queryAndConvert()
            # print(f"DEBUG: Resultados convertidos para '{person_name}'.")

            if results["results"]["bindings"]:
                binding = results["results"]["bindings"][0]
                # print(f"DEBUG: Bindings encontrados para '{person_name}'.")

                def get_value(data_dict, key, default="Não Informado"):
                    if key in data_dict and data_dict[key] is not None and data_dict[key].get("value") is not None:
                        return data_dict[key]["value"]
                    return default

                data_nascimento_raw = get_value(binding, "birthDate")
                data_nascimento = data_nascimento_raw.split("T")[0] if data_nascimento_raw != "Não Informado" else "Não Informado"

                local_nascimento = get_value(binding, "birthPlaceLabel")
                data_falecimento_raw = get_value(binding, "deathDate")
                data_falecimento = data_falecimento_raw.split("T")[0] if data_falecimento_raw != "Não Informado" else "Não Informado"
                local_falecimento = get_value(binding, "deathPlaceLabel")
                pais_origem = get_value(binding, "countryLabel")
                imagem_url = get_value(binding, "image")

                latitude, longitude = "Não Informado", "Não Informado"
                coord_val = get_value(binding, "coord")
                if coord_val != "Não Informado" and coord_val is not None:
                    try:
                        lon_lat_str = coord_val.replace("Point(", "").replace(")", "").split()
                        if len(lon_lat_str) == 2:
                            longitude = lon_lat_str[0]
                            latitude = lon_lat_str[1]
                    except Exception as coord_e:
                        print(f"DEBUG: Formato de coordenadas inesperado para {person_name}: '{coord_val}'. Erro: {coord_e}")

                result_data = {
                    "Nome": get_value(binding, "personLabel", person_name),
                    "Data de Nascimento": data_nascimento,
                    "Local de Nascimento": local_nascimento,
                    "Data de Falecimento": data_falecimento,
                    "Local de Falecimento": local_falecimento,
                    "País": pais_origem,
                    "Imagem": imagem_url,
                    "Latitude": latitude,
                    "Longitude": longitude
                }
                _sparql_cache[person_name] = result_data
                # print(f"DEBUG: Dados SPARQL processados com sucesso para {person_name}.")
                return result_data
            else:
                # print(f"DEBUG: SPARQL: Nenhum resultado ('bindings') encontrado para {person_name}.")
                _sparql_cache[person_name] = None
                return None
        except json.JSONDecodeError as json_e: # Erro específico de decodificação JSON
            print(f"CRITICAL: JSONDecodeError para '{person_name}' (tentativa {attempt + 1}/{retries}): {json_e}. Query: {query}")
            if attempt < retries - 1:
                print(f"DEBUG: Aguardando {delay_base * (2 ** attempt)}s antes da próxima tentativa para '{person_name}'.")
                time.sleep(delay_base * (2 ** attempt))
            else:
                print(f"CRITICAL: Falha final de JSONDecodeError para '{person_name}' após {retries} tentativas.")
                _sparql_cache[person_name] = None # Cacheia a falha
                return None
        except Exception as e: # Outros erros (rede, timeout, etc.)
            print(f"CRITICAL: Erro Inesperado na query SPARQL para '{person_name}' (tentativa {attempt + 1}/{retries}): {type(e).__name__} - {e}. Query: {query}")
            if attempt < retries - 1:
                print(f"DEBUG: Aguardando {delay_base * (2 ** attempt)}s antes da próxima tentativa para '{person_name}'.")
                time.sleep(delay_base * (2 ** attempt))
            else:
                print(f"CRITICAL: Falha final de query SPARQL para '{person_name}' após {retries} tentativas.")
                _sparql_cache[person_name] = None # Cacheia a falha
                return None
    _sparql_cache[person_name] = None
    return None
