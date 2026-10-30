import os
from contextlib import suppress
from datetime import date, timedelta
from typing import Dict, List, Optional

# Chart geometry, kept from the previous plotly rendering: a 700x500 canvas whose bars
# sit on a baseline 28px above the bottom, in evenly spread slots filled at 80%
WIDTH = 700
HEIGHT = 500
BASELINE_Y = 472
BAR_FILL = 0.8
TOP_PADDING = 34
LABEL_GAP = 10
THEME_COLOUR = '#6caee0'
# Calendar and cumulative charts: days with several movies, days with none, and the previous year's line
DARK_COLOUR = '#2d6ea3'
EMPTY_COLOUR = '#efefef'
PREVIOUS_COLOUR = '#bbbbbb'
FONT_FAMILY = 'Trebuchet MS, Helvetica, sans-serif'
FONT_SIZE = 22


def cleanup_distribution_plots(path_starts_with: str):
    # The folder is gitignored, so it may not exist yet on a fresh checkout
    dirname = os.path.dirname(path_starts_with)
    os.makedirs(dirname, exist_ok=True)
    for file in os.listdir(dirname):
        filepath = os.path.join(dirname, file)
        if filepath.startswith(path_starts_with):
            assert filepath.endswith('.svg')
            # Another gunicorn worker, rendering the same page at the same time, may have removed it first
            with suppress(FileNotFoundError):
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


def _days(year: int, end: Optional[date] = None) -> List[date]:
    first = date(year, 1, 1)
    last = end or date(year, 12, 31)
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def plot_cumulative(daily_counts: Dict[date, int], year: int, end: date, path: str) -> None:
    left, right = 20, 640
    # Spread each year along the same width, whatever its number of days
    def x(day: date) -> float:
        first, last = date(day.year, 1, 1), date(day.year, 12, 31)
        return left + (day - first).days / (last - first).days * (right - left)
    # Sum up the movies day after day: the whole previous year, the applicable one up to its end
    lines = {}
    for line_year, line_end in [(year - 1, None), (year, end)]:
        total, points = 0, []
        for day in _days(line_year, line_end):
            total += daily_counts.get(day, 0)
            points.append((x(day), total))
        lines[line_year] = points
    current = lines[year][-1][1]
    previous = lines[year - 1][min(len(lines[year]), len(lines[year - 1])) - 1][1]
    highest = max(current, lines[year - 1][-1][1], 1)
    # Leave room above the lines for two labels
    def y(value: int) -> float:
        return BASELINE_Y - value / highest * (BASELINE_Y - TOP_PADDING - 30)
    end_x = x(end)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="white"/>',
        f'<g font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">',
        f'<line x1="{left}" y1="{BASELINE_Y}" x2="{right}" y2="{BASELINE_Y}" '
        f'stroke="{EMPTY_COLOUR}" stroke-width="2"/>',
    ]
    # Mark today while the year is still under way, along with the previous year's total
    if end < date(year, 12, 31):
        parts.append(f'<line x1="{end_x:.1f}" y1="{TOP_PADDING}" x2="{end_x:.1f}" y2="{BASELINE_Y}" '
                     f'stroke="{EMPTY_COLOUR}" stroke-width="2" stroke-dasharray="6 6"/>')
        parts.append(f'<text x="{right + 8}" y="{y(lines[year - 1][-1][1]) + 8:.1f}" '
                     f'fill="{PREVIOUS_COLOUR}">{lines[year - 1][-1][1]}</text>')
    # Draw both lines, the applicable year over the previous one, each ending on a dot
    for line_year, colour, width, radius, value in [(year - 1, PREVIOUS_COLOUR, 4, 7, previous),
                                                     (year, THEME_COLOUR, 6, 8, current)]:
        points = ' '.join(f'{px:.1f},{y(total):.1f}' for px, total in lines[line_year])
        parts.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="{width}" '
                     f'stroke-linejoin="round"/>')
        parts.append(f'<circle cx="{end_x:.1f}" cy="{y(value):.1f}" r="{radius}" fill="{colour}"/>')
    # Label the higher dot above on its left, where the lines leave room, and the lower one below on its right, or
    # above the first label once the year is over and there is no room left on the right
    labels = sorted([(current, year, THEME_COLOUR), (previous, year - 1, PREVIOUS_COLOUR)], reverse=True)
    (high, high_year, high_colour), (low, low_year, low_colour) = labels
    low_x, low_y = end_x + 120, y(low) + 36
    if low_x > WIDTH - 4:
        low_x, low_y = end_x - 14, y(high) - 44
    parts.append(f'<text x="{end_x - 14:.1f}" y="{y(high) - 16:.1f}" text-anchor="end" '
                 f'fill="{high_colour}">{high_year}: {high}</text>')
    parts.append(f'<text x="{low_x:.1f}" y="{low_y:.1f}" text-anchor="end" '
                 f'fill="{low_colour}">{low_year}: {low}</text>')
    # Write the initial of each month under its middle
    for month, initial in enumerate('JFMAMJJASOND', start=1):
        parts.append(f'<text x="{x(date(year, month, 15)):.1f}" y="{HEIGHT - 6}" text-anchor="middle" '
                     f'fill="{THEME_COLOUR}">{initial}</text>')
    parts += ['</g>', '</svg>']
    with open(path, 'w') as f:
        f.write(''.join(parts))


def plot_calendar(daily_counts: Dict[date, int], year: int, end: date, path: str) -> None:
    # One block per month, four blocks a row, each a calendar of square days starting on Monday
    block_width, block_height, pitch, side = 175, 190, 23, 19
    height = 3 * block_height
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}">',
        f'<rect width="{WIDTH}" height="{height}" fill="white"/>',
        f'<g font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}" fill="{THEME_COLOUR}">',
    ]
    for day in _days(year):
        left = (day.month - 1) % 4 * block_width + 7
        top = (day.month - 1) // 4 * block_height
        if day.day == 1:
            parts.append(f'<text x="{left}" y="{top + 24}">{day.strftime("%b")}</text>')
        # Colour each day by its number of movies, and only outline the days to come
        count = daily_counts.get(day, 0)
        if day > end:
            fill, outline = 'white', f' stroke="{EMPTY_COLOUR}" stroke-width="1.5"'
        else:
            fill, outline = DARK_COLOUR if count > 1 else THEME_COLOUR if count else EMPTY_COLOUR, ''
        slot = day.day - 1 + day.replace(day=1).weekday()
        parts.append(f'<rect x="{left + slot % 7 * pitch}" y="{top + 34 + slot // 7 * pitch}" '
                     f'width="{side}" height="{side}" rx="3" fill="{fill}"{outline}/>')
    parts += ['</g>', '</svg>']
    with open(path, 'w') as f:
        f.write(''.join(parts))
