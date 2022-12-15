import os
import shutil
import time
import webbrowser
import pandas as pd
import folium


# Função que gera a visualização com as informações salvas no arquivo csv.
def generate_visualization():
    timestamp_fname = time.strftime("%Y%m%d-%H%M%S") + "_"
    df = pd.read_csv("person_info.csv")
    df.to_csv("person_info.csv", index=False)
    folium_map = folium.Map()

    for idx, linha in df.iterrows():
        html = f"""
        <div id="dados" style='border:solid; border-radius:10px; width: 700px;height: 300px'>
            <div style="padding: 10px;margin-top:7px;float: right">
                <img src="{linha['Imagem']}"
                width="189" height="266"/>
            </div>
            <h2 style="text-align: center">{linha['Nome Completo']}</h2>
                <p style="font-weight: bold;margin-left: 20px">Dados Biográficos</p>
                    <ul style="margin-left: 20px">
                        <li>Origem/Nacionalidade: {linha['Origem/Nacionalidade']}</li>    
                        <li>Data de Nascimento: {linha['Data de Nascimento']}</li>
                        <li>Local de Nascimento: {linha['Local de Nascimento']}</li>
                        <li>Data de Falecimento: {linha['Data de Falecimento']}</li>
                        <li>Local de Falecimento: {linha['Local de Falecimento']}</li>
                    </ul>
                </p>
            <p style="margin-left: 20px">Link para artigo completo na  <a href="{linha['Url']}" 
            target="_blank">Wikipedia</a></p>
        </div>
        """
        iframe = folium.IFrame(html=html, width=730, height=330)
        popup = folium.Popup(iframe, max_width=2650)
        folium.Marker(
            [linha['Latitude'], linha['Longitude']],
            popup=popup,
            tooltip=linha['Nome Completo']
        ).add_to(folium_map)

        if not os.path.exists("data"):
            os.makedirs("data")
        folium_map.save("data/" + timestamp_fname + 'map.html')

    shutil.move('person_info.csv', 'data/' +
                timestamp_fname + 'person_info.csv')
    webbrowser.open('file://' + os.path.realpath('data/' +
                    timestamp_fname + 'map.html'))