import math

STEP = 62        # vertical distance between stage nodes
TOP = 190        # room above the last stage node for the title and scenery
BOTTOM = 110     # room below the first stage node
RADIUS = {'stage': 22, 'mini_boss': 31, 'main_boss': 38}

WORLD_STEP = 150
WORLD_TOP = 150
WORLD_BOTTOM = 160
WORLD_AMPLITUDE = 85
WORLD_RADIUS = 38


def layout(count, step=STEP, top=TOP, bottom=BOTTOM, amplitude=105, wave=0.95):
    """Centre of every node. The first one is at the bottom and the path winds upward."""
    height = top + bottom + step * max(count - 1, 0)
    points = []
    for i in range(count):
        x = round(195 + amplitude * math.sin(i * wave))
        y = height - bottom - i * step
        points.append((x, y))
    return points, height


def path_data(points):
    """A smooth SVG path through the points."""
    if not points:
        return ''
    d = 'M{} {}'.format(*points[0])
    if len(points) == 1:
        return d
    mid = lambda a, b: (round((a[0] + b[0]) / 2), round((a[1] + b[1]) / 2))
    d += ' L{} {}'.format(*mid(points[0], points[1]))
    for i in range(1, len(points) - 1):
        m = mid(points[i], points[i + 1])
        d += ' Q{} {} {} {}'.format(points[i][0], points[i][1], m[0], m[1])
    d += ' L{} {}'.format(*points[-1])
    return d


def build_map(items):
    """items is a list of (stage, stage_progress) in order. Returns what the template draws."""
    points, height = layout(len(items))
    nodes = []
    number = 0
    current = None
    for index, ((stage, progress), (x, y)) in enumerate(zip(items, points)):
        if stage.kind == 'stage':
            number += 1
        if current is None and progress.status == 'unlocked':
            current = index
        nodes.append({
            'stage': stage, 'progress': progress, 'x': x, 'y': y,
            'number': number if stage.kind == 'stage' else None,
            'radius': RADIUS[stage.kind],
            'is_current': current == index,
        })
    done_to = len(items) - 1 if current is None else current
    return {
        'nodes': nodes, 'height': height,
        'path': path_data(points), 'done_path': path_data(points[:done_to + 1]),
        'current': current,
    }


def build_world_map(rows, totals, done):
    """rows is a list of (level, level_progress) in order. Returns what the map page draws."""
    points, height = layout(len(rows), WORLD_STEP, WORLD_TOP, WORLD_BOTTOM, WORLD_AMPLITUDE, 1.1)
    nodes = []
    current = None
    for index, ((level, progress), (x, y)) in enumerate(zip(rows, points)):
        if current is None and progress.status == 'unlocked':
            current = index
        nodes.append({
            'level': level, 'progress': progress, 'x': x, 'y': y,
            'radius': WORLD_RADIUS,
            'side': 'right' if x < 195 else 'left',        # which side the label goes on
            'count': totals.get(level.id, 0), 'got': done.get(level.id, 0),
            'is_current': current == index,
        })
    done_to = len(rows) - 1 if current is None else current
    return {
        'nodes': nodes, 'height': height,
        'path': path_data(points), 'done_path': path_data(points[:done_to + 1]),
        'current': current,
    }