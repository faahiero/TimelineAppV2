#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptador para manter compatibilidade entre SQLite e sistema CSV atual
"""
import os
from typing import Dict, Any, List, Optional
from modules.database_manager import db_manager


class DataAdapter:
    """Adaptador que mantém compatibilidade com o sistema atual"""
    
    def __init__(self):
        self.db = db_manager
        self.temp_session = "temp_session"  # Sessão temporária
        self.current_session = self.temp_session  # Sempre inicia com sessão temporária
        self.active_saved_session = None  # Sessão salva ativa (None = usando temporária)
        self.recently_saved_session = None  # Rastreia sessão que foi recém-salva
        
        # NOVA ESTRUTURA PARA SESSÃO EM MEMÓRIA
        self.memory_session = {
            'loaded_from_db': None,  # Nome da sessão original no banco (ou None se nova)
            'session_id': None,      # ID da sessão original no banco
            'personalities': [],     # Lista de personalidades em memória
            'original_count': 0,     # Quantidade de personalidades originais (para detectar mudanças)
            'is_dirty': False        # Indica se houve modificações
        }
        
        self._ensure_temp_session()
    
    def _is_memory_session_active(self) -> bool:
        """Verifica se há uma sessão carregada em memória"""
        return self.memory_session['loaded_from_db'] is not None
    
    def _add_personality_to_memory(self, personality_data: dict):
        """Adiciona personalidade à sessão em memória"""
        self.memory_session['personalities'].append(personality_data)
        self.memory_session['is_dirty'] = True
        print(f"🧠 Personalidade adicionada à sessão em memória: {personality_data.get('full_name', 'N/A')}")
    
    def _get_memory_session_personalities(self) -> List[dict]:
        """Retorna personalidades da sessão em memória"""
        return self.memory_session['personalities']
    
    def _clear_memory_session(self):
        """Limpa sessão em memória"""
        self.memory_session = {
            'loaded_from_db': None,
            'session_id': None,
            'personalities': [],
            'original_count': 0,
            'is_dirty': False
        }
    
    def _save_memory_session_as_new(self, session_name: str, description: str = "") -> bool:
        """Salva sessão em memória como nova sessão no banco"""
        try:
            personalities = self._get_memory_session_personalities()
            
            if not personalities:
                print("❌ Não há dados na sessão em memória para salvar")
                return False
            
            # Cria nova sessão permanente
            success = self.db.create_session(session_name, description or f"Sessão salva em {self._get_timestamp()}")
            
            if success:
                # Adiciona personalidades da memória à nova sessão
                personality_ids = [p['id'] for p in personalities]
                self.db.add_to_session(session_name, personality_ids)
                
                # Limpa sessão em memória
                self._clear_memory_session()
                
                # Marca como recém-salva para mensagens contextuais
                self.recently_saved_session = session_name
                print(f"✅ Sessão em memória salva como '{session_name}' com {len(personality_ids)} personalidade(s)")
                return True
            else:
                print(f"❌ Erro ao criar sessão '{session_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao salvar sessão em memória: {e}")
            return False
    
    def save_memory_session_changes(self, new_session_name: Optional[str] = None, new_description: Optional[str] = None) -> bool:
        """Salva modificações da sessão em memória de volta à sessão original no banco"""
        try:
            if not self._is_memory_session_active():
                print("❌ Não há sessão em memória ativa para salvar")
                return False

            if not self.memory_session['is_dirty'] and not new_session_name and new_description is None:
                print("ℹ️  Não há modificações para salvar")
                return True

            original_session_name = self.memory_session['loaded_from_db']
            personalities = self._get_memory_session_personalities()

            # Validações antes de salvar
            if not original_session_name:
                print("❌ Nome da sessão original não encontrado")
                return False

            if not personalities:
                print("❌ Nenhuma personalidade para salvar")
                return False
            # Extrai IDs das personalidades
            personality_ids = []
            for p in personalities:
                if isinstance(p, dict) and 'id' in p:
                    personality_ids.append(p['id'])
                else:
                    print(f"⚠️  Personalidade inválida encontrada: {p}")

            if not personality_ids:
                print("❌ Nenhum ID de personalidade válido encontrado")
                return False

            # Limpa relacionamentos da sessão original
            clear_success = self.db.clear_session_relationships(original_session_name)
            if not clear_success:
                print("❌ Erro ao limpar relacionamentos da sessão")
                return False

            # Adiciona todas as personalidades da memória (originais + novas)
            add_success = self.db.add_to_session(original_session_name, personality_ids)
            if not add_success:
                print("❌ Erro ao adicionar personalidades à sessão")
                return False
            
            # Atualiza nome e/ou descrição da sessão se fornecidos
            if new_session_name or new_description is not None:
                update_success = self.db.update_session_info(
                    original_session_name, 
                    new_session_name, 
                    new_description
                )
                if not update_success:
                    print("⚠️  Erro ao atualizar informações da sessão, mas personalidades foram salvas")
                else:
                    if new_session_name and new_session_name != original_session_name:
                        print(f"✅ Nome da sessão atualizado para '{new_session_name}'")
                        # Atualiza a referência na memória
                        self.memory_session['loaded_from_db'] = new_session_name
                    if new_description is not None:
                        print(f"✅ Descrição da sessão atualizada")
            
            # Marca como não modificada
            self.memory_session['is_dirty'] = False
            self.memory_session['original_count'] = len(personalities)
            
            final_session_name = new_session_name if new_session_name else original_session_name
            print(f"✅ Modificações salvas na sessão '{final_session_name}'")
            print(f"📊 {len(personality_ids)} personalidade(s) na sessão")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar modificações: {e}")
            import traceback
            print(f"🔍 Detalhes do erro:")
            traceback.print_exc()
            return False
    
    def _ensure_temp_session(self):
        """Cria/limpa uma sessão temporária vazia a cada inicialização"""
        # Remove sessão temporária anterior se existir
        sessions = self.db.get_sessions()
        temp_exists = any(s['name'] == self.temp_session for s in sessions)
        
        if temp_exists:
            # Remove a sessão temporária anterior (dados perdidos intencionalmente)
            self.db.delete_session_with_personalities(self.temp_session, delete_personalities=True)
        
        # Cria nova sessão temporária vazia
        self.db.create_session(
            self.temp_session, 
            "Sessão temporária (dados perdidos ao encerrar sem salvar)"
        )
    
    def write_to_csv_compatible(self, person_info: Dict[str, Any]):
        """Substitui a função write_to_csv original, salvando no SQLite com busca inteligente"""
        # Busca primeiro se a personalidade já existe no banco
        search_term = person_info.get('Termo Buscado', '')
        full_name = person_info.get('Nome Completo', '')
        
        existing_personality = self.db.find_existing_personality(search_term=search_term, full_name=full_name)
        
        if existing_personality:
            print(f"✅ Personalidade '{full_name}' já existe no banco - reutilizando dados")
            personality_id = existing_personality['id']
        else:
            # Adiciona nova personalidade ao banco
            personality_id = self.db.add_personality(person_info)
            if personality_id:
                print(f"✅ Nova personalidade '{full_name}' adicionada ao banco")
            else:
                print(f"❌ Erro ao adicionar personalidade '{full_name}'")
                return False
        
        if personality_id:
            # NOVA LÓGICA: Verifica se há sessão em memória ativa
            if self._is_memory_session_active():
                # Busca os dados completos da personalidade para adicionar à memória
                personality_data = self.db.get_personality_by_id(personality_id)
                if personality_data:
                    # Verifica se já está na sessão em memória
                    memory_personalities = self._get_memory_session_personalities()
                    already_in_memory = any(p['id'] == personality_id for p in memory_personalities)
                    
                    if not already_in_memory:
                        # Adiciona à sessão em memória
                        self._add_personality_to_memory(personality_data)
                        print(f"🧠 '{personality_data.get('full_name', 'N/A')}' adicionada à sessão em memória")
                    else:
                        print(f"ℹ️  '{personality_data.get('full_name', 'N/A')}' já está na sessão em memória")
            else:
                # Lógica original para sessão temporária ou salva
                target_session = self.active_saved_session or self.current_session
                self.db.add_to_session(target_session, [personality_id])
            
            # Dados já salvos no SQLite - não precisa exportar CSV
            return True
        
        return False
    
    def smart_search_and_add(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Busca inteligente que verifica no banco com múltiplas estratégias"""
        # Normaliza o termo de busca
        normalized_term = self._normalize_search_term(search_term)
        
        # Tenta várias estratégias de busca
        search_variations = [
            search_term,  # Termo original
            normalized_term,  # Termo normalizado
            search_term.title(),  # Primeira letra maiúscula
            search_term.lower(),  # Tudo minúsculo
        ]
        
        # Remove duplicatas mantendo ordem
        unique_variations = []
        for variation in search_variations:
            if variation not in unique_variations:
                unique_variations.append(variation)
        
        for variation in unique_variations:
            existing_personality = self.db.find_existing_personality(search_term=variation)
            
            if existing_personality:
                full_name = existing_personality.get('full_name', 'N/A')
                search_strategy = "termo original" if variation == search_term else f"variação '{variation}'"
                print(f"🔍 Personalidade encontrada no banco ({search_strategy}): {full_name}")
                
                # NOVA LÓGICA: Verifica se há sessão em memória ativa
                if self._is_memory_session_active():
                    # Verifica se já está na sessão em memória
                    memory_personalities = self._get_memory_session_personalities()
                    already_in_memory = any(p['id'] == existing_personality['id'] for p in memory_personalities)
                    
                    if already_in_memory:
                        print(f"ℹ️  '{full_name}' já está na sessão em memória")
                    else:
                        # Adiciona à sessão em memória
                        self._add_personality_to_memory(existing_personality)
                        print(f"🧠 '{full_name}' adicionada à sessão em memória")
                else:
                    # Lógica original para sessão temporária
                    target_session = self.active_saved_session or self.current_session
                    current_personalities = self.db.get_session_personalities(target_session)
                    already_linked = any(p['id'] == existing_personality['id'] for p in current_personalities)
                    
                    if already_linked:
                        session_type = f"sessão '{self.active_saved_session}'" if self.active_saved_session else "sessão temporária"
                        print(f"ℹ️  '{full_name}' já está vinculada à {session_type} atual")
                    else:
                        # Vincula à sessão ativa (salva ou temporária)
                        self.db.add_to_session(target_session, [existing_personality['id']])
                        session_type = f"sessão '{self.active_saved_session}'" if self.active_saved_session else "sessão temporária"
                        print(f"🔗 '{full_name}' vinculada à {session_type}")
                
                # Retorna os dados da personalidade encontrada
                
                return existing_personality
        
        return None
    
    def _normalize_search_term(self, term: str) -> str:
        """Normaliza termo de busca removendo acentos e caracteres especiais"""
        import unicodedata
        import re
        
        # Remove acentos
        normalized = unicodedata.normalize('NFD', term)
        normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
        
        # Remove caracteres especiais exceto espaços e hífens
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        
        # Normaliza espaços múltiplos
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    # Funções CSV removidas - usando apenas SQLite
    
    def get_current_session_info(self) -> Optional[Dict[str, Any]]:
        """Retorna informações da sessão ativa (memória, salva ou temporária)"""
        # NOVA LÓGICA: Prioriza sessão em memória
        if self._is_memory_session_active():
            personalities = self._get_memory_session_personalities()
            print(f"🧠 Obtendo informações da sessão em memória: {len(personalities)} personalidade(s)")
        else:
            # Usa sessão ativa (salva ou temporária)
            active_session = self.active_saved_session or self.current_session
            personalities = self.db.get_session_personalities(active_session)
        
        # Se não há personalidades na sessão ativa, retorna None
        if not personalities or len(personalities) == 0:
            return None
        
        # Converte para formato esperado pelo sistema atual
        df_data = []
        for p in personalities:
            # Só adiciona se tem nome completo válido
            full_name = p.get('full_name', '').strip()
            if full_name and full_name != '':
                df_data.append({
                    'Nome Completo': full_name,
                    'Origem/Nacionalidade': p.get('country', ''),
                    'Século': p.get('century', '')
                })
        
        # Se não há dados válidos, retorna None
        if not df_data:
            return None
        
        # Calcula estatísticas usando Python puro
        unique_people = len(set(item['Nome Completo'] for item in df_data if item['Nome Completo']))
        countries = len(set(item['Origem/Nacionalidade'] for item in df_data if item['Origem/Nacionalidade']))
        centuries = len(set(item['Século'] for item in df_data if item['Século']))
        people_list = list(set(item['Nome Completo'] for item in df_data if item['Nome Completo']))[:5]
        
        # Verifica se realmente há dados válidos
        if unique_people == 0:
            return None
        
        return {
            'total_records': len(df_data),
            'unique_people': unique_people,
            'countries': countries,
            'centuries': centuries,
            'people_list': people_list
        }
    
    def import_existing_csv(self, csv_file: str = "person_info.csv") -> int:
        """Importa CSV existente para o banco de dados"""
        if os.path.exists(csv_file):
            return self.db.import_from_csv(csv_file)
        return 0
    
    def create_session_from_current(self, session_name: str, description: str = "") -> bool:
        """Cria uma nova sessão com os dados atuais"""
        # Cria a sessão
        session_id = self.db.create_session(session_name, description)
        if not session_id:
            return False
        
        # Copia personalidades da sessão atual
        current_personalities = self.db.get_session_personalities(self.current_session)
        personality_ids = [p['id'] for p in current_personalities]
        
        if personality_ids:
            return self.db.add_to_session(session_name, personality_ids)
        
        return True
    
    def load_session_for_work(self, session_name: str) -> bool:
        """Carrega uma sessão para trabalho (substitui sessão atual)"""
        try:
            # Limpa a sessão atual
            self.clear_current_session()
            
            # Copia personalidades da sessão selecionada para a atual
            personalities = self.db.get_session_personalities(session_name)
            personality_ids = [p['id'] for p in personalities]
            
            if personality_ids:
                self.db.add_to_session(self.current_session, personality_ids)
            
            # Dados já disponíveis via SQLite
            
            return True
            
        except Exception as e:
            print(f"Erro ao carregar sessão para trabalho: {e}")
            return False
    
    def save_temp_session(self, session_name: str, description: str = "") -> bool:
        """Salva sessão (memória ou temporária) como permanente"""
        try:
            # NOVA LÓGICA: Verifica se há sessão em memória ativa
            if self._is_memory_session_active():
                return self._save_memory_session_as_new(session_name, description)
            
            # Lógica original para sessão temporária
            temp_personalities = self.db.get_session_personalities(self.temp_session)
            
            if not temp_personalities or len(temp_personalities) == 0:
                print("❌ Não há dados na sessão temporária para salvar")
                return False
            
            # Cria nova sessão permanente
            success = self.db.create_session(session_name, description or f"Sessão salva em {self._get_timestamp()}")
            
            if success:
                # Copia personalidades da sessão temporária para a nova sessão
                personality_ids = [p['id'] for p in temp_personalities]
                self.db.add_to_session(session_name, personality_ids)
                
                # Remove registros da sessão temporária para evitar duplicação
                self.db.clear_session_relationships(self.temp_session)
                print(f"🧹 Registros da sessão temporária removidos para evitar duplicação")
                
                # NOVA LÓGICA: Transiciona para a sessão salva CARREGANDO EM MEMÓRIA
                # Primeiro carrega a sessão salva em memória
                success_load = self.load_saved_session_to_temp(session_name)
                if success_load:
                    # Marca como recém-salva para mensagens contextuais  
                    self.recently_saved_session = session_name
                    print(f"✅ Sessão '{session_name}' salva com {len(personality_ids)} personalidade(s)")
                    print(f"🔄 Sessão carregada em memória - novas buscas serão adicionadas aqui")
                    return True
                else:
                    # Se falhar ao carregar em memória, pelo menos mantém referência ativa
                    self.active_saved_session = session_name
                    self.recently_saved_session = session_name
                    print(f"✅ Sessão '{session_name}' salva com {len(personality_ids)} personalidade(s)")
                    print(f"⚠️  Sessão salva mas não carregada em memória")
                    return True
            else:
                print(f"❌ Erro ao criar sessão '{session_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao salvar sessão temporária: {e}")
            return False
    
    def load_saved_session_to_temp(self, session_name: str) -> bool:
        """Carrega uma sessão salva EM MEMÓRIA - permite visualizar e adicionar novos dados"""
        try:
            # Verifica se há mudanças não salvas na sessão em memória atual
            if self.memory_session['is_dirty']:
                print("⚠️ Há modificações não salvas na sessão em memória atual!")
                print(f"   Sessão atual: {self.memory_session.get('loaded_from_db', 'Nova sessão')}")
                resposta = input("Deseja continuar? Modificações serão perdidas (s/N): ").strip().lower()
                if resposta != 's':
                    print("❌ Carregamento cancelado")
                    return False
            
            # Busca dados da sessão no banco
            personalities = self.db.get_session_personalities(session_name)
            session_info = next((s for s in self.db.get_sessions() if s['name'] == session_name), None)
            
            if not session_info:
                print(f"❌ Sessão '{session_name}' não encontrada no banco")
                return False
            
            # CARREGA DADOS EM MEMÓRIA (não altera o banco)
            self.memory_session = {
                'loaded_from_db': session_name,
                'session_id': session_info['id'],
                'personalities': personalities.copy(),  # Cópia em memória
                'original_count': len(personalities),
                'is_dirty': False  # Ainda não foi modificada
            }
            
            # MARCA SESSÃO SALVA COMO ATIVA
            self.active_saved_session = session_name
            
            # Limpa sessão temporária no banco
            self.clear_current_session()
            
            print(f"✅ Sessão '{session_name}' carregada EM MEMÓRIA")
            print(f"📊 {len(personalities)} personalidade(s) carregada(s)")
            print(f"🧠 Dados estão em memória - modificações só afetam o banco ao salvar")
            print(f"🎯 Agora você pode:")
            print(f"   • Gerar visualizações dos dados existentes")
            print(f"   • Buscar novas personalidades (adicionadas à memória)")
            print(f"   • Salvar modificações de volta ao banco")
            print(f"   • Sair sem salvar (mudanças serão perdidas)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar sessão: {e}")
            return False
    
    def get_saved_sessions(self) -> List[Dict[str, Any]]:
        """Retorna lista de sessões salvas (exclui sessão temporária)"""
        all_sessions = self.db.get_sessions()
        return [s for s in all_sessions if s['name'] != self.temp_session]
    
    def has_temp_data(self) -> bool:
        """Verifica se há dados na sessão ativa (salva, temporária ou em memória)"""
        # NOVA LÓGICA: Verifica primeiro se há sessão em memória ativa
        if self._is_memory_session_active():
            personalities = self._get_memory_session_personalities()
            return personalities is not None and len(personalities) > 0
        
        # Lógica original para sessão no banco
        active_session = self.active_saved_session or self.temp_session
        personalities = self.db.get_session_personalities(active_session)
        return personalities is not None and len(personalities) > 0
    
    def save_or_update_active_session(self, session_name: Optional[str] = None, description: str = "", new_session_name: Optional[str] = None, new_description: Optional[str] = None) -> bool:
        """Salva nova sessão ou atualiza sessão ativa existente (incluindo sessão em memória)"""
        try:
            # NOVA LÓGICA: Verifica se há sessão em memória ativa
            if self._is_memory_session_active():
                if self.memory_session['is_dirty']:
                    # Salva modificações de volta à sessão original
                    return self.save_memory_session_changes(new_session_name, new_description)
                else:
                    # Mesmo sem modificações nas personalidades, pode atualizar nome/descrição
                    if new_session_name or new_description is not None:
                        original_session_name = self.memory_session['loaded_from_db']
                        update_success = self.db.update_session_info(
                            original_session_name, 
                            new_session_name, 
                            new_description
                        )
                        if update_success:
                            if new_session_name and new_session_name != original_session_name:
                                print(f"✅ Nome da sessão atualizado para '{new_session_name}'")
                                self.memory_session['loaded_from_db'] = new_session_name
                            if new_description is not None:
                                print(f"✅ Descrição da sessão atualizada")
                            return True
                        else:
                            print("❌ Erro ao atualizar informações da sessão")
                            return False
                    else:
                        print("ℹ️  Não há modificações na sessão em memória para salvar")
                        return True
            
            elif self.active_saved_session:
                # Já está trabalhando em uma sessão salva - apenas atualiza
                current_info = self.get_current_session_info()
                if current_info:
                    # Atualiza nome e/ou descrição se fornecidos
                    if new_session_name or new_description is not None:
                        update_success = self.db.update_session_info(
                            self.active_saved_session,
                            new_session_name,
                            new_description
                        )
                        if update_success:
                            if new_session_name and new_session_name != self.active_saved_session:
                                print(f"✅ Nome da sessão atualizado para '{new_session_name}'")
                                self.active_saved_session = new_session_name
                            if new_description is not None:
                                print(f"✅ Descrição da sessão atualizada")
                        else:
                            print("❌ Erro ao atualizar informações da sessão")
                            return False
                    elif description:  # Mantém compatibilidade com chamadas antigas
                        self.db.update_session_description(self.active_saved_session, description)
                    
                    final_name = new_session_name if new_session_name else self.active_saved_session
                    print(f"✅ Sessão '{final_name}' atualizada")
                    print(f"📊 Total: {current_info['unique_people']} personalidade(s)")
                    return True
                else:
                    print("❌ Nenhum dado para atualizar")
                    return False
            else:
                # Está em sessão temporária - salva como nova sessão
                if not session_name:
                    timestamp = self._get_timestamp().replace(":", "").replace("-", "").replace(" ", "-")
                    session_name = f"sessao_{timestamp}"
                
                return self.save_temp_session(session_name, description)
                
        except Exception as e:
            print(f"❌ Erro ao salvar/atualizar sessão: {e}")
            return False
    
    def get_personality_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas sobre personalidades no banco"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de personalidades
                cursor.execute("SELECT COUNT(*) FROM personalities")
                total_personalities = cursor.fetchone()[0]
                
                # Personalidades vinculadas a sessões
                cursor.execute("""
                    SELECT COUNT(DISTINCT personality_id) 
                    FROM session_personalities sp
                    JOIN sessions s ON sp.session_id = s.id
                """)
                linked_personalities = cursor.fetchone()[0]
                
                # Personalidades órfãs (sem vínculos)
                cursor.execute("""
                    SELECT COUNT(*) FROM personalities p
                    WHERE p.id NOT IN (
                        SELECT DISTINCT personality_id 
                        FROM session_personalities
                    )
                """)
                orphan_personalities = cursor.fetchone()[0]
                
                # Top 5 personalidades mais vinculadas
                cursor.execute("""
                    SELECT p.full_name, COUNT(sp.session_id) as session_count
                    FROM personalities p
                    JOIN session_personalities sp ON p.id = sp.personality_id
                    GROUP BY p.id, p.full_name
                    ORDER BY session_count DESC
                    LIMIT 5
                """)
                top_personalities = cursor.fetchall()
                
                return {
                    'total_personalities': total_personalities,
                    'linked_personalities': linked_personalities,
                    'orphan_personalities': orphan_personalities,
                    'top_personalities': top_personalities
                }
                
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {
                'total_personalities': 0,
                'linked_personalities': 0,
                'orphan_personalities': 0,
                'top_personalities': []
            }
    
    def _get_timestamp(self):
        """Retorna timestamp formatado para usar em nomes de sessão"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def clear_current_session(self):
        """Limpa a sessão temporária atual"""
        try:
            # Remove a sessão atual e recria
            self.db.delete_session(self.current_session)
            self._ensure_temp_session()
            
            # CSV não é mais usado - dados estão apenas no SQLite
                
        except Exception as e:
            print(f"Erro ao limpar sessão atual: {e}")
    
    def get_all_sessions_info(self) -> List[Dict[str, Any]]:
        """Retorna informações de todas as sessões (exceto a atual e vazias)"""
        sessions = self.db.get_sessions()
        # Filtra sessões que não são a atual e que têm pelo menos uma personalidade
        return [s for s in sessions 
                if s['name'] != self.current_session and s['personality_count'] > 0]
    
    def delete_session(self, session_name: str) -> bool:
        """Remove uma sessão e limpa referências internas se necessário"""
        if session_name == self.current_session:
            return False  # Não permite remover sessão atual
        
        # Remove a sessão do banco
        success = self.db.delete_session(session_name)
        
        if success:
            # Limpa referências internas se a sessão removida estava ativa
            if self.active_saved_session == session_name:
                print(f"🧹 Limpando referência da sessão removida '{session_name}'")
                self.active_saved_session = None
            
            # Limpa sessão em memória se corresponde à sessão removida
            if (self._is_memory_session_active() and 
                self.memory_session.get('loaded_from_db') == session_name):
                print(f"🧹 Limpando sessão em memória correspondente à sessão removida")
                self.memory_session = {
                    'personalities': None,
                    'loaded_from_db': None,
                    'original_count': 0,
                    'is_dirty': False
                }
            
            # Limpa flag de recently_saved se corresponde
            if self.recently_saved_session == session_name:
                print(f"🧹 Limpando flag recently_saved da sessão removida")
                self.recently_saved_session = None
        
        return success
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados"""
        return self.db.get_statistics()
    
    def create_new_temp_session(self) -> bool:
        """Cria nova sessão temporária (reset) - limpa qualquer sessão ativa"""
        try:
            # Limpa sessão em memória se houver
            if self._is_memory_session_active():
                print("🧠 Limpando sessão em memória ativa...")
                self.memory_session = {
                    'personalities': None,
                    'loaded_from_db': None,
                    'original_count': 0,
                    'is_dirty': False
                }
            
            # Limpa referência de sessão salva ativa
            if self.active_saved_session:
                print(f"💾 Desconectando da sessão salva '{self.active_saved_session}'...")
                self.active_saved_session = None
            
            # Recria sessão temporária limpa
            print("🗂️  Criando nova sessão temporária...")
            self._ensure_temp_session()
            
            print("✅ Nova sessão temporária criada com sucesso!")
            print("💡 Agora você pode:")
            print("   • [1] - Buscar novas personalidades")
            print("   • [5] - Carregar uma sessão existente")
            print("   • [4] - Salvar quando tiver dados")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar nova sessão temporária: {e}")
            return False


# Instância global do adaptador
data_adapter = DataAdapter()