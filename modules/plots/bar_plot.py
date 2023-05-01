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
            tickfont=dict(size=15),  # customize tick font size
        ),
        yaxis=dict(
            title='# Ocorrências',
            dtick=1,  # set the step to 1
            tickmode='linear',  # use a linear tick mode
            tickfont=dict(size=15)  # customize tick font size
        ),
        legend_title='Século',
        legend=dict(
            yanchor="top",
            y=0.95,
            xanchor="right",
            x=1.05
        ),
        width=1600,
        height=700,
    )

    return fig
