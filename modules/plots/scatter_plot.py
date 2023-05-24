# import plotly.express as px
#
#
# def scatter_plot_chart(dataframe):
#     # count the number of occurrences of a century in each country
#     counts = dataframe.groupby(['Origem/Nacionalidade', 'Século']).size().reset_index(name='Ocorrências')
#
#     # create the scatter plot
#     fig = px.scatter(counts, y='Século', x='Origem/Nacionalidade', size='Ocorrências', size_max=50,
#                      color='Origem/Nacionalidade', hover_name='Origem/Nacionalidade',
#                      hover_data={'Século': True, 'Ocorrências': True},
#                      labels={'Século': 'Século', 'Ocorrências': 'Ocorrências'})
#     fig.update_layout(
#         title={
#             'text': '<b>Ocorrência de Nacionalidades por Século (Dispersão)</b>',
#             'x': 0.5,
#             'y': 0.95,
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': {'size': 20}
#         },
#         margin=dict(
#             t=100,  # add margin to the top of the plot
#         ),
#         xaxis=dict(
#             title='Origem/Nacionalidade',
#             tickfont=dict(size=15),  # customize tick font size
#         ),
#         yaxis=dict(
#             title='Século',
#             tickfont=dict(size=15),  # customize tick font size
#             dtick=5,  # set the step to 1
#         ),
#         width=1600,
#         height=700,
#     )
#     return fig
#




# import plotly.express as px
#
# def scatter_plot_chart(dataframe):
#     # count the number of occurrences of a century in each country
#     counts = dataframe.groupby(['Origem/Nacionalidade', 'Século']).size().reset_index(name='Ocorrências')
#
#     # extract the century value and format it for the Y axis
#     try:
#         counts['Século'] = counts['Século'].apply(lambda x: str(x) + ' a.C.' if int(x) < 0 else str(x))
#     except ValueError:
#         pass
#
#     # sort the counts dataframe by 'Século'
#     counts = counts.sort_values('Século')
#
#     # create the scatter plot
#     fig = px.scatter(counts, y='Século', x='Origem/Nacionalidade', size='Ocorrências', size_max=50,
#                      color='Origem/Nacionalidade', hover_name='Origem/Nacionalidade',
#                      hover_data={'Século': True, 'Ocorrências': True},
#                      labels={'Século': 'Século', 'Ocorrências': 'Ocorrências'})
#
#     unique_centuries = counts['Século'].unique()
#
#     tickvals = list(range(len(unique_centuries)))  # Generate tick values
#     ticktext = [unique_centuries[i] for i in tickvals]  # Generate tick labels
#
#     fig.update_layout(
#         title={
#             'text': '<b>Ocorrência de Nacionalidades por Século (Dispersão)</b>',
#             'x': 0.5,
#             'y': 0.95,
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': {'size': 20}
#         },
#         margin=dict(
#             t=100,  # add margin to the top of the plot
#         ),
#         xaxis=dict(
#             title='Origem/Nacionalidade',
#             tickfont=dict(size=15),  # customize tick font size
#         ),
#         yaxis=dict(
#             title='Século',
#             tickfont=dict(size=15),  # customize tick font size
#             tickmode='array',
#             tickvals=tickvals,
#             ticktext=ticktext,
#         ),
#         width=1600,
#         height=700,
#     )
#
#     return fig









# import plotly.express as px
#
# def scatter_plot_chart(dataframe):
#     # count the number of occurrences of a century in each country
#     counts = dataframe.groupby(['Origem/Nacionalidade', 'Século']).size().reset_index(name='Ocorrências')
#
#     # extract the century value and format it for the Y axis
#     try:
#         counts['Século'] = counts['Século'].apply(lambda x: str(x) + ' a.C.' if int(x) < 0 else str(x))
#     except ValueError:
#         pass
#
#     # sort the counts dataframe by 'Século'
#     counts = counts.sort_values('Século')
#
#     # create the scatter plot with inverted axes
#     fig = px.scatter(counts, x='Século', y='Origem/Nacionalidade', size='Ocorrências', size_max=50,
#                      color='Origem/Nacionalidade', hover_name='Origem/Nacionalidade',
#                      hover_data={'Século': True, 'Ocorrências': True},
#                      labels={'Século': 'Século', 'Ocorrências': 'Ocorrências'})
#
#     unique_centuries = counts['Século'].unique()
#
#     tickvals = list(range(len(unique_centuries)))  # Generate tick values
#     ticktext = [unique_centuries[i] for i in tickvals]  # Generate tick labels
#
#     fig.update_layout(
#         title={
#             'text': '<b>Ocorrência de Nacionalidades por Século (Dispersão)</b>',
#             'x': 0.5,
#             'y': 0.95,
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': {'size': 20}
#         },
#         margin=dict(
#             t=100,  # add margin to the top of the plot
#         ),
#         xaxis=dict(
#             title='Século',
#             tickfont=dict(size=15),  # customize tick font size
#             tickmode='array',
#             tickvals=tickvals,
#             ticktext=ticktext,
#         ),
#         yaxis=dict(
#             title='Origem/Nacionalidade',
#             tickfont=dict(size=15),  # customize tick font size
#         ),
#         width=1600,
#         height=700,
#     )
#
#     return fig

# import plotly.express as px
# import pandas as pd
#
# def scatter_plot_chart(dataframe):
#     # count the number of occurrences of a century in each country
#     counts = dataframe.groupby(['Origem/Nacionalidade', 'Século']).size().reset_index(name='Ocorrências')
#
#     # extract the century value and format it for the X axis
#     try:
#         counts['Século'] = counts['Século'].apply(lambda x: str(x) + ' a.C.' if int(x) < 0 else str(x))
#     except ValueError:
#         pass
#
#     # create a custom sorting key function
#     def sort_key(century):
#         if 'a.C.' in century:
#             return -int(century.split()[0])
#         else:
#             return int(century)
#
#     # sort the counts dataframe by 'Século' using the custom sorting key
#     counts['SortKey'] = counts['Século'].apply(sort_key)
#     counts = counts.sort_values('SortKey')
#     counts = counts.drop(columns='SortKey')
#
#     unique_centuries = counts['Século'].unique()
#
#     # create the scatter plot
#     fig = px.scatter(counts, x='Século', y='Origem/Nacionalidade', size='Ocorrências', size_max=50,
#                      color='Origem/Nacionalidade', hover_name='Origem/Nacionalidade',
#                      hover_data={'Século': True, 'Ocorrências': True},
#                      labels={'Século': 'Século', 'Ocorrências': 'Ocorrências'})
#
#     fig.update_layout(
#         title={
#             'text': '<b>Ocorrência de Nacionalidades por Século (Dispersão)</b>',
#             'x': 0.5,
#             'y': 0.95,
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': {'size': 20}
#         },
#         margin=dict(
#             t=100,  # add margin to the top of the plot
#         ),
#         xaxis=dict(
#             title='Século',
#             tickfont=dict(size=15),  # customize tick font size
#             dtick=1,  # set the interval between ticks
#         ),
#         yaxis=dict(
#             title='Origem/Nacionalidade',
#             tickfont=dict(size=15),  # customize tick font size
#         ),
#         width=1600,
#         height=700,
#     )
#
#     return fig


#TODO EIXO X ORDENADO
# import plotly.express as px
# import pandas as pd
#
# def scatter_plot_chart(dataframe):
#     # count the number of occurrences of a century in each country
#     counts = dataframe.groupby(['Origem/Nacionalidade', 'Século']).size().reset_index(name='Ocorrências')
#
#     # extract the century value and format it for the X axis
#     try:
#         counts['Século'] = counts['Século'].apply(lambda x: str(x) + ' a.C.' if int(x) < 0 else str(x))
#     except ValueError:
#         pass
#
#     # create a custom sorting key function
#     def sort_key(century):
#         if 'a.C.' in century:
#             return -int(century.split()[0])
#         else:
#             return int(century)
#
#     # sort the counts dataframe by 'Século' using the custom sorting key
#     counts['SortKey'] = counts['Século'].apply(sort_key)
#     counts = counts.sort_values('SortKey')
#     counts = counts.drop(columns='SortKey')
#
#     unique_centuries = counts['Século'].unique()
#
#     # create the scatter plot
#     fig = px.scatter(counts, x='Século', y='Origem/Nacionalidade', size='Ocorrências', size_max=50,
#                      color='Origem/Nacionalidade', hover_name='Origem/Nacionalidade',
#                      hover_data={'Século': True, 'Ocorrências': True},
#                      labels={'Século': 'Século', 'Ocorrências': 'Ocorrências'})
#
#     fig.update_layout(
#         title={
#             'text': '<b>Ocorrência de Nacionalidades por Século (Dispersão)</b>',
#             'x': 0.5,
#             'y': 0.95,
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': {'size': 20}
#         },
#         margin=dict(
#             t=100,  # add margin to the top of the plot
#         ),
#         xaxis=dict(
#             title='Século',
#             tickfont=dict(size=15),  # customize tick font size
#             categoryorder='array',
#             categoryarray=unique_centuries,  # specify the order of categories
#         ),
#         yaxis=dict(
#             title='Origem/Nacionalidade',
#             tickfont=dict(size=15),  # customize tick font size
#         ),
#         width=1600,
#         height=700,
#     )
#
#     return fig


import plotly.express as px
import pandas as pd

def scatter_plot_chart(dataframe):
    # count the number of occurrences of a century in each country
    counts = dataframe.groupby(['Origem/Nacionalidade', 'Século']).size().reset_index(name='Ocorrências')

    # extract the century value and format it for the X axis
    try:
        counts['Século'] = counts['Século'].apply(lambda x: str(x) + ' a.C.' if int(x) < 0 else str(x))
    except ValueError:
        pass

    # create a custom sorting key function
    def sort_key(century):
        if 'a.C.' in century:
            return -int(century.split()[0])
        else:
            return int(century)

    # sort the counts dataframe by 'Século' using the custom sorting key
    counts['SortKey'] = counts['Século'].apply(sort_key)
    counts = counts.sort_values('SortKey')
    counts = counts.drop(columns='SortKey')

    unique_centuries = counts['Século'].unique()

    # create the scatter plot
    fig = px.scatter(counts, x='Século', y='Origem/Nacionalidade', size='Ocorrências', size_max=50,
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
            title='Século',
            tickfont=dict(size=15),  # customize tick font size
            categoryorder='array',
            categoryarray=unique_centuries,  # specify the order of categories
            fixedrange=True,  # disable panning and zooming by dragging
            range=[-0.5, len(unique_centuries) - 0.5],  # set the initial range of the X axis
            showspikes=True,  # show spikes on hover
            spikemode='toaxis',  # show spikes to the axis
            spikedash='dot',  # dashed spike lines
            spikethickness=1,  # spike line thickness
            showline=True,  # show axis line
            linecolor='gray',  # axis line color
            linewidth=1,  # axis line width
            mirror=True,  # mirror the axis line
            scaleratio=1,  # maintain aspect ratio during zoom
            rangemode='normal',  # allow zooming beyond the data range
            rangebreaks=[dict(bounds=[-0.5, -0.49], pattern=''),  # break
                            dict(bounds=[len(unique_centuries) - 0.51, len(unique_centuries) - 0.5], pattern='')],  # break
        ),
        yaxis=dict(
            title='Origem/Nacionalidade',
            tickfont=dict(size=15),  # customize tick font size
            fixedrange=True,  # disable panning and zooming by dragging
            showspikes=True,  # show spikes on hover
            spikemode='toaxis',  # show spikes to the axis
            spikedash='dot',  # dashed spike lines
            spikethickness=1,  # spike line thickness
            showline=True,  # show axis line
            linecolor='gray',  # axis line color
            linewidth=1,  # axis line width
            mirror=True,  # mirror the axis line
            scaleratio=1,  # maintain aspect ratio during zoom
            rangemode='normal',  # allow zooming beyond the data range
            rangebreaks=[dict(bounds=[-0.5, -0.49], pattern=''),  # break
                            dict(bounds=[len(unique_centuries) - 0.51, len(unique_centuries) - 0.5], pattern='')],  # break
        ),
        width=1600,
        height=900,
    )

    return fig


