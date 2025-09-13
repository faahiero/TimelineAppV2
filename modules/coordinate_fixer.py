"""
Módulo para corrigir coordenadas ausentes nos dados existentes
"""
import pandas as pd
import os
from modules.wiki_functions import sparql_query_wikidata

def fix_missing_coordinates(csv_file="person_info.csv"):
    """Corrige coordenadas ausentes no arquivo CSV"""
    if not os.path.exists(csv_file):
        print(f"Arquivo {csv_file} não encontrado.")
        return
    
    # Lê o CSV
    df = pd.read_csv(csv_file)
    
    # Identifica linhas com coordenadas ausentes
    missing_coords = df[
        (df['Latitude'] == 'Não Informado') | 
        (df['Longitude'] == 'Não Informado') |
        (df['Latitude'].isna()) | 
        (df['Longitude'].isna())
    ]
    
    if missing_coords.empty:
        print("Todas as coordenadas já estão preenchidas.")
        return
    
    print(f"Encontradas {len(missing_coords)} personalidades sem coordenadas:")
    
    updated_count = 0
    for idx, row in missing_coords.iterrows():
        nome = row['Nome Completo']
        termo_buscado = row['Termo Buscado']
        
        print(f"Tentando obter coordenadas para: {nome}")
        
        # Tenta buscar dados atualizados
        sparql_data = sparql_query_wikidata(termo_buscado)
        
        if sparql_data and sparql_data.get('Latitude') != 'Não Informado' and sparql_data.get('Longitude') != 'Não Informado':
            # Atualiza as coordenadas no DataFrame
            df.at[idx, 'Latitude'] = sparql_data['Latitude']
            df.at[idx, 'Longitude'] = sparql_data['Longitude']
            
            print(f"✓ Coordenadas atualizadas para {nome}: {sparql_data['Latitude']}, {sparql_data['Longitude']}")
            updated_count += 1
        else:
            print(f"✗ Não foi possível obter coordenadas para {nome}")
    
    if updated_count > 0:
        # Salva o arquivo atualizado
        df.to_csv(csv_file, index=False)
        print(f"\n{updated_count} coordenadas foram atualizadas e salvas em {csv_file}")
    else:
        print("\nNenhuma coordenada foi atualizada.")

def add_default_coordinates_by_country(csv_file="person_info.csv"):
    """Adiciona coordenadas padrão baseadas no país quando não há coordenadas específicas"""
    if not os.path.exists(csv_file):
        print(f"Arquivo {csv_file} não encontrado.")
        return
    
    # Coordenadas das capitais dos países
    country_coords = {
        "Rússia": (55.7558, 37.6176),  # Moscou
        "Brasil": (-15.7942, -47.8822),  # Brasília
        "Estados Unidos": (38.9072, -77.0369),  # Washington DC
        "França": (48.8566, 2.3522),  # Paris
        "Reino Unido": (51.5074, -0.1278),  # Londres
        "Alemanha": (52.5200, 13.4050),  # Berlim
        "China": (39.9042, 116.4074),  # Pequim
        "Japão": (35.6762, 139.6503),  # Tóquio
        "Itália": (41.9028, 12.4964),  # Roma
        "Espanha": (40.4168, -3.7038),  # Madrid
        "Portugal": (38.7223, -9.1393),  # Lisboa
        "Argentina": (-34.6118, -58.3960),  # Buenos Aires
        "México": (19.4326, -99.1332),  # Cidade do México
        "Canadá": (45.4215, -75.6972),  # Ottawa
        "Austrália": (-35.2809, 149.1300),  # Canberra
        "Índia": (28.6139, 77.2090),  # Nova Delhi
        "Coreia do Sul": (37.5665, 126.9780),  # Seul
    }
    
    # Lê o CSV
    df = pd.read_csv(csv_file)
    
    # Identifica linhas com coordenadas ausentes
    missing_coords = df[
        (df['Latitude'] == 'Não Informado') | 
        (df['Longitude'] == 'Não Informado') |
        (df['Latitude'].isna()) | 
        (df['Longitude'].isna())
    ]
    
    if missing_coords.empty:
        print("Todas as coordenadas já estão preenchidas.")
        return
    
    updated_count = 0
    for idx, row in missing_coords.iterrows():
        pais = row['Origem/Nacionalidade']
        nome = row['Nome Completo']
        
        if pais in country_coords:
            lat, lon = country_coords[pais]
            df.at[idx, 'Latitude'] = lat
            df.at[idx, 'Longitude'] = lon
            print(f"✓ Coordenadas padrão adicionadas para {nome} ({pais}): {lat}, {lon}")
            updated_count += 1
        else:
            print(f"✗ País '{pais}' não encontrado na lista de coordenadas padrão para {nome}")
    
    if updated_count > 0:
        # Salva o arquivo atualizado
        df.to_csv(csv_file, index=False)
        print(f"\n{updated_count} coordenadas padrão foram adicionadas e salvas em {csv_file}")
    else:
        print("\nNenhuma coordenada padrão foi adicionada.")

if __name__ == "__main__":
    print("=== Correção de Coordenadas ===")
    print("1. Tentando obter coordenadas específicas via SPARQL...")
    fix_missing_coordinates()
    
    print("\n2. Adicionando coordenadas padrão por país...")
    add_default_coordinates_by_country()