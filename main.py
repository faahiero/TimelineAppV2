#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import shutil
import sys
import time

from modules.utils import clear_console, display_menu, manage_sessions
from modules.info_gathering import fetch_data
from modules.vis_functions import generate_visualization, generate_visualization_history
from modules.coordinate_fixer import fix_missing_coordinates, add_default_coordinates_by_country

# Constante para o diretório de sessões
SESSIONS_DIR = "data/sessions"

# Garante que o diretório de sessões existe
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

while True:
    clear_console()
    display_menu()
    options = input("Escolha uma das opções: ")
    if options == "1":
        search_term = input("Digite o nome da personalidade (0 para encerrar): ")
        if search_term == "0":
            clear_console()
            print("Obrigado por usar o software!!")
            time.sleep(1)
            sys.exit()
        fetch_data(search_term, True)
    elif options == "2":
        generate_visualization()
    elif options == "3":
        clear_console()
        print("Histórico de navegação")
        generate_visualization_history()
    elif options == "4":
        manage_sessions("", "save")
        time.sleep(2)
    elif options == "5":
        # Carrega sessão diretamente via SQLite - sem necessidade de backup CSV
        session_result = manage_sessions("", "load")
        if session_result:
            clear_console()
            if session_result["type"] == "active":
                if session_result.get("already_loaded", False):
                    # Sessão já estava carregada, não precisa mostrar mensagem adicional
                    pass
                else:
                    print(f"✅ Sessão '{session_result['file']}' carregada e ativa")
                    print("💡 Agora você pode:")
                    print("   • [1] - Adicionar novas personalidades")
                    print("   • [2] - Gerar visualização")
                    print("   • [4] - Salvar modificações da sessão")
            else:
                print(f"📊 Sessão {session_result['file']} carregada")
                
        time.sleep(2)
    elif options == "6":
        result = manage_sessions(SESSIONS_DIR, "remove")
        if result:
            if result["type"] == "all":
                print(f"🎉 Todas as {result['removed']} sessões foram removidas!")
            elif result["type"] == "single":
                print(f"🎉 Sessão '{result['file']}' removida com sucesso!")
        time.sleep(2)
    elif options == "7":
        clear_console()
        print(" Corrigindo coordenadas ausentes...")
        
        print("1. Tentando obter coordenadas específicas via SPARQL...")
        fix_missing_coordinates()
        
        print("\n2. Adicionando coordenadas padrão por país...")
        add_default_coordinates_by_country()
        
        print("\n✅ Correção de coordenadas concluída!")
        time.sleep(3)
    elif options == "8":
        clear_console()
        from modules.utils import show_database_statistics, display_database_statistics
        print("📊 Escolha o tipo de estatísticas:")
        print("[1] - Estatísticas completas (análise detalhada)")
        print("[2] - Estatísticas resumidas (versão atual)")
        print("[0] - Voltar")
        
        stats_choice = input("Opção: ").strip()
        clear_console()
        
        if stats_choice == "1":
            display_database_statistics()
        elif stats_choice == "2":
            show_database_statistics()
        elif stats_choice == "0":
            continue
        else:
            print("Opção inválida!")
        
        input("\nPressione Enter para continuar...")
    elif options == "9":
        clear_console()
        from modules.utils import perform_database_maintenance
        perform_database_maintenance()
        input("\nPressione Enter para continuar...")
    elif options == "10":
        # Verifica se há dados carregados antes de permitir criar nova sessão temporária
        from modules.data_adapter import data_adapter
        current_info = data_adapter.get_current_session_info()
        has_data = current_info is not None and current_info.get('unique_people', 0) > 0
        
        if not has_data:
            print("❌ Esta opção não está disponível no momento")
            time.sleep(1)
        else:
            clear_console()
            from modules.utils import create_new_temp_session
            result = create_new_temp_session()
            if result:
                print("💡 Nova sessão temporária pronta para uso!")
            time.sleep(2)
    elif options == "0":
        clear_console()
        
        # Verifica se há dados não salvos na sessão ativa
        from modules.data_adapter import data_adapter
        if data_adapter.has_temp_data():
            current_info = data_adapter.get_current_session_info()
            
            # NOVA LÓGICA: Verifica se é sessão em memória
            if data_adapter._is_memory_session_active():
                memory_personalities = data_adapter._get_memory_session_personalities()
                original_session = data_adapter.memory_session['loaded_from_db']
                original_count = data_adapter.memory_session['original_count']
                is_dirty = data_adapter.memory_session['is_dirty']
                
                if is_dirty:
                    new_personalities = len(memory_personalities) - original_count
                    print(f"⚠️  ATENÇÃO: Há modificações na sessão '{original_session}' não salvas!")
                    if new_personalities > 0:
                        print(f"   • {new_personalities} personalidade(s) nova(s) adicionada(s)")
                    print("   • Modificações serão perdidas se não salvar")
                    
                    print("\nO que deseja fazer?")
                    print(f"[1] - Salvar modificações na sessão '{original_session}' antes de sair")
                    print("[2] - Sair sem salvar (modificações serão perdidas)")
                    print("[0] - Cancelar (voltar ao menu)")
                else:
                    # Não há modificações, pode sair diretamente
                    break
            elif data_adapter.active_saved_session:
                # Está em sessão salva com modificações
                print(f"⚠️  ATENÇÃO: Há modificações na sessão '{data_adapter.active_saved_session}' não atualizadas!")
                if current_info:
                    print(f"   • {current_info['unique_people']} personalidade(s) na sessão")
                
                print("\nO que deseja fazer?")
                print(f"[1] - Atualizar sessão '{data_adapter.active_saved_session}' antes de sair")
                print("[2] - Sair sem atualizar")
                print("[0] - Cancelar (voltar ao menu)")
            else:
                # Está em sessão temporária
                print("⚠️  ATENÇÃO: Há dados na sessão temporária que serão perdidos!")
                if current_info:
                    print(f"   • {current_info['unique_people']} personalidade(s) não salva(s)")
                
                print("\nO que deseja fazer?")
                print("[1] - Salvar sessão temporária antes de sair")
                print("[2] - Sair sem salvar (dados serão perdidos)")
                print("[0] - Cancelar (voltar ao menu)")
            
            exit_choice = input("Escolha uma opção: ").strip()
            
            if exit_choice == "1":
                # Salva/atualiza sessão antes de sair
                save_result = manage_sessions(SESSIONS_DIR, "save")
                if save_result:
                    action_word = "atualizada" if data_adapter.active_saved_session else "salva"
                    print(f"✅ Sessão {action_word} com sucesso!")
                    time.sleep(2)
                else:
                    print("❌ Erro ao salvar - voltando ao menu")
                    time.sleep(2)
                    continue
            elif exit_choice == "0":
                continue  # Volta ao menu
            # Se escolheu 2, continua para sair sem salvar
        
        print("Saindo...")
        
        # Limpeza da sessão temporária ao sair
        try:
            from modules.data_adapter import data_adapter
            print("🧹 Limpando sessão temporária...")
            data_adapter.db.delete_session_with_personalities("temp_session", delete_personalities=False)
        except Exception as e:
            pass  # Falha silenciosa na limpeza
        
        print("Obrigado por usar o software!!")
        time.sleep(1)
        sys.exit()
    else:
        print("❌ Opção inválida")
        time.sleep(1)

