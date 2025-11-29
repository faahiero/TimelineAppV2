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

    # Correção para evitar crash do RangeSlider quando min == max (apenas 1 século nos dados)
    if seculo_min == seculo_max:
        seculo_min -= 1
        seculo_max += 1
        # Atualiza marks para incluir os novos limites, se não existirem
        if str(seculo_min) not in seculo_values_marks:
            seculo_values_marks[str(seculo_min)] = str(seculo_min) if seculo_min > 0 else f"{abs(seculo_min)} a.C."
        if str(seculo_max) not in seculo_values_marks:
            seculo_values_marks[str(seculo_max)] = str(seculo_max) if seculo_max > 0 else f"{abs(seculo_max)} a.C."

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