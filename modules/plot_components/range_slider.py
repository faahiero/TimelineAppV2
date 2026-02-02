from dash import dcc


def range_slide_component(dataframe):
    seculo_values = dataframe['Século'].unique()

    seculo_values_marks = {}
    # Verifica se o sufixo "a.C." está presente em algum valor da coluna
    if any("a.C." in str(valor) for valor in seculo_values):
        seculo_values_int = []

        for valor in seculo_values:
            if "a.C." in str(valor):
                valor_int = -int(valor.replace(" a.C.", ""))
                seculo_values_marks[str(valor_int)] = f"{abs(valor_int)} a.C."
            else:
                valor_int = int(valor)
                seculo_values_marks[str(valor_int)] = str(valor_int)
            seculo_values_int.append(valor_int)

        seculo_min = min(seculo_values_int)
        seculo_max = max(seculo_values_int)
        position = "left"
    else:
        seculo_min = min(int(valor) for valor in seculo_values)
        seculo_max = max(int(valor) for valor in seculo_values)
        position = "right"
        for valor in seculo_values:
            seculo_values_marks[str(valor)] = str(valor)

    # Salva os valores originais para usar no 'value' do slider
    original_seculo_min = seculo_min
    original_seculo_max = seculo_max

    # Se houver apenas um século, usa dcc.Slider (ponto único)
    if seculo_min == seculo_max:
        # Cria um range artificial apenas para centralizar o ponto
        slider_min = seculo_min - 1
        slider_max = seculo_max + 1
        
        # Limpa os marks para mostrar APENAS o século real
        # Isso esconde os números do range expandido (18 e 20)
        single_mark = {str(seculo_min): str(seculo_min)} if seculo_min > 0 else {str(seculo_min): f"{abs(seculo_min)} a.C."}

        return dcc.Slider(
            id='seculo-slider',
            min=slider_min,
            max=slider_max,
            value=original_seculo_min,
            marks=single_mark, # Mostra rótulo apenas para o valor central
            step=1,
            vertical=False,
            persistence=False,
            disabled=True,
            included=False, # Remove o preenchimento (sombra) à esquerda
            tooltip={'always_visible': False}
        )

    return dcc.RangeSlider(
        id='seculo-slider',
        min=seculo_min,
        max=seculo_max,
        value=[original_seculo_min, original_seculo_max],
        marks=seculo_values_marks,
        step=1,
        allowCross=True,
        vertical=False,
        persistence=False,
        disabled=False
    )