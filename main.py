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
        clear_console()
        print("Gerando visualizações")
        generate_visualization()
    elif options == "3":
        clear_console()
        print("Histórico de navegação")
        generate_visualization_history()
    elif options == "4":
        manage_sessions(SESSIONS_DIR, "save")
        time.sleep(2)
    elif options == "5":
        # Salva o estado atual antes de carregar sessão
        current_session_backup = None
        if os.path.exists("person_info.csv"):
            current_session_backup = "person_info.csv.backup"
            shutil.copy2("person_info.csv", current_session_backup)
        
        session_result = manage_sessions(SESSIONS_DIR, "load")
        if session_result:
            clear_console()
            if session_result["type"] == "view":
                # Apenas visualizar a sessão - restaura backup depois
                print(f"📊 Gerando visualização da sessão: {session_result['file']}")
                generate_visualization(custom_file_path=session_result["path"])
                
                # Restaura o arquivo original após visualização
                if current_session_backup and os.path.exists(current_session_backup):
                    shutil.move(current_session_backup, "person_info.csv")
                    print("✅ Sessão atual restaurada")
                    
            elif session_result["type"] == "work":
                # Sessão carregada para trabalho - remove backup pois foi substituída
                if current_session_backup and os.path.exists(current_session_backup):
                    os.remove(current_session_backup)
                    
                print(f"📂 Sessão '{session_result['file']}' carregada para trabalho")
                print("💡 Agora você pode:")
                print("   • Usar opção [1] para adicionar novas personalidades")
                print("   • Usar opção [2] para gerar visualização")
                print("   • Usar opção [4] para salvar a sessão atualizada")
        else:
            # Se cancelou, restaura backup
            if current_session_backup and os.path.exists(current_session_backup):
                shutil.move(current_session_backup, "person_info.csv")
                
        time.sleep(3)
    elif options == "6":
        clear_console()
        print("🔧 Corrigindo coordenadas ausentes...")
        
        print("1. Tentando obter coordenadas específicas via SPARQL...")
        fix_missing_coordinates()
        
        print("\n2. Adicionando coordenadas padrão por país...")
        add_default_coordinates_by_country()
        
        print("\n✅ Correção de coordenadas concluída!")
        time.sleep(3)
    elif options == "0":
        clear_console()
        print("Saindo...")
        print("Obrigado por usar o software!!")
        time.sleep(1)
        sys.exit()
    else:
        print("Opção inválida")
        time.sleep(1)

