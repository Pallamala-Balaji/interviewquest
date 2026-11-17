from types import SimpleNamespace

from services.stagemap import build_map, layout, path_data


def item(kind='stage', status='locked'):
    return SimpleNamespace(kind=kind), SimpleNamespace(status=status)


def test_layout_gives_one_point_per_node_with_the_first_at_the_bottom():
    points, height = layout(14)
    assert len(points) == 14
    assert points[0][1] > points[-1][1]
    assert all(0 < x < 390 for x, _ in points)
    assert all(0 < y < height for _, y in points)


def test_path_data_handles_empty_one_and_many_points():
    assert path_data([]) == ''
    assert path_data([(10, 20)]) == 'M10 20'
    assert path_data([(0, 0), (10, 10), (20, 0)]).startswith('M0 0 L')


def test_build_map_finds_the_current_node_and_numbers_only_stages():
    items = [item('stage', 'completed'), item('stage', 'completed'), item('stage', 'unlocked'),
             item('mini_boss'), item('stage'), item('main_boss')]
    result = build_map(items)
    assert result['current'] == 2
    assert [n['number'] for n in result['nodes']] == [1, 2, 3, None, 4, None]
    assert [n['is_current'] for n in result['nodes']].count(True) == 1
    assert result['done_path'] != result['path']


def test_build_map_with_everything_done_has_no_current_node():
    result = build_map([item('stage', 'completed'), item('main_boss', 'completed')])
    assert result['current'] is None
    assert result['done_path'] == result['path']


def test_build_map_with_no_items_is_empty():
    result = build_map([])
    assert result['nodes'] == [] and result['path'] == ''