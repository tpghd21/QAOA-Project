# Chapter 3 — Theory: From the Cost Function to a Cost Hamiltonian

This folder builds the theoretical foundation of QAOA for MaxCut: how the classical cost function becomes a quantum operator, why the QAOA ansatz has the form it does, and what classical baselines QAOA must compete against.

| Notebook | Title | Contents |
|---|---|---|
| `01_QAOA_Theory_Part1_Hamiltonian.ipynb` | From Combinatorial Problem to Quantum Hamiltonian | MaxCut → Ising → $H_C$ → QAOA ansatz |
| `02_QAOA_Theory_Part2_Circuits_and_Landscape.ipynb` | Circuits, Classical Baselines, and Landscape | CNOT–$R_Z$–CNOT decomposition, greedy & GW, barren plateaus |

---

## Part I — From combinatorial problem to quantum Hamiltonian

### 1. What are we looking for?

After running QAOA we measure $|\psi\rangle$ in the computational basis. A measurement gives a bitstring $z = z_0 z_1 \cdots z_{n-1}$. We interpret it as a partition via

$$z_i = 0 \;\Leftrightarrow\; i \in S, \qquad z_i = 1 \;\Leftrightarrow\; i \in \bar S$$

On $C_4$, bitstrings like $|1010\rangle$ and $|0101\rangle$ correspond to the two MaxCut partitions with cut value $4$. **The goal of QAOA is to maximise the probability of sampling a bitstring whose cut value equals $C_{\max}$.**

### 2. Cost Hamiltonian: three steps

The classical cost function $C(z) = \sum_{(i,j) \in E} \mathbf{1}[z_i \neq z_j]$ becomes a quantum operator in three substitutions.

**Step 1 — Decision variable.** $z_i \in \{0, 1\}$ with the partition convention above. Then

$$C(z) = \sum_{(i,j) \in E} \mathbf{1}[z_i \neq z_j]$$

**Step 2 — Rewrite with spin variable.** Substitute $s_i = 1 - 2 z_i \in \{+1, -1\}$. A short check:

$$\mathbf{1}[z_i \neq z_j] = \frac{1 - s_i s_j}{2}$$

This rewrites $C$ as a polynomial in $\pm 1$ spins, i.e. a classical **Ising model**.

**Step 3 — Quantise.** Replace $s_i \to Z_i$ (Pauli-$Z$ on qubit $i$). Because $Z_i$ is diagonal in the computational basis with eigenvalues $\pm 1$ matching $s_i$, the substitution is **exact** on every basis state simultaneously. The result is the **cost Hamiltonian**:

$$\boxed{\; H_C = \sum_{(i,j) \in E} \frac{I - Z_i Z_j}{2} \;}$$

Key property: $H_C$ is diagonal in the computational basis, and its $(z, z)$ entry is exactly $C(z)$. So maximising $\langle \psi | H_C | \psi \rangle$ concentrates $|\psi\rangle$ on high-cut bitstrings.

On $C_4$, $H_C$ is a $16 \times 16$ diagonal matrix with maximum eigenvalue $4$, attained on $|0101\rangle$ and $|1010\rangle$.

### 3. The QAOA ansatz

QAOA prepares a parameterised state by alternating two families of unitaries over $p$ layers:

$$|\psi_p(\boldsymbol\gamma, \boldsymbol\beta)\rangle = U_B(\beta_p) U_C(\gamma_p) \cdots U_B(\beta_1) U_C(\gamma_1)\, |+\rangle^{\otimes n}$$

- **Cost unitary** $U_C(\gamma) = e^{-i\gamma H_C}$: imprints a phase $e^{-i\gamma C(z)}$ on each basis state. On its own this is **phase separation** — all probabilities $|\langle z | \psi \rangle|^2$ remain unchanged.
- **Mixer unitary** $U_B(\beta) = e^{-i\beta H_B}$ with $H_B = \sum_i X_i$: rotates amplitudes between Hamming-1 neighbours. This is what redistributes probability — probabilities change through the interference between phases imprinted by $U_C$ and amplitude mixing by $U_B$.
- **Parameters** $(\boldsymbol\gamma, \boldsymbol\beta) \in \mathbb{R}^{2p}$ are tuned to maximise $F_p = \langle \psi_p | H_C | \psi_p \rangle$.

### 4. Why start from $|+\rangle^{\otimes n}$?

The starting state $|+\rangle^{\otimes n} = H^{\otimes n} |0\rangle^{\otimes n} = 2^{-n/2} \sum_{z} |z\rangle$ is chosen for four reasons:

1. **Uniform over candidates.** Every bitstring has the same initial amplitude — no partition is preferred a priori.
2. **Aligned with the mixer.** $X|+\rangle = |+\rangle$, so $|+\rangle^{\otimes n}$ is the maximum-eigenvalue eigenstate of $H_B = \sum_i X_i$ (eigenvalue $+n$). This makes the first mixer layer maximally effective.
3. **Cheap to prepare.** A single layer of Hadamard gates on $|0\rangle^{\otimes n}$ — constant depth, no entangling gates.
4. **Adiabatic starting point.** In the adiabatic interpretation of QAOA, we interpolate from $H_B$ (at $t = 0$) to $H_C$ (at $t = T$). The ground state of $H(0) = H_B$ is exactly $|+\rangle^{\otimes n}$ (in the convention $H_B = -\sum_i X_i$) or its maximum-eigenstate (as we use it). Either way it is the natural start.

### 5. Measurement and shots

After preparing $|\psi_p\rangle$, measuring in the computational basis yields bitstring $z$ with probability $|\langle z | \psi_p \rangle|^2$. Running $S$ independent **shots** gives an estimate

$$\hat F_p = \frac{1}{S} \sum_{s=1}^{S} C(z^{(s)}) \xrightarrow{S \to \infty} F_p$$

This is the **shot-noise** regime in which a real device operates. The estimator's standard error scales as $O(|E|/\sqrt S)$, so estimating $F_p$ to precision $\varepsilon$ costs $S = O(|E|^2 / \varepsilon^2)$ shots. Shot noise corrupts gradient estimates and is one of the main reasons a gradient-free optimiser like SPSA is preferred on hardware.

---

## Part II — Circuits, classical baselines, and landscape

### 1. Gate decomposition: CNOT–$R_Z$–CNOT

Each edge term $e^{i(\gamma/2) Z_i Z_j}$ in $U_C(\gamma)$ (up to a global phase) is implemented by

$$e^{i\frac{\gamma}{2} Z_i Z_j} = \text{CNOT}_{ij} \cdot (I \otimes R_Z(-\gamma))_j \cdot \text{CNOT}_{ij}$$

The identity follows from the conjugation rule $\text{CNOT}(I \otimes Z)\text{CNOT} = Z \otimes Z$ — sandwiching a single-qubit $R_Z$ between two CNOTs promotes it to a two-qubit $ZZ$-rotation. Numerical verification against `scipy.linalg.expm` confirms the decomposition to machine precision.

Resource cost per layer:

- $U_C$: $2|E|$ CNOTs and $|E|$ $R_Z$ gates.
- $U_B$: $n$ single-qubit $R_X(2\beta)$ gates, no entangling gates.

For $C_{10}$, one layer is $20$ CX + $10$ $R_Z$ + $10$ $R_X$; depth $p$ scales these linearly.

### 2. Classical benchmarks

QAOA must compete against polynomial-time classical algorithms. We benchmark against three:

**Greedy.** Visit vertices in some order; each vertex joins the side that cuts more of its already-assigned neighbours. Guaranteed ratio $\geq 0.5$. Runs in $O(|V| + |E|)$ — far cheaper than a single QAOA objective evaluation.

**Greedy best-of-5.** Run greedy with 5 independent random orderings, keep the best cut. Still $O(|V| + |E|)$, but empirically much stronger than single-pass greedy.

**Goemans–Williamson (GW).** Relax the integer program by replacing $s_i \in \{\pm 1\}$ with unit vectors $v_i \in \mathbb R^n$, solve the resulting semidefinite program, and round by a random hyperplane. Guaranteed ratio

$$\mathbb E[C_{\text{GW}}] \geq \alpha_{\text{GW}} \cdot C_{\max}, \qquad \alpha_{\text{GW}} \approx 0.8786$$

Runtime $O(n^{3.5})$ — the polynomial-time gold standard. Under the Unique Games Conjecture this bound is tight: no polynomial-time algorithm can do better on worst-case instances (Khot et al. 2007).

The unconditional NP-hardness bound $16/17 \approx 0.941$ (Håstad 2001) sits above GW — improving beyond $0.941$ is provably impossible in polynomial time unless $P = NP$, but the $0.941$–$0.8786$ gap is only conditionally closed.

### 3. Why GW is a hard ceiling for shallow QAOA

**Globality of GW.** The SDP solution captures pairwise information among all $\binom{n}{2}$ vertex pairs simultaneously; the hyperplane rounding is equally global.

**Locality of shallow QAOA.** After $p$ layers, qubit $i$ has only interacted with qubits within graph distance $p$. Bravyi et al. (2021) formalise this: QAOA at depth $p$ cannot distinguish two graphs that agree within radius $p$ of every vertex. On sparse, locally tree-like graphs this is a meaningful obstruction — shallow QAOA cannot reach the GW ratio without $p$ growing with the graph.

This is a known limitation. It does not preclude QAOA from being competitive on denser graphs, at larger $p$, or on graphs with special non-local structure exploited by the cost unitary.

### 4. Barren plateaus

For a sufficiently expressive ansatz on a $k$-local cost function (McClean et al. 2018), the gradient variance is bounded by $\mathrm{Var}[\partial_\theta F_p] \leq C/b^n$ with $b \geq 2$ — exponential decay in system size. When this holds, no polynomial number of shots can distinguish the gradient from zero, and gradient-based optimisation becomes exponentially hard. MaxCut at low depth is partially shielded by its 2-local structure, and noise compounds the flattening (Wang et al. 2021). Notebook 02 §5 contains the formal statement and a numerical demonstration on cycle graphs $n \in \{4, \ldots, 12\}$ — at our scale the decay is only $O(1/\mathrm{poly}(n))$.

### 5. Numerical error sources (brief)

Three distinct sources of error enter the numerical experiments:

- **Floating-point error.** Statevectors are stored in double precision; after $d$ gates, rounding errors accumulate as $O(d \varepsilon_{\text{mach}})$ with $\varepsilon_{\text{mach}} \approx 2.2 \times 10^{-16}$. Negligible at the depths we run.
- **Shot noise.** Finite-sample estimator of $F_p$ with standard error $O(|E|/\sqrt S)$. Relevant when Qiskit Aer is used with a finite shot count or on real hardware.
- **Optimiser convergence error.** Any iterative solver returns an approximate optimum; for gradient-free methods the gap depends on landscape ruggedness and the evaluation budget.

---

## Dependencies

```
numpy, scipy, matplotlib, networkx, qiskit, cvxpy
```

---

## References

- Farhi, Goldstone, Gutmann. *A quantum approximate optimization algorithm.* arXiv:1411.4028, 2014.
- Goemans, Williamson. *Improved approximation algorithms for maximum cut and satisfiability problems using semidefinite programming.* JACM 42(6), 1995.
- Håstad, J. *Some optimal inapproximability results.* JACM 48(4), 2001.
- Khot et al. *Optimal inapproximability results for MAX-CUT and other 2-variable CSPs.* JACM 54(3), 2007.
- McClean et al. *Barren plateaus in quantum neural network training landscapes.* Nature Commun. 9, 2018.
- Wang et al. *Noise-induced barren plateaus in variational quantum algorithms.* Nature Commun. 12, 2021.
- Bravyi et al. *Obstacles to variational quantum optimization from symmetry protection.* arXiv:2110.14206, 2021.
