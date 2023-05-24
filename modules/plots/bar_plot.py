import plotly.graph_objects as go

def stacked_bar_plot(dataframe):
    counts = dataframe.groupby(['Origem/Nacionalidade', 'Século']).size().unstack()
    fig = go.Figure(data=[
        go.Bar(name=century, x=counts.index, y=counts[century]) for century in counts.columns
    ])

    fig.update_layout(
        title={
            'text': '<b>Ocorrência de Nacionalidades por Século (Barras Empilhadas)</b>',
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20},
        },
        barmode='stack',
        xaxis=dict(
            title='Origem/Nacionalidade',
            tickfont=dict(size=15),
        ),
        yaxis=dict(
            title='# Ocorrências',
            dtick=1,
            tickmode='linear',
            tickfont=dict(size=15)
        ),
        legend_title='Século',
        legend=dict(
            yanchor="top",
            y=0.98,  # Ajuste o valor para afastar a legenda para cima
            xanchor="right",
            x=1.1,  # Ajuste o valor para afastar a legenda para a direita
        ),
        width=1600,
        height=900,
    )

    return fig
