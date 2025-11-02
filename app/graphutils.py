import os
from typing import Dict, Optional, Tuple
from plotly import graph_objs as go

# get path to current file's folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def cleanup_distribution_plots(path_starts_with: str):
    dirname = os.path.dirname(path_starts_with)
    for file in os.listdir(dirname):
        filepath = os.path.join(dirname, file)
        if filepath.startswith(path_starts_with):
            assert filepath.endswith('.png')
            os.remove(filepath)


def plot_distribution(key_values: Dict[int, int], path: str, force_range: Optional[list] = None) -> go.Figure:
    fig = go.Figure(data=[go.Bar(
        x=list(key_values.keys()),
        y=list(key_values.values()),
        marker_color='#6caee0'
    )])
    range_ = force_range or range(min(key_values.keys()), max(key_values.keys()) + 1)
    fig.update_layout(
        plot_bgcolor='white',
        xaxis=dict(
            tickmode='array',
            tickvals=force_range or range_,
            ticktext=[str(i) for i in range_],
            tickfont_color='#6caee0',
            tickfont_size=22,
            tickfont_family='Trebuchet MS'
        ),
        yaxis=dict(showticklabels=False),
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    # Show value of each column on top of it in color #6caee0 and size 16
    fig.update_traces(
        texttemplate='%{y}',
        textposition='outside',
        textfont_color='#6caee0',
        textfont_size=22,
        textfont_family='Trebuchet MS'
    )
    fig.write_image(path)
