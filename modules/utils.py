import os
import art
import time
from modules.data_adapter import data_adapter


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
    except Exception:
        print(f"{AMARELO}=== GeoHist Wikipedia ==={NORMAL}")
    print(NORMAL)
    
    # Verifica status via banco de dados SQLite
    current_session_info = data_adapter.get_current_session_info()
    has_current_data = current_session_info is not None and current_session_info.get('unique_people', 0) > 0
    
    # Verifica se existem sessões salvas no banco (exclui sessão temporária)
    saved_sessions = data_adapter.get_saved_sessions()
    has_saved_sessions = len(saved_sessions) > 0
    
    print(f"{VERDE}📊 COLETA DE DADOS{NORMAL}")
    print(f"[1] - Buscar nova personalidade (🧠 busca inteligente no banco)")
    
    print(f"\n{VERDE}📈 VISUALIZAÇÕES{NORMAL}")
    status_atual = f"{VERDE}✓{NORMAL}" if has_current_data else f"{CINZA}✗{NORMAL}"
    print(f"[2] - Gerar visualização (sessão atual) {status_atual}")
    print(f"[3] - Gerar visualização (histórico de navegação)")
    
    print(f"\n{CIANO}💾 GERENCIAMENTO DE SESSÕES{NORMAL}")
    save_status = f"{VERDE}✓{NORMAL}" if has_current_data else f"{CINZA}✗{NORMAL}"
    
    # NOVA LÓGICA: Mostra status da sessão (memória, salva ou temporária)
    if data_adapter._is_memory_session_active():
        memory_session_name = data_adapter.memory_session['loaded_from_db']
        dirty_status = " (modificada)" if data_adapter.memory_session['is_dirty'] else ""
        print(f"[4] - Salvar modificações da sessão '{memory_session_name}'{dirty_status} {save_status}")
    elif data_adapter.active_saved_session:
        print(f"[4] - Atualizar sessão '{data_adapter.active_saved_session}' {save_status}")
    else:
        print(f"[4] - Salvar sessão temporária {save_status}")
    
    load_status = f"{VERDE}✓{NORMAL}" if has_saved_sessions else f"{CINZA}✗{NORMAL}"
    print(f"[5] - Carregar sessão (visualizar + adicionar dados) {load_status}")
    print(f"[6] - Remover sessões salvas {load_status}")
    
    print(f"\n{VERDE}🔧 FERRAMENTAS{NORMAL}")
    fix_coords_status = f"{VERDE}✓{NORMAL}" if has_current_data else f"{CINZA}✗{NORMAL}"
    print(f"[7] - Corrigir coordenadas ausentes {fix_coords_status}")
    print(f"[8] - Estatísticas do banco de dados ✓")
    print(f"[9] - Manutenção do banco de dados ✓")
    
    # Mostra opção de criar nova sessão temporária apenas se houver dados carregados
    if has_current_data:
        print(f"[10] - Criar nova sessão temporária ✓")
    
    print(f"\n{AMARELO}[0] - Encerrar programa{NORMAL}")
    print("-" * 50)
    
    # Mostra informações de status da sessão atual via banco
    if has_current_data:
        show_session_status()
    
    # Mostra informações das sessões salvas no banco
    if has_saved_sessions:
        print(f"{CINZA}💾 Sessões salvas no banco: {len(saved_sessions)}{NORMAL}")
        
        # Mostra resumo das 3 sessões mais recentes
        recent_sessions = sorted(saved_sessions, key=lambda x: x.get('updated_at', ''), reverse=True)[:3]
        for session in recent_sessions:
            print(f"   • {session['name']} ({session['personality_count']} personalidade(s))")
    
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


def write_to_csv(person_info, file_name=None):
    """Função compatível que agora usa SQLite internamente"""
    return data_adapter.write_to_csv_compatible(person_info)


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
        # VERIFICAÇÕES PRELIMINARES
        # 1. Verifica se há dados para salvar
        if not data_adapter.has_temp_data():
            print("❌ Nenhum dado na sessão ativa para salvar")
            return None
        
        # 2. Obtém informações da sessão atual
        current_info = data_adapter.get_current_session_info()
        
        # 3. Verifica se há sessão em memória ativa
        if data_adapter._is_memory_session_active():
            memory_personalities = data_adapter._get_memory_session_personalities()
            original_session = data_adapter.memory_session['loaded_from_db']
            original_count = data_adapter.memory_session['original_count']
            is_dirty = data_adapter.memory_session['is_dirty']
            
            print(f"🧠 SALVAR MODIFICAÇÕES DA SESSÃO EM MEMÓRIA")
            print(f"   📂 Sessão original: '{original_session}'")
            print(f"   📊 Personalidades atuais: {len(memory_personalities)}")
            print(f"   📊 Personalidades originais: {original_count}")
            
            if is_dirty:
                print(f"   🔄 Status: MODIFICADA (+{len(memory_personalities) - original_count} personalidade(s))")
                print(f"   💾 Ação: Atualizar sessão original no banco")
            else:
                print(f"   ℹ️  Status: SEM MODIFICAÇÕES")
                print(f"   💾 Ação: Nenhuma ação necessária")
                return None
            
            print()
            
            # Lista as personalidades que serão salvas
            if len(memory_personalities) > 0:
                print("📋 Personalidades que serão salvas:")
                for i, p in enumerate(memory_personalities[:5], 1):  # Mostra máximo 5
                    print(f"   {i}. {p.get('full_name', 'N/A')}")
                if len(memory_personalities) > 5:
                    print(f"   ... e mais {len(memory_personalities) - 5} personalidade(s)")
                print()
            
            # Confirmação antes de salvar
            confirm = input("Confirma salvar as modificações? (s/N): ").strip().lower()
            if confirm != 's':
                print("❌ Salvamento cancelado")
                return None
            
            # Solicita atualização de nome e descrição
            print("\n📝 ATUALIZAÇÃO DE INFORMAÇÕES DA SESSÃO (opcional)")
            new_name = input(f"Novo nome da sessão (deixe vazio para manter '{original_session}'): ").strip()
            new_description = input("Nova descrição (deixe vazio para manter atual): ").strip()
            
            # Converte string vazia para None para manter valores atuais
            final_new_name = new_name if new_name else None
            final_new_description = new_description if new_description else None
            
            # EXECUTA O SALVAMENTO DAS MODIFICAÇÕES DA SESSÃO EM MEMÓRIA
            try:
                success = data_adapter.save_or_update_active_session(
                    new_session_name=final_new_name,
                    new_description=final_new_description
                )
                if success:
                    final_session_name = new_name if new_name else original_session
                    print(f"✅ Modificações da sessão '{final_session_name}' salvas com sucesso!")
                    return final_session_name
                else:
                    print("❌ Erro ao salvar modificações")
                    return None
            except Exception as e:
                print(f"❌ Erro ao salvar modificações: {e}")
                return None
        
        elif data_adapter.active_saved_session:
            # Já está trabalhando em uma sessão salva - apenas atualiza
            print(f"💾 ATUALIZAR SESSÃO '{data_adapter.active_saved_session}'")
            if current_info:
                print(f"   • {current_info['unique_people']} personalidade(s) única(s)")
                print(f"   • {current_info['countries']} país(es) diferente(s)")
            print()
            
            print("📝 ATUALIZAÇÃO DE INFORMAÇÕES DA SESSÃO (opcional)")
            new_name = input(f"Novo nome da sessão (deixe vazio para manter '{data_adapter.active_saved_session}'): ").strip()
            new_description = input("Nova descrição (deixe vazio para manter atual): ").strip()
            
            # Converte string vazia para None para manter valores atuais
            final_new_name = new_name if new_name else None
            final_new_description = new_description if new_description else None
            
            try:
                success = data_adapter.save_or_update_active_session(
                    new_session_name=final_new_name,
                    new_description=final_new_description
                )
                if success:
                    final_session_name = new_name if new_name else data_adapter.active_saved_session
                    # Atualiza a referência ativa se o nome mudou
                    if new_name:
                        data_adapter.active_saved_session = new_name
                    return final_session_name
                else:
                    return None
            except Exception as e:
                print(f"❌ Erro ao atualizar sessão: {e}")
                return None
        else:
            # Está em sessão temporária - salva como nova
            print(f"💾 SALVAR NOVA SESSÃO")
            if current_info:
                print(f"   📊 Personalidades: {current_info['unique_people']}")
                print(f"   🌍 Países: {current_info['countries']}")
                print(f"   📅 Séculos: {current_info['centuries'] if 'centuries' in current_info else 'N/A'}")
            print()
            
            # Lista algumas personalidades que serão salvas
            temp_personalities = data_adapter.db.get_session_personalities(data_adapter.temp_session)
            if temp_personalities and len(temp_personalities) > 0:
                print("📋 Personalidades que serão salvas:")
                for i, p in enumerate(temp_personalities[:5], 1):  # Mostra máximo 5
                    print(f"   {i}. {p.get('full_name', 'N/A')}")
                if len(temp_personalities) > 5:
                    print(f"   ... e mais {len(temp_personalities) - 5} personalidade(s)")
                print()
            
            # Confirmação antes de pedir nome
            confirm = input("Confirma salvar estes dados como nova sessão? (s/N): ").strip().lower()
            if confirm != 's':
                print("❌ Salvamento cancelado")
                return None
            
            # Gera nome da sessão com timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            session_name = input(f"Nome da sessão (deixe vazio para usar 'sessao_{timestamp}'): ").strip()
            
            if not session_name:
                session_name = f"sessao_{timestamp}"
            
            description = input("Descrição (opcional): ").strip()
            if not description:
                if current_info:
                    description = f"Sessão salva em {datetime.now().strftime('%d/%m/%Y %H:%M')} com {current_info['unique_people']} personalidade(s)"
                else:
                    description = f"Sessão salva em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            try:
                success = data_adapter.save_or_update_active_session(session_name, description)
                if success:
                    return session_name
                else:
                    return None
            except Exception as e:
                print(f"❌ Erro ao salvar sessão: {e}")
                return None
    
    elif action == "load":
        # Carregar sessão salva para sessão temporária
        saved_sessions = data_adapter.get_saved_sessions()
        
        if not saved_sessions:
            print("❌ Nenhuma sessão salva encontrada")
            return None
        
        # Inicializa variável de controle para forçar recarregamento
        force_reload = False
        
        # NOVA LÓGICA: Verifica tipo de sessão ativa e se há modificações
        if data_adapter._is_memory_session_active():
            # Há sessão em memória ativa
            memory_session_name = data_adapter.memory_session['loaded_from_db']
            is_dirty = data_adapter.memory_session['is_dirty']
            
            if is_dirty:
                # Há modificações não salvas - perguntar se quer salvar
                current_info = data_adapter.get_current_session_info()
                memory_personalities = data_adapter._get_memory_session_personalities()
                original_count = data_adapter.memory_session['original_count']
                new_count = len(memory_personalities) - original_count
                
                print(f"⚠️  ATENÇÃO: Há modificações não salvas na sessão '{memory_session_name}'!")
                if new_count > 0:
                    print(f"   • {new_count} personalidade(s) nova(s) adicionada(s)")
                if current_info:
                    print(f"   • Total: {current_info['unique_people']} personalidade(s) na sessão")
                
                print("\nO que deseja fazer?")
                print(f"[1] - Continuar (modificações da sessão '{memory_session_name}' serão perdidas)")
                print(f"[2] - Salvar modificações na sessão '{memory_session_name}' primeiro")
                print("[0] - Cancelar")
                
                temp_choice = input("Escolha uma opção: ").strip()
                if temp_choice == "2":
                    # Salva modificações da sessão em memória primeiro
                    save_result = manage_sessions(sessions_dir, "save")
                    if not save_result:
                        return None
                elif temp_choice == "0":
                    return None
                elif temp_choice == "1":
                    # Usuário escolheu descartar modificações - marca para forçar recarregamento
                    force_reload = True
                else:
                    print("❌ Opção inválida")
                    return None
            else:
                # Não há modificações - carregamento normal
                force_reload = False
        elif data_adapter.has_temp_data():
            # Há dados na sessão temporária regular
            print("⚠️  ATENÇÃO: Há dados na sessão temporária atual!")
            current_info = data_adapter.get_current_session_info()
            if current_info:
                print(f"   • {current_info['unique_people']} personalidade(s) na sessão temporária")
            
            print("\nO que deseja fazer?")
            print("[1] - Continuar (dados temporários serão perdidos)")
            print("[2] - Salvar sessão temporária primeiro")
            print("[0] - Cancelar")
            
            temp_choice = input("Escolha uma opção: ").strip()
            if temp_choice == "2":
                # Salva sessão temporária primeiro
                save_result = manage_sessions(sessions_dir, "save")
                if not save_result:
                    return None
            elif temp_choice == "0":
                return None
            elif temp_choice == "1":
                # Continua normalmente (dados temporários serão perdidos)
                force_reload = False
            else:
                print("❌ Opção inválida")
                return None
        else:
            # Não há dados em memória nem temporários - carregamento normal
            force_reload = False
        
        print(f"\n📋 Sessões salvas disponíveis:")
        for i, session in enumerate(saved_sessions, 1):
            print(f"[{i}] {session['name']}")
            personalities = data_adapter.db.get_session_personalities(session['name'])
            print(f"    📊 {len(personalities)} personalidade(s)")
            if session['description']:
                print(f"    📝 {session['description']}")
        
        try:
            choice = int(input("\nEscolha uma sessão (número): ")) - 1
            if 0 <= choice < len(saved_sessions):
                selected_session = saved_sessions[choice]
                session_name = selected_session['name']
                
                # OTIMIZAÇÃO: Verifica se é a mesma sessão já carregada ANTES de qualquer consulta ao banco
                # MAS só se não estiver forçando recarregamento (quando usuário escolheu descartar modificações)
                session_already_loaded = False
                
                if not force_reload:
                    # Verificação 1: Sessão em memória
                    if data_adapter._is_memory_session_active():
                        current_memory_session = data_adapter.memory_session['loaded_from_db']
                        if current_memory_session == session_name:
                            session_already_loaded = True
                    
                    # Verificação 2: Sessão salva ativa
                    if data_adapter.active_saved_session == session_name:
                        session_already_loaded = True
                    
                    if session_already_loaded:
                        print(f"ℹ️ Sessão '{session_name}' já está carregada e ativa. Nenhuma alteração detectada.")
                        time.sleep(2)
                        return {"type": "active", "file": session_name, "loaded": False, "already_loaded": True}
                elif force_reload:
                    # Usuário escolheu descartar modificações - forçar recarregamento
                    print(f"\n🔄 Recarregando sessão '{session_name}' (descartando modificações)...")
                
                # Nova lógica: carrega a sessão como ativa (permite visualização E adição de dados)
                # Só executa consulta ao banco se for sessão diferente da já carregada
                print(f"\n📂 Sessão selecionada: {session_name}")
                personalities = data_adapter.db.get_session_personalities(session_name)
                print(f"   📊 {len(personalities)} personalidade(s)")
                if selected_session['description']:
                    print(f"   📝 {selected_session['description']}")
                
                print("\nConfirma carregar esta sessão em memória? (s/N): ", end="")
                
                confirmation = input().strip().lower()
                
                if confirmation == 's':
                    # Carrega a sessão como ativa
                    try:
                        success = data_adapter.load_saved_session_to_temp(session_name)
                        if success:
                            return {"type": "active", "file": session_name, "loaded": True}
                        else:
                            print(f"❌ Erro ao carregar sessão")
                            return None
                    except Exception as e:
                        print(f"❌ Erro ao carregar sessão: {e}")
                        return None
                    
                else:
                    print("❌ Operação cancelada")
                    return None
                    
            else:
                print("❌ Opção inválida")
                return None
        except ValueError:
            print("❌ Entrada inválida")
            return None
    
    elif action == "remove":
        # Remover sessões salvas (não inclui sessão temporária)
        sessions = data_adapter.get_saved_sessions()
        
        if not sessions:
            print("❌ Nenhuma sessão encontrada para remover")
            return None
        
        print(f"\n🗑️  Sessões disponíveis para remoção:")
        print(f"ℹ️  Personalidades serão mantidas no banco para reutilização")
        print()
        for i, session in enumerate(sessions, 1):
            print(f"[{i}] {session['name']}")
            print(f"    📊 {session['personality_count']} personalidade(s), {session['country_count']} país(es)")
        
        print(f"[{len(sessions) + 1}] Remover TODAS as sessões")
        print("[0] Cancelar")
        
        try:
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == "0":
                print("❌ Operação cancelada")
                return None
            elif choice == str(len(sessions) + 1):
                # Remover todas as sessões
                confirm = input("⚠️  Tem certeza que deseja remover TODAS as sessões? (digite 'CONFIRMAR'): ")
                if confirm == "CONFIRMAR":
                    removed_count = 0
                    for session in sessions:
                        try:
                            if data_adapter.delete_session(session['name']):
                                removed_count += 1
                        except Exception as e:
                            print(f"❌ Erro ao remover {session['name']}: {e}")
                    
                    print(f"✅ {removed_count} sessão(ões) removida(s)")
                    return {"removed": removed_count, "type": "all"}
                else:
                    print("❌ Operação cancelada - confirmação incorreta")
                    return None
            else:
                # Remover sessão específica
                try:
                    session_index = int(choice) - 1
                    if 0 <= session_index < len(sessions):
                        selected_session = sessions[session_index]
                        session_name = selected_session['name']
                        
                        print(f"📋 Sessão selecionada: {session_name}")
                        print(f"   📊 {selected_session['personality_count']} personalidade(s)")
                        print(f"   🌍 {selected_session['country_count']} país(es)")
                        print()
                        print("Opções de remoção:")
                        print("[1] - Remover apenas a sessão (manter personalidades no banco)")
                        print("[2] - Remover sessão + personalidades exclusivas desta sessão")
                        print("[0] - Cancelar")
                        
                        remove_option = input("Escolha uma opção: ").strip()
                        
                        if remove_option == "0":
                            print("❌ Operação cancelada")
                            return None
                        elif remove_option in ["1", "2"]:
                            delete_personalities = remove_option == "2"
                            
                            if delete_personalities:
                                confirm = input(f"⚠️  ATENÇÃO: Isso removerá personalidades que existem APENAS nesta sessão!\n   Tem certeza? (digite 'CONFIRMAR'): ")
                                if confirm != "CONFIRMAR":
                                    print("❌ Operação cancelada")
                                    return None
                            else:
                                confirm = input(f"⚠️  Remover sessão '{session_name}'? (s/n): ")
                                if confirm.lower() != 's':
                                    print("❌ Operação cancelada")
                                    return None
                            
                            try:
                                if delete_personalities:
                                    success = data_adapter.db.delete_session_with_personalities(session_name, True)
                                else:
                                    success = data_adapter.delete_session(session_name)
                                
                                if success:
                                    action = "e personalidades exclusivas" if delete_personalities else ""
                                    print(f"✅ Sessão '{session_name}'{action} removida com sucesso")
                                    return {"removed": 1, "type": "single", "file": session_name, "with_personalities": delete_personalities}
                                else:
                                    print(f"❌ Erro ao remover sessão")
                                    return None
                            except Exception as e:
                                print(f"❌ Erro ao remover sessão: {e}")
                                return None
                        else:
                            print("❌ Opção inválida")
                            return None
                    else:
                        print("❌ Opção inválida")
                        return None
                except ValueError:
                    print("❌ Entrada inválida")
                    return None
        except KeyboardInterrupt:
            print("\n❌ Operação cancelada pelo usuário")
            return None

    return None

def get_current_session_info():
    """Retorna informações sobre a sessão atual (agora usando SQLite)"""
    return data_adapter.get_current_session_info()

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
    
    # NOVA LÓGICA: Mostra status baseado no tipo de sessão ativa (memória, salva ou temporária)
    if data_adapter._is_memory_session_active():
        memory_session_name = data_adapter.memory_session['loaded_from_db']
        is_dirty = data_adapter.memory_session['is_dirty']
        original_count = data_adapter.memory_session['original_count']
        current_count = session_info['unique_people']
        
        print(f"{CIANO}🧠 STATUS DA SESSÃO EM MEMÓRIA '{memory_session_name}':{NORMAL}")
        print(f"   • {current_count} personalidade(s) em memória")
        print(f"   • {session_info['countries']} país(es) diferente(s)")
        print(f"   • {session_info['centuries']} século(s) diferente(s)")
        
        if is_dirty:
            added_count = current_count - original_count
            print(f"   • {AMARELO}🔄 Modificada (+{added_count} personalidade(s)){NORMAL}")
            print(f"   • {AMARELO}⚠️  Modificações serão perdidas se não salvar{NORMAL}")
        else:
            print(f"   • {VERDE}✓ Não modificada desde o carregamento{NORMAL}")
        
    elif data_adapter.active_saved_session:
        print(f"{CIANO}📊 STATUS DA SESSÃO '{data_adapter.active_saved_session}':{NORMAL}")
        print(f"   • {session_info['unique_people']} personalidade(s) única(s)")
        print(f"   • {session_info['countries']} país(es) diferente(s)")
        print(f"   • {session_info['centuries']} século(s) diferente(s)")
        print(f"   • {VERDE}💾 Sessão salva - modificações podem ser atualizadas{NORMAL}")
    else:
        print(f"{CIANO}📊 STATUS DA SESSÃO TEMPORÁRIA:{NORMAL}")
        print(f"   • {session_info['unique_people']} personalidade(s) única(s)")
        print(f"   • {session_info['countries']} país(es) diferente(s)")
        print(f"   • {session_info['centuries']} século(s) diferente(s)")
        print(f"   • {AMARELO}⚠️  Dados serão perdidos se não salvar antes de encerrar{NORMAL}")
    
    if session_info['people_list']:
        names_preview = ', '.join(session_info['people_list'])
        if session_info['unique_people'] > 5:
            names_preview += f" e mais {session_info['unique_people'] - 5}..."
        print(f"   • Personalidades: {names_preview}")
    
    print()

def get_session_status_message(session_name):
    """Retorna mensagem contextual baseada no estado da sessão"""
    current_info = data_adapter.get_current_session_info()
    is_dirty = data_adapter.memory_session.get('is_dirty', False)
    recently_saved = (data_adapter.recently_saved_session == session_name)
    
    if recently_saved:
        # Contexto 2: Recém-salva
        message = f"💾 A sessão '{session_name}' já está ativa com modificações salvas!"
        if current_info:
            message += f"\n   • {current_info['unique_people']} personalidade(s) disponíveis (✅ sincronizadas com o banco)"
        message += "\n   • Modificações foram salvas com sucesso"
        message += "\n   • Você pode continuar adicionando dados ou gerar visualizações"
        
        # Limpa o flag de recém-salva após mostrar a mensagem
        data_adapter.recently_saved_session = None
        return message
        
    elif is_dirty:
        # Contexto 3: Com modificações pendentes
        message = f"⚠️  A sessão '{session_name}' já está ativa com modificações não salvas!"
        if current_info:
            message += f"\n   • {current_info['unique_people']} personalidade(s) disponíveis (⚠️  há alterações pendentes)"
        message += "\n   • Você tem modificações que ainda não foram salvas"
        message += "\n   • Use a opção [4] para salvar ou continue adicionando dados"
        return message
        
    else:
        # Contexto 1: Normal
        message = f"Deseja recarregar a sessão '{session_name}'?"
        if current_info:
            message += f"\n   • {current_info['unique_people']} personalidade(s) disponíveis"
        message += "\n   • Carregamento substituirá dados atuais"
        return message

def show_database_statistics():
    """Mostra estatísticas detalhadas do banco de dados"""
    VERDE = "\033[1;32m"
    AMARELO = "\033[1;33m"
    CIANO = "\033[1;36m"
    ROXO = "\033[1;35m"
    NORMAL = "\033[0m"
    
    print(f"{CIANO}📊 ESTATÍSTICAS DO BANCO DE DADOS{NORMAL}")
    print("-" * 50)
    
    # Estatísticas de personalidades (nova funcionalidade)
    personality_stats = data_adapter.get_personality_statistics()
    saved_sessions = data_adapter.get_saved_sessions()
    
    print(f"{VERDE}📈 PERSONALIDADES:{NORMAL}")
    print(f"   • Total no banco: {personality_stats.get('total_personalities', 0)}")
    print(f"   • Vinculadas a sessões: {personality_stats.get('linked_personalities', 0)}")
    print(f"   • Disponíveis para reuso: {personality_stats.get('orphan_personalities', 0)}")
    
    print(f"\n{VERDE}� SESSÕES:{NORMAL}")
    print(f"   • Sessões salvas: {len(saved_sessions)}")
    print(f"   • Sessão temporária ativa: {'Sim' if data_adapter.has_temp_data() else 'Não'}")
    
    # Top personalidades mais reutilizadas
    top_personalities = personality_stats.get('top_personalities', [])
    if top_personalities:
        print(f"\n{ROXO}⭐ PERSONALIDADES MAIS REUTILIZADAS:{NORMAL}")
        for name, count in top_personalities:
            print(f"   • {name}: {count} sessão(ões)")
    
    # Tamanho do banco
    try:
        import os
        db_path = data_adapter.db.db_path
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            db_size_mb = db_size / (1024 * 1024)
            print(f"\n{VERDE}💾 ARMAZENAMENTO:{NORMAL}")
            print(f"   • Tamanho do banco: {db_size_mb:.2f} MB")
    except Exception:
        pass
    
    # Informações da sessão temporária atual
    current_info = data_adapter.get_current_session_info()
    if current_info:
        print(f"\n{AMARELO}📋 SESSÃO TEMPORÁRIA:{NORMAL}")
        print(f"   • {current_info['unique_people']} personalidade(s) vinculada(s)")
        print(f"   • ⚠️  Dados serão perdidos se não salvar antes de encerrar")
        print(f"   • {current_info['countries']} país(es) diferente(s)")
        print(f"   • {current_info['centuries']} século(s) diferente(s)")
    
    print()


def display_database_statistics():
    """Exibe estatísticas detalhadas do banco de dados"""
    from modules.database_manager import DatabaseManager
    
    VERDE = "\033[1;32m"
    AMARELO = "\033[1;33m"
    AZUL = "\033[1;34m"
    VERMELHO = "\033[1;31m"
    NORMAL = "\033[0m"
    
    db_manager = DatabaseManager()
    stats = db_manager.check_database_integrity()
    
    if not stats:
        print(f"{VERMELHO}❌ Erro ao obter estatísticas do banco{NORMAL}")
        return
        
    print(f"\n{AZUL}📊 ESTATÍSTICAS DO BANCO DE DADOS{NORMAL}")
    print("=" * 50)
    
    print(f"{VERDE}📚 Dados Principais:{NORMAL}")
    print(f"  • Sessões: {stats['total_sessions']}")
    print(f"  • Personalidades: {stats['total_personalities']}")
    print(f"  • Relacionamentos: {stats['total_relationships']}")
    
    print(f"\n{AMARELO}🔍 Análise de Integridade:{NORMAL}")
    if stats['integrity_issues'] == 0:
        print(f"  {VERDE}✓ Banco íntegro - sem problemas detectados{NORMAL}")
    else:
        print(f"  {VERMELHO}⚠️  {stats['integrity_issues']} problema(s) detectado(s):{NORMAL}")
        if stats['orphaned_sessions'] > 0:
            print(f"    • {stats['orphaned_sessions']} relacionamento(s) órfão(s) - sessões inexistentes")
        if stats['orphaned_personalities'] > 0:
            print(f"    • {stats['orphaned_personalities']} relacionamento(s) órfão(s) - personalidades inexistentes")
    
    print(f"\n{AZUL}📋 Dados Complementares:{NORMAL}")
    print(f"  • Sessões vazias: {stats['empty_sessions']}")
    print(f"  • Personalidades não vinculadas: {stats['unlinked_personalities']}")
    
    print("\n" + "=" * 50)


def perform_database_maintenance():
    """Realiza manutenção do banco de dados"""
    from modules.database_manager import DatabaseManager
    
    VERDE = "\033[1;32m"
    AMARELO = "\033[1;33m"
    AZUL = "\033[1;34m"
    VERMELHO = "\033[1;31m"
    NORMAL = "\033[0m"
    
    print(f"\n{AZUL}🔧 MANUTENÇÃO DO BANCO DE DADOS{NORMAL}")
    print("=" * 50)
    
    db_manager = DatabaseManager()
    
    # Verifica integridade primeiro
    print(f"{AMARELO}1. Verificando integridade...{NORMAL}")
    stats = db_manager.check_database_integrity()
    
    if not stats:
        print(f"{VERMELHO}❌ Erro ao verificar integridade{NORMAL}")
        return
    
    if stats['integrity_issues'] == 0:
        print(f"  {VERDE}✓ Banco íntegro - nenhuma manutenção necessária{NORMAL}")
        return
    
    print(f"  {AMARELO}⚠️  {stats['integrity_issues']} problema(s) encontrado(s){NORMAL}")
    
    # Pergunta se deve prosseguir com a limpeza
    print(f"\n{AMARELO}2. Limpeza de registros órfãos:{NORMAL}")
    resposta = input("Deseja limpar os registros órfãos? (s/N): ").strip().lower()
    
    if resposta == 's':
        print(f"  {AMARELO}Limpando registros órfãos...{NORMAL}")
        removed_count = db_manager.cleanup_orphaned_session_personalities()
        
        if removed_count > 0:
            print(f"  {VERDE}✓ {removed_count} registro(s) órfão(s) removido(s){NORMAL}")
        elif removed_count == 0:
            print(f"  {VERDE}✓ Nenhum registro órfão encontrado{NORMAL}")
        else:
            print(f"  {VERMELHO}❌ Erro durante a limpeza{NORMAL}")
    else:
        print(f"  {AMARELO}Limpeza cancelada{NORMAL}")
    
    print("\n" + "=" * 50)


def create_new_temp_session():
    """Cria nova sessão temporária com verificação de modificações não salvas"""
    AMARELO = "\033[1;33m"
    VERMELHO = "\033[1;31m"
    VERDE = "\033[1;32m"
    NORMAL = "\033[0m"
    
    # Verifica se há dados ativos que serão perdidos
    current_info = data_adapter.get_current_session_info()
    has_data = current_info is not None and current_info.get('unique_people', 0) > 0
    
    if has_data:
        print(f"{AMARELO}🔄 CRIAR NOVA SESSÃO TEMPORÁRIA{NORMAL}")
        print()
        
        # Verifica tipo de sessão ativa
        if data_adapter._is_memory_session_active():
            # Há sessão em memória ativa
            memory_session_name = data_adapter.memory_session['loaded_from_db']
            is_dirty = data_adapter.memory_session['is_dirty']
            
            if is_dirty:
                # Há modificações não salvas
                memory_personalities = data_adapter._get_memory_session_personalities()
                original_count = data_adapter.memory_session['original_count']
                new_count = len(memory_personalities) - original_count
                
                print(f"{VERMELHO}⚠️  ATENÇÃO: Há modificações não salvas na sessão '{memory_session_name}'!{NORMAL}")
                if new_count > 0:
                    print(f"   • {new_count} personalidade(s) nova(s) adicionada(s)")
                if current_info:
                    print(f"   • Total: {current_info['unique_people']} personalidade(s) na sessão")
                
                print("\nO que deseja fazer?")
                print(f"[1] - Continuar (modificações da sessão '{memory_session_name}' serão perdidas)")
                print(f"[2] - Salvar modificações na sessão '{memory_session_name}' primeiro")
                print("[0] - Cancelar")
                
                choice = input("Escolha uma opção: ").strip()
                if choice == "2":
                    # Salva modificações primeiro
                    save_result = manage_sessions("data/sessions", "save")
                    if not save_result:
                        print("❌ Cancelando criação de nova sessão")
                        return False
                elif choice == "0":
                    print("❌ Operação cancelada")
                    return False
                # Se escolheu 1, continua normalmente
            else:
                # Não há modificações, mas confirma se quer sair da sessão carregada
                print(f"ℹ️  Você está trabalhando na sessão '{memory_session_name}' (sem modificações)")
                if current_info:
                    print(f"   • {current_info['unique_people']} personalidade(s) carregada(s)")
                
                confirm = input("Confirma criar nova sessão temporária? (s/N): ").strip().lower()
                if confirm != 's':
                    print("❌ Operação cancelada")
                    return False
                    
        elif data_adapter.active_saved_session:
            # Há sessão salva ativa
            print(f"ℹ️  Você está trabalhando na sessão '{data_adapter.active_saved_session}'")
            if current_info:
                print(f"   • {current_info['unique_people']} personalidade(s) na sessão")
            
            print("\nO que deseja fazer?")
            print(f"[1] - Continuar (sair da sessão '{data_adapter.active_saved_session}')")
            print(f"[2] - Atualizar sessão '{data_adapter.active_saved_session}' primeiro")
            print("[0] - Cancelar")
            
            choice = input("Escolha uma opção: ").strip()
            if choice == "2":
                # Atualiza sessão primeiro
                save_result = manage_sessions("data/sessions", "save")
                if not save_result:
                    print("❌ Cancelando criação de nova sessão")
                    return False
            elif choice == "0":
                print("❌ Operação cancelada")
                return False
            # Se escolheu 1, continua normalmente
            
        else:
            # Há dados em sessão temporária
            print(f"{VERMELHO}⚠️  ATENÇÃO: Há dados na sessão temporária atual que serão perdidos!{NORMAL}")
            if current_info:
                print(f"   • {current_info['unique_people']} personalidade(s) não salva(s)")
            
            print("\nO que deseja fazer?")
            print("[1] - Continuar (dados temporários serão perdidos)")
            print("[2] - Salvar sessão temporária primeiro")
            print("[0] - Cancelar")
            
            choice = input("Escolha uma opção: ").strip()
            if choice == "2":
                # Salva sessão temporária primeiro
                save_result = manage_sessions("data/sessions", "save")
                if not save_result:
                    print("❌ Cancelando criação de nova sessão")
                    return False
            elif choice == "0":
                print("❌ Operação cancelada")
                return False
            # Se escolheu 1, continua normalmente
    else:
        # Não há dados, apenas confirma
        print(f"{VERDE}🔄 CRIAR NOVA SESSÃO TEMPORÁRIA{NORMAL}")
        print("ℹ️  Nenhum dado será perdido (sessão atual vazia)")
        
        confirm = input("Confirma criar nova sessão temporária? (s/N): ").strip().lower()
        if confirm != 's':
            print("❌ Operação cancelada")
            return False
    
    # Executa a criação da nova sessão temporária
    print()
    success = data_adapter.create_new_temp_session()
    
    if success:
        print(f"\n{VERDE}✅ Nova sessão temporária criada com sucesso!{NORMAL}")
        return True
    else:
        print(f"\n{VERMELHO}❌ Erro ao criar nova sessão temporária{NORMAL}")
        return False


def display_warning_on_exit():
    """Exibe aviso ao sair dependendo do estado da sessão"""
    AMARELO = "\033[1;33m"
    VERMELHO = "\033[1;31m"
    NORMAL = "\033[0m"
    
    current_info = data_adapter.get_current_session_info()
    has_data = current_info is not None and current_info.get('unique_people', 0) > 0
    
    if has_data:
        if data_adapter.active_saved_session:
            print(f"{AMARELO}⚠️  Você tem dados na sessão '{data_adapter.active_saved_session}'.{NORMAL}")
        else:
            print(f"{VERMELHO}⚠️  ATENÇÃO: Você tem dados em uma sessão TEMPORÁRIA que será perdida!{NORMAL}")
        print("   Para salvar, use a opção 4 do menu antes de sair.")
    
    print("Tchau! 👋")