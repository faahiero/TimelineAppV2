import wptools
import wikipedia
from SPARQLWrapper import SPARQLWrapper, JSON
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry # Corrigido o import do Retry

# Configurações globais para SPARQLWrapper e requests
SPARQL_USER_AGENT = "GeoHistWikipediaApp/1.0 (https://github.com/CainaDRP/GeoHist-Wikipedia; cainademorais@gmail.com)"
WIKIPEDIA_API_USER_AGENT = {"User-Agent": SPARQL_USER_AGENT}
WIKIPEDIA_LANG = "pt"

# Cache simples em memória para evitar buscas repetidas na mesma sessão
_wikidata_cache = {}
_summary_cache = {}
_sparql_cache = {}

def _requests_session_with_retries(retries=3, backoff_factor=0.5, status_forcelist=(500, 502, 503, 504)):
    """Cria uma sessão de requests com retentativas configuradas."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "POST"], # Adicionado POST para SPARQLWrapper se necessário
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(WIKIPEDIA_API_USER_AGENT)
    return session

# Sessão global para ser usada por wptools e outras chamadas HTTP diretas, se aplicável.
global_session = _requests_session_with_retries()

# Configura a biblioteca wikipedia para usar o User-Agent globalmente.
# A lib wikipedia não suporta passar uma sessão diretamente para suas funções principais.
wikipedia.set_lang(WIKIPEDIA_LANG)
wikipedia.set_user_agent(SPARQL_USER_AGENT)


def search_wikidata(search_term):
    """Busca um termo na Wikidata usando wptools, com cache e sessão global de requests."""
    if search_term in _wikidata_cache:
        return _wikidata_cache[search_term]

    try:
        # wptools pode usar a sessão passada para `page.get_query()`, mas não para `page.get_wikidata()` diretamente.
        # O User-Agent configurado na sessão global deve ser usado por wptools se ele usar `requests.get` ou `session.get`.
        page = wptools.page(search_term, lang=WIKIPEDIA_LANG, silent=True, verbose=False, session=global_session)
        page.get_wikidata() # Esta chamada faz a requisição principal.
        _wikidata_cache[search_term] = page
        return page
    except LookupError:
        # print(f"Termo '{search_term}' não encontrado na Wikipedia em português via wptools.")
        _wikidata_cache[search_term] = None
        return None
    except requests.exceptions.RequestException as e: # Captura erros de request
        print(f"Erro de rede ao buscar '{search_term}' com wptools: {e}")
        _wikidata_cache[search_term] = None
        return None
    except Exception as e: # Outras exceções
        print(f"Erro inesperado ao buscar '{search_term}' com wptools: {e}")
        _wikidata_cache[search_term] = None
        return None

def get_summary(search_term, sentences=5):
    """Obtém um resumo do artigo da Wikipedia, com cache."""
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


def sparql_query_wikidata(person_name, retries=2, delay_base=1, timeout=15):
    """Realiza uma consulta SPARQL na Wikidata, com cache, retentativas exponenciais e timeout."""
    if person_name in _sparql_cache:
        return _sparql_cache[person_name]

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent=SPARQL_USER_AGENT)
    sparql.setTimeout(timeout)
    sparql.setReturnFormat(JSON)
    sparql.setMethod('POST') # POST é geralmente mais robusto para queries SPARQL

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
      # SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,[AUTO_LANGUAGE],en". } # Para obter labels automaticamente (já está implícito com rdfs:label)
    }
    LIMIT 1
    """ % person_name.replace('"', '\\"') # Escapa aspas no nome para a query

    for attempt in range(retries):
        try:
            results = sparql.queryAndConvert()
            if results["results"]["bindings"]:
                binding = results["results"]["bindings"][0]

                # Função auxiliar para obter valor ou "Não Informado", tratando ausência de 'value'
                def get_value(data_dict, key, default="Não Informado"):
                    if key in data_dict and data_dict[key]["value"]:
                        return data_dict[key]["value"]
                    return default

                data_nascimento = get_value(binding, "birthDate").split("T")[0] if get_value(binding, "birthDate") != "Não Informado" else "Não Informado"
                local_nascimento = get_value(binding, "birthPlaceLabel", get_value(binding, "birthPlace", "Não Informado"))
                data_falecimento = get_value(binding, "deathDate").split("T")[0] if get_value(binding, "deathDate") != "Não Informado" else "Não Informado"
                local_falecimento = get_value(binding, "deathPlaceLabel", get_value(binding, "deathPlace", "Não Informado"))
                pais_origem = get_value(binding, "countryLabel", get_value(binding, "country", "Não Informado"))
                imagem_url = get_value(binding, "image")

                latitude, longitude = "Não Informado", "Não Informado"
                coord_val = get_value(binding, "coord")
                if coord_val != "Não Informado":
                    try:
                        # Formato "Point(Longitude Latitude)"
                        lon_lat_str = coord_val.replace("Point(", "").replace(")", "").split()
                        if len(lon_lat_str) == 2:
                            longitude = lon_lat_str[0]
                            latitude = lon_lat_str[1]
                    except Exception:
                        print(f"Formato de coordenadas inesperado para {person_name}: {coord_val}")

                result_data = {
                    "Nome": person_name, "Data de Nascimento": data_nascimento,
                    "Local de Nascimento": local_nascimento, "Data de Falecimento": data_falecimento,
                    "Local de Falecimento": local_falecimento, "País": pais_origem,
                    "Imagem": imagem_url, "Latitude": latitude, "Longitude": longitude
                }
                _sparql_cache[person_name] = result_data
                return result_data
            else:
                # print(f"SPARQL: Nenhum resultado para {person_name} na tentativa {attempt + 1}.")
                _sparql_cache[person_name] = None
                return None # Retorna None se não encontrar resultados para evitar mais tentativas desnecessárias
        except Exception as e: # Captura erros de rede, timeout, JSON parsing, etc.
            print(f"Erro na consulta SPARQL para '{person_name}' (tentativa {attempt + 1}/{retries}): {type(e).__name__} - {e}")
            if attempt < retries - 1:
                current_delay = delay_base * (2 ** attempt) # Backoff exponencial
                # print(f"Aguardando {current_delay}s antes da próxima tentativa...")
                time.sleep(current_delay)
            else:
                print(f"Falha final ao obter dados SPARQL para '{person_name}' após {retries} tentativas.")
                _sparql_cache[person_name] = None # Cacheia a falha
                return None
    _sparql_cache[person_name] = None # Caso o loop termine sem sucesso (improvável com retries>0)
    return None
