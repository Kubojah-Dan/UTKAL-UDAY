"""
EM-based BKT estimator.

Usage (from project root):
python -m app.core.bkt_em data/processed/sequences.pkl --out app/models/bkt_params.json --max_iter 50
(or run with `python -m app.core.bkt_em ...` to use package imports)
"""

import argparse
import pickle
import math
from collections import defaultdict
import json
import os

EPS = 1e-9

def forward_backward(obs, pL0, T, G, S):
    """
    Performs scaled forward-backward for a single observation sequence `obs` (list of 0/1 ints).
    Returns gamma (list of pairs: P(L_t=0), P(L_t=1)) and xi (list of 2x2 matrices for t=1..T-1).
    """
    n = len(obs)
    # emission probabilities b(state, obs)
    def b(state, o):
        if state == 0:
            return G if o == 1 else (1.0 - G)
        else:
            return (1.0 - S) if o == 1 else S

    # transition matrix A[i][j]
    # 0 -> 0 : 1-T, 0->1 : T
    # 1 -> 0 : 0,     1->1 : 1
    A = [[1.0 - T, T],
         [0.0, 1.0]]

    # alpha scaled
    alpha = [ [0.0, 0.0] for _ in range(n) ]
    scales = [1.0]*n

    # init
    alpha0_0 = (1.0 - pL0) * b(0, obs[0])
    alpha0_1 = pL0 * b(1, obs[0])
    s0 = alpha0_0 + alpha0_1
    if s0 <= 0: s0 = EPS
    alpha[0][0] = alpha0_0 / s0
    alpha[0][1] = alpha0_1 / s0
    scales[0] = s0

    # forward
    for t in range(1, n):
        for j in (0,1):
            s = 0.0
            for i in (0,1):
                s += alpha[t-1][i] * A[i][j]
            val = s * b(j, obs[t])
            alpha[t][j] = val
        st = alpha[t][0] + alpha[t][1]
        if st <= 0: st = EPS
        alpha[t][0] /= st
        alpha[t][1] /= st
        scales[t] = st

    # beta scaled
    beta = [ [0.0, 0.0] for _ in range(n) ]
    beta[n-1][0] = 1.0
    beta[n-1][1] = 1.0

    # backward (note: must un-scale consistent with forward scaling — we kept alpha scaled to 1 sum at each t)
    # to compute gamma and xi directly we can recompute more stable expressions:

    # gamma_t(i) proportional to alpha_t(i) * beta_t(i). Because alpha scaled to sum 1 and we kept beta unscaled,
    # we will compute gamma using a normalized version.
    # For numeric stability, compute gamma by forward-backward in log domain or compute xi using direct formula:

    # compute gamma (posterior marginals) using an alternative stable formula:
    # We'll compute full (unscaled) alpha and beta by using scales:
    # Let alpha_unscaled[t][i] = alpha[t][i] * prod_{k=0..t} scales[k]
    # Let beta_unscaled[t][i] = beta_unscaled defined similarly backward.

    # Build prefix product of scales
    prefix = [1.0]*n
    prod = 1.0
    for t in range(n):
        prod *= scales[t]
        prefix[t] = prod

    # unscaled alpha
    alpha_un = [ [0.0, 0.0] for _ in range(n) ]
    for t in range(n):
        alpha_un[t][0] = alpha[t][0] * prefix[t]
        alpha_un[t][1] = alpha[t][1] * prefix[t]

    # compute unscaled beta via backward recursing with scales (safe)
    beta_un = [ [0.0, 0.0] for _ in range(n) ]
    beta_un[n-1][0] = 1.0
    beta_un[n-1][1] = 1.0
    for t in range(n-2, -1, -1):
        for i in (0,1):
            s = 0.0
            for j in (0,1):
                # transition A[i][j] * b(j, obs[t+1]) * beta_un[t+1][j]
                s += A[i][j] * b(j, obs[t+1]) * beta_un[t+1][j]
            beta_un[t][i] = s
        # scale to avoid overflow
        ssum = beta_un[t][0] + beta_un[t][1]
        if ssum <= 0: ssum = EPS
        beta_un[t][0] /= ssum
        beta_un[t][1] /= ssum

    # now compute gamma normalized:
    gamma = []
    for t in range(n):
        g0 = alpha_un[t][0] * beta_un[t][0]
        g1 = alpha_un[t][1] * beta_un[t][1]
        s = g0 + g1
        if s <= 0: s = EPS
        gamma.append((g0 / s, g1 / s))

    # compute xi for t=0..n-2
    xi = []
    for t in range(n-1):
        denom = 0.0
        x = [[0.0, 0.0],[0.0, 0.0]]
        for i in (0,1):
            for j in (0,1):
                term = alpha_un[t][i] * A[i][j] * b(j, obs[t+1]) * beta_un[t+1][j]
                x[i][j] = term
                denom += term
        if denom <= 0:
            # fallback: distribute according to gamma
            denom = 1.0
            # use product of marginals
            for i in (0,1):
                for j in (0,1):
                    x[i][j] = (alpha_un[t][i] * beta_un[t][i]) * (alpha_un[t+1][j] * beta_un[t+1][j])
            denom = sum(sum(row) for row in x)
            if denom <= 0:
                # final fallback equal split
                x = [[0.25,0.25],[0.25,0.25]]
                denom = 1.0
        # normalize
        for i in (0,1):
            for j in (0,1):
                x[i][j] = x[i][j] / denom
        xi.append(x)
    return gamma, xi

def em_for_skill(sequences, max_iter=50, tol=1e-4, verbose=False):
    """
    sequences: list of lists of steps, where each step is dict with keys 'skill_id' and 'correct' (0/1)
    This function expects sequences already filtered to steps *of this skill only*, per student.
    Example input: [[0,1,1,0], [1,0,1], ...] or list of lists of ints
    """
    # Build list of observation sequences: each is a list of 0/1
    obs_seqs = sequences

    # initialize parameters sensibly
    pL0 = 0.2
    T = 0.08
    G = 0.12
    S = 0.06

    for iteration in range(max_iter):
        # expected counts
        sum_gamma_init_1 = 0.0
        sum_gamma_0 = 0.0
        sum_xi_01 = 0.0

        sum_gamma_obs_if_unlearned = 0.0  # numerator for G (obs=1 when unlearned)
        sum_gamma_unlearned_total = 0.0   # denom for G

        sum_gamma_obs_if_learned_wrong = 0.0  # numerator for S (obs=0 when learned)
        sum_gamma_learned_total = 0.0          # denom for S

        for obs in obs_seqs:
            if len(obs) == 0:
                continue
            # run forward-backward with current params
            gamma, xi = forward_backward(obs, pL0, T, G, S)
            # initial learned expected
            sum_gamma_init_1 += gamma[0][1]
            # accumulate for G and S and transitions
            for t, (g0, g1) in enumerate(gamma):
                # obs[t] is 0 or 1
                o = obs[t]
                sum_gamma_unlearned_total += g0
                if o == 1:
                    sum_gamma_obs_if_unlearned += g0
                sum_gamma_learned_total += g1
                if o == 0:
                    sum_gamma_obs_if_learned_wrong += g1
            # xi length is len(obs)-1
            for t_xi, x in enumerate(xi):
                # x is 2x2 matrix
                sum_xi_01 += x[0][1]
                # we also need sum of gamma_0 over t=1..T-1 for denom
                sum_gamma_0 += gamma[t_xi][0]

        # M-step: update params (avoid divide by zero)
        nseq = len(obs_seqs) if len(obs_seqs) > 0 else 1

        new_pL0 = sum_gamma_init_1 / nseq
        new_T = (sum_xi_01 / (sum_gamma_0 + EPS))
        new_G = (sum_gamma_obs_if_unlearned / (sum_gamma_unlearned_total + EPS))
        new_S = (sum_gamma_obs_if_learned_wrong / (sum_gamma_learned_total + EPS))

        # clamp values into reasonable interval
        new_pL0 = max(1e-4, min(0.9999, new_pL0))
        new_T   = max(1e-6, min(0.9999, new_T))
        new_G   = max(1e-6, min(0.4999, new_G))  # guess should be <0.5
        new_S   = max(1e-6, min(0.4999, new_S))

        # check convergence
        delta = abs(new_pL0 - pL0) + abs(new_T - T) + abs(new_G - G) + abs(new_S - S)
        pL0, T, G, S = new_pL0, new_T, new_G, new_S
        if verbose:
            print(f"iter {iteration+1}: pL0={pL0:.4f}, T={T:.4f}, G={G:.4f}, S={S:.4f}, delta={delta:.6f}")
        if delta < tol:
            break

    return {'p_init': round(pL0,6), 'p_trans': round(T,6), 'p_guess': round(G,6), 'p_slip': round(S,6)}


def build_skill_sequences(full_sequences):
    """
    full_sequences: list of {'student_id': ..., 'steps': [ {skill_id, correct, ...}, ... ] }
    returns: dict skill_id -> list of observation sequences (list of 0/1 lists), one per student (only steps for that skill)
    """
    skill_map = {}
    # per student, extract per skill
    for s in full_sequences:
        steps = s.get('steps', [])
        # group by skill for this student preserving order
        per_skill = {}
        for st in steps:
            sid = st.get('skill_id', 0)
            corr = int(st.get('correct', 0))
            per_skill.setdefault(sid, []).append(corr)
        # append per-skill sequences
        for sid, seq in per_skill.items():
            skill_map.setdefault(sid, []).append(seq)
    return skill_map

def main(processed_pkl, out_json="app/models/bkt_params.json", max_iter=50, tol=1e-4, min_seqs_per_skill=5):
    # load processed sequences
    if not os.path.exists(processed_pkl):
        raise FileNotFoundError(processed_pkl)
    with open(processed_pkl, "rb") as f:
        payload = pickle.load(f)
    sequences = payload.get('sequences', payload)  # some pickles might store raw list
    print(f"Loaded {len(sequences)} student sequences")

    skill_seqs = build_skill_sequences(sequences)
    print(f"Found {len(skill_seqs)} skills")

    results = {}
    for sid, seqs in skill_seqs.items():
        if len(seqs) < min_seqs_per_skill:
            # skip skills with too few sequences to estimate reliably
            continue
        # remove sequences of length 0
        cleaned = [s for s in seqs if len(s) >= 1]
        if not cleaned:
            continue
        params = em_for_skill(cleaned, max_iter=max_iter, tol=tol, verbose=False)
        results[int(sid)] = params

    # save results
    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    with open(out_json, "w", encoding="utf8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved BKT params for {len(results)} skills to {out_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("processed_pkl", help="path to processed sequences.pkl (data/processed/sequences.pkl)")
    parser.add_argument("--out", default="app/models/bkt_params.json")
    parser.add_argument("--max_iter", type=int, default=50)
    parser.add_argument("--min_seqs", type=int, default=5, help="min number of student sequences per skill to attempt estimation")
    args = parser.parse_args()
    main(args.processed_pkl, out_json=args.out, max_iter=args.max_iter, min_seqs_per_skill=args.min_seqs)
