from urllib import parse

import requests
from bs4 import BeautifulSoup

WIKIPEDIA_URL = "https://pt.wikipedia.org/"


# Função para corrigir o termo buscado, através de webscraping na página de pesquisa da wikipedia,
# para garantir que seja encontrado o artigo correto.
def get_correct_search_term(search_term):
    corrected_search_term = None
    # encoded_search_term = urllib.parse.quote_plus(search_term)
    encoded_search_term = parse.quote_plus(search_term)
    base_wikipedia_url = WIKIPEDIA_URL
    wikipedia_search_url = (
        base_wikipedia_url
        + "w/index.php?search={}&title=Especial:Pesquisar&profile=advanced&"
        "fulltext=1&ns0=1".format(encoded_search_term)
    )
    page = requests.get(wikipedia_search_url)
    soup = BeautifulSoup(page.content, "html.parser")

    # correção palavra errada (você quis dizer)
    if soup.find_all("div", class_="searchdidyoumean"):
        for data in soup.find_all("div", class_="searchdidyoumean"):
            for a in data.find_all("a"):
                link = a.get("href")
                corrected_search = requests.get(base_wikipedia_url + link)
                soup_correct_search = BeautifulSoup(
                    corrected_search.content, "html.parser"
                )
                corrected_search_term = (
                    soup_correct_search.find("div", class_="mw-search-result-heading")
                    .find("a")
                    .text
                )
                break
            break
        return corrected_search_term

    # palavra certa
    if soup.find("div", class_="mw-search-result-heading"):
        corrected_search_term = soup.find(
            "div", class_="mw-search-result-heading"
        ).text.strip()
        return corrected_search_term
    print("Artigo não encontrado na wikipedia")
    # retrieve_information(corrected_search_term, False)
    # info_gathering.retrieve_information(corrected_search_term, False)
    return


# Função para obter o nome completo, caso não consiga utilizar a wptools.
def extract_full_name(page_url):
    global full_name
    request_page = requests.get(page_url)
    soup = BeautifulSoup(request_page.text, "html.parser")

    for table in soup.find_all("table"):
        table.decompose()

    if soup.find("div", class_="hatnote"):
        soup.find("div", class_="hatnote").decompose()

    if soup.find("p", class_="mw-empty-elt"):
        soup.find("p", class_="mw-empty-elt").decompose()

    for div in soup.find_all("div", class_="mw-parser-output"):
        if div.find("p") and div.find("p").find("b"):
            full_name = div.find("p").find("b").text.replace(",", "").strip()
            break

    # full_name = soup.find(
    #     'div', attrs={'class': 'mw-parser-output'}).p.b.text.replace(",", "").strip()
    return full_name
