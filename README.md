# QAOA for Maximum Cut

**Sehong Park and Adolfo Menendez Rua — Physics 565 / 656, Spring 2026**

A study of the Quantum Approximate Optimization Algorithm (QAOA) applied to the MaxCut problem on small graphs: from the combinatorial definition through the quantum circuit, classical baselines, and noise robustness.

The READMEs and notebooks together cover the project end-to-end: motivation (QUBO / MaxCut), theory (Hamiltonian, ansatz, circuit decomposition, classical baselines), implementation ($C_4$ walkthrough, optimiser comparison, warm start, explicit Qiskit circuit on $C_{10}$), and results (classical benchmarks, depolarizing noise sweep).

---

## TL;DR

- **QUBO** ($\min x^T Q x + c^T x$, $x \in \{0,1\}^n$) is the unifying form for many real-world binary optimisation problems — portfolio selection, job scheduling, facility location, network partitioning. Quantum hardware solves it directly via the Ising substitution $x_i = (1 - Z_i)/2$.
- **MaxCut** is the simplest QUBO ($h_i = 0$, only $ZZ$ couplings). By Barahona's theorem, every QUBO on $n$ variables reduces to MaxCut on $n+1$ vertices, so studying MaxCut QAOA loses no generality.
- **QAOA** encodes the MaxCut Hamiltonian $H_C$ and alternates two unitaries — the *cost* $U_C(\gamma)$ and *mixer* $U_B(\beta)$ — over $p$ layers. The classical outer loop tunes $(\gamma, \beta)$ to maximise $\langle H_C \rangle$.
- **Noiseless performance** improves monotonically with depth: on three 10-vertex graphs, QAOA $p=1 \to 2 \to 3$ gives approximation ratios roughly $0.75 \to 0.83 \to 0.87$.
- **Classical comparison:** QAOA $p=1$ beats random and single-pass greedy but not best-of-5 greedy or Goemans–Williamson (GW). QAOA $p=3$ approaches the GW bound ($\approx 0.8786$) on the chord graph, where greedy heuristics struggle most.
- **Under noise** (depolarizing channel on each CX gate), the ordering among depths reverses: above $p_{cx} \approx 1\%$, the shallower $p=1$ circuit outperforms $p=3$ because deeper circuits accumulate more gate error.

![Algorithm comparison](Results/figures/algorithm_comparison.png)

*Approximation ratios for all methods across three graph instances (noiseless simulation). Left: full comparison including classical baselines and the GW bound (dashed). Right: QAOA ratio vs depth $p$ — monotone increase with $p$, most pronounced on the chord graph.*

---

## Repository Structure

```
.
├── Motivation/                          ← Introduction and motivation
│   └── 00_Applications_and_Motivation.ipynb
├── Theory/                              ← QAOA theory
│   ├── 01_QAOA_Theory_Part1_Hamiltonian.ipynb
│   └── 02_QAOA_Theory_Part2_Circuits_and_Landscape.ipynb
├── Implementation/                      ← Implementation
│   ├── 03_QAOA_C4_Complete_Analysis.ipynb
│   ├── 04_QAOA_Optimizer_Comparison.ipynb
│   └── 05_QAOA_QuantumCircuit.ipynb
└── Results/                             ← Experiments and noise
    ├── 06_QAOA_Experiments.ipynb
    └── 07_QAOA_Noise.ipynb
```

Each folder contains its own README with a detailed walkthrough.

---

## Chapter 1 — Introduction: Graphs, Cuts, MaxCut

A graph $G = (V, E)$ is a finite vertex set $V$ together with an edge set $E$ of unordered pairs. A **cut** partitions $V$ into two disjoint sets $S$ and $\bar S$; the cut value is the number of edges with one endpoint on each side:

$$C(S) = \big|\{(i,j) \in E : i \in S, j \in \bar S\}\big|$$

**MaxCut** asks for the partition that maximises $C(S)$. On the 4-cycle $C_4$, there are $2^4 = 16$ labelled partitions, $2^3 = 8$ distinct cuts, and the maximum cut value is $4$ — achieved when adjacent vertices are on opposite sides.

MaxCut is **NP-hard** in general (Karp 1972), so we must accept approximation for large inputs. See [Motivation/README.md](Motivation/README.md) for the full development.

---

## Chapter 2 — Motivation: From QUBO to MaxCut

The story behind why this project tackles MaxCut has three steps.

**Step 1 — Real-world problems are QUBO.** Portfolio selection, job scheduling, facility location, and network partitioning are all NP-hard binary optimisation problems with pairwise interactions. They share a unifying form:

$$\min_{x \in \{0,1\}^n}\; x^T Q x + c^T x$$

with $Q$ encoding pairwise interactions and $c$ encoding individual costs. Lucas (2014) gives explicit QUBO formulations for 25+ NP-hard problems.

**Step 2 — QUBO is solved directly on quantum hardware.** The substitution $x_i = (1 - Z_i)/2$ converts QUBO into an Ising Hamiltonian — Pauli-$Z$ fields and $ZZ$ couplings, which is the *native vocabulary* of every major qubit platform. QAOA optimises this Hamiltonian as-is; no reduction tricks are required.

**Step 3 — MaxCut is the canonical simplest QUBO.** Pure quadratic ($h_i = 0$, only $ZZ$ couplings), it admits the cleanest theoretical analysis and serves as the standard cross-paper benchmark. By **Barahona's universality theorem (1982)**, every QUBO on $n$ variables is equivalent to MaxCut on $n+1$ vertices via a single ancilla qubit — focusing on MaxCut therefore loses no generality, while keeping the math and circuits as transparent as possible.

The notebook walks through portfolio selection (Markowitz binary form, with a separate pure-MaxCut "risk-only partitioning" framing motivated by Hierarchical Risk Parity and long-short hedging), job scheduling on a conflict graph, facility location with overlap penalties, and network partitioning. Each is a QUBO; the QAOA circuit is the same across all of them — only the numerical weights $\{J_{ij}, h_i\}$ in $U_C(\gamma) = e^{-i\gamma H_C}$ change.

---

## Chapter 3 — Theory: From the Cost Function to a Cost Hamiltonian

The key theoretical step is turning the classical cost function into a quantum operator whose eigenvalues are exactly the cut values.

### 3.1 Three-step derivation

Starting from the indicator for a cut edge, $\mathbf{1}[z_i \neq z_j]$:

1. **Binary variable.** $z_i \in \{0, 1\}$, with $z_i = 0 \Leftrightarrow i \in S$ and $z_i = 1 \Leftrightarrow i \in \bar S$. Then $C(z) = \sum_{(i,j)\in E} \mathbf{1}[z_i \neq z_j]$.
2. **Spin variable.** Substitute $s_i = 1 - 2 z_i \in \{+1, -1\}$. Then $\mathbf{1}[z_i \neq z_j] = (1 - s_i s_j)/2$.
3. **Quantise.** Replace $s_i \to Z_i$ (Pauli-Z on qubit $i$). The substitution is exact on every computational basis state.

$$\boxed{\; H_C \;=\; \sum_{(i,j) \in E} \tfrac{I - Z_i Z_j}{2} \;}$$

$H_C$ is diagonal in the computational basis; its $(z, z)$ entry is exactly $C(z)$. Maximising $\langle \psi | H_C | \psi \rangle$ therefore pushes the state toward the MaxCut bitstrings.

### 3.2 The QAOA ansatz

$$|\psi_p(\boldsymbol\gamma, \boldsymbol\beta)\rangle = U_B(\beta_p)\, U_C(\gamma_p) \cdots U_B(\beta_1)\, U_C(\gamma_1)\, |+\rangle^{\otimes n}$$

- $U_C(\gamma) = e^{-i\gamma H_C}$ imprints a phase $e^{-i\gamma C(z)}$ on every basis state (**phase separation**; probabilities don't change yet).
- $U_B(\beta) = e^{-i\beta \sum_i X_i}$ mixes amplitudes between bitstrings. Interference between $U_C$ and $U_B$ is what concentrates probability on high-cut states.
- Starting state $|+\rangle^{\otimes n} = H^{\otimes n}|0\rangle^{\otimes n}$ is chosen because it is (i) the uniform superposition over all candidates, (ii) the maximum-eigenvalue eigenstate of the mixer $H_B$, (iii) cheap to prepare, and (iv) the natural adiabatic starting point.

### 3.3 Classical benchmarks

QAOA is compared against three classical algorithms:

- **Greedy.** Process vertices in order; each joins the side that cuts more already-assigned neighbours. Guaranteed ratio $\geq 0.5$.
- **Greedy best-of-5.** Run greedy with 5 independent random orderings, keep the best cut. Still $O(|V| + |E|)$ but much stronger in practice.
- **Goemans–Williamson (GW).** Relax spins to unit vectors, solve a semidefinite program, round by a random hyperplane. Guaranteed ratio $\geq 0.8786$ (Goemans–Williamson 1995). Unconditional improvements are believed impossible: $16/17 \approx 0.941$ is NP-hard (Håstad 2001), and under the Unique Games Conjecture $0.8786$ is already tight (Khot et al. 2007).

See [Theory/README.md](Theory/README.md) for the full Theory chapter.

---

## Chapter 4 — Implementation: Circuit, Optimisation, Warm Start

### 4.1 Quantum circuit on $C_{10}$

Each layer applies the two unitaries:

- $U_C(\gamma) = \prod_{(i,j) \in E} e^{-i\gamma (I - Z_i Z_j)/2}$, decomposed edge-by-edge as **CNOT — $R_Z(-\gamma)$ — CNOT**.
- $U_B(\beta) = \prod_k R_X(2\beta)_k$ — a separable layer of single-qubit X-rotations; no entangling gates.

Per layer on $C_{10}$ that's 20 CX + 10 $R_Z$ gates for $U_C$ and 10 $R_X$ gates for $U_B$. The full circuit has $2p$ variational parameters.

### 4.2 Hybrid optimisation loop

QAOA is a **quantum-classical hybrid**: the quantum processor prepares $|\psi_p(\gamma, \beta)\rangle$ and estimates $F_p = \langle H_C \rangle$ by sampling; a classical optimiser updates $(\gamma, \beta)$; repeat until convergence. Only scalar cost values cross the boundary.

We use **L-BFGS-B** (gradient-based via per-edge parameter-shift) for noiseless simulation, run in parallel with **COBYLA** (gradient-free) as a cross-check. On real hardware, SPSA would replace both. Two subtleties worth flagging:

- **Parameter-shift gradient.** For QAOA, the correct gradient with respect to a shared $\gamma_\ell$ is a **sum of per-edge shifts**, not a single shift of the global $\gamma$. Getting this wrong silently produces an incorrect search direction regardless of which solver is used downstream.
- **Shot noise.** On hardware, $F_p$ is estimated from a finite number of shots $S$. The standard error of the estimate scales as $O(|E| / \sqrt S)$, which corrupts gradient estimates unless $S$ is large enough.

### 4.3 Barren plateaus

Gradient variance can decay exponentially with $n$ on highly expressive ansätze (McClean et al. 2018). MaxCut at low $p$ is mostly shielded by its 2-local structure, and at our scale ($n \le 12$, $p \le 3$) the variance drops only as $O(1/\mathrm{poly}(n))$ — gradient-based optimisation works fine. See [Theory/02 §5](Theory/02_QAOA_Theory_Part2_Circuits_and_Landscape.ipynb) for the full statement and numerical demonstration.

### 4.4 Warm start (Zhou et al. 2020)

A $p$-layer optimum is already a good region for $(p+1)$ layers — adding one small-$\gamma$-small-$\beta$ layer is close to the identity. The algorithm:

1. Optimise $p=1$ globally with random restarts.
2. For $k = 2, \ldots, p$: initialise $(\gamma^*_{p-1}, \gamma^*_{p-1}[-1]) \| (\beta^*_{p-1}, \beta^*_{p-1}[-1])$ plus small noise, then locally optimise.

Empirically this reduces variance dramatically at $p=3$ on the chord graph.

See [Implementation/README.md](Implementation/README.md) for the full Implementation chapter.

---

## Chapter 5 — Results

### 5.1 Three graph instances

| Graph | $n$ | $|E|$ | $C_{\max}$ | Structural role |
|---|---|---|---|---|
| $C_{10}$ (cycle) | 10 | 10 | 8 | Highly regular, analytically tractable |
| $C_{10}$ + 3 chords | 10 | 13 | 10 | Long-range edges disrupt local heuristics |
| 3-regular ($n = 10$) | 10 | 15 | 13 | Degree-uniform, classical benchmark family |

### 5.2 Performance comparison

QAOA is run at $p = 1, 2, 3$ against Random, Greedy, Greedy best-of-5, and GW-SDP. Results are reported as approximation ratios $F_p / C_{\max}$.

- **QAOA $p=1$:** beats Random and single-pass Greedy, **does not** beat Greedy best-of-5 or GW on any of the three instances.
- **QAOA $p=3$:** matches or slightly exceeds Greedy best-of-5 on the chord graph, but does **not** match GW on any instance.
- **Monotone improvement with depth:** $p = 1 \to 2 \to 3$ gains on every graph; the gain is largest on the chord graph where local heuristics fail.

### 5.3 Noise model and crossover

After each CX gate we apply the two-qubit **depolarizing channel** with probability $p_{cx}$:

$$\mathcal E(\rho) = (1 - p_{cx})\rho + \frac{p_{cx}}{15} \sum_{P \in \{I, X, Y, Z\}^{\otimes 2} \setminus \{I^{\otimes 2}\}} P \rho P^\dagger$$

A depth-$p$ circuit has $2p|E|$ CX gates, so noise accumulates linearly in $p$. Consequences seen in the sweep $p_{cx} \in [0, 0.025]$:

- Approximation ratio degrades monotonically with $p_{cx}$ for every $(p, \text{graph})$.
- Deeper circuits degrade faster. Above $p_{cx} \approx 1\%$, QAOA $p=1$ outperforms $p=3$ on all three graphs.
- The optimal depth on a real device is not determined by expressibility alone — it trades off the quality gain per layer against the extra gate error that layer introduces.

Current IBM devices sit near $p_{cx} \approx 0.3$–$0.5\%$, close to the crossover region.

See [Results/README.md](Results/README.md) for the full Results chapter.

---

## Conclusions

Pulling the seven notebooks together:

- **Setup.** MaxCut is the canonical simplest QUBO; by Barahona's theorem its QAOA analysis extends to every QUBO problem (portfolio, scheduling, facility location, networks). QAOA itself is a **classical–quantum hybrid** — the quantum processor evaluates the objective, the classical optimiser tunes the parameters.
- **Depth helps, but optimisation gets harder.** Approximation ratio rises monotonically with $p$ on every graph we tested (Notebook 06), yet each added layer doubles the parameter count and flattens the landscape (Notebook 04, Notebook 07 §6) — the limiting factor at moderate $p$ is *finding* a good $(\boldsymbol\gamma, \boldsymbol\beta)$, not the expressivity of the ansatz.
- **Classical optimiser choice is decisive.** L-BFGS-B with per-edge parameter-shift gradients dominates noiseless simulation; COBYLA (and SPSA on hardware) survive the shot noise and landscape flattening that ruin gradient estimates (Notebook 04). Warm start lets either optimiser skip the flat random-init region.
- **Even toy instances are structured but non-trivial.** $C_4$ (Notebook 03) and the $n = 10$ benchmark graphs (Notebook 06) already exhibit non-convex landscapes with multiple basins — small does not mean easy.
- **Noise is the binding constraint.** Two-qubit error $p_{cx} \sim 10^{-2}$ flattens the landscape and reverses the depth advantage well before $p = 3$ pays off (Notebook 07); above $p_{cx} \approx 1\%$, $p = 1$ already outperforms $p = 3$ on all three graphs. Practical scalability is gated by hardware fidelity, not by the algorithm.

> **One-line conclusion.** *QAOA is fundamentally limited not by expressivity, but by optimisation difficulty and noise sensitivity.*

We have not proved a quantum advantage, but we have not ruled it out either. The regime where it might appear is narrow: it requires graph structure that classical heuristics handle poorly, enough circuit depth to exploit non-local correlations, and hardware fidelity high enough to support that depth.

---

## Scope and limitations

All experiments use statevector simulation (noiseless) or Qiskit Aer with a simplified depolarizing model. Graphs are small ($n = 10$) and unweighted. The noise model does not capture coherent errors, crosstalk, or qubit-specific variation. Findings should be read as indicative of trends on small instances under idealised conditions, not as predictions for specific hardware or larger problem sizes.

---

## Dependencies

```
numpy scipy matplotlib networkx qiskit qiskit-aer cvxpy
```

```bash
pip install numpy scipy matplotlib networkx qiskit qiskit-aer cvxpy
```

---

## References

- Barahona, F. *On the computational complexity of Ising spin glass models.* J. Phys. A **15**, 3241, 1982.
- Bravyi et al. *Obstacles to variational quantum optimization from symmetry protection.* arXiv:2110.14206, 2021.
- Farhi, Goldstone, Gutmann. *A quantum approximate optimization algorithm.* arXiv:1411.4028, 2014.
- Goemans, Williamson. *Improved approximation algorithms for maximum cut and satisfiability problems using semidefinite programming.* JACM 42(6), 1995.
- Håstad, J. *Some optimal inapproximability results.* JACM 48(4), 2001.
- Karp, R. *Reducibility among combinatorial problems.* 1972.
- Khot et al. *Optimal inapproximability results for MAX-CUT and other 2-variable CSPs.* JACM 54(3), 2007.
- López de Prado, M. *Building diversified portfolios that outperform out of sample.* Journal of Portfolio Management 42(4), 2016.
- Lucas, A. *Ising formulations of many NP problems.* Front. Phys. 2, 2014.
- McClean et al. *Barren plateaus in quantum neural network training landscapes.* Nature Commun. 9, 2018.
- Wang et al. *Noise-induced barren plateaus in variational quantum algorithms.* Nature Commun. 12, 2021.
- Zhou et al. *Quantum approximate optimization algorithm: Performance, mechanism, and implementation on near-term devices.* Phys. Rev. X 10, 2020.
