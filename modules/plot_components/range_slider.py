from dash import dcc


def range_slide_component(dataframe):
    return dcc.RangeSlider(
        id='seculo-slider',
        min=dataframe['Século'].min(),
        max=dataframe['Século'].max(),
        value=[dataframe['Século'].min(), dataframe['Século'].max()],
        marks={str(seculo): str(seculo) for seculo in dataframe['Século'].unique()},
        step=None
    )