# QAOA — Preparation Notebooks


This folder contains two notebooks that sit between the theory foundations (Parts I–II) and the full experimental comparisons (Parts IV–V). Together they answer a single question in two stages: **does the circuit do what the theory says it does, and given that it does, how should its parameters be optimised?**

Notebook 03 answers the first half on the smallest non-trivial instance ($C_4$): it derives the gate decomposition from first principles, traces the statevector step-by-step, and establishes the $p=1$ optimal parameters that will serve as a reference point throughout. Notebook 04 takes up where 03 leaves off — once the circuit is verified, the question becomes how to find good parameters reliably on larger graphs where the $p=1$ landscape intuition no longer transfers cleanly. The central finding from 04 is that **gradient correctness (per-edge parameter-shift formulation) is a more fundamental bottleneck than optimizer choice**: an incorrect gradient formula produces a wrong search direction regardless of which solver is used, while the choice among correct-gradient solvers is largely a matter of noise regime and budget.

---

## Notebook Overview

| Notebook | Title | Role |
|---|---|---|
| `03_QAOA_C4_Complete_Analysis.ipynb` | C4 Complete Analysis — Gate-by-Gate Derivation | Circuit verification, statevector tracking, resource scaling |
| `04_QAOA_Optimizer_Comparison.ipynb` | Optimization — Landscape, Barren Plateaus, and Optimizer Comparison | Gradient correctness, solver benchmarking, warm-start strategy |

---

## 03 — C4 Complete Analysis

### 1. C4 as a Controlled Testbed

The 4-cycle $C_4 = (\{0,1,2,3\},\, \{(0,1),(1,2),(2,3),(3,0)\})$ is bipartite (partition $\{0,2\}$ vs $\{1,3\}$), so every edge crosses the cut and $C_{\max} = |E| = 4$. The two optimal bitstrings are $|0101\rangle$ and $|1010\rangle$. Because $C_4$ is small enough for exact statevector simulation but non-trivial enough to exhibit the full QAOA structure, it serves as the primary verification instance throughout the project.

The cost Hamiltonian is:

$$H_C = \frac{I - Z_0Z_1}{2} + \frac{I - Z_1Z_2}{2} + \frac{I - Z_2Z_3}{2} + \frac{I - Z_3Z_0}{2}$$

$H_C$ is diagonal in the computational basis; the $(z,z)$ entry equals $C(z)$.

### 2. Gate Decomposition: CNOT–$R_Z$–CNOT

Each edge term in $U_C(\gamma) = e^{-i\gamma H_C}$ requires implementing $e^{i(\gamma/2) Z_iZ_j}$. The identity used is:

$$e^{i\frac{\gamma}{2} Z_iZ_j} = \mathrm{CNOT}_{i \to j} \cdot (I \otimes R_Z(-\gamma))_j \cdot \mathrm{CNOT}_{i \to j}$$

The derivation follows from the conjugation rule $\mathrm{CNOT}(I \otimes Z)\mathrm{CNOT} = Z \otimes Z$: sandwiching an $R_Z$ on the target qubit between two CNOTs promotes it to a two-qubit $ZZ$-rotation. For edge $(0,1)$ the action on each basis state is explicit:

$$|00\rangle \to e^{+i\gamma/2}|00\rangle, \quad |01\rangle \to e^{-i\gamma/2}|01\rangle, \quad |10\rangle \to e^{-i\gamma/2}|10\rangle, \quad |11\rangle \to e^{+i\gamma/2}|11\rangle$$

This is verified numerically by comparing the circuit product against `scipy.linalg.expm(i·γ/2·Z⊗Z)`, with agreement to $< 10^{-14}$.

### 3. Statevector Tracking at $p = 1$

The $p=1$ evolution is traced step by step.

**Step 0** — Initialisation via Hadamard: $|\psi_0\rangle = |+\rangle^{\otimes 4} = \frac{1}{4}\sum_{z \in \{0,1\}^4} |z\rangle$.

**Step 1** — Cost unitary: each basis state acquires a phase proportional to its cut value,
$$U_C(\gamma)|\psi_0\rangle = \frac{1}{4}\sum_z e^{-i\gamma C(z)}|z\rangle$$
This is phase separation; it does not change any probability $|\langle z|\psi\rangle|^2$ on its own.

**Step 2** — Mixer unitary: $U_B(\beta) = \bigotimes_{k=0}^{3} R_X(2\beta)_k$ rotates each qubit's Bloch sphere, coupling amplitudes across Hamming-1 neighbours. The redistribution of probability mass toward high-cut bitstrings results from the interference between Steps 1 and 2.

### 4. Optimal Parameters at $p = 1$

For $C_4$ the $p=1$ landscape $F_1(\gamma,\beta)$ can be computed analytically. The numerical optimum is at $\gamma^* = \pi/4$, $\beta^* = \pi/8$.

The intuition for $\gamma^* = \pi/4$: max-cut states ($C = 4$) acquire phase $e^{-i\pi} = -1$ while zero-cut states ($C = 0$) stay at $+1$. This maximises the phase contrast between the two extremes before the mixer acts. The intuition for $\beta^* = \pi/8$: the mixer angle $R_X(\pi/4)$ is the sweet spot between under-rotation (no amplitude transfer) and over-rotation (mixing away from the desired basin).

At these parameters the two max-cut bitstrings together receive the majority of the total probability.

### 5. Scaling to $p = 2, 3$

For $p > 1$ the landscape is a non-convex multivariate trigonometric polynomial in $2p$ parameters. The notebook optimises with multi-start COBYLA (20 random initialisations per depth) and reports $F_p$ and the corresponding probability distributions.

### 6. Resource Analysis

For $C_4$ ($|E| = 4$, $n = 4$), the gate counts per depth $p$ are:

| $p$ | Parameters | CX gates | $R_Z$ gates | $R_X$ gates |
|-----|-----------|----------|-------------|-------------|
| 1   | 2         | 8        | 4           | 4           |
| 2   | 4         | 16       | 8           | 8           |
| 3   | 6         | 24       | 12          | 12          |

The general formula is CX count $= 2p|E|$, which is $8p$ for $C_4$. In serial execution, circuit depth scales as $O(p|E|)$. Since $C_4$ has chromatic index 2 (two edge colours suffice to partition all edges into independent sets), all 4 edges can be executed in 2 parallel groups per layer, reducing circuit depth to $O(2p)$.

The $C_4$ analysis establishes what QAOA does correctly on a tractable instance. What it does not establish is how to find good parameters when the landscape is no longer well-behaved enough for any random initialisation to succeed. On $C_4$ at $p=1$, COBYLA converges reliably from any starting point; this breaks down already at $C_{10}$, $p=2$. Notebook 04 diagnoses why and prescribes fixes.

---

## 04 — Optimizer Comparison

### 1. Landscape Geometry

The QAOA objective $F_p : \mathbb{R}^{2p} \to \mathbb{R}$ is a multivariate trigonometric polynomial whose structure is inherited from the circuit. Key properties:

- **Periodicity:** $e^{i\gamma Z_iZ_j/2}$ is $2\pi$-periodic in $\gamma$; by symmetry it suffices to search $\gamma_k \in [0, \pi]$, $\beta_k \in [0, \pi/2]$.
- **Non-convexity:** Multiple local optima exist for $p \geq 2$; their number grows with $p$.
- **Shot noise:** On hardware, $F_p$ is estimated from $S$ shots; the resulting noise $O(1/\sqrt{S})$ corrupts gradient estimates and destabilises gradient-based methods unless step sizes are carefully tuned.

### 2. Barren Plateaus

A **barren plateau** is a parameter region where the gradient is exponentially small in system size. For a $k$-local cost function evaluated on a sufficiently expressive ansatz (McClean et al. 2018):

$$\mathbb{E}_{\boldsymbol{\theta}}\!\left[\frac{\partial F_p}{\partial \theta_k}\right] = 0, \qquad \mathrm{Var}\!\left[\frac{\partial F_p}{\partial \theta_k}\right] \leq \frac{C}{b^n}, \quad b \geq 2$$

The notebook demonstrates this numerically: gradient variance (normalised by $|E|$ to remove trivial graph-size scaling) is measured at 300 random initialisations for $n \in \{4, 6, 8, 10, 12\}$ at $p=1$. The variance decreases with $n$, consistent with the theoretical bound.

Gradient-free optimisers are not immune. In flat regions, COBYLA's linear model becomes degenerate when function values at simplex vertices differ by less than floating-point resolution; Nelder-Mead's simplex collapses when all vertices have similar values; SPSA's step sizes must be calibrated to the gradient scale or the signal is buried in perturbation noise.

QAOA at low depth on a 2-local cost function is partially shielded from the worst barren plateau behaviour — the locality of $H_C$ prevents rapid convergence to a Haar-random distribution — but the variance nonetheless decreases with system size and gradient-based optimisation becomes progressively harder.

### 3. Parameter-Shift Rule: Correct Per-Gate Formulation

For any gate $e^{-i\theta G}$ where $G$ has eigenvalues $\pm r$, the expectation value $F(\theta)$ is exactly sinusoidal and the gradient is:

$$\frac{\partial F}{\partial \theta} = r\!\left[F\!\left(\theta + \frac{\pi}{4r}\right) - F\!\left(\theta - \frac{\pi}{4r}\right)\right]$$

This is an **exact** identity, not a finite-difference approximation, and requires no step-size tuning.

For QAOA the two gate families have distinct generators and hence distinct shift angles:

**Mixer gates** $R_X(2\beta)_k = e^{-i\beta X_k}$: generator $X_k$, eigenvalues $\pm 1$, shift $= \pi/2$ in $\beta$.

**Cost gates** $e^{i(\gamma/2)Z_iZ_j}$: each edge contributes an independent gate. The correct gradient with respect to a shared global $\gamma$ is obtained by summing per-edge shifts:

$$\frac{\partial F_p}{\partial \gamma_\ell} = \frac{1}{2} \sum_{(i,j) \in E} \left[F_p(\ldots,\, \gamma_\ell^{(ij)} + \tfrac{\pi}{2},\, \ldots) - F_p(\ldots,\, \gamma_\ell^{(ij)} - \tfrac{\pi}{2},\, \ldots)\right]$$

where $\gamma_\ell^{(ij)}$ denotes shifting only the parameter of the gate associated with edge $(i,j)$ in layer $\ell$.

A common error is to shift the global $\gamma$ by $\pi/2$ simultaneously across all edges. The notebook verifies numerically that this gives an incorrect gradient and that the per-edge formulation matches finite differences to high precision.

### 4. Optimizer Catalogue

| Optimizer | Gradient required | Recommended setting | Known failure mode |
|---|---|---|---|
| **COBYLA** | No | Noiseless / low-noise sim, $p \leq 5$ | Stagnates when landscape is flat at large $n$ |
| **Nelder-Mead** | No | Fallback when COBYLA stagnates | Slow; simplex collapses in flat regions |
| **L-BFGS-B** | Yes (param-shift) | Noiseless statevector sim | Unreliable on shot-noisy hardware |
| **SPSA** | No (2 circuits/step) | Real hardware, large $p$ | Requires hand-tuning of $a_k$, $c_k$ to gradient scale |

### 5. Convergence Comparison on $C_{10}$, $p=2$

All four optimisers are benchmarked on the 10-cycle $C_{10}$ at $p=2$ with 30 random initialisations each. Results are reported as approximation ratios relative to $C_{\max} = 10$, with the Goemans–Williamson bound $\alpha_{\text{GW}} \approx 0.8786$ shown as the classical reference.

The comparison illustrates that on a moderately sized, noiseless statevector simulation, COBYLA and L-BFGS-B are competitive in solution quality while SPSA shows higher variance due to stochastic perturbations. The critical difference between $C_4$ and $C_{10}$ is visible in convergence curves: $C_4$ converges reliably from any random initialisation, while $C_{10}$ already shows meaningful spread, motivating the warm-start strategy below.

### 6. Warm-Start: Layer-by-Layer Initialisation

The layer-by-layer strategy (Zhou et al. 2020) reduces sensitivity to random initialisation:

1. Optimise $p=1$ with multiple random starts (2 parameters — cheap).
2. Initialise $p=2$ parameters as $(\gamma_1^*, \gamma_1^*,\, \beta_1^*, \beta_1^*)$ with small Gaussian noise.
3. Optimise $p=2$. Repeat inductively for $p=3, 4, \ldots$

The mechanism: the $p=2$ landscape restricted to the subspace $\gamma_1 = \gamma_2$, $\beta_1 = \beta_2$ is exactly the $p=1$ landscape, so the $p=1$ optimum is a feasible starting point with non-negligible gradients. This is demonstrated on $C_{10}$ augmented with 3 chords ($|E| = 13$, $C_{\max} = 13$, $p=3$), where warm-start consistently outperforms random initialisation in both median ratio and variance. No general theoretical guarantee for warm-start exists; the empirical benefit is graph- and depth-dependent.

### 7. Practical Guidelines

| Setting | Optimizer | Initialisation |
|---|---|---|
| Statevector simulation (noiseless) | L-BFGS-B + per-edge param-shift | Warm-start |
| Shot-based simulation ($S \geq 500$) | COBYLA | Warm-start |
| Real hardware | SPSA (calibrated $a_k$, $c_k$) | Warm-start |
| Large $p$ (barren plateau regime) | SPSA + layer-by-layer | Inductively from $p=1$ |

---

## Key Findings

These two notebooks collectively establish three claims that carry forward into the experiment notebooks:

**1. The CNOT–$R_Z$–CNOT decomposition is exact.** The circuit product matches `expm(i·γ/2·Z⊗Z)` to $< 10^{-14}$, and the explicit basis-state action confirms that $U_C(\gamma)$ performs phase separation — not amplitude reshaping — on its own.

**2. Per-edge parameter-shift correctness is a prerequisite, not an optimisation detail.** Shifting the global $\gamma$ by $\pi/2$ simultaneously across all edges produces a gradient that is numerically wrong (verified against finite differences on $C_4$). This error propagates independently of which optimiser is used downstream. Fixing the gradient formula is therefore more fundamental than any solver choice.

**3. Warm-start dominates random initialisation for $p \geq 2$ on non-trivial graphs.** On $C_{10}$ augmented with 3 chords at $p=3$, warm-start consistently achieves higher median approximation ratio and lower variance than random initialisation. The mechanism is structural: the $p=1$ optimum is a feasible starting point for $p=2$ with non-negligible gradients. This benefit is empirical and graph-dependent; no general guarantee exists.

---

## Dependencies

```
numpy, scipy, matplotlib, networkx, qiskit, qiskit-aer
```

---

## References

- Farhi, Goldstone, Gutmann. *A quantum approximate optimization algorithm.* arXiv:1411.4028, 2014.
- McClean et al. *Barren plateaus in quantum neural network training landscapes.* Nature Commun. 9, 2018.
- Cerezo et al. *Cost function dependent barren plateaus in shallow parametrized quantum circuits.* Nature Commun. 12, 2021.
- Zhou et al. *Quantum approximate optimization algorithm: Performance, mechanism, and implementation on near-term devices.* Phys. Rev. X 10, 2020.
- Bravyi et al. *Obstacles to variational quantum optimization from symmetry protection.* arXiv:2110.14206, 2021.
