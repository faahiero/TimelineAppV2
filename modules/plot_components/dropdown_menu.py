from dash import dcc

def dropdown_component(dataframe):
    return dcc.Dropdown(
        id='name-dropdown',
        # nome completo + termo buscado + século. Exemplo: 'Joaquim Jose da Silva Xavier (Tiradentes) - Século 19'
        options=[{'label': f'{row["Nome Completo"]} ({row["Termo Buscado"]}) - Século {row["Século"]}', 'value': row["Nome Completo"]} for idx, row in dataframe.iterrows()],
        value=None,
        multi=True
    )