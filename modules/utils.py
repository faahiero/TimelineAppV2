import os
import art
import csv


# Limpar o console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


# Menu do programa
def menu():
    """Função de compatibilidade - usa display_menu()"""
    display_menu()

def display_menu():
    """Exibe o menu principal formatado com informações de status."""
    AZUL = "\033[1;34m"
    VERDE = "\033[1;32m"
    AMARELO = "\033[1;33m"
    CIANO = "\033[1;36m"
    NORMAL = "\033[0m"
    CINZA = "\033[0;37m"

    print(AZUL)
    try:
        banner = art.text2art("Wikipedia GeoHist", font="small")
        print(banner)
    except art.ArtError:
        print(f"{AMARELO}=== GeoHist Wikipedia ==={NORMAL}")
    print(NORMAL)
    
    # Verifica status dos arquivos
    person_csv_exists = os.path.exists("person_info.csv")
    sessions_exist = os.path.exists("data/sessions") and os.path.isdir("data/sessions") and len(os.listdir("data/sessions")) > 0
    
    print(f"{VERDE}📊 COLETA DE DADOS{NORMAL}")
    print(f"[1] - Buscar nova personalidade")
    
    print(f"\n{VERDE}📈 VISUALIZAÇÕES{NORMAL}")
    status_atual = f"{VERDE}✓{NORMAL}" if person_csv_exists else f"{CINZA}✗{NORMAL}"
    print(f"[2] - Gerar visualização (dados da busca atual) {status_atual}")
    print(f"[3] - Gerar visualização (histórico de navegação)")
    
    print(f"\n{CIANO}💾 GERENCIAMENTO DE SESSÕES{NORMAL}")
    save_status = f"{VERDE}✓{NORMAL}" if person_csv_exists else f"{CINZA}✗{NORMAL}"
    print(f"[4] - Salvar dados da busca atual como sessão {save_status}")
    
    load_status = f"{VERDE}✓{NORMAL}" if sessions_exist else f"{CINZA}✗{NORMAL}"
    print(f"[5] - Carregar sessão e gerar visualização {load_status}")
    print(f"[7] - Carregar sessão para adicionar novas buscas {load_status}")
    
    print(f"\n{VERDE}🔧 FERRAMENTAS{NORMAL}")
    fix_coords_status = f"{VERDE}✓{NORMAL}" if person_csv_exists else f"{CINZA}✗{NORMAL}"
    print(f"[6] - Corrigir coordenadas ausentes {fix_coords_status}")
    
    print(f"\n{AMARELO}[0] - Encerrar programa{NORMAL}")
    print("-" * 50)
    
    # Mostra informações de status da sessão atual
    if person_csv_exists:
        show_session_status()
    
    if sessions_exist:
        try:
            session_count = len([f for f in os.listdir("data/sessions") if f.endswith('.csv')])
            print(f"{CINZA}💾 Sessões salvas: {session_count}{NORMAL}")
        except:
            pass
    
    print()


def int_to_roman(input):
    if not isinstance(input, type(1)):
        raise Exception("expected integer")
    if not 0 < input < 4000:
        raise Exception("Argument must be between 1 and 3999")
    ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
    nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
    result = []
    for i in range(len(ints)):
        count = int(input / ints[i])
        result.append(nums[i] * count)
        input -= ints[i] * count
    return ''.join(result)


def write_to_csv(person_info, file_name):
    if not os.path.isfile(file_name):
        with open(file_name, 'a', newline='') as csvfile:
            fieldnames = person_info.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(person_info)
    else:
        with open(file_name, 'r+', newline='') as csvfile:
            fieldnames = person_info.keys()
            reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            for row in reader:
                if row['Nome Completo'] == person_info['Nome Completo']:
                    return
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(person_info)


def calcula_seculo(data: str):
    # check if date contains a.C
    if data.find("a.C") != -1:
        ano = int(data.split()[0])

        # Calcula o século
        seculo = ((ano - 1) // 100) + 1

        # Formata a string de retorno
        seculo_formatado = "{} a.C.".format(seculo)

        return seculo_formatado
    else:
        ano = int(data.split()[-1])
        if ano % 100 == 0:
            ano -= 1
        seculo_formatado = (ano // 100) + 1

        return seculo_formatado

def manage_sessions(sessions_dir, action):
    """Gerencia sessões salvas (salvar/carregar/carregar incremental)"""
    import shutil
    from datetime import datetime
    
    if action == "save":
        # Salvar sessão atual
        if not os.path.exists("person_info.csv"):
            print("❌ Nenhum dado atual encontrado para salvar como sessão")
            return None
        
        if not os.path.exists(sessions_dir):
            os.makedirs(sessions_dir)
        
        # Gera nome da sessão com timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        session_name = input(f"Nome da sessão (deixe vazio para usar timestamp {timestamp}): ").strip()
        
        if not session_name:
            session_name = f"sessao_{timestamp}"
        else:
            session_name = f"{session_name}_{timestamp}"
        
        session_file = f"{session_name}.csv"
        session_path = os.path.join(sessions_dir, session_file)
        
        try:
            shutil.copy2("person_info.csv", session_path)
            print(f"✅ Sessão salva como: {session_file}")
            return session_file
        except Exception as e:
            print(f"❌ Erro ao salvar sessão: {e}")
            return None
    
    elif action == "load":
        # Carregar sessão
        if not os.path.exists(sessions_dir):
            print("❌ Nenhuma sessão encontrada")
            return None
        
        session_files = [f for f in os.listdir(sessions_dir) if f.endswith('.csv')]
        
        if not session_files:
            print("❌ Nenhuma sessão encontrada")
            return None
        
        print(f"\n📋 Sessões disponíveis:")
        for i, session_file in enumerate(session_files, 1):
            # Extrai informações do arquivo
            try:
                import pandas as pd
                session_path = os.path.join(sessions_dir, session_file)
                df = pd.read_csv(session_path)
                count = len(df)
                print(f"[{i}] {session_file} ({count} personalidade{'s' if count != 1 else ''})")
            except:
                print(f"[{i}] {session_file}")
        
        try:
            choice = int(input("\nEscolha uma sessão (número): ")) - 1
            if 0 <= choice < len(session_files):
                return session_files[choice]
            else:
                print("❌ Opção inválida")
                return None
        except ValueError:
            print("❌ Entrada inválida")
            return None
    
    elif action == "load_incremental":
        # Carregar sessão para trabalho incremental
        if not os.path.exists(sessions_dir):
            print("❌ Nenhuma sessão encontrada")
            return None
        
        session_files = [f for f in os.listdir(sessions_dir) if f.endswith('.csv')]
        
        if not session_files:
            print("❌ Nenhuma sessão encontrada")
            return None
        
        print(f"\n📋 Sessões disponíveis para carregamento incremental:")
        for i, session_file in enumerate(session_files, 1):
            try:
                import pandas as pd
                session_path = os.path.join(sessions_dir, session_file)
                df = pd.read_csv(session_path)
                count = len(df)
                print(f"[{i}] {session_file} ({count} personalidade{'s' if count != 1 else ''})")
            except:
                print(f"[{i}] {session_file}")
        
        try:
            choice = int(input("\nEscolha uma sessão para carregar incrementalmente (número): ")) - 1
            if 0 <= choice < len(session_files):
                selected_session = session_files[choice]
                session_path = os.path.join(sessions_dir, selected_session)
                
                # Copia a sessão para o arquivo de trabalho atual
                try:
                    shutil.copy2(session_path, "person_info.csv")
                    print(f"✅ Sessão '{selected_session}' carregada para trabalho incremental")
                    print("💡 Agora você pode fazer novas buscas que serão adicionadas a esta sessão")
                    return selected_session
                except Exception as e:
                    print(f"❌ Erro ao carregar sessão: {e}")
                    return None
            else:
                print("❌ Opção inválida")
                return None
        except ValueError:
            print("❌ Entrada inválida")
            return None
    
    return None

def get_current_session_info():
    """Retorna informações sobre a sessão atual"""
    if not os.path.exists("person_info.csv"):
        return None
    
    try:
        import pandas as pd
        df = pd.read_csv("person_info.csv")
        
        # Conta personalidades únicas
        unique_people = df['Nome Completo'].nunique()
        total_records = len(df)
        
        # Verifica se há países diferentes (indicativo de sessão diversificada)
        countries = df['Origem/Nacionalidade'].nunique()
        
        # Verifica se há séculos diferentes
        centuries = df['Século'].nunique()
        
        return {
            'total_records': total_records,
            'unique_people': unique_people,
            'countries': countries,
            'centuries': centuries,
            'people_list': df['Nome Completo'].unique()[:5].tolist()  # Primeiros 5 nomes
        }
    except:
        return None

def show_session_status():
    """Mostra o status detalhado da sessão atual"""
    VERDE = "\033[1;32m"
    AMARELO = "\033[1;33m"
    CIANO = "\033[1;36m"
    NORMAL = "\033[0m"
    
    session_info = get_current_session_info()
    
    if not session_info:
        print(f"{AMARELO}📋 Nenhuma sessão ativa{NORMAL}")
        return
    
    print(f"{CIANO}📊 STATUS DA SESSÃO ATUAL:{NORMAL}")
    print(f"   • {session_info['unique_people']} personalidade(s) única(s)")
    print(f"   • {session_info['countries']} país(es) diferente(s)")
    print(f"   • {session_info['centuries']} século(s) diferente(s)")
    
    if session_info['people_list']:
        names_preview = ', '.join(session_info['people_list'])
        if session_info['unique_people'] > 5:
            names_preview += f" e mais {session_info['unique_people'] - 5}..."
        print(f"   • Personalidades: {names_preview}")
    
    print()