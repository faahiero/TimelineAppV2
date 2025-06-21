# GeoHist Wikipedia

GeoHist Wikipedia é uma aplicação de console em Python que permite aos usuários buscar informações sobre personalidades históricas na Wikipedia, extrair dados relevantes como datas e locais de nascimento/falecimento, e gerar visualizações geográficas e temporais desses dados.

## Funcionalidades

- **Busca de Personalidades**: Permite ao usuário digitar o nome de uma personalidade para buscar informações na Wikipedia.
- **Extração de Dados**: Coleta informações como nome completo, nacionalidade, datas e locais de nascimento e falecimento, século, coordenadas geográficas e URL da imagem.
- **Visualização de Dados**:
    - Gera um mapa interativo (usando Dash e Dash Leaflet) mostrando a localização geográfica das personalidades.
    - Apresenta gráficos de barras e de dispersão para analisar a distribuição das personalidades por século e nacionalidade.
- **Visualização do Histórico de Navegação**: Analisa o histórico dos navegadores instalados, identifica buscas por personalidades na Wikipedia e gera uma visualização similar com esses dados.
- **Gerenciamento de Sessões**:
    - Permite salvar os dados de uma busca atual como uma sessão nomeada (em formatos CSV e JSON).
    - Permite carregar sessões salvas anteriormente para visualização.
- **Interface de Console Interativa**: Menu de fácil navegação para acessar as funcionalidades.

## Como Usar

### Pré-requisitos

- Python 3.x
- As dependências listadas no arquivo `requirements.txt`.

### Instalação

1.  Clone o repositório:
    ```bash
    git clone <url_do_repositorio>
    cd GeoHist-Wikipedia
    ```
2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
    Pode ser necessário instalar dependências de sistema listadas em `requirements.txt` (como `libcurl4-openssl-dev` em sistemas baseados em Debian/Ubuntu) usando o gerenciador de pacotes do seu sistema (ex: `sudo apt-get install curl libcurl4-openssl-dev`).

### Execução

Para iniciar a aplicação, execute o arquivo `main.py`:

```bash
python main.py
```

Siga as instruções apresentadas no menu do console:

-   **[1] Buscar nova personalidade**: Insira o nome de uma personalidade para buscar e salvar seus dados. Os dados são salvos em `person_info.csv`.
-   **[2] Gerar visualização (dados da busca atual)**: Gera e abre no navegador uma visualização baseada nos dados do arquivo `person_info.csv`.
-   **[3] Gerar visualização (histórico de navegação)**: Analisa o histórico do navegador, coleta dados de personalidades encontradas e gera uma visualização. Os dados são salvos em `browser_history_person_info.csv`.
-   **[4] Salvar dados da busca atual como sessão**: Permite nomear e salvar os dados de `person_info.csv` em `data/sessions/` como arquivos CSV e JSON.
-   **[5] Carregar sessão e gerar visualização**: Lista as sessões salvas em `data/sessions/` e permite carregar uma para visualização.
-   **[0] Encerrar programa**: Fecha a aplicação.

Os arquivos de dados gerados (CSV, JSON, mapas HTML) são armazenados no diretório `data/` e `data/sessions/`.

## Estrutura do Projeto

```
.
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Lista de dependências Python e de sistema
├── modules/                # Contém os módulos da aplicação
│   ├── __init__.py
│   ├── info_gathering.py   # Lógica para buscar e processar dados de personalidades
│   ├── vis_functions.py    # Funções para gerar as visualizações com Dash
│   ├── wiki_functions.py   # Funções de interação com a API da Wikipedia e Wikidata (SPARQL)
│   ├── webscraping_functions.py # Funções para extrair dados de páginas web
│   ├── browse_history_info_gathering.py # Lógica para coletar dados do histórico
│   ├── utils.py            # Funções utilitárias (menu, limpeza de console, CSV, etc.)
│   ├── plot_components/    # Componentes reutilizáveis para os plots Dash
│   └── plots/              # Lógica específica para os diferentes tipos de gráficos
├── data/                   # Diretório para armazenar dados gerados (CSVs, mapas HTML)
│   └── sessions/           # Diretório para armazenar sessões salvas
└── tests/                  # Testes unitários
    └── test_utils.py
```

## Principais Tecnologias e Bibliotecas Usadas

-   **Python**: Linguagem de programação principal.
-   **Requests**: Para realizar requisições HTTP.
-   **Beautiful Soup (bs4)**: Para parsing de HTML (web scraping).
-   **Wikipedia**: Wrapper para a API da Wikipedia.
-   **Wptools**: Para interagir com MediaWiki (usado para Wikidata).
-   **SPARQLWrapper**: Para realizar consultas SPARQL na Wikidata.
-   **Pandas**: Para manipulação e análise de dados.
-   **Dash / Plotly**: Para criar as visualizações interativas baseadas na web.
-   **Dash Leaflet**: Para integrar mapas Leaflet em aplicações Dash.
-   **Folium**: (Implicitamente usado ou anteriormente usado para mapas, Dash Leaflet é o principal agora).
-   **Browser-history**: Para acessar o histórico de navegação.
-   **Art**: Para gerar o banner em arte ASCII no console.
-   **Alphabet-detector**: Para detectar o alfabeto de strings (usado para nomes).

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes (Nota: Arquivo LICENSE não fornecido no contexto original, adicione se necessário).
