
#!/usr/bin/env python3
import sys
import re
import math
from heapq import heappush, heappop
from typing import List, Tuple, Set, FrozenSet, Optional, Dict
from collections import defaultdict, deque

PAREN_RE = re.compile(r"\((.*?)\)")
BRACE_RE = re.compile(r"\{(.*?)\}")

def parse_lines(text: str) -> List[Tuple[List[int], List[FrozenSet[int]]]]:
    machines = []
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        m = BRACE_RE.search(line)
        if not m:
            raise ValueError(f"No joltage requirements found in line: {line}")
        targets_str = m.group(1).strip()
        targets = []
        for part in targets_str.split(','):
            part = part.strip()
            if part == '':
                continue
            targets.append(int(part))
        n = len(targets)
        button_sets: List[FrozenSet[int]] = []
        for pm in PAREN_RE.finditer(line):
            content = pm.group(1).strip()
            if not content:
                # bouton no-op (inutile), on l’ignorera plus loin
                button_sets.append(frozenset())
                continue
            idxs = [s.strip() for s in content.split(',') if s.strip() != '']
            s: Set[int] = set()
            for t in idxs:
                j = int(t)
                if j < 0 or j >= n:
                    raise ValueError(f"Index {j} out of range for {n} counters in line: {line}")
                s.add(j)
            button_sets.append(frozenset(s))
        machines.append((targets, button_sets))
    return machines

def compress_zeros(targets: List[int], buttons: List[FrozenSet[int]]) -> Tuple[List[int], List[FrozenSet[int]]]:
    # Supprime compteurs déjà satisfaits (0) et remappe les boutons
    active_idx = [i for i, v in enumerate(targets) if v > 0]
    if len(active_idx) == len(targets):
        return targets, buttons
    idx_map = {old: new for new, old in enumerate(active_idx)}
    new_targets = [targets[i] for i in active_idx]
    new_buttons = []
    for s in buttons:
        ns = frozenset(idx_map[i] for i in s if i in idx_map)
        new_buttons.append(ns)
    return new_targets, new_buttons

def feasibility_checks(targets: List[int], buttons: List[FrozenSet[int]]) -> None:
    # Retire boutons no-op
    buttons[:] = [s for s in buttons if len(s) > 0]
    # Impossibilité triviale
    if not buttons and any(v > 0 for v in targets):
        raise ValueError("Unsolvable: all buttons are no-ops but some targets are > 0")
    # Counters avec couverture identique => cibles identiques
    signature: Dict[Tuple[int, ...], int] = {}
    for j in range(len(targets)):
        sig = tuple(1 if j in s else 0 for s in buttons)
        if sig in signature:
            if signature[sig] != targets[j]:
                raise ValueError("Unsolvable: counters with identical button coverage have different targets")
        else:
            signature[sig] = targets[j]

def components(targets: List[int], buttons: List[FrozenSet[int]]) -> List[Tuple[List[int], List[FrozenSet[int]]]]:
    """
    Décompose une machine en composantes connexes dans un graphe bipartite
    (compteurs ↔ boutons). Chaque composante est indépendante et se résout séparément.
    """
    m = len(targets)
    B = len(buttons)
    # Construire la bi-partite: C_j connecté à bouton i si j in buttons[i]
    graph_c_to_b: List[List[int]] = [[] for _ in range(m)]
    graph_b_to_c: List[List[int]] = [[] for _ in range(B)]
    for i, s in enumerate(buttons):
        for j in s:
            graph_c_to_b[j].append(i)
            graph_b_to_c[i].append(j)

    seen_c = [False]*m
    seen_b = [False]*B
    comps = []
    for cj in range(m):
        if seen_c[cj]:
            continue
        # ignorer les compteurs isolés (devrait être impossible si v>0 et boutons filtrés)
        if not graph_c_to_b[cj] and targets[cj] == 0:
            seen_c[cj] = True
            continue
        # BFS sur biparti
        queue_c = deque([cj])
        cur_c: Set[int] = set()
        cur_b: Set[int] = set()
        seen_c[cj] = True
        while queue_c:
            u = queue_c.popleft()
            cur_c.add(u)
            for bi in graph_c_to_b[u]:
                if not seen_b[bi]:
                    seen_b[bi] = True
                    cur_b.add(bi)
                    # Ajouter tous les compteurs couverts par ce bouton
                    for v in graph_b_to_c[bi]:
                        if not seen_c[v]:
                            seen_c[v] = True
                            queue_c.append(v)
        # Constituer la composante
        if cur_c:
            sub_targets = [targets[i] for i in sorted(cur_c)]
            # remapper boutons vers indices locaux
            idx_map_c = {old: new for new, old in enumerate(sorted(cur_c))}
            sub_buttons = []
            for bi in sorted(cur_b):
                s = frozenset(idx_map_c[j] for j in graph_b_to_c[bi] if j in cur_c)
                if s:
                    sub_buttons.append(s)
            comps.append((sub_targets, sub_buttons))
    return comps

def greedy_upper_bound(targets: List[int], button_sets: List[FrozenSet[int]]) -> Optional[int]:
    """Greedy 'safe' : ne presse que des boutons dont tous les compteurs sont >0."""
    r = targets[:]
    presses = 0
    buttons = [set(s) for s in button_sets]
    while True:
        total = sum(r)
        if total == 0:
            return presses
        best_i = -1
        best_cov = -1
        best_t = 0
        for i, s in enumerate(buttons):
            if not s:
                continue
            if any(r[j] == 0 for j in s):
                continue
            cov = sum(r[j] for j in s)
            if cov > best_cov:
                best_cov = cov
                best_i = i
                best_t = min(r[j] for j in s)
        if best_i == -1:
            return None
        t = best_t
        for j in buttons[best_i]:
            r[j] -= t
        presses += t

def min_presses_component(targets: List[int], button_sets: List[FrozenSet[int]]) -> int:
    """
    A* exact sur une seule composante.
    État = demandes restantes (tuple d’int >=0).
    Action = presser un bouton (tous les indices du set décrémentés de 1),
    jamais d’overshoot (interdit si une composante du set vaut déjà 0).
    """
    if sum(targets) == 0:
        return 0
    unique_buttons = list(set(button_sets))
    Smax = max(len(s) for s in unique_buttons)

    def heuristic(r: Tuple[int, ...]) -> int:
        s = sum(r)
        if s == 0:
            return 0
        # Chaque press réduit la somme au plus de Smax => borne inf admissible
        return (s + Smax - 1) // Smax

    ub = greedy_upper_bound(targets, unique_buttons)
    if ub is None:
        ub = math.inf

    start = tuple(targets)
    pq = []
    g0 = 0
    f0 = g0 + heuristic(start)
    heappush(pq, (f0, g0, start))
    best: Dict[Tuple[int, ...], int] = {start: 0}
    buttons_idx = [tuple(sorted(s)) for s in unique_buttons]

    while pq:
        f, g, state = heappop(pq)
        if sum(state) == 0:
            return g
        if f > ub:
            continue
        for s in buttons_idx:
            # press 'safe' uniquement
            if any(state[j] == 0 for j in s):
                continue
            ns = list(state)
            for j in s:
                ns[j] -= 1
            ns_t = tuple(ns)
            ng = g + 1
            if ns_t in best and best[ns_t] <= ng:
                continue
            best[ns_t] = ng
            nf = ng + heuristic(ns_t)
            if nf <= ub:
                heappush(pq, (nf, ng, ns_t))
    raise ValueError("Search exhausted without solution; input may be unsolvable.")

def min_presses_machine(targets: List[int], buttons: List[FrozenSet[int]]) -> int:
    # Compression des 0
    targets, buttons = compress_zeros(targets, buttons)
    # Checks de faisabilité
    feasibility_checks(targets, buttons)
    if sum(targets) == 0:
        return 0
    # Décomposition en composantes
    comps = components(targets, buttons)
    # Certaines machines peuvent n’avoir qu’une seule composante (cas général)
    total = 0
    for ct, cb in comps:
        total += min_presses_component(ct, cb)
    return total

def total_min_presses_part2(text: str) -> int:
    machines = parse_lines(text)
    total = 0
    for targets, button_sets in machines:
        total += min_presses_machine(targets, button_sets)
    return total

def main():
    print("Reading input...")
    data = sys.stdin.read()
    if not data.strip():
        print("Usage: pipe your input text into stdin or run: python solve_factory_part2.py < input.txt")
        return
    ans = total_min_presses_part2(data)
    print(ans)

if __name__ == "__main__":
    main()
