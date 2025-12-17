INF = 1e30


def _cost_with_best(best_d, weights):
    return sum(w * d for w, d in zip(weights, best_d))


def solve_k_median_uncap(dist_matrix, weights, k: int, max_swap_rounds: int = 15):
    """不考虑容量的 K-median：贪心初始化 + 1-swap 局部搜索。

    dist_matrix: shape (n_demands, n_candidates)
    weights: len=n_demands
    """
    n_dem = len(dist_matrix)
    if n_dem == 0:
        raise ValueError("dist_matrix 为空")
    n_cand = len(dist_matrix[0])
    if k <= 0 or k > n_cand:
        raise ValueError(f"k 必须在 [1, {n_cand}]，当前 k={k}")

    # 贪心：维护每个 demand 到当前 open_set 的最近距离 best_d[i]
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

    # swap 改进：预计算每个 demand 的 best/second-best（对当前 open_set）
    def recompute_best2():
        best1 = [INF] * n_dem
        best2 = [INF] * n_dem
        bestj = [-1] * n_dem
        for i in range(n_dem):
            for j in open_set:
                d = dist_matrix[i][j]
                if d < best1[i]:
                    best2[i] = best1[i]
                    best1[i] = d
                    bestj[i] = j
                elif d < best2[i]:
                    best2[i] = d
        return best1, best2, bestj

    cur_cost = _cost_with_best(best_d, weights)

    for _round in range(max_swap_rounds):
        best1, best2, bestj = recompute_best2()

        improved = False
        best_trial_cost = cur_cost
        best_swap = None

        closed = [j for j in range(n_cand) if j not in open_set]
        opened = list(open_set)

        for j_out in opened:
            for j_in in closed:
                c = 0.0
                for i in range(n_dem):
                    keep = best2[i] if bestj[i] == j_out else best1[i]
                    din = dist_matrix[i][j_in]
                    c += weights[i] * (din if din < keep else keep)
                if c < best_trial_cost:
                    best_trial_cost = c
                    best_swap = (j_out, j_in)

        if best_swap is not None:
            j_out, j_in = best_swap
            open_set.remove(j_out)
            open_set.add(j_in)
            # 简单直接重算 best_d
            best_d = [min(dist_matrix[i][j] for j in open_set) for i in range(n_dem)]
            cur_cost = best_trial_cost
            improved = True

        if not improved:
            break

    return sorted(open_set), cur_cost


