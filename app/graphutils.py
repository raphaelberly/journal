import os
from typing import Dict
from plotly import graph_objs as go

# get path to current file's folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def cleanup_grade_distribution_plots(path_starts_with: str):
    dirname = os.path.dirname(path_starts_with)
    for file in os.listdir(dirname):
        filepath = os.path.join(dirname, file)
        if filepath.startswith(path_starts_with):
            assert filepath.endswith('.png')
            os.remove(filepath)


def plot_grade_distribution(grades: Dict[int, int], path: str):
    fig = go.Figure(data=[go.Bar(
        x=list(grades.keys()),
        y=list(grades.values()),
        marker_color='#6caee0'
    )])
    fig.update_layout(
        plot_bgcolor='white',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 11)),
            ticktext=[str(i) for i in range(1, 11)],
            tickfont_color='#6caee0',
            tickfont_size=18,
        ),
        yaxis=dict(showticklabels=False),
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    # Show value of each column on top of it in color #6caee0 and size 16
    fig.update_traces(texttemplate='%{y}', textposition='outside', textfont_color='#6caee0', textfont_size=18)
    fig.write_image(path)
