# QAOA for MaxCut: Optimization Behavior, Scaling, and Noise Sensitivity

A circuit-level implementation and empirical study of the Quantum Approximate Optimization
Algorithm (QAOA) on the MaxCut problem, covering theory, optimizer comparison, multi-graph
experiments, and depolarizing noise analysis.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Quantum simulation | Qiskit, Qiskit Aer (statevector + density matrix) |
| Classical optimization | SciPy (COBYLA, Nelder-Mead, L-BFGS-B, SPSA) |
| SDP baseline (GW) | CVXPY |
| Graph construction | NetworkX |
| Numerics / plotting | NumPy, Matplotlib |

---

## Setup

```bash
pip install qiskit qiskit-aer scipy cvxpy networkx numpy matplotlib
```

Then open the notebooks in order (see Project Structure below).
Tested on Python 3.10+.

---

## Key Questions

- When does QAOA perform well on combinatorial optimization problems?
- How sensitive is QAOA to optimizer choice and initialization?
- How does circuit depth affect performance and optimization difficulty?
- How does noise impact solution quality and optimal circuit depth?

---

## Problem Formulation

The MaxCut problem is encoded as a QUBO:

$$\max \sum_{(i,j)\in E} w_{ij} (x_i + x_j - 2x_i x_j), \quad x_i \in \{0,1\}$$

which maps to the Ising cost Hamiltonian:

$$H_C = \sum_{(i,j)\in E} \frac{w_{ij}}{2}(I - Z_i Z_j)$$

Each edge contributes a CNOT–$R_Z(\gamma)$–CNOT block per layer; the gate count scales
as $2p|E|$ CX gates for a depth-$p$ circuit.

---

## Project Structure

### `00` — Applications and Motivation
Uses MaxCut as the canonical QUBO testbed, motivated by its appearance as the core
pairwise structure in several classes of practical binary optimization problems
(job scheduling, portfolio diversification, facility placement, network design).
Some reductions to MaxCut are exact (e.g. unweighted scheduling); others are more
naturally expressed as general QUBO formulations that share the same Ising Hamiltonian
structure. Many of these reduce to similar QUBO structures with the same Ising Hamiltonian form — often differing in edge weights and additional linear terms.

### `01` — QAOA Theory: Hamiltonian Formulation
Derives the Ising Hamiltonian from the MaxCut binary program step by step, introduces
cost and mixer Hamiltonians, and constructs the QAOA ansatz. Includes explicit
gate-count formulas and a justification for the $|{+}\rangle^{\otimes n}$ initial state.

### `02a` — QAOA Theory: Circuits and Landscape
Gate-level decomposition of $U_C(\gamma)$ from first principles (CNOT–$R_Z$–CNOT),
comparison with classical baselines (random, greedy, Goemans–Williamson), and a
mathematical treatment of barren plateaus — including why gradient variance does not vanish as rapidly as in generic global-cost ansätze, due to the locality of the cost Hamiltonian.

### `02b` — C4 Complete Analysis
Exact gate-by-gate analysis on the 4-cycle as a controlled calibration instance.
Tracks statevector evolution, computes analytic optima ($\gamma^* = \pi/4$,
$\beta^* = \pi/8$), and scales to $p = 1, 2, 3$.

### `03` — Optimizer Comparison
Benchmarks COBYLA, Nelder-Mead, L-BFGS-B, and SPSA on $C_{10}$ at $p=2$ with
30 random restarts. Covers the parameter-shift rule, warm-start layer-by-layer
initialization (Zhou et al. 2020), and practical failure modes.

### `04` — Experiments
Evaluates QAOA at $p = 1, 2, 3$ against Random, Greedy, Best-of-5 Greedy, and
Goemans–Williamson on three graph instances: $C_{10}$, $C_{10}$ + 3 chords,
and a 3-regular graph ($n=10$).

### `05` — Noise Analysis
Sweeps depolarizing CX error rate $p_{cx} \in [0, 0.025]$ using noiseless optimal
parameters to isolate noise effects. Measures landscape flattening and identifies
depth-noise crossover points.

---

## Key Results

### C4 — Controlled instance

| Depth $p$ | Approx. ratio | $P(\text{max cut})$ | CX gates |
|-----------|--------------|---------------------|----------|
| 1 | 0.750 | 0.531 | 8 |
| 2 | **1.000** | **1.000** | 16 |
| 3 | **1.000** | **1.000** | 24 |

$C_4$ is bipartite — QAOA achieves the exact optimum at $p=2$ and maintains
it at $p=3$.

### Multi-graph experiments

Three graphs with distinct structural regimes: a 2-regular cycle (analytically tractable),
a cycle with long-range chords (disrupted locality), and a 3-regular graph (the instance
studied in Farhi et al. 2014).

| Method | $C_{10}$ ($\|E\|=10$, OPT=10) | $C_{10}$ + chords ($\|E\|=13$, OPT=13) | 3-regular ($\|E\|=15$, OPT=13) |
|--------|-------------------------------|----------------------------------------|-------------------------------|
| Random | 0.499 | 0.500 | 0.576 |
| Greedy (1-pass) | 0.659 | 0.726 | 0.845 |
| Greedy (best-of-5) | 0.810 | 0.864 | **0.937** |
| Goemans–Williamson | **1.000** | **1.000** | **1.000** |
| QAOA $p=1$ | 0.750 | 0.707 | 0.775 |
| QAOA $p=2$ | 0.833 | 0.791 | 0.851 |
| QAOA $p=3$ | 0.875 | **0.872** | 0.901 |

Key observations:
- **$C_{10}$ + 3 chords**: QAOA $p=3$ (0.872) edges out Best-of-5 Greedy (0.864). Adding
  long-range chords breaks the local structure that greedy exploits, giving QAOA a relative
  advantage.
- **3-regular**: QAOA $p=3$ (0.901) surpasses Greedy 1-pass (0.845) but falls short of
  Best-of-5 (0.937). The denser graph ($|E|=15$) gives greedy more local signal to work with,
  while also increasing QAOA's CX gate count (30 per layer vs. 20 for $C_{10}$).
- GW achieves the optimum on the three instances considered here.

### Optimizer comparison — $C_{10}$, $p=2$, 30 random starts

| Optimizer | Best ratio | Mean | Std | Function evals |
|-----------|-----------|------|-----|----------------|
| L-BFGS-B | 0.8333 | 0.8333 | 0.000 | **22** |
| Nelder-Mead | 0.8333 | 0.8333 | 0.000 | 280 |
| COBYLA | 0.8333 | 0.8328 | 0.002 | 268 |
| SPSA | 0.8333 | 0.8183 | 0.024 | 901 |

L-BFGS-B with the parameter-shift gradient converges to the same optimum as
Nelder-Mead at **13× fewer function evaluations**. SPSA has the highest variance
and cost.

### Noise analysis — approximation ratio vs. $p_{cx}$ (depolarizing on CX gates)

CX gates per layer: $C_{10}$ = 20, $C_{10}$+chords = 26, 3-regular = 30.

**$C_{10}$** (total CX at $p=3$: 60 gates)

| $p_{cx}$ | $p=1$ | $p=2$ | $p=3$ |
|----------|-------|-------|-------|
| 0.000 | 0.750 | 0.834 | 0.876 |
| 0.010 | 0.737 | 0.797 | 0.816 |
| 0.020 | 0.724 | 0.765 | **0.763** ← crossover |
| 0.025 | 0.717 | 0.752 | 0.742 |

**$C_{10}$ + 3 chords** (total CX at $p=3$: 78 gates)

| $p_{cx}$ | $p=1$ | $p=2$ | $p=3$ |
|----------|-------|-------|-------|
| 0.000 | 0.707 | 0.792 | 0.872 |
| 0.010 | 0.692 | 0.748 | 0.777 |
| 0.020 | 0.680 | 0.711 | **0.712** ← crossover |
| 0.025 | 0.670 | 0.694 | 0.685 |

**3-regular ($n=10$)** (total CX at $p=3$: 90 gates)

| $p_{cx}$ | $p=1$ | $p=2$ | $p=3$ |
|----------|-------|-------|-------|
| 0.000 | 0.777 | 0.850 | 0.891 |
| 0.010 | 0.758 | 0.807 | **0.802** ← crossover |
| 0.015 | 0.752 | 0.787 | 0.767 |
| 0.020 | 0.747 | 0.767 | 0.744 |

The crossover point (where $p=3$ is overtaken by $p=2$) is earlier for denser graphs:
$p_{cx} \approx 0.020$ for $C_{10}$, $\approx 0.020$ for $C_{10}$+chords, and
**$\approx 0.010$ for 3-regular** — consistent with the increased CX count per layer
gates per layer than $C_{10}$. The landscape standard deviation on $C_{10}$
drops 10.9% at $p_{cx}=0.02$, further degrading optimizer reliability.

---

## Interpretation

Performance is determined by three interacting factors — not by circuit expressiveness alone:

**Optimization dynamics.** For $p \geq 2$, the landscape is non-convex with multiple
local optima. Multi-start strategies and warm initialization are necessary for
reproducible results; SPSA without warm-start fails to match gradient-based methods
even with $40\times$ more function evaluations.

**Problem structure.** QAOA's locality limitation (depth $p$ can only see radius-$p$
graph neighborhoods) means that on the instances tested, graphs with long-range
connectivity (chords) can in some cases favor QAOA, as observed in our chorded cycle instance, while denser regular graphs
give greedy more local signal to work with. Whether this pattern generalizes requires
experiments on larger and more varied instances.

**Noise and depth tradeoff.** Each additional QAOA layer adds $2|E|$ CX gates.
The crossover point where $p=3$ loses to $p=2$ depends directly on graph density:
$p_{cx} \approx 0.020$ for $C_{10}$ (20 CX/layer) but $\approx 0.010$ for
3-regular (30 CX/layer). On NISQ-era hardware the optimal circuit depth is
graph-dependent, not just hardware-dependent.

---

## Limitations

- All experiments are limited to $n \leq 10$ qubits and three graph instances — results should be treated as illustrative rather than general.
- Noise model is idealized 2-qubit depolarizing; crosstalk and readout errors are not included.
- Noiseless optimal parameters are reused for noise sweeps — re-optimization under
  noise would likely shift crossover points.
- No quantum advantage is demonstrated; GW matches or exceeds QAOA on all instances tested.

---

## Conclusion

QAOA at $p=3$ outperforms Best-of-5 Greedy on the chorded cycle instance but falls short on denser graphs
where greedy has more local signal (3-regular: QAOA 0.901 vs. Best-of-5 0.937).
Optimizer choice matters substantially: L-BFGS-B with parameter-shift gradients
reaches the same best ratio as Nelder-Mead at 13× fewer function evaluations.
Under depolarizing noise, the depth–noise crossover is graph-dependent — the
3-regular graph's 50% higher CX count per layer shifts the crossover from
$p_{cx} \approx 0.020$ (on $C_{10}$) down to $\approx 0.010$, meaning hardware
fidelity requirements tighten with graph density. These findings suggest that
benchmarking QAOA requires jointly reporting the approximation ratio, optimizer
budget, graph structure, and noise regime under which results were obtained.

---

## References

- Farhi, Goldstone, Gutmann. *A quantum approximate optimization algorithm.* arXiv:1411.4028 (2014).
- Goemans, Williamson. *Improved approximation algorithms for maximum cut.* JACM 42(6), 1995.
- McClean et al. *Barren plateaus in quantum neural network training landscapes.* Nature Commun. 9, 2018.
- Wang et al. *Noise-induced barren plateaus in variational quantum algorithms.* Nature Commun. 12, 2021.
- Zhou et al. *Quantum approximate optimization algorithm: Performance, mechanism, and implementation.* PRX Quantum 1, 2020.
- Bravyi et al. *Obstacles to variational quantum optimization from symmetry protection.* PRL 125, 2020.
