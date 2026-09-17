import os
from typing import Dict, Optional

# Chart geometry, kept from the previous plotly rendering: a 700x500 canvas whose bars
# sit on a baseline 28px above the bottom, in evenly spread slots filled at 80%
WIDTH = 700
HEIGHT = 500
BASELINE_Y = 472
BAR_FILL = 0.8
TOP_PADDING = 34
LABEL_GAP = 10
THEME_COLOUR = '#6caee0'
FONT_FAMILY = 'Trebuchet MS, Helvetica, sans-serif'
FONT_SIZE = 22


def cleanup_distribution_plots(path_starts_with: str):
    # The folder is gitignored, so it may not exist yet on a fresh checkout
    dirname = os.path.dirname(path_starts_with)
    os.makedirs(dirname, exist_ok=True)
    for file in os.listdir(dirname):
        filepath = os.path.join(dirname, file)
        if filepath.startswith(path_starts_with):
            # .png covers the charts generated before the switch to SVG
            assert filepath.endswith(('.svg', '.png'))
            os.remove(filepath)


def plot_distribution(key_values: Dict[int, int], path: str, force_range: Optional[list] = None) -> None:
    keys = force_range or sorted(key_values)
    slot = WIDTH / len(keys)
    bar_width = slot * BAR_FILL
    plot_height = BASELINE_Y - TOP_PADDING
    highest = max(key_values.values())
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="white"/>',
        f'<g font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}" fill="{THEME_COLOUR}" text-anchor="middle">',
    ]
    # Draw each bar with its value above it and its key underneath
    for i, key in enumerate(keys):
        centre = i * slot + slot / 2
        parts.append(f'<text x="{centre:.1f}" y="{HEIGHT - 6}">{key}</text>')
        value = key_values.get(key, 0)
        if not value:
            continue
        height = value / highest * plot_height
        top = BASELINE_Y - height
        parts.append(
            f'<rect x="{centre - bar_width / 2:.1f}" y="{top:.1f}" '
            f'width="{bar_width:.1f}" height="{height:.1f}" fill="{THEME_COLOUR}"/>'
        )
        parts.append(f'<text x="{centre:.1f}" y="{top - LABEL_GAP:.1f}">{value}</text>')
    parts += ['</g>', '</svg>']
    with open(path, 'w') as f:
        f.write(''.join(parts))
