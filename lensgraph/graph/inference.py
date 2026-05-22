from __future__ import annotations

from collections import defaultdict


def threshold_edges(edges: dict[tuple[int, int], float], threshold: float) -> dict[tuple[int, int], float]:
    return {e: s for e, s in edges.items() if s >= threshold}


def connected_components_partition(n: int, edges: dict[tuple[int, int], float], threshold: float) -> list[set[int]]:
    kept = threshold_edges(edges, threshold)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in kept:
        union(a, b)
    groups: dict[int, set[int]] = defaultdict(set)
    for i in range(n):
        groups[find(i)].add(i)
    return list(groups.values())


def pivot_correlation_clustering(n: int, edges: dict[tuple[int, int], float], threshold: float) -> list[set[int]]:
    """Deterministic pivot-style approximation for sparse positive graph.

    Nodes are processed by descending weighted degree. A pivot absorbs currently
    unassigned neighbors whose edge score exceeds threshold, but neighbors are
    not allowed to trigger transitive chain merges as in plain CC.
    """
    adj: dict[int, list[tuple[int, float]]] = defaultdict(list)
    degree = [0.0] * n
    for (a, b), s in edges.items():
        if s < threshold:
            continue
        adj[a].append((b, s))
        adj[b].append((a, s))
        degree[a] += s
        degree[b] += s
    remaining = set(range(n))
    order = sorted(range(n), key=lambda i: (-degree[i], i))
    groups: list[set[int]] = []
    for pivot in order:
        if pivot not in remaining:
            continue
        group = {pivot}
        for j, _ in sorted(adj.get(pivot, []), key=lambda t: (-t[1], t[0])):
            if j in remaining:
                group.add(j)
        remaining.difference_update(group)
        groups.append(group)
    return groups
