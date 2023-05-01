import locale
import wptools
import wikipedia as wiki
from datetime import datetime
from SPARQLWrapper import SPARQLWrapper, JSON

wiki.set_lang('pt')
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


# Função que utiliza a biblioteca SPARQLWrapper para fazer a consulta no wikidata. Ao final da execução,
# ela monta um objeto, retornado para a função get_info_person sendo utilizado gerar um arquivo csv.
def sparql_query_wikidata(term_to_query):
    endpoint_url = WIKIDATA_SPARQL_ENDPOINT

    query = """
    SELECT ?item ?itemLabel ?imagem ?dataNascimento ?localNascimento ?localNascimentoLabel ?dataFalecimento ?localFalecimento 
           ?localFalecimentoLabel ?pais ?paisLabel ?geo
      WHERE {{
        ?item wdt:P31 wd:Q5 .
        ?item ?label "{term_to_query}"@pt .
        ?item wdt:P569 ?dataNascimento .
        ?item wdt:P19 ?localNascimento .
        ?localNascimento wdt:P17 ?pais .
        ?localNascimento wdt:P625 ?geo .
        OPTIONAL {{ ?item wdt:P18 ?imagem . }}
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

    if not query_results:
        return None

    # check if have imagem property in query
    if 'imagem' in query_results[0]:
        imagem = (query_results[0]["imagem"]["value"])
    else:
        imagem = 'Sem Imagem'

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
