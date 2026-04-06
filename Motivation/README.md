# QAOA — Motivation


Before deriving any quantum algorithm, this notebook answers the prior question: **why MaxCut?** The answer is not that MaxCut is a convenient graph theory puzzle — it is that MaxCut is the mathematical skeleton of a broad class of binary optimisation problems that arise independently across finance, operations research, and system design. The QAOA circuit structure is the same across all of them; only the edge weights change.

---

## Notebook

| Notebook | Title |
|---|---|
| `00_Applications_and_Motivation.ipynb` | Why MaxCut? Real-World Applications |

---

## 1. The Unifying Structure

Many practical optimisation problems share the following form:

- A set of **objects** (assets, jobs, sites, tasks)
- **Pairwise relationships** between them (correlation, conflict, overlap, communication cost)
- A binary **assignment decision** for each object

This maps directly onto a weighted graph $G = (V, E, w)$ where $w : E \to \mathbb{R}$ encodes the pairwise relationship. The optimisation objective — whether maximising diversity, minimising conflict, or balancing load — turns out in each case to be equivalent (up to sign and constant) to a weighted cut value:

$$C(z) = \sum_{(i,j) \in E} w_{ij}\, \mathbf{1}[z_i \neq z_j], \qquad z_i \in \{0,1\}$$

This is not a coincidence. The notebook shows explicitly that portfolio diversification, job scheduling, facility location, and network partitioning all reduce to this form.

---

## 2. Portfolio Diversification — Full Derivation

The main worked example is portfolio diversification, where the reduction is derived in full.

**Setup.** An investor holds $n$ assets with daily returns $r_i(t)$. The pairwise correlation is

$$\rho_{ij} = \frac{\mathrm{Cov}(r_i, r_j)}{\sigma_i \sigma_j} \in [-1, 1]$$

High correlation between two assets means concentrated risk: when one falls, the other is likely to fall simultaneously. Diversification requires separating correlated assets into different groups.

**Reduction.** Assign $z_i \in \{0,1\}$ indicating which of two groups asset $i$ belongs to. The total within-group correlation is

$$\sum_{(i,j)} |\rho_{ij}|\, \mathbf{1}[z_i = z_j] = \sum_{(i,j)} |\rho_{ij}| - \sum_{(i,j)} |\rho_{ij}|\, \mathbf{1}[z_i \neq z_j]$$

Minimising within-group correlation is therefore equivalent to **maximising the weighted cut** on the graph with edge weights $w_{ij} = |\rho_{ij}|$. The synthetic data used in the notebook has sector structure (Tech / Finance / Energy), so the optimal cut should recover the sector boundaries — which it does.

**Solution.** The weighted MaxCut SDP (Goemans–Williamson generalised to weighted graphs) is applied and the rounded solution is shown to align with sector boundaries.

---

## 3. Further Reductions

These three examples each highlight a structurally distinct aspect of the QUBO reduction.

**Job scheduling** — *pure combinatorial conflict.* $n$ jobs must be assigned to one of two time slots. Jobs $i$ and $j$ conflict with penalty $c_{ij}$ if they run in the same slot. The total conflict cost is

$$\text{Conflict}(z) = \sum_{(i,j)} c_{ij}\, \mathbf{1}[z_i = z_j] = \sum_{(i,j)} c_{ij} - C(z)$$

Minimising conflict is equivalent to maximising the weighted cut on the conflict graph. Unlike portfolio diversification, the edge weights here are integer-valued conflict counts rather than continuous correlations — the reduction works regardless of weight type.

**Facility location** — *asymmetric same-side penalty.* $n$ candidate sites are assigned open ($z_i = 1$) or closed ($z_i = 0$). The overlap penalty $o_{ij}$ is incurred only when both sites are open ($z_i = z_j = 1$), not when both are closed. This is an asymmetric same-side cost, which requires a symmetrisation step before the QUBO form applies. After symmetrisation, the problem reduces to weighted MaxCut on the overlap graph. The symmetrisation step is what distinguishes this from the scheduling case.

**Network partitioning / load balancing** — *MaxCut–MinCut duality.* A workload graph has vertices (tasks) and edges weighted by inter-task communication volume. Minimising communication cost between two processors requires placing tasks that communicate heavily on the same processor — minimising the weighted cut, not maximising it. This is weighted **MinCut**, which is equivalent to weighted MaxCut on the sign-negated weights and shares the same QUBO structure. This duality shows that the QUBO formulation is not restricted to maximisation objectives.

---

## 4. QUBO Unification

All four problems are instances of **Quadratic Unconstrained Binary Optimisation (QUBO)**:

$$\min_{z \in \{0,1\}^n} z^T Q z = \min_z \sum_{i,j} Q_{ij} z_i z_j$$

where $Q \in \mathbb{R}^{n \times n}$ encodes the problem structure. MaxCut is the special case $Q_{ij} = -w_{ij}$ for $(i,j) \in E$ and $Q_{ii} = \sum_j w_{ij}$ (row sums), which gives:

$$z^T Q z = \sum_{(i,j) \in E} w_{ij}(z_i - z_j)^2 = \sum_{(i,j) \in E} w_{ij}\, \mathbf{1}[z_i \neq z_j]$$

since $z_i \in \{0,1\}$ implies $(z_i - z_j)^2 = \mathbf{1}[z_i \neq z_j]$.

Every QUBO maps to an Ising Hamiltonian via $z_i = (1 - s_i)/2$, $s_i \in \{-1,+1\}$:

$$H_C = \sum_{(i,j) \in E} \frac{w_{ij}}{2}(I - Z_iZ_j) + \text{const}$$

This is the same $H_C$ that appears in all subsequent notebooks. The QAOA circuit is therefore not specific to MaxCut — it is a general variational ansatz for any QUBO problem, and the only modification needed to apply it to the problems above is changing the edge weights.

---

## Key Takeaway

MaxCut is studied here not because it is the most practically important combinatorial problem in isolation, but because it is a **canonical QUBO instance**: the reduction from weighted graph to Ising Hamiltonian is exact, the QAOA circuit structure is unchanged across problem instances, and the classical approximation guarantees (in particular, Goemans–Williamson) are the strongest known for any NP-hard problem in this class. Understanding QAOA on unweighted MaxCut is therefore a prerequisite for understanding it on the broader class of binary quadratic optimisation problems.

These reductions justify MaxCut as a unifying model. They do not by themselves justify the use of QAOA. Classical polynomial-time algorithms such as Goemans–Williamson provide strong approximation guarantees ($\geq 0.8786 \cdot C_{\max}$), and fast heuristics such as greedy are competitive on many instances. QAOA introduces a different mechanism: the objective is encoded into a quantum phase, and alternating unitary layers use coherent interference to shape the probability distribution over bitstrings. Whether this mechanism provides any practical advantage over classical methods — and if so, under what conditions on graph structure, circuit depth, and hardware noise — is precisely the question this project investigates in the subsequent notebooks.

---

## Dependencies

```
numpy, matplotlib, networkx, cvxpy
```

---

## References

- Karp, R. *Reducibility among combinatorial problems.* 1972.
- Goemans, Williamson. *Improved approximation algorithms for maximum cut and satisfiability problems using semidefinite programming.* JACM 42(6), 1995.
- Farhi, Goldstone, Gutmann. *A quantum approximate optimization algorithm.* arXiv:1411.4028, 2014.
