#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
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
        session_file = manage_sessions(SESSIONS_DIR, "load")
        if session_file:
            clear_console()
            print(f"Carregando sessão: {session_file}")
            session_path = os.path.join(SESSIONS_DIR, session_file)
            generate_visualization(custom_file_path=session_path)
    elif options == "6":
        clear_console()
        print("🔧 Corrigindo coordenadas ausentes...")
        
        print("1. Tentando obter coordenadas específicas via SPARQL...")
        fix_missing_coordinates()
        
        print("\n2. Adicionando coordenadas padrão por país...")
        add_default_coordinates_by_country()
        
        print("\n✅ Correção de coordenadas concluída!")
        time.sleep(3)
    elif options == "7":
        session_file = manage_sessions(SESSIONS_DIR, "load_incremental")
        if session_file:
            print(f"📂 Sessão '{session_file}' carregada com sucesso!")
            print("🔍 Agora você pode fazer novas buscas usando a opção [1]")
            print("💾 As novas personalidades serão adicionadas à sessão atual")
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

