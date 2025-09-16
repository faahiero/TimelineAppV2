#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de banco de dados SQLite para o Wikipedia GeoHist
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd


class DatabaseManager:
    """Gerenciador principal do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "data/geohist.db"):
        self.db_path = db_path
        self._ensure_data_dir()
        self._init_database()
    
    def _ensure_data_dir(self):
        """Garante que o diretório data/ existe"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Tabela de personalidades
                CREATE TABLE IF NOT EXISTS personalities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_term TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    country TEXT,
                    birth_date TEXT,
                    birth_place TEXT,
                    death_date TEXT,
                    death_place TEXT,
                    century TEXT,
                    latitude REAL,
                    longitude REAL,
                    url TEXT,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(full_name, birth_date) -- Evita duplicatas
                );
                
                -- Tabela de sessões
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Tabela de relacionamento sessão-personalidade
                CREATE TABLE IF NOT EXISTS session_personalities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    personality_id INTEGER NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (personality_id) REFERENCES personalities(id) ON DELETE CASCADE,
                    UNIQUE(session_id, personality_id) -- Evita duplicatas na sessão
                );
                
                -- Índices para performance
                CREATE INDEX IF NOT EXISTS idx_personalities_country ON personalities(country);
                CREATE INDEX IF NOT EXISTS idx_personalities_century ON personalities(century);
                CREATE INDEX IF NOT EXISTS idx_personalities_search_term ON personalities(search_term);
                CREATE INDEX IF NOT EXISTS idx_sessions_name ON sessions(name);
                CREATE INDEX IF NOT EXISTS idx_session_personalities_session ON session_personalities(session_id);
            """)
    
    def find_existing_personality(self, search_term: Optional[str] = None, full_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Busca personalidade existente no banco com busca inteligente e variações"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if search_term:
                    # Busca por múltiplos critérios em ordem de relevância
                    search_queries = [
                        # 1. Busca exata no search_term
                        ("SELECT * FROM personalities WHERE LOWER(search_term) = LOWER(?) ORDER BY created_at DESC LIMIT 1", 
                         (search_term,)),
                        
                        # 2. Busca exata no full_name
                        ("SELECT * FROM personalities WHERE LOWER(full_name) = LOWER(?) ORDER BY created_at DESC LIMIT 1", 
                         (search_term,)),
                        
                        # 3. Busca parcial no full_name (contém o termo)
                        ("SELECT * FROM personalities WHERE LOWER(full_name) LIKE LOWER(?) ORDER BY created_at DESC LIMIT 1", 
                         (f"%{search_term}%",)),
                        
                        # 4. Busca parcial no search_term (contém o termo)
                        ("SELECT * FROM personalities WHERE LOWER(search_term) LIKE LOWER(?) ORDER BY created_at DESC LIMIT 1", 
                         (f"%{search_term}%",)),
                        
                        # 5. Busca por palavras individuais no full_name
                        ("SELECT * FROM personalities WHERE " + 
                         " AND ".join([f"LOWER(full_name) LIKE LOWER('%{word}%')" for word in search_term.split()]) + 
                         " ORDER BY created_at DESC LIMIT 1", 
                         ())
                    ]
                    
                    # Executa as buscas em ordem de prioridade
                    for query, params in search_queries:
                        cursor.execute(query, params)
                        row = cursor.fetchone()
                        if row:
                            return dict(row)
                            
                elif full_name:
                    cursor.execute("""
                        SELECT * FROM personalities 
                        WHERE LOWER(full_name) = LOWER(?)
                        ORDER BY created_at DESC LIMIT 1
                    """, (full_name,))
                    row = cursor.fetchone()
                    return dict(row) if row else None
                
                return None
                
        except sqlite3.Error as e:
            print(f"Erro ao buscar personalidade existente: {e}")
            return None

    def get_personality_by_id(self, personality_id: int) -> Optional[Dict[str, Any]]:
        """Busca personalidade pelo ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM personalities WHERE id = ?", (personality_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except sqlite3.Error as e:
            print(f"Erro ao buscar personalidade por ID {personality_id}: {e}")
            return None

    def add_personality(self, personality_data: Dict[str, Any]) -> Optional[int]:
        """Adiciona uma personalidade ao banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Mapeia os dados do CSV para o banco
                cursor.execute("""
                    INSERT OR IGNORE INTO personalities (
                        search_term, full_name, country, birth_date, birth_place,
                        death_date, death_place, century, latitude, longitude,
                        url, image_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    personality_data.get('Termo Buscado', ''),
                    personality_data.get('Nome Completo', ''),
                    personality_data.get('Origem/Nacionalidade', ''),
                    personality_data.get('Data de Nascimento', ''),
                    personality_data.get('Local de Nascimento', ''),
                    personality_data.get('Data de Falecimento', ''),
                    personality_data.get('Local de Falecimento', ''),
                    personality_data.get('Século', ''),
                    self._parse_coordinate(personality_data.get('Latitude')),
                    self._parse_coordinate(personality_data.get('Longitude')),
                    personality_data.get('Url', ''),
                    personality_data.get('Imagem', '')
                ))
                
                return cursor.lastrowid if cursor.rowcount > 0 else None
                
        except sqlite3.Error as e:
            print(f"Erro ao adicionar personalidade: {e}")
            return None
    
    def _parse_coordinate(self, coord_str: Any) -> Optional[float]:
        """Converte string de coordenada para float"""
        if not coord_str or coord_str == 'Não Informado':
            return None
        try:
            return float(str(coord_str).strip())
        except (ValueError, AttributeError):
            return None
    
    def get_personalities(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Recupera personalidades com filtros opcionais"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM personalities"
                params = []
                
                if filters:
                    conditions = []
                    if 'country' in filters:
                        conditions.append("country = ?")
                        params.append(filters['country'])
                    if 'century' in filters:
                        conditions.append("century = ?")
                        params.append(filters['century'])
                    if 'search_term' in filters:
                        conditions.append("search_term LIKE ?")
                        params.append(f"%{filters['search_term']}%")
                    
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            print(f"Erro ao recuperar personalidades: {e}")
            return []
    
    def create_session(self, name: str, description: str = "") -> Optional[int]:
        """Cria uma nova sessão"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (name, description) VALUES (?, ?)
                """, (name, description))
                return cursor.lastrowid
                
        except sqlite3.IntegrityError:
            print(f"Sessão '{name}' já existe")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao criar sessão: {e}")
            return None
    
    def add_to_session(self, session_name: str, personality_ids: List[int]) -> bool:
        """Adiciona personalidades a uma sessão"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Busca o ID da sessão
                cursor.execute("SELECT id FROM sessions WHERE name = ?", (session_name,))
                session_row = cursor.fetchone()
                if not session_row:
                    return False
                
                session_id = session_row[0]
                
                # Adiciona personalidades à sessão
                for personality_id in personality_ids:
                    cursor.execute("""
                        INSERT OR IGNORE INTO session_personalities (session_id, personality_id)
                        VALUES (?, ?)
                    """, (session_id, personality_id))
                
                # Atualiza timestamp da sessão
                cursor.execute("""
                    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (session_id,))
                
                return True
                
        except sqlite3.Error as e:
            print(f"Erro ao adicionar à sessão: {e}")
            return False
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """Recupera todas as sessões com contagem de personalidades"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        s.*,
                        COUNT(sp.personality_id) as personality_count,
                        COUNT(DISTINCT p.country) as country_count
                    FROM sessions s
                    LEFT JOIN session_personalities sp ON s.id = sp.session_id
                    LEFT JOIN personalities p ON sp.personality_id = p.id
                    GROUP BY s.id
                    ORDER BY s.updated_at DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            print(f"Erro ao recuperar sessões: {e}")
            return []
    
    def get_session_personalities(self, session_name: str) -> List[Dict[str, Any]]:
        """Recupera personalidades de uma sessão específica"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT p.*, sp.added_at
                    FROM personalities p
                    JOIN session_personalities sp ON p.id = sp.personality_id
                    JOIN sessions s ON sp.session_id = s.id
                    WHERE s.name = ?
                    ORDER BY sp.added_at DESC
                """, (session_name,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            print(f"Erro ao recuperar personalidades da sessão: {e}")
            return []
    
    def delete_session(self, session_name: str) -> bool:
        """Remove uma sessão e seus relacionamentos (com CASCADE DELETE)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # IMPORTANTE: Habilita foreign keys para CASCADE DELETE funcionar
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sessions WHERE name = ?", (session_name,))
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Erro ao remover sessão: {e}")
            return False
    
    def clear_session_relationships(self, session_name: str) -> bool:
        """Remove apenas os relacionamentos de uma sessão (mantém a sessão, remove as personalidades vinculadas)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove relacionamentos da sessão específica
                cursor.execute("""
                    DELETE FROM session_personalities 
                    WHERE session_id = (SELECT id FROM sessions WHERE name = ?)
                """, (session_name,))
                
                removed_count = cursor.rowcount
                return removed_count >= 0  # Retorna True mesmo se não houver registros para remover
                
        except sqlite3.Error as e:
            print(f"Erro ao limpar relacionamentos da sessão: {e}")
            return False
    
    def update_session_description(self, session_name: str, description: str) -> bool:
        """Atualiza a descrição de uma sessão existente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions 
                    SET description = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE name = ?
                """, (description, session_name))
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Erro ao atualizar descrição da sessão: {e}")
            return False
    
    def update_session_info(self, old_session_name: str, new_session_name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """Atualiza nome e/ou descrição de uma sessão existente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Se novo nome foi fornecido, verifica se já existe
                if new_session_name and new_session_name != old_session_name:
                    cursor.execute("SELECT id FROM sessions WHERE name = ?", (new_session_name,))
                    if cursor.fetchone():
                        print(f"❌ Sessão com nome '{new_session_name}' já existe")
                        return False
                
                # Monta a query dinamicamente baseada no que foi fornecido
                updates = []
                params = []
                
                if new_session_name and new_session_name != old_session_name:
                    updates.append("name = ?")
                    params.append(new_session_name)
                
                if description is not None:  # Permite string vazia
                    updates.append("description = ?")
                    params.append(description)
                
                # Sempre atualiza o timestamp
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(old_session_name)  # Para o WHERE
                
                if not updates[:-1]:  # Se não há atualizações além do timestamp
                    return True
                
                query = f"UPDATE sessions SET {', '.join(updates)} WHERE name = ?"
                cursor.execute(query, params)
                
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Erro ao atualizar informações da sessão: {e}")
            return False
    
    def cleanup_orphaned_session_personalities(self) -> int:
        """Remove registros órfãos da tabela session_personalities que referenciam sessões inexistentes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Primeiro, verifica quantos registros órfãos existem
                cursor.execute("""
                    SELECT COUNT(*) FROM session_personalities sp
                    WHERE sp.session_id NOT IN (SELECT id FROM sessions)
                """)
                orphaned_count = cursor.fetchone()[0]
                
                if orphaned_count > 0:
                    print(f"🔍 Encontrados {orphaned_count} registro(s) órfão(s) na tabela session_personalities")
                    
                    # Remove registros órfãos
                    cursor.execute("""
                        DELETE FROM session_personalities 
                        WHERE session_id NOT IN (SELECT id FROM sessions)
                    """)
                    
                    removed_count = cursor.rowcount
                    print(f"🧹 Removidos {removed_count} registro(s) órfão(s)")
                    
                    return removed_count
                else:
                    print("✅ Nenhum registro órfão encontrado na tabela session_personalities")
                    return 0
                
        except sqlite3.Error as e:
            print(f"Erro ao limpar registros órfãos: {e}")
            return -1
    
    def check_database_integrity(self) -> Dict[str, Any]:
        """Verifica a integridade do banco de dados e retorna estatísticas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contagem de tabelas principais
                cursor.execute("SELECT COUNT(*) FROM sessions")
                total_sessions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM personalities")
                total_personalities = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM session_personalities")
                total_relationships = cursor.fetchone()[0]
                
                # Verifica registros órfãos em session_personalities
                cursor.execute("""
                    SELECT COUNT(*) FROM session_personalities sp
                    WHERE sp.session_id NOT IN (SELECT id FROM sessions)
                """)
                orphaned_sessions = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM session_personalities sp
                    WHERE sp.personality_id NOT IN (SELECT id FROM personalities)
                """)
                orphaned_personalities = cursor.fetchone()[0]
                
                # Sessões sem personalidades
                cursor.execute("""
                    SELECT COUNT(*) FROM sessions s
                    WHERE s.id NOT IN (SELECT DISTINCT session_id FROM session_personalities)
                """)
                empty_sessions = cursor.fetchone()[0]
                
                # Personalidades sem sessões
                cursor.execute("""
                    SELECT COUNT(*) FROM personalities p
                    WHERE p.id NOT IN (SELECT DISTINCT personality_id FROM session_personalities)
                """)
                unlinked_personalities = cursor.fetchone()[0]
                
                return {
                    'total_sessions': total_sessions,
                    'total_personalities': total_personalities,
                    'total_relationships': total_relationships,
                    'orphaned_sessions': orphaned_sessions,
                    'orphaned_personalities': orphaned_personalities,
                    'empty_sessions': empty_sessions,
                    'unlinked_personalities': unlinked_personalities,
                    'integrity_issues': orphaned_sessions + orphaned_personalities
                }
                
        except sqlite3.Error as e:
            print(f"Erro ao verificar integridade do banco: {e}")
            return {}
    
    def delete_session_with_personalities(self, session_name: str, delete_personalities: bool = False) -> bool:
        """Remove uma sessão mas mantém personalidades no banco (apenas quebra vínculos)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # IMPORTANTE: Habilita foreign keys para CASCADE DELETE funcionar
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # NOVA LÓGICA: Nunca remove personalidades, apenas quebra vínculos
                # As personalidades permanecem no banco para serem reutilizadas
                
                if delete_personalities:
                    print("ℹ️  Personalidades serão mantidas no banco para reutilização futura")
                
                # Remove apenas a sessão (vínculos são quebrados automaticamente por CASCADE)
                cursor.execute("DELETE FROM sessions WHERE name = ?", (session_name,))
                
                if cursor.rowcount > 0:
                    print(f"✅ Sessão '{session_name}' removida (personalidades mantidas no banco)")
                    return True
                else:
                    print(f"❌ Sessão '{session_name}' não encontrada")
                    return False
                
        except sqlite3.Error as e:
            print(f"Erro ao remover sessão: {e}")
            return False
    
    def export_to_csv(self, session_name: Optional[str] = None, output_file: str = "export.csv") -> bool:
        """Exporta dados para CSV (compatibilidade com sistema atual)"""
        try:
            if session_name:
                personalities = self.get_session_personalities(session_name)
            else:
                personalities = self.get_personalities()
            
            if not personalities:
                return False
            
            # Converte para formato CSV original
            csv_data = []
            for p in personalities:
                csv_data.append({
                    'Termo Buscado': p.get('search_term', ''),
                    'Nome Completo': p.get('full_name', ''),
                    'Origem/Nacionalidade': p.get('country', ''),
                    'Data de Nascimento': p.get('birth_date', ''),
                    'Local de Nascimento': p.get('birth_place', ''),
                    'Data de Falecimento': p.get('death_date', ''),
                    'Local de Falecimento': p.get('death_place', ''),
                    'Século': p.get('century', ''),
                    'Latitude': p.get('latitude', 'Não Informado'),
                    'Longitude': p.get('longitude', 'Não Informado'),
                    'Url': p.get('url', ''),
                    'Imagem': p.get('image_url', '')
                })
            
            df = pd.DataFrame(csv_data)
            df.to_csv(output_file, index=False)
            return True
            
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            return False
    
    def import_from_csv(self, csv_file: str) -> int:
        """Importa dados de um arquivo CSV existente"""
        try:
            if not os.path.exists(csv_file):
                return 0
            
            df = pd.read_csv(csv_file)
            imported_count = 0
            
            for _, row in df.iterrows():
                personality_data = row.to_dict()
                if self.add_personality(personality_data):
                    imported_count += 1
            
            return imported_count
            
        except Exception as e:
            print(f"Erro ao importar CSV: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contagem total de personalidades
                cursor.execute("SELECT COUNT(*) FROM personalities")
                total_personalities = cursor.fetchone()[0]
                
                # Contagem de sessões
                cursor.execute("SELECT COUNT(*) FROM sessions")
                total_sessions = cursor.fetchone()[0]
                
                # Países mais comuns
                cursor.execute("""
                    SELECT country, COUNT(*) as count 
                    FROM personalities 
                    WHERE country IS NOT NULL AND country != ''
                    GROUP BY country 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_countries = cursor.fetchall()
                
                # Séculos mais comuns
                cursor.execute("""
                    SELECT century, COUNT(*) as count 
                    FROM personalities 
                    WHERE century IS NOT NULL AND century != ''
                    GROUP BY century 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_centuries = cursor.fetchall()
                
                return {
                    'total_personalities': total_personalities,
                    'total_sessions': total_sessions,
                    'top_countries': top_countries,
                    'top_centuries': top_centuries,
                    'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                }
                
        except sqlite3.Error as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {}


# Instância global do gerenciador de banco
db_manager = DatabaseManager()