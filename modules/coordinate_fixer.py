"""
Módulo para corrigir coordenadas ausentes nos dados existentes
"""
import os
from modules.wiki_functions import sparql_query_wikidata

def fix_missing_coordinates():
    """Corrige coordenadas ausentes via SQLite na sessão ativa"""
    from modules.data_adapter import data_adapter
    
    # Busca personalidades da sessão ativa
    active_session = data_adapter.active_saved_session or data_adapter.current_session
    personalities = data_adapter.db.get_session_personalities(active_session)
    
    if not personalities:
        print("Nenhuma personalidade encontrada na sessão ativa.")
        return
    
    # Identifica personalidades com coordenadas ausentes
    missing_coords = []
    for p in personalities:
        if (not p.get('latitude') or not p.get('longitude') or 
            p.get('latitude') == 'Não Informado' or p.get('longitude') == 'Não Informado'):
            missing_coords.append(p)
    
    if not missing_coords:
        print("Todas as coordenadas já estão preenchidas.")
        return
    
    print(f"Encontradas {len(missing_coords)} personalidades sem coordenadas:")
    
    updated_count = 0
    for person in missing_coords:
        nome = person.get('full_name', '')
        
        print(f"Tentando obter coordenadas para: {nome}")
        
        # Tenta buscar dados atualizados via SPARQL
        from modules.wiki_functions import sparql_query_wikidata
        sparql_data = sparql_query_wikidata(nome)
        
        if (sparql_data and 
            sparql_data.get('Latitude') != 'Não Informado' and 
            sparql_data.get('Longitude') != 'Não Informado'):
            
            # Atualiza as coordenadas no banco SQLite
            import sqlite3
            try:
                with sqlite3.connect(data_adapter.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE personalities 
                        SET latitude = ?, longitude = ? 
                        WHERE id = ?
                    """, (sparql_data['Latitude'], sparql_data['Longitude'], person['id']))
                    
                print(f"✓ Coordenadas atualizadas para {nome}: {sparql_data['Latitude']}, {sparql_data['Longitude']}")
                updated_count += 1
            except Exception as e:
                print(f"✗ Erro ao atualizar {nome}: {e}")
        else:
            print(f"✗ Não foi possível obter coordenadas para {nome}")
    
    if updated_count > 0:
        print(f"\n{updated_count} coordenadas foram atualizadas no banco de dados")
    else:
        print("\nNenhuma coordenada foi atualizada.")

def add_default_coordinates_by_country():
    """Adiciona coordenadas padrão baseadas no país via SQLite na sessão ativa"""
    from modules.data_adapter import data_adapter
    
    # Busca personalidades da sessão ativa
    active_session = data_adapter.active_saved_session or data_adapter.current_session
    personalities = data_adapter.db.get_session_personalities(active_session)
    
    if not personalities:
        print("Nenhuma personalidade encontrada na sessão ativa.")
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
    
    # Identifica personalidades com coordenadas ausentes
    missing_coords = []
    for p in personalities:
        if (not p.get('latitude') or not p.get('longitude') or 
            p.get('latitude') == 'Não Informado' or p.get('longitude') == 'Não Informado'):
            missing_coords.append(p)
    
    if not missing_coords:
        print("Todas as coordenadas já estão preenchidas.")
        return
    
    updated_count = 0
    for person in missing_coords:
        pais = person.get('country', '')
        nome = person.get('full_name', '')
        
        if pais in country_coords:
            lat, lon = country_coords[pais]
            
            # Atualiza no banco SQLite
            import sqlite3
            try:
                with sqlite3.connect(data_adapter.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE personalities 
                        SET latitude = ?, longitude = ? 
                        WHERE id = ?
                    """, (lat, lon, person['id']))
                    
                print(f"✓ Coordenadas padrão adicionadas para {nome} ({pais}): {lat}, {lon}")
                updated_count += 1
            except Exception as e:
                print(f"✗ Erro ao atualizar {nome}: {e}")
        else:
            print(f"✗ País '{pais}' não encontrado na lista de coordenadas padrão para {nome}")
    
    if updated_count > 0:
        print(f"\n{updated_count} coordenadas padrão foram adicionadas no banco de dados")
    else:
        print("\nNenhuma coordenada padrão foi adicionada.")

if __name__ == "__main__":
    print("=== Correção de Coordenadas ===")
    print("1. Tentando obter coordenadas específicas via SPARQL...")
    fix_missing_coordinates()
    
    print("\n2. Adicionando coordenadas padrão por país...")
    add_default_coordinates_by_country()