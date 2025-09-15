#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migração para importar dados CSV existentes para SQLite
"""
import os
import glob
from modules.database_manager import db_manager
from modules.data_adapter import data_adapter


def migrate_csv_files():
    """Migra todos os arquivos CSV existentes para SQLite"""
    print("=== MIGRAÇÃO PARA SQLITE ===")
    print()
    
    # Lista todos os arquivos CSV
    csv_files = []
    
    # CSV atual
    if os.path.exists("person_info.csv"):
        csv_files.append("person_info.csv")
    
    # CSVs na pasta data/
    if os.path.exists("data/"):
        data_csvs = glob.glob("data/*_person_info.csv")
        csv_files.extend(data_csvs)
    
    # CSVs de sessões antigas
    if os.path.exists("data/sessions/"):
        session_csvs = glob.glob("data/sessions/*.csv")
        csv_files.extend(session_csvs)
    
    if not csv_files:
        print("❌ Nenhum arquivo CSV encontrado para migrar")
        return
    
    print(f"📁 Encontrados {len(csv_files)} arquivo(s) CSV:")
    for csv_file in csv_files:
        print(f"   - {csv_file}")
    
    print()
    confirm = input("Deseja prosseguir com a migração? (s/n): ")
    if confirm.lower() != 's':
        print("❌ Migração cancelada")
        return
    
    print("\n🔄 Iniciando migração...")
    
    total_imported = 0
    sessions_created = 0
    
    # Importa CSV atual para sessão de trabalho
    if "person_info.csv" in csv_files:
        print("\n📋 Importando sessão atual...")
        count = data_adapter.import_existing_csv("person_info.csv")
        if count > 0:
            print(f"✅ {count} personalidade(s) importada(s) para sessão atual")
            total_imported += count
    
    # Importa CSVs de sessões antigas
    session_files = [f for f in csv_files if f.startswith("data/sessions/")]
    for session_file in session_files:
        session_name = os.path.basename(session_file).replace('.csv', '')
        print(f"\n📂 Importando sessão: {session_name}")
        
        # Importa dados para o banco
        count = db_manager.import_from_csv(session_file)
        if count > 0:
            # Cria a sessão
            session_id = db_manager.create_session(
                session_name, 
                f"Migrada de {session_file}"
            )
            
            if session_id:
                # Busca as personalidades recém-importadas e adiciona à sessão
                personalities = db_manager.get_personalities()
                recent_ids = [p['id'] for p in personalities[-count:]]
                
                if db_manager.add_to_session(session_name, recent_ids):
                    print(f"✅ Sessão '{session_name}' criada com {count} personalidade(s)")
                    sessions_created += 1
                    total_imported += count
                else:
                    print(f"⚠️  Dados importados mas erro ao criar sessão")
            else:
                print(f"⚠️  Dados importados mas sessão já existe")
    
    # Importa outros CSVs como sessões individuais
    other_files = [f for f in csv_files if not f.startswith("data/sessions/") and f != "person_info.csv"]
    for csv_file in other_files:
        file_name = os.path.basename(csv_file).replace('.csv', '').replace('_person_info', '')
        session_name = f"migrada_{file_name}"
        
        print(f"\n📄 Importando arquivo: {csv_file}")
        count = db_manager.import_from_csv(csv_file)
        
        if count > 0:
            session_id = db_manager.create_session(
                session_name,
                f"Migrada de {csv_file}"
            )
            
            if session_id:
                personalities = db_manager.get_personalities()
                recent_ids = [p['id'] for p in personalities[-count:]]
                
                if db_manager.add_to_session(session_name, recent_ids):
                    print(f"✅ Sessão '{session_name}' criada com {count} personalidade(s)")
                    sessions_created += 1
                    total_imported += count
    
    print(f"\n🎉 MIGRAÇÃO CONCLUÍDA!")
    print(f"   • {total_imported} personalidade(s) importada(s)")
    print(f"   • {sessions_created} sessão(ões) criada(s)")
    print(f"   • Banco de dados: data/geohist.db")
    
    # Mostra estatísticas
    stats = db_manager.get_statistics()
    if stats:
        print(f"\n📊 ESTATÍSTICAS DO BANCO:")
        print(f"   • Total de personalidades: {stats['total_personalities']}")
        print(f"   • Total de sessões: {stats['total_sessions']}")
        
        db_size = stats.get('database_size', 0)
        if db_size > 0:
            db_size_mb = db_size / (1024 * 1024)
            print(f"   • Tamanho do banco: {db_size_mb:.2f} MB")


def create_backup():
    """Cria backup dos arquivos CSV antes da migração"""
    print("💾 Criando backup dos arquivos CSV...")
    
    backup_dir = "backup_csv_migration"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup do CSV atual
    if os.path.exists("person_info.csv"):
        shutil.copy2("person_info.csv", f"{backup_dir}/person_info_{timestamp}.csv")
    
    # Backup da pasta data/
    if os.path.exists("data/"):
        shutil.copytree("data/", f"{backup_dir}/data_{timestamp}", dirs_exist_ok=True)
    
    print(f"✅ Backup criado em: {backup_dir}/")


if __name__ == "__main__":
    print("🔄 MIGRAÇÃO PARA SQLITE")
    print("Este script irá migrar todos os dados CSV existentes para SQLite")
    print()
    
    # Cria backup
    create_backup()
    
    # Executa migração
    migrate_csv_files()
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Execute: python3 main.py")
    print("   2. Use opção [8] para ver estatísticas do banco")
    print("   3. Teste as funcionalidades normalmente")
    print("   4. Os dados CSV originais foram preservados no backup")