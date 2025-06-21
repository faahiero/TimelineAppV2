import os
import art
import csv
import sys # Adicionado para sys.exit()
import time # Adicionado para time.sleep()


# Limpar o console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


# Menu do programa
def display_menu():
    """Exibe o menu principal formatado."""
    AZUL = "\033[1;34m"
    VERDE = "\033[1;32m"
    AMARELO = "\033[1;33m"
    CIANO = "\033[1;36m" # Nova cor para opções de sessão
    NORMAL = "\033[0m"

    print(AZUL)
    try:
        banner_text = art.text2art("GeoHist Wikipedia", font="small")
        print(f"{AMARELO}{banner_text}{NORMAL}")
    except art.ArtError:
        print(f"{AMARELO}=== GeoHist Wikipedia ==={NORMAL}")
    print(NORMAL)
    print(f"{VERDE}[1]{NORMAL} - Buscar nova personalidade")
    print(f"{VERDE}[2]{NORMAL} - Gerar visualização (dados da busca atual)")
    print(f"{VERDE}[3]{NORMAL} - Gerar visualização (histórico de navegação)")
    print(f"{CIANO}[4]{NORMAL} - Salvar dados da busca atual como sessão")
    print(f"{CIANO}[5]{NORMAL} - Carregar sessão e gerar visualização")
    print(f"{VERDE}[0]{NORMAL} - Encerrar programa")
    print("-" * 40)

def get_user_choice():
    """Obtém e valida a escolha do usuário no menu."""
    AMARELO = "\033[1;33m"
    NORMAL = "\033[0m"
    valid_choices = ["1", "2", "3", "4", "5", "0"]
    while True:
        try:
            choice = input(f"Escolha uma opção ({', '.join(valid_choices)}): ")
            if choice in valid_choices:
                return choice
            else:
                print(f"{AMARELO}Opção inválida. Por favor, digite um número entre 0 e 5.{NORMAL}")
        except KeyboardInterrupt:
            clear_console()
            print("\nSaindo a pedido do usuário...")
            print("Obrigado por usar o software GeoHist Wikipedia!")
            time.sleep(1.5)
            sys.exit()
        except Exception as e:
            print(f"Ocorreu um erro inesperado ao ler sua entrada: {e}")
            time.sleep(1)

# (O restante das funções int_to_roman, write_to_csv, calcula_seculo permanecem aqui)
# ...

def int_to_roman(input_val):
    if not isinstance(input_val, int):
        raise TypeError("A entrada esperada é um inteiro.")
    if not 0 < input_val < 4000:
        raise ValueError("O argumento deve estar entre 1 e 3999.")

    ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
    nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')

    result = []
    for i, value in enumerate(ints):
        count = input_val // value
        result.append(nums[i] * count)
        input_val -= value * count
    return ''.join(result)


def write_to_csv(person_info, file_name, write_header=None): # Adicionado write_header opcional
    """Escreve informações da pessoa em um arquivo CSV."""
    if not isinstance(person_info, dict):
        print("Erro: 'person_info' deve ser um dicionário.")
        return
    if not person_info:
        print("Erro: 'person_info' está vazio.")
        return
    if not file_name or not isinstance(file_name, str):
        print("Erro: 'file_name' inválido.")
        return

    file_exists = os.path.isfile(file_name)
    # Se write_header não for especificado, decide com base na existência do arquivo
    # ou se o arquivo existe mas está vazio.
    if write_header is None:
        should_write_header = not file_exists or (file_exists and os.path.getsize(file_name) == 0)
    else:
        should_write_header = write_header

    # Se o arquivo é 'person_info.csv' (o arquivo de busca atual), verificamos duplicatas.
    # Para arquivos de sessão salvos, não verificamos duplicatas ao salvar a sessão inteira.
    if os.path.basename(file_name) == "person_info.csv" and file_exists and os.path.getsize(file_name) > 0 :
        try:
            with open(file_name, 'r', newline='', encoding='utf-8') as csvfile_read:
                reader = csv.DictReader(csvfile_read)
                if reader.fieldnames and "Nome Completo" in reader.fieldnames:
                    for row in reader:
                        if row.get("Nome Completo") == person_info.get("Nome Completo"):
                            return
        except Exception as e:
            print(f"Alerta: Não foi possível ler '{file_name}' para verificar duplicatas: {e}.")

    try:
        with open(file_name, 'a', newline='', encoding='utf-8') as csvfile_append:
            fieldnames = list(person_info.keys())
            writer = csv.DictWriter(csvfile_append, fieldnames=fieldnames, extrasaction='ignore')

            if should_write_header:
                writer.writeheader()
            writer.writerow(person_info)
    except IOError as e:
        print(f"Erro Crítico de I/O ao manusear o arquivo '{file_name}': {e}")
    except Exception as e:
        print(f"Erro Crítico inesperado ao escrever no CSV '{file_name}': {e}")


def calcula_seculo(data: str):
    """
    Calcula o século a partir de uma string de data.
    Lida com 'a.C.', datas parciais e diferentes formatos.
    Retorna o século como string (ex: "20", "5 a.C.") ou "Não Informado".
    """
    if not isinstance(data, str) or not data.strip() or data == "Não Informado":
        return "Não Informado"

    data_clean = data.lower().strip()
    is_ac = "a.c." in data_clean or "ac" in data_clean or "bc" in data_clean
    year_str = ""

    if data_clean.startswith('-'):
        year_str = "-" + "".join(filter(str.isdigit, data_clean[1:]))
    else:
        text_to_filter = data_clean.replace("a.c.", "").replace("ac", "").replace("bc", "")
        parts = text_to_filter.split()
        potential_years = []
        for part in parts:
            cleaned_part = "".join(filter(str.isdigit, part))
            if cleaned_part:
                potential_years.append(cleaned_part)

        if potential_years:
            year_str = next((py for py in reversed(potential_years) if 0 < len(py) <= 4), None)
            if not year_str and potential_years:
                 year_str = potential_years[-1]

    if not year_str:
        return "Não Informado"

    try:
        ano = int(year_str)
    except ValueError:
        return "Não Informado"

    if ano == 0:
        return "Não Informado"

    if is_ac and ano > 0:
        ano = -ano

    if ano < 0:
        seculo = (abs(ano) - 1) // 100 + 1
        return f"{seculo} a.C."
    else:
        if ano % 100 == 0:
            seculo = ano // 100
        else:
            seculo = ano // 100 + 1
        return str(seculo)

# --- Funções de Gerenciamento de Sessão ---
import json # Para salvar em JSON
import shutil # Para copiar arquivos

def save_session(sessions_dir, current_data_file="person_info.csv"):
    """Salva os dados do arquivo CSV atual (person_info.csv) como uma nova sessão."""
    clear_console()
    print("--- Salvar Sessão ---")
    if not os.path.exists(current_data_file) or os.path.getsize(current_data_file) == 0:
        print(f"Nenhum dado de busca atual ('{current_data_file}') para salvar.")
        return

    session_name = input("Digite um nome para esta sessão (ex: 'cientistas_renascentistas'): ").strip()
    if not session_name:
        print("Nome da sessão não pode ser vazio.")
        return

    # Remove caracteres inválidos para nomes de arquivo (simplificado)
    session_name_safe = "".join(c for c in session_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    if not session_name_safe:
        print("Nome da sessão inválido após sanitização.")
        return

    # Salvar em CSV
    csv_filename = os.path.join(sessions_dir, f"{session_name_safe}.csv")
    try:
        shutil.copyfile(current_data_file, csv_filename)
        print(f"Sessão salva como CSV em: {csv_filename}")
    except Exception as e:
        print(f"Erro ao salvar sessão CSV: {e}")
        return # Não prossegue para JSON se CSV falhar

    # Salvar em JSON
    json_filename = os.path.join(sessions_dir, f"{session_name_safe}.json")
    try:
        data_to_save = []
        with open(current_data_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data_to_save.append(row)

        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data_to_save, jsonfile, indent=4, ensure_ascii=False)
        print(f"Sessão salva como JSON em: {json_filename}")
    except Exception as e:
        print(f"Erro ao salvar sessão JSON: {e}")


def load_session(sessions_dir):
    """Lista sessões salvas e permite ao usuário escolher uma para carregar (retorna o nome do arquivo)."""
    clear_console()
    print("--- Carregar Sessão ---")

    try:
        files = [f for f in os.listdir(sessions_dir) if os.path.isfile(os.path.join(sessions_dir, f)) and (f.endswith(".csv") or f.endswith(".json"))]
    except FileNotFoundError:
        print(f"Diretório de sessões '{sessions_dir}' não encontrado.")
        return None
    except Exception as e:
        print(f"Erro ao listar sessões: {e}")
        return None

    if not files:
        print("Nenhuma sessão salva encontrada.")
        return None

    print("Sessões disponíveis:")
    for i, filename in enumerate(files):
        print(f"  [{i+1}] {filename}")
    print("  [0] Voltar ao menu")

    while True:
        try:
            choice = input("Escolha uma sessão para carregar (pelo número): ")
            choice_int = int(choice)
            if choice_int == 0:
                return None
            if 1 <= choice_int <= len(files):
                selected_file = files[choice_int - 1]
                print(f"Sessão '{selected_file}' selecionada para visualização.")
                # A função que chama load_session será responsável por passar este nome de arquivo
                # para generate_visualization.
                return selected_file
            else:
                print("Escolha inválida.")
        except ValueError:
            print("Por favor, digite um número.")
        except Exception as e:
            print(f"Erro ao processar escolha: {e}")
            return None


def manage_sessions(sessions_dir, action):
    """Ponto de entrada para salvar ou carregar sessões."""
    if action == "save":
        # Assume-se que os dados a serem salvos estão em "person_info.csv"
        # Se não houver dados, save_session deve tratar isso.
        save_session(sessions_dir, current_data_file="person_info.csv")
        return None # Não retorna nome de arquivo ao salvar
    elif action == "load":
        return load_session(sessions_dir) # Retorna o nome do arquivo da sessão a ser carregada
    else:
        print(f"Ação desconhecida para gerenciamento de sessão: {action}")
        return None