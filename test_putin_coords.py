#!/usr/bin/env python3
"""
Teste rápido para verificar se Putin tem coordenadas válidas
"""
import pandas as pd
import os

def test_putin_coordinates():
    csv_file = "person_info.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo {csv_file} não encontrado")
        return
    
    df = pd.read_csv(csv_file)
    
    # Procura por Putin
    putin_rows = df[df['Nome Completo'].str.contains('Putin', case=False, na=False)]
    
    if putin_rows.empty:
        print("❌ Putin não encontrado no arquivo CSV")
        return
    
    print("📊 Dados de Putin encontrados:")
    for idx, row in putin_rows.iterrows():
        print(f"\n👤 Nome: {row['Nome Completo']}")
        print(f"🌍 País: {row['Origem/Nacionalidade']}")
        print(f"📍 Coordenadas: {row['Latitude']}, {row['Longitude']}")
        print(f"📅 Século: {row['Século']}")
        
        # Verifica se as coordenadas são válidas
        try:
            lat = float(row['Latitude'])
            lon = float(row['Longitude'])
            
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                print("✅ Coordenadas válidas - Putin deve aparecer no mapa!")
            else:
                print("❌ Coordenadas fora do range válido")
        except (ValueError, TypeError):
            print("❌ Coordenadas inválidas (não numéricas)")
    
    # Verifica quantas pessoas têm coordenadas válidas
    valid_coords = 0
    invalid_coords = 0
    
    for idx, row in df.iterrows():
        try:
            lat = float(row['Latitude'])
            lon = float(row['Longitude'])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                valid_coords += 1
            else:
                invalid_coords += 1
        except (ValueError, TypeError):
            invalid_coords += 1
    
    print(f"\n📈 Resumo do arquivo:")
    print(f"✅ Pessoas com coordenadas válidas: {valid_coords}")
    print(f"❌ Pessoas com coordenadas inválidas: {invalid_coords}")
    print(f"📊 Total de pessoas: {len(df)}")

if __name__ == "__main__":
    test_putin_coordinates()