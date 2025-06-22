#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import time
import os # Necessário para listar arquivos e criar diretórios

from modules.utils import clear_console, display_menu, get_user_choice, manage_sessions
from modules.info_gathering import fetch_data
from modules.vis_functions import generate_visualization, generate_visualization_history

# Define o diretório de sessões
SESSIONS_DIR = "data/sessions/"
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)


def handle_fetch_data():
    """Lida com a busca de dados de uma nova personalidade."""
    MAX_ATTEMPTS = 3
    attempts = 0

    while attempts < MAX_ATTEMPTS:
        search_term = input("Digite o nome da personalidade (ou 0 para voltar ao menu): ").strip()
        if search_term == "0":
            return # Volta ao menu principal

        if not search_term:
            print("O nome da personalidade não pode ser vazio. Tente novamente.")
            attempts += 1
            if attempts >= MAX_ATTEMPTS:
                print("Número máximo de tentativas atingido.")
            input("Pressione Enter para tentar novamente ou digite 0 no próximo prompt para voltar.")
            clear_console() # Limpa para a próxima tentativa de input ou para o menu
            continue # Pede o input novamente

        # Chama fetch_data. A função fetch_data agora não pede input e não lida com 'is_correct_term'.
        # Ela processa o termo e retorna. A lógica de "dados corretos?" está dentro de fetch_data,
        # mas não resulta em novas chamadas recursivas a fetch_data de dentro dela mesma.
        fetch_data(search_term)

        # Após fetch_data terminar (seja sucesso ou falha parcial com mensagem),
        # perguntamos ao usuário se quer tentar uma nova busca ou voltar.
        # A pausa para "Pressione Enter para continuar..." é feita após esta interação.

        # A lógica de "tentar novamente o mesmo termo" ou "refinar busca" que existia
        # com _handle_incorrect_information foi simplificada. Agora, se a busca não for
        # satisfatória (usuário responde 'n' para confirmação em fetch_data), fetch_data retorna
        # e o usuário pode simplesmente iniciar uma nova busca pelo menu.
        # Se quisermos uma lógica de "tentar novamente este termo" ou "digitar novo termo" aqui,
        # precisaríamos de um loop mais complexo ou de fetch_data retornar um status.
        # Por ora, simplificamos: uma chamada a handle_fetch_data é uma tentativa de busca.
        break # Sai do loop de tentativas de input se um search_term válido foi processado.

    input("\nPressione Enter para voltar ao menu...")

def handle_generate_visualization(session_file=None):
    """Lida com a geração de visualização, opcionalmente a partir de um arquivo de sessão."""
    clear_console()
    if session_file:
        print(f"Gerando visualização da sessão: {session_file}...")
        # Aqui, generate_visualization precisa ser adaptado para aceitar um nome de arquivo
        # e possivelmente um caminho, se não estiver no diretório raiz.
        # Por enquanto, vamos assumir que ele pode pegar o arquivo de SESSIONS_DIR.
        # Esta é uma simplificação e pode precisar de ajustes em generate_visualization.

        # Copia o arquivo da sessão para o nome esperado por generate_visualization (person_info.csv)
        # ou modifica generate_visualization para aceitar um caminho de arquivo.
        # Optando por modificar generate_visualization é mais limpo.
        # Por agora, apenas passamos o nome do arquivo.
        generate_visualization(custom_file_path=os.path.join(SESSIONS_DIR, session_file))
    else:
        print("Gerando visualização dos dados da busca atual (person_info.csv)...")
        generate_visualization() # Usa o person_info.csv padrão
    print("\nVisualização gerada (ou tentativa). Verifique seu navegador.")
    input("Pressione Enter para continuar...")

def handle_generate_history_visualization():
    """Lida com a geração de visualização do histórico de navegação."""
    clear_console()
    print("Gerando visualização do histórico de navegação (browser_history_person_info.csv)...")
    generate_visualization_history() # Usa o browser_history_person_info.csv padrão
    print("\nVisualização do histórico gerada (ou tentativa). Verifique seu navegador.")
    input("Pressione Enter para continuar...")

def main():
    """Função principal que executa o loop do menu."""
    while True:
        clear_console()
        display_menu() # display_menu precisa ser atualizado para incluir opções de sessão
        choice = get_user_choice() # get_user_choice precisa ser atualizado para as novas opções

        if choice == "1":
            handle_fetch_data()
        elif choice == "2":
            handle_generate_visualization()
        elif choice == "3":
            handle_generate_history_visualization()
        elif choice == "4": # Salvar sessão
            manage_sessions(SESSIONS_DIR, action="save")
            input("\nPressione Enter para continuar...")
        elif choice == "5": # Carregar sessão
            session_to_load = manage_sessions(SESSIONS_DIR, action="load")
            if session_to_load:
                handle_generate_visualization(session_file=session_to_load)
            else:
                input("\nNenhuma sessão carregada. Pressione Enter para continuar...")
        elif choice == "0":
            clear_console()
            print("Saindo...")
            print("Obrigado por usar o software GeoHist Wikipedia!")
            time.sleep(1.5)
            sys.exit()

if __name__ == "__main__":
    main()

