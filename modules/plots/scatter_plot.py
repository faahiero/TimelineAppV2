import plotly.express as px


def scatter_plot_chart(dataframe):
    # count the number of occurrences of a century in each country
    counts = dataframe.groupby(['Origem/Nacionalidade', 'Século']).size().reset_index(name='Ocorrências')

    # create the scatter plot
    fig = px.scatter(counts, y='Século', x='Origem/Nacionalidade', size='Ocorrências', size_max=50,
                     color='Origem/Nacionalidade', hover_name='Origem/Nacionalidade',
                     hover_data={'Século': True, 'Ocorrências': True},
                     labels={'Século': 'Século', 'Ocorrências': 'Ocorrências'})
    fig.update_layout(
        title={
            'text': '<b>Ocorrência de Nacionalidades por Século (Dispersão)</b>',
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        margin=dict(
            t=100,  # add margin to the top of the plot
        ),
        xaxis=dict(
            title='Origem/Nacionalidade',
            tickfont=dict(size=15),  # customize tick font size
        ),
        yaxis=dict(
            title='Século',
            tickfont=dict(size=15),  # customize tick font size
            dtick=5,  # set the step to 1
        ),
        width=1600,
        height=700,
    )
    return fig
