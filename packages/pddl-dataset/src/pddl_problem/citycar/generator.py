"""Parameterized instance generator for the CityCar model."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from random import Random

from pddl_problem.base import GeneratedProblem
from pddl_problem.common import make_rng
from pddl_problem.io import load_domain_text

from .schema import CityCarConfig

Coord = tuple[int, int]
Edge = tuple[Coord, Coord]

TOPOLOGY_FAMILIES = [
    "open_grid",
    "parallel_lanes",
    "ring_with_spurs",
    "three_spokes",
    "rooms_and_doors",
    "blocked_center",
    "diagonal_mix",
]


@dataclass(frozen=True)
class CityCarLayout:
    rows: int
    columns: int
    cars: int
    garages: int
    roads: int
    open_cells: set[Coord]
    garage_cells: list[Coord]
    car_garages: list[int]
    goal_cells: list[Coord]
    family: str


def render_domain_pddl() -> str:
    """Return the static CityCar domain text."""

    return load_domain_text(__file__)


def generate_problem(config: CityCarConfig) -> GeneratedProblem:
    """Generate one CityCar problem instance."""

    rng = make_rng(config.seed)
    if config.mode == "current":
        layout = _generate_current_layout(config, rng)
    elif config.mode == "topology-first":
        layout = _generate_topology_first_layout(config, rng)
    else:
        layout = _generate_solution_first_layout(config, rng)
    problem_name = _resolve_problem_name(config, layout)
    return GeneratedProblem(
        name=problem_name,
        domain_name="citycar",
        problem_pddl=_render_problem(problem_name, layout),
    )


def _generate_current_layout(config: CityCarConfig, rng: Random) -> CityCarLayout:
    """Density-style layout matching the old generator's parameter shape."""

    cells = _all_cells(config.rows, config.columns)
    rng.shuffle(cells)
    clear_count = max(
        config.garages + min(config.cars, len(cells) - config.garages),
        round(len(cells) * config.density),
    )
    open_cells = set(cells[: max(1, min(len(cells), clear_count))])

    while len(open_cells) < min(len(cells), config.garages + 1):
        open_cells.add(cells[len(open_cells)])

    garage_candidates = sorted(open_cells, key=lambda cell: (cell[0], cell[1]))
    garage_cells = _sample_distinct(garage_candidates, min(config.garages, len(garage_candidates)), rng)
    if len(garage_cells) < config.garages:
        raise ValueError("not enough clear cells to place garages")

    goal_candidates = [cell for cell in sorted(open_cells) if cell not in garage_cells] or sorted(open_cells)
    goal_pool = _sample_distinct(goal_candidates, min(config.cars, len(goal_candidates)), rng)
    goal_cells = [goal_pool[index % len(goal_pool)] for index in range(config.cars)]
    car_garages = [rng.randrange(config.garages) for _ in range(config.cars)]

    return CityCarLayout(
        rows=config.rows,
        columns=config.columns,
        cars=config.cars,
        garages=config.garages,
        roads=config.roads,
        open_cells=open_cells,
        garage_cells=garage_cells,
        car_garages=car_garages,
        goal_cells=goal_cells,
        family="current_density",
    )


def _generate_topology_first_layout(config: CityCarConfig, rng: Random) -> CityCarLayout:
    """Solution 1: choose a compact topology first, then place routed traffic in it."""

    family_names = TOPOLOGY_FAMILIES if config.topology_family == "auto" else [config.topology_family]
    for _ in range(200):
        family = rng.choice(family_names)
        open_cells = _topology_mask(config.rows, config.columns, family, rng)
        layout = _try_route_inside_topology(config, rng, open_cells, family)
        if layout is not None:
            return layout
    return _generate_solution_first_layout(config, rng)


def _generate_solution_first_layout(config: CityCarConfig, rng: Random) -> CityCarLayout:
    """Solution 2: build a small certified route skeleton, then add topology around it."""

    hub = (config.rows // 2, config.columns // 2)
    neighbors = [cell for cell in _neighbors8(hub, config.rows, config.columns)]
    if len(neighbors) < config.garages + 1:
        raise ValueError("grid is too small for a solution-first CityCar skeleton")

    leftish = sorted(neighbors, key=lambda cell: (cell[1] >= hub[1], abs(cell[0] - hub[0]), cell[1]))
    rightish = sorted(neighbors, key=lambda cell: (cell[1] <= hub[1], abs(cell[0] - hub[0]), -cell[1]))
    garage_cells = _take_unique(leftish, config.garages)
    remaining_neighbors = [cell for cell in rightish if cell not in garage_cells]
    goal_slots = max(1, min(config.cars, config.roads - len(garage_cells), len(remaining_neighbors)))
    if goal_slots <= 0:
        raise ValueError("roads must leave room for at least one goal route")
    goal_pool = _take_unique(remaining_neighbors, goal_slots)
    goal_cells = [goal_pool[index % len(goal_pool)] for index in range(config.cars)]
    car_garages = [index % config.garages for index in range(config.cars)]

    route_cells = {hub, *garage_cells, *goal_pool}
    family = config.topology_family if config.topology_family != "auto" else rng.choice(TOPOLOGY_FAMILIES)
    open_cells = set(route_cells)
    candidates = [cell for cell in _topology_mask(config.rows, config.columns, family, rng) if cell not in open_cells]
    rng.shuffle(candidates)
    target_size = min(config.rows * config.columns, max(len(route_cells) + 2, config.cars + config.garages + 4))
    open_cells.update(candidates[: max(0, target_size - len(open_cells))])

    return CityCarLayout(
        rows=config.rows,
        columns=config.columns,
        cars=config.cars,
        garages=config.garages,
        roads=config.roads,
        open_cells=open_cells,
        garage_cells=garage_cells,
        car_garages=car_garages,
        goal_cells=goal_cells,
        family=f"solution_first_{family}",
    )


def _try_route_inside_topology(
    config: CityCarConfig,
    rng: Random,
    open_cells: set[Coord],
    family: str,
) -> CityCarLayout | None:
    component = _largest_component(open_cells, config.rows, config.columns)
    if len(component) < config.garages + 2:
        return None

    hubs = sorted(
        component,
        key=lambda cell: (abs(cell[0] - config.rows // 2) + abs(cell[1] - config.columns // 2), cell),
    )
    rng.shuffle(hubs[: min(8, len(hubs))])
    for hub in hubs[: min(16, len(hubs))]:
        garage_paths = _endpoint_paths(component, config.rows, config.columns, hub, reverse=True)
        goal_paths = _endpoint_paths(component, config.rows, config.columns, hub, reverse=False)
        if len(garage_paths) < config.garages:
            continue

        garage_paths = _spread_paths(garage_paths, hub, rng)
        route_edges: set[Edge] = set()
        garage_cells: list[Coord] = []
        for path in garage_paths:
            added = set(_path_edges(path))
            if len(route_edges | added) > config.roads - 1:
                continue
            garage_cells.append(path[0])
            route_edges.update(added)
            if len(garage_cells) == config.garages:
                break
        if len(garage_cells) < config.garages:
            continue

        goal_pool: list[Coord] = []
        for path in _spread_paths(goal_paths, hub, rng):
            if path[-1] in garage_cells:
                continue
            added = set(_path_edges(path))
            if len(route_edges | added) > config.roads:
                continue
            goal_pool.append(path[-1])
            route_edges.update(added)
            if len(goal_pool) == max(1, min(config.cars, config.roads - len(garage_cells))):
                break
        if not goal_pool:
            continue

        return CityCarLayout(
            rows=config.rows,
            columns=config.columns,
            cars=config.cars,
            garages=config.garages,
            roads=config.roads,
            open_cells=component,
            garage_cells=garage_cells,
            car_garages=[index % config.garages for index in range(config.cars)],
            goal_cells=[goal_pool[index % len(goal_pool)] for index in range(config.cars)],
            family=f"topology_first_{family}",
        )
    return None


def _topology_mask(rows: int, columns: int, family: str, rng: Random) -> set[Coord]:
    cells = set(_all_cells(rows, columns))
    mid_r = rows // 2
    mid_c = columns // 2

    if family == "open_grid":
        return cells
    if family == "parallel_lanes":
        lane_rows = {0, mid_r, rows - 1}
        connectors = {0, mid_c, columns - 1}
        return {(r, c) for r, c in cells if r in lane_rows or c in connectors}
    if family == "ring_with_spurs":
        return {(r, c) for r, c in cells if r in {0, rows - 1} or c in {0, columns - 1} or r == mid_r or c == mid_c}
    if family == "three_spokes":
        spokes = {(mid_r, c) for c in range(columns)} | {(r, mid_c) for r in range(rows)}
        spokes.update({(0, 0), (0, columns - 1), (rows - 1, 0), (rows - 1, columns - 1)})
        return spokes
    if family == "rooms_and_doors":
        rooms = set()
        for r in range(rows):
            for c in range(columns):
                in_corner_room = (r in {0, 1, rows - 2, rows - 1}) and (c in {0, 1, columns - 2, columns - 1})
                if in_corner_room or r == mid_r or c == mid_c:
                    rooms.add((r, c))
        return rooms
    if family == "blocked_center":
        blocked = {(mid_r, mid_c)}
        if rows >= 5 and columns >= 5:
            blocked.update({(mid_r - 1, mid_c), (mid_r + 1, mid_c), (mid_r, mid_c - 1), (mid_r, mid_c + 1)})
        return cells - blocked
    if family == "diagonal_mix":
        mask = {(r, c) for r, c in cells if (r + c) % 2 == 0 or r == mid_r or c == mid_c}
        mask.update({(0, 0), (rows - 1, columns - 1), (0, columns - 1), (rows - 1, 0)})
        return mask

    # Unknown family names intentionally degrade to a seeded sparse-but-connected-ish mask.
    keep = max(rows + columns, round(len(cells) * 0.65))
    shuffled = list(cells)
    rng.shuffle(shuffled)
    return set(shuffled[:keep])


def _render_problem(problem_name: str, layout: CityCarLayout) -> str:
    junctions = [_junction_name(cell) for cell in _all_cells(layout.rows, layout.columns)]
    cars = [f"car{i}" for i in range(layout.cars)]
    garages = [f"garage{i}" for i in range(layout.garages)]
    roads = [f"road{i}" for i in range(layout.roads)]

    init_lines: list[str] = []
    for source, target in _same_line_pairs(layout.rows, layout.columns):
        init_lines.append(f"({_pred('same_line', source, target)})")
    for source, target in _diagonal_pairs(layout.rows, layout.columns):
        init_lines.append(f"({_pred('diagonal', source, target)})")
    for cell in sorted(layout.open_cells):
        init_lines.append(f"(clear {_junction_name(cell)})")
    for index, cell in enumerate(layout.garage_cells):
        init_lines.append(f"(at_garage garage{index} {_junction_name(cell)})")
    for car_index, garage_index in enumerate(layout.car_garages):
        init_lines.append(f"(starting car{car_index} garage{garage_index})")
    init_lines.append("(= (total-cost) 0)")

    goal_lines = [
        f"(arrived car{index} {_junction_name(goal_cell)})" for index, goal_cell in enumerate(layout.goal_cells)
    ]

    return f"""(define (problem {problem_name})
(:domain citycar)
(:objects
{_object_line(junctions, "junction")}
{_object_line(cars, "car")}
{_object_line(garages, "garage")}
{_object_line(roads, "road")}
)
(:init
{chr(10).join(init_lines)}
)
(:goal
(and
{chr(10).join(goal_lines)}
)
)
(:metric minimize (total-cost))
)
"""


def _resolve_problem_name(config: CityCarConfig, layout: CityCarLayout) -> str:
    if config.problem_name != "citycar":
        return config.problem_name

    parts = [
        "citycar",
        _pddl_symbol(config.mode),
        _pddl_symbol(_display_family(layout.family)),
        f"{layout.rows}x{layout.columns}",
        f"c{layout.cars}",
        f"g{layout.garages}",
        f"r{layout.roads}",
        f"o{len(layout.open_cells)}",
        _difficulty_label(layout),
    ]
    if config.mode == "current":
        parts.append(f"d{round(config.density * 100):03d}")
    if config.seed is not None:
        parts.append(f"s{config.seed}")
    return "-".join(parts)


def _difficulty_label(layout: CityCarLayout) -> str:
    traffic_load = layout.cars + layout.roads
    topology_load = len(layout.open_cells)
    if layout.cars >= 5 or layout.roads >= 6 or topology_load >= 18:
        return "hard"
    if layout.cars >= 4 or traffic_load >= 9 or topology_load >= 12:
        return "medium"
    return "easy"


def _pddl_symbol(value: str) -> str:
    return value.lower().replace("_", "-")


def _display_family(family: str) -> str:
    for prefix in ("topology_first_", "solution_first_"):
        if family.startswith(prefix):
            return family.removeprefix(prefix)
    if family == "current_density":
        return "density"
    return family


def _all_cells(rows: int, columns: int) -> list[Coord]:
    return [(r, c) for r in range(rows) for c in range(columns)]


def _junction_name(cell: Coord) -> str:
    return f"junction{cell[0]}-{cell[1]}"


def _object_line(names: list[str], type_name: str) -> str:
    return f"{' '.join(names)} - {type_name}"


def _pred(name: str, source: Coord, target: Coord) -> str:
    return f"{name} {_junction_name(source)} {_junction_name(target)}"


def _same_line_pairs(rows: int, columns: int) -> list[tuple[Coord, Coord]]:
    pairs: list[tuple[Coord, Coord]] = []
    for r in range(rows):
        for c in range(columns):
            for target in ((r + 1, c), (r, c + 1)):
                if target[0] < rows and target[1] < columns:
                    pairs.append(((r, c), target))
                    pairs.append((target, (r, c)))
    return pairs


def _diagonal_pairs(rows: int, columns: int) -> list[tuple[Coord, Coord]]:
    pairs: list[tuple[Coord, Coord]] = []
    for r in range(rows - 1):
        for c in range(columns):
            for target in ((r + 1, c + 1), (r + 1, c - 1)):
                if target[1] < columns and 0 <= target[1]:
                    pairs.append(((r, c), target))
                    pairs.append((target, (r, c)))
    return pairs


def _neighbors8(cell: Coord, rows: int, columns: int) -> list[Coord]:
    r, c = cell
    neighbors = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            target = (r + dr, c + dc)
            if 0 <= target[0] < rows and 0 <= target[1] < columns:
                neighbors.append(target)
    return neighbors


def _largest_component(open_cells: set[Coord], rows: int, columns: int) -> set[Coord]:
    unseen = set(open_cells)
    best: set[Coord] = set()
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            for neighbor in _neighbors8(cell, rows, columns):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        if len(component) > len(best):
            best = component
    return best


def _shortest_path(open_cells: set[Coord], rows: int, columns: int, start: Coord, goal: Coord) -> list[Coord] | None:
    queue = deque([start])
    previous: dict[Coord, Coord | None] = {start: None}
    while queue:
        cell = queue.popleft()
        if cell == goal:
            path = [cell]
            while previous[path[-1]] is not None:
                path.append(previous[path[-1]])  # type: ignore[arg-type]
            return list(reversed(path))
        for neighbor in _neighbors8(cell, rows, columns):
            if neighbor in open_cells and neighbor not in previous:
                previous[neighbor] = cell
                queue.append(neighbor)
    return None


def _endpoint_paths(open_cells: set[Coord], rows: int, columns: int, hub: Coord, *, reverse: bool) -> list[list[Coord]]:
    paths = []
    for endpoint in open_cells:
        if endpoint == hub:
            continue
        if reverse:
            path = _shortest_path(open_cells, rows, columns, endpoint, hub)
        else:
            path = _shortest_path(open_cells, rows, columns, hub, endpoint)
        if path is not None and len(path) <= 3:
            paths.append(path)
    return paths


def _path_edges(path: list[Coord]) -> list[Edge]:
    return list(zip(path, path[1:]))


def _spread_paths(paths: list[list[Coord]], hub: Coord, rng: Random) -> list[list[Coord]]:
    shuffled = list(paths)
    rng.shuffle(shuffled)
    return sorted(
        shuffled,
        key=lambda path: (
            abs(path[0][0] - hub[0]) + abs(path[0][1] - hub[1]),
            path[0][0],
            path[0][1],
        ),
    )


def _sample_distinct(candidates: list[Coord], count: int, rng: Random) -> list[Coord]:
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    return shuffled[:count]


def _take_unique(candidates: list[Coord], count: int) -> list[Coord]:
    result: list[Coord] = []
    for cell in candidates:
        if cell not in result:
            result.append(cell)
            if len(result) == count:
                return result
    raise ValueError("not enough unique cells")
