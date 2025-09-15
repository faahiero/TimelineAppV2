#!/usr/bin/env python3
"""
Script de debug para investigar o problema no salvamento da sessão em memória
"""

import sys
import os

# Adiciona o diretório modules ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
sys.path.insert(0, modules_dir)

from data_adapter import DataAdapter

def debug_memory_session():
    """Debug da sessão em memória"""
    
    # Inicializa o data_adapter
    data_adapter = DataAdapter()
    
    print("=== DEBUG DA SESSÃO EM MEMÓRIA ===")
    
    # Verifica se há sessão em memória ativa
    if data_adapter._is_memory_session_active():
        print("✅ Sessão em memória ATIVA")
        
        # Obtém dados da sessão em memória
        memory_session = data_adapter.memory_session
        print(f"📂 Carregada de: {memory_session['loaded_from_db']}")
        print(f"🔄 Modificada: {memory_session['is_dirty']}")
        print(f"📊 Contagem original: {memory_session['original_count']}")
        
        # Obtém personalidades
        personalities = data_adapter._get_memory_session_personalities()
        print(f"👥 Personalidades atuais: {len(personalities)}")
        
        if personalities:
            print("\n📋 ESTRUTURA DAS PERSONALIDADES:")
            for i, p in enumerate(personalities[:3]):  # Mostra apenas as 3 primeiras
                print(f"  {i+1}. Tipo: {type(p)}")
                if isinstance(p, dict):
                    print(f"     Chaves: {list(p.keys())}")
                    if 'id' in p:
                        print(f"     ID: {p['id']}")
                    if 'full_name' in p:
                        print(f"     Nome: {p['full_name']}")
                else:
                    print(f"     Valor: {p}")
                print()
            
            # Testa extração de IDs
            print("🔍 TESTE DE EXTRAÇÃO DE IDs:")
            personality_ids = []
            for p in personalities:
                if isinstance(p, dict) and 'id' in p:
                    personality_ids.append(p['id'])
                    print(f"  ✅ ID extraído: {p['id']}")
                else:
                    print(f"  ❌ Personalidade inválida: {p}")
            
            print(f"\n📊 Total de IDs válidos: {len(personality_ids)}")
            print(f"🆔 IDs: {personality_ids}")
            
            # Testa se as funções do database funcionam
            print("\n🔧 TESTE DAS FUNÇÕES DO DATABASE:")
            
            # Testa clear_session_relationships
            original_session = memory_session['loaded_from_db']
            print(f"🧹 Testando clear_session_relationships('{original_session}')...")
            clear_result = data_adapter.db.clear_session_relationships(original_session)
            print(f"   Resultado: {clear_result}")
            
            # Testa add_to_session
            if personality_ids:
                print(f"➕ Testando add_to_session('{original_session}', {personality_ids[:2]})...")  # Testa apenas os 2 primeiros IDs
                add_result = data_adapter.db.add_to_session(original_session, personality_ids[:2])
                print(f"   Resultado: {add_result}")
        
    else:
        print("❌ Nenhuma sessão em memória ativa")
        
        # Verifica outros tipos de sessão
        if data_adapter.active_saved_session:
            print(f"📊 Sessão salva ativa: {data_adapter.active_saved_session}")
        else:
            print("📝 Apenas sessão temporária ativa")

if __name__ == "__main__":
    debug_memory_session()