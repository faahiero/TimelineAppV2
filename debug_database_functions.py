#!/usr/bin/env python3
"""
Script de debug detalhado para identificar o problema no salvamento
"""

import sys
import os
import sqlite3

# Adiciona o diretório modules ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
sys.path.insert(0, modules_dir)

from database_manager import DatabaseManager

def test_database_functions():
    """Testa as funções específicas do database manager"""
    
    db = DatabaseManager()
    
    print("=== TESTE DAS FUNÇÕES DO DATABASE ===")
    
    # Lista todas as sessões
    sessions = db.get_sessions()
    print(f"📊 Total de sessões no banco: {len(sessions)}")
    
    for session in sessions[:3]:  # Mostra apenas as 3 primeiras
        print(f"  • {session['name']} ({session['personality_count']} personalidades)")
    
    if not sessions:
        print("❌ Nenhuma sessão encontrada no banco")
        return
    
    # Pega a primeira sessão para teste
    test_session = sessions[0]
    session_name = test_session['name']
    
    print(f"\n🔍 TESTANDO COM SESSÃO: '{session_name}'")
    
    # Testa get_session_personalities
    personalities = db.get_session_personalities(session_name)
    print(f"👥 Personalidades encontradas: {len(personalities)}")
    
    if personalities:
        first_personality = personalities[0]
        print(f"\n📋 ESTRUTURA DA PRIMEIRA PERSONALIDADE:")
        print(f"   Tipo: {type(first_personality)}")
        print(f"   Chaves: {list(first_personality.keys())}")
        
        # Verifica campos essenciais
        if 'id' in first_personality:
            print(f"   ✅ Campo 'id': {first_personality['id']} (tipo: {type(first_personality['id'])})")
        else:
            print(f"   ❌ Campo 'id' AUSENTE!")
            
        if 'full_name' in first_personality:
            print(f"   ✅ Campo 'full_name': {first_personality['full_name']}")
        else:
            print(f"   ❌ Campo 'full_name' AUSENTE!")
        
        # Testa extração de IDs
        print(f"\n🔍 TESTE DE EXTRAÇÃO DE IDs:")
        personality_ids = []
        for i, p in enumerate(personalities[:3]):
            if isinstance(p, dict) and 'id' in p:
                personality_ids.append(p['id'])
                print(f"   {i+1}. ✅ ID extraído: {p['id']} (tipo: {type(p['id'])})")
            else:
                print(f"   {i+1}. ❌ Erro na personalidade: {p}")
        
        print(f"\n📊 IDs válidos extraídos: {personality_ids}")
        
        # Testa clear_session_relationships
        print(f"\n🧹 TESTANDO clear_session_relationships('{session_name}')...")
        try:
            clear_result = db.clear_session_relationships(session_name)
            print(f"   Resultado: {clear_result}")
            if clear_result:
                print("   ✅ Função executou sem erro")
            else:
                print("   ❌ Função retornou False")
        except Exception as e:
            print(f"   ❌ ERRO: {e}")
        
        # Verifica se os relacionamentos foram realmente removidos
        remaining_personalities = db.get_session_personalities(session_name)
        print(f"   📊 Personalidades restantes após clear: {len(remaining_personalities)}")
        
        # Testa add_to_session
        if personality_ids:
            print(f"\n➕ TESTANDO add_to_session('{session_name}', {personality_ids[:2]})...")
            try:
                add_result = db.add_to_session(session_name, personality_ids[:2])
                print(f"   Resultado: {add_result}")
                if add_result:
                    print("   ✅ Função executou sem erro")
                else:
                    print("   ❌ Função retornou False")
            except Exception as e:
                print(f"   ❌ ERRO: {e}")
            
            # Verifica se foram realmente adicionadas
            final_personalities = db.get_session_personalities(session_name)
            print(f"   📊 Personalidades após add: {len(final_personalities)}")
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == "__main__":
    test_database_functions()