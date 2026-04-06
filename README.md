# QAOA for Maximum Cut

**A quantitative comparison of QAOA against classical MaxCut algorithms: performance, limits, and noise robustness.**

Seven notebooks build the comparison from scratch — problem motivation and mathematical foundations, circuit verification and optimizer methodology, experimental benchmarks against classical baselines, and noise robustness analysis under a depolarizing model.

---

## TL;DR

- **Noiseless QAOA improves monotonically with depth**: $p=1,2,3$ approximation ratios increase consistently across all graph instances tested.
- **Shallow QAOA ($p \leq 3$) does not outperform GW or best-of-5 greedy in general** — it gains a marginal advantage only on graphs where local heuristics fail (long-range edges).
- **Noise limits the usable depth**: above ~1% CX error rate, $p=1$ outperforms $p=3$. The crossover point is hardware-dependent.
- **Gradient correctness (per-edge parameter-shift)** is a more critical bottleneck than optimizer choice.
- Overall: QAOA is competitive in a **narrow regime defined by graph structure, circuit depth, and hardware fidelity**. The depth at which it would clearly outperform classical methods likely exceeds what current NISQ hardware can support reliably.

![Algorithm comparison](results/figures/algorithm_comparison.png)
*Approximation ratios for all methods across three graph instances (noiseless simulation). Left: full comparison including classical baselines and GW bound (dashed). Right: QAOA ratio vs depth $p$ — monotone increase with $p$, most pronounced on the chord graph.*

---

## Repository Structure

```
.
├── motivation/
│   └── 00_Applications_and_Motivation.ipynb
├── theory/
│   ├── 01_QAOA_Theory_Part1_Hamiltonian.ipynb
│   └── 02_QAOA_Theory_Part2_Circuits_and_Landscape.ipynb
├── implementation/
│   ├── 03_QAOA_C4_Complete_Analysis.ipynb
│   └── 04_QAOA_Optimizer_Comparison.ipynb
└── results/
    ├── 05_QAOA_Experiments.ipynb
    └── 06_QAOA_Noise.ipynb
```

Each folder has its own README with full mathematical detail. This document gives the project-level overview.

---

## Project Arc

### Motivation
**Why MaxCut?** Portfolio diversification, job scheduling, facility location, and network partitioning all reduce to a weighted cut problem on an appropriate graph. The unifying structure is QUBO (Quadratic Unconstrained Binary Optimisation):

$$\min_{z \in \{0,1\}^n} z^T Q z \;\longleftrightarrow\; H_C = \sum_{(i,j) \in E} \frac{w_{ij}}{2}(I - Z_iZ_j)$$

The QAOA circuit is not specific to MaxCut — it is a general variational ansatz for any QUBO, with only the edge weights changing across problem instances. Whether this mechanism provides any advantage over classical methods is the question the project investigates.

### Theory
The theory notebooks derive the full mathematical structure of QAOA from scratch, assuming linear algebra background but minimal physics prerequisite.

**Part I** (Notebook 01) builds the chain: MaxCut combinatorics → Ising spin model → quantum Hamiltonian via Pauli-Z. The key step is the substitution $s_i \to Z_i$, which is exact on all computational basis states simultaneously, giving

$$H_C = \sum_{(i,j) \in E} \frac{I - Z_iZ_j}{2}$$

with diagonal entries equal to $C(z)$. The QAOA ansatz

$$|\psi_p(\boldsymbol{\gamma}, \boldsymbol{\beta})\rangle = U_B(\beta_p) U_C(\gamma_p) \cdots U_B(\beta_1) U_C(\gamma_1) |+\rangle^{\otimes n}$$

is derived and each component justified: $U_C(\gamma) = e^{-i\gamma H_C}$ performs phase separation (not amplitude reshaping); $U_B(\beta) = e^{-i\beta \sum_i X_i}$ mixes amplitudes; $|+\rangle^{\otimes n}$ is the maximum-eigenvalue eigenstate of $H_B$.

**Part II** (Notebook 02) covers the classical algorithms QAOA competes against, derives the CNOT–$R_Z$–CNOT gate decomposition of $U_C$, and characterises the optimisation landscape including barren plateaus and three distinct sources of numerical error.

### Implementation
The implementation notebooks make all analytical and algorithmic choices explicit before those choices are committed to the larger pipeline.

**Notebook 03** verifies the circuit construction gate-by-gate on $C_4$ — the smallest bipartite cycle, with $C_{\max} = 4$ and exact optimal parameters $\gamma^* = \pi/4$, $\beta^* = \pi/8$ at $p=1$. Statevector evolution is traced step by step; the CNOT–$R_Z$–CNOT decomposition is verified numerically to $< 10^{-14}$ against `scipy.linalg.expm`. Resource counts are established: CX gates $= 2p|E|$, reducible to $O(2p)$ depth via edge 2-coloring on $C_4$.

**Notebook 04** establishes the correct gradient formulation and benchmarks four optimisers (COBYLA, Nelder-Mead, L-BFGS-B, SPSA) on $C_{10}$. The central finding is that **per-edge parameter-shift correctness is a prerequisite, not an optimisation detail**: shifting the global $\gamma$ by $\pi/2$ simultaneously across all edges gives a wrong gradient regardless of which solver is used downstream. The correct formulation sums per-edge shifts:

$$\frac{\partial F_p}{\partial \gamma_\ell} = \frac{1}{2} \sum_{(i,j) \in E} \left[F_p(\ldots,\, \gamma_\ell^{(ij)} + \tfrac{\pi}{2},\, \ldots) - F_p(\ldots,\, \gamma_\ell^{(ij)} - \tfrac{\pi}{2},\, \ldots)\right]$$

Layer-by-layer warm-start (Zhou et al. 2020) is demonstrated to reduce variance at $p=3$ on a chord graph.

### Results
**Notebook 05** benchmarks QAOA $p=1,2,3$ against four classical algorithms — random assignment, single-pass greedy, best-of-5 greedy, and Goemans–Williamson SDP — on three graph instances with distinct structural properties.

**Notebook 06** sweeps depolarizing CX error rate $p_{cx} \in [0, 0.025]$ on all three graphs and identifies the circuit depth at which additional layers become counterproductive.

---

## Key Findings

### Performance vs Classical

**1. QAOA $p=1$ beats single-pass greedy but not best-of-5 greedy or GW on any instance tested.**
The right classical baseline is best-of-5 greedy, not single-pass greedy: it is almost always stronger and far cheaper than a single QAOA objective evaluation. GW remains superior on all instances.

**2. QAOA gains the most where greedy is weakest.**
On the chord graph ($C_{10}$ + 3 long-range edges), single-pass greedy drops to ratio $0.726$ while QAOA $p=3$ reaches $0.872$, marginally above best-of-5 greedy ($0.864$). On the plain cycle, where greedy is stronger, the advantage of deeper QAOA is smaller. This is consistent with QAOA's known locality limitation: shallow QAOA cannot distinguish graphs that agree within radius $p$ of every vertex (Bravyi et al. 2021).

### Algorithmic Insight

**3. Gradient correctness is a more fundamental bottleneck than optimizer choice.**
Shifting the global $\gamma$ by $\pi/2$ simultaneously across all edges gives a wrong gradient on $C_4$ regardless of which solver is used downstream. The correct formulation sums per-edge shifts; fixing this is a prerequisite before any optimizer comparison is meaningful.

### Hardware Constraints

**4. Deeper circuits are not unconditionally better under noise.**
Under the depolarizing model used here, $p=3$ has $3\times$ more CX gates than $p=1$ and degrades faster. Above $p_{cx} \approx 1\%$, $p=1$ outperforms $p=3$ on all three graphs. The optimal depth is a function of both the target approximation ratio and the native CX fidelity of the device.

**5. Noise and barren plateaus act in the same direction.**
Depolarizing noise flattens the energy landscape monotonically with $p_{cx}$. This compounds the barren plateau effect: both mechanisms reduce the gradient signal available to the optimiser and cannot be addressed independently.

---

## Honest Scope

All experiments use statevector simulation (noiseless) or Qiskit Aer with a simplified depolarizing model. Graphs are small ($n = 10$) and unweighted. The noise model does not capture coherent errors, crosstalk, or qubit-specific variation. Findings should be interpreted as indicative of trends on small instances under idealised conditions, not as predictions for specific hardware or large-scale problems.

---

## Dependencies

```
numpy scipy matplotlib networkx qiskit qiskit-aer cvxpy
```

Install via:

```bash
pip install numpy scipy matplotlib networkx qiskit qiskit-aer cvxpy
```

---

## References

- Farhi, Goldstone, Gutmann. *A quantum approximate optimization algorithm.* arXiv:1411.4028, 2014.
- Goemans, Williamson. *Improved approximation algorithms for maximum cut and satisfiability problems using semidefinite programming.* JACM 42(6), 1995.
- Karp, R. *Reducibility among combinatorial problems.* 1972.
- Khot et al. *Optimal inapproximability results for MAX-CUT and other 2-variable CSPs.* JACM 54(3), 2007.
- McClean et al. *Barren plateaus in quantum neural network training landscapes.* Nature Commun. 9, 2018.
- Wang et al. *Noise-induced barren plateaus in variational quantum algorithms.* Nature Commun. 12, 2021.
- Cerezo et al. *Cost function dependent barren plateaus in shallow parametrized quantum circuits.* Nature Commun. 12, 2021.
- Bravyi et al. *Obstacles to variational quantum optimization from symmetry protection.* arXiv:2110.14206, 2021.
- Zhou et al. *Quantum approximate optimization algorithm: Performance, mechanism, and implementation on near-term devices.* Phys. Rev. X 10, 2020.
