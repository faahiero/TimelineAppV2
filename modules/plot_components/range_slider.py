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

    return dcc.RangeSlider(
        id='seculo-slider',
        min=seculo_min,
        max=seculo_max,
        value=[seculo_min, seculo_max],
        marks=seculo_values_marks,
        step=None,
        allowCross=True,
        vertical=False
    )