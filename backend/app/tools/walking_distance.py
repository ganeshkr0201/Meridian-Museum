"""
Walking Distance Tool
Provides deterministic shortest-path walking time and distance between
museum galleries using a seeded graph and Dijkstra's algorithm.
All distances are prototype estimates, not live GPS measurements.
"""

from __future__ import annotations
import heapq
from dataclasses import dataclass, field
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

# Museum graph: (from_gallery_id, to_gallery_id) -> (distance_m, walk_min, accessible, has_stairs)
# Bidirectional edges defined once, expanded at build time.
_RAW_EDGES = [
    ("G01", "G02", 80.0,  2.0,  True,  False),  # Ground to Science (lift available)
    ("G01", "G04", 60.0,  1.5,  True,  False),  # Ground to Natural History
    ("G02", "G03", 40.0,  1.0,  True,  False),  # Science to Art (same floor)
    ("G03", "G04", 90.0,  2.5,  True,  False),  # Art to Natural History (via lift)
    ("G01", "G03", 110.0, 3.0,  True,  True),   # Ground to Art (stairs shortcut)
    ("G02", "G04", 100.0, 2.5,  True,  True),   # Science to Natural History (stairs)
]

# Stair-free distances for accessible routes (longer path via lift)
_ACCESSIBLE_EXTRAS = {
    frozenset(("G01", "G03")): (140.0, 4.0),
    frozenset(("G02", "G04")): (130.0, 3.5),
}


@dataclass
class WalkingResult:
    from_gallery_id: str
    to_gallery_id: str
    distance_m: float
    walk_minutes: float
    is_accessible: bool
    path: list[str] = field(default_factory=list)
    note: str = "Prototype estimate — not a live GPS measurement."


def _build_graph(accessible_only: bool) -> dict[str, list[tuple[str, float, float]]]:
    """Return adjacency list {node: [(neighbour, distance_m, walk_min)]}."""
    graph: dict[str, list[tuple[str, float, float]]] = {}

    for src, dst, dist, mins, acc, stairs in _RAW_EDGES:
        if accessible_only:
            key = frozenset((src, dst))
            if stairs:
                # Replace stair edge with accessible equivalent if defined
                if key in _ACCESSIBLE_EXTRAS:
                    dist, mins = _ACCESSIBLE_EXTRAS[key]
                else:
                    continue  # Skip inaccessible edge with no alternative

        for a, b in [(src, dst), (dst, src)]:
            graph.setdefault(a, [])
            graph.setdefault(b, [])
            graph[a].append((b, dist, mins))

    return graph


def _dijkstra(
    graph: dict[str, list[tuple[str, float, float]]],
    start: str,
    end: str,
) -> tuple[float, float, list[str]]:
    """Return (total_distance_m, total_minutes, path). Returns inf if unreachable."""
    dist_map: dict[str, float] = {start: 0.0}
    min_map: dict[str, float] = {start: 0.0}
    prev: dict[str, Optional[str]] = {start: None}
    heap: list[tuple[float, str]] = [(0.0, start)]

    while heap:
        cur_min, node = heapq.heappop(heap)
        if node == end:
            break
        if cur_min > min_map.get(node, float("inf")):
            continue
        for neighbour, d, m in graph.get(node, []):
            new_min = cur_min + m
            if new_min < min_map.get(neighbour, float("inf")):
                min_map[neighbour] = new_min
                dist_map[neighbour] = dist_map[node] + d
                prev[neighbour] = node
                heapq.heappush(heap, (new_min, neighbour))

    if end not in min_map:
        return float("inf"), float("inf"), []

    # Reconstruct path
    path: list[str] = []
    cur: Optional[str] = end
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
    path.reverse()
    return dist_map[end], min_map[end], path


def get_walking_distance(
    from_gallery_id: str,
    to_gallery_id: str,
    accessible_mode: bool = False,
) -> WalkingResult:
    """
    Calculate walking distance and time between two galleries.

    Args:
        from_gallery_id: Source gallery ID.
        to_gallery_id: Destination gallery ID.
        accessible_mode: If True, avoids stairs and uses accessible paths.

    Returns:
        WalkingResult with distance, time, and path.
    """
    if from_gallery_id == to_gallery_id:
        return WalkingResult(
            from_gallery_id=from_gallery_id,
            to_gallery_id=to_gallery_id,
            distance_m=0.0,
            walk_minutes=0.0,
            is_accessible=True,
            path=[from_gallery_id],
        )

    graph = _build_graph(accessible_only=accessible_mode)
    dist_m, walk_min, path = _dijkstra(graph, from_gallery_id, to_gallery_id)

    if dist_m == float("inf"):
        logger.warning(
            "No %spath from %s to %s",
            "accessible " if accessible_mode else "",
            from_gallery_id,
            to_gallery_id,
        )
        return WalkingResult(
            from_gallery_id=from_gallery_id,
            to_gallery_id=to_gallery_id,
            distance_m=9999.0,
            walk_minutes=30.0,
            is_accessible=False,
            path=[],
            note="No feasible path found.",
        )

    logger.debug(
        "Walk %s→%s: %.1f m, %.1f min, accessible=%s",
        from_gallery_id, to_gallery_id, dist_m, walk_min, accessible_mode,
    )
    return WalkingResult(
        from_gallery_id=from_gallery_id,
        to_gallery_id=to_gallery_id,
        distance_m=dist_m,
        walk_minutes=walk_min,
        is_accessible=accessible_mode,
        path=path,
    )
