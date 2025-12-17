INF = 1e30


def _assign_greedy_continuous(dist_matrix, weights, open_idx, capacity_per_shelter: float, eps: float = 1e-9):
    """连续“流量”版本容量分配（可快速评估一个开点集合的可行性与成本）。

    - demand i 的需求量为 weights[i]（可为浮点）
    - 每个 open shelter 容量为 capacity_per_shelter
    - 按 (distance) 由近到远贪心分配 flow
    """
    k = len(open_idx)
    n_dem = len(weights)

    rem_d = [float(w) for w in weights]
    rem_c = [float(capacity_per_shelter) for _ in range(k)]

    pairs = []
    for i in range(n_dem):
        for kk in range(k):
            j = open_idx[kk]
            pairs.append((dist_matrix[i][j], i, kk))
    pairs.sort(key=lambda x: x[0])

    total_cost = 0.0
    for d, i, kk in pairs:
        if rem_d[i] <= eps or rem_c[kk] <= eps:
            continue
        flow = rem_d[i] if rem_d[i] < rem_c[kk] else rem_c[kk]
        rem_d[i] -= flow
        rem_c[kk] -= flow
        total_cost += flow * d

    feasible = all(x <= eps for x in rem_d)
    return feasible, total_cost


def solve_k_median_cap(dist_matrix, weights, k: int, capacity_per_shelter: float, max_swap_rounds: int = 15):
    """考虑容量（同容量上限）的 K-median：无容量贪心初始化 + 容量分配评估 + 1-swap 搜索。"""
    n_dem = len(dist_matrix)
    if n_dem == 0:
        raise ValueError("dist_matrix 为空")
    n_cand = len(dist_matrix[0])
    if k <= 0 or k > n_cand:
        raise ValueError(f"k 必须在 [1, {n_cand}]，当前 k={k}")

    total_demand = sum(float(w) for w in weights)
    if capacity_per_shelter * k + 1e-9 < total_demand:
        raise ValueError(
            f"容量不可行：K*cap={capacity_per_shelter*k} < total_demand={total_demand}，请增大 K 或 cap"
        )

    # 初始化：先用“无容量贪心”选 K 个点（快），再用容量分配算真实 cost
    open_set = set()
    best_d = [INF] * n_dem
    for _ in range(k):
        best_j = None
        best_cost = INF
        for j in range(n_cand):
            if j in open_set:
                continue
            c = 0.0
            for i in range(n_dem):
                d = dist_matrix[i][j]
                c += weights[i] * (d if d < best_d[i] else best_d[i])
            if c < best_cost:
                best_cost = c
                best_j = j
        open_set.add(best_j)
        for i in range(n_dem):
            dj = dist_matrix[i][best_j]
            if dj < best_d[i]:
                best_d[i] = dj

    open_idx = sorted(open_set)
    feasible, cur_cost = _assign_greedy_continuous(dist_matrix, weights, open_idx, capacity_per_shelter)
    if not feasible:
        # 常见原因：距离矩阵里存在 INF（不连通）导致“实际上无法到达”
        raise RuntimeError("容量分配不可行：可能存在 demand 到所有 open shelter 不连通（距离=INF）")

    # swap 搜索：每次试探换一个点，用容量分配重新评估
    for _round in range(max_swap_rounds):
        improved = False
        best_trial_cost = cur_cost
        best_swap = None

        closed = [j for j in range(n_cand) if j not in open_set]
        opened = list(open_set)

        for j_out in opened:
            for j_in in closed:
                trial = sorted((open_set - {j_out}) | {j_in})
                feasible, c = _assign_greedy_continuous(dist_matrix, weights, trial, capacity_per_shelter)
                if feasible and c < best_trial_cost:
                    best_trial_cost = c
                    best_swap = (j_out, j_in)

        if best_swap is not None:
            j_out, j_in = best_swap
            open_set.remove(j_out)
            open_set.add(j_in)
            cur_cost = best_trial_cost
            improved = True

        if not improved:
            break

    return sorted(open_set), cur_cost


