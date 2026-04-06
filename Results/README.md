# QAOA — Results Notebooks


This folder contains the two experimental notebooks that answer the project's central question: **for MaxCut on small unweighted graphs, when does shallow QAOA beat simple classical heuristics in solution quality, and how robust is that conclusion under depolarizing noise?**

Notebook 05 benchmarks QAOA against four classical algorithms on three graph instances with distinct structural properties; Notebook 06 stress-tests the $p=1,2,3$ circuits under a depolarizing noise model and identifies the error rate at which increasing circuit depth becomes counterproductive. Together they frame QAOA neither as universally superior nor universally inferior to classical methods, but as competitive in a specific regime that depends on graph structure, circuit depth, and hardware fidelity.

---

## Notebook Overview

| Notebook | Title | Role |
|---|---|---|
| `05_QAOA_Experiments.ipynb` | Experiments — QAOA vs Classical Baselines | Solution quality comparison across three graph families |
| `06_QAOA_Noise.ipynb` | Noise Analysis | Depolarizing noise sweep, crossover analysis, landscape flattening |

---

## 05 — QAOA vs Classical Baselines

### 1. Graph Instances

Three graphs are chosen to represent distinct structural regimes:

| Graph | $n$ | $|E|$ | $C_{\max}$ | Role |
|---|---|---|---|---|
| $C_{10}$ | 10 | 10 | 8 | Analytically tractable 2-regular cycle; Farhi et al. (2014) gives $p=1$ lower bound |
| $C_{10}$ + 3 chords | 10 | 13 | 10 | Disrupted local structure; tests locality limitations of shallow QAOA |
| 3-regular ($n=10$) | 10 | 15 | — | Degree-uniform graph studied directly in Farhi et al. (2014) |

The three instances together probe two known failure modes of shallow QAOA: sensitivity to long-range edges (chord graph) and performance on the degree-regular family where theoretical $p=1$ bounds are known.

### 2. Classical Baselines

Four classical algorithms are included, chosen to span a range of quality and cost:

**Random assignment** independently assigns each vertex to $S$ or $\bar{S}$ with probability $\frac{1}{2}$. The expected cut is $|E|/2$, giving approximation ratio exactly $0.5$ — a floor that any reasonable algorithm should clear.

**Single-pass greedy** processes vertices in a random order, assigning each to the side that maximises cuts with already-placed neighbours. Achieves ratio $\geq 0.5$ deterministically and runs in $O(|V| + |E|)$. A single greedy call costs orders of magnitude less than a single QAOA objective evaluation; this asymmetry is kept in view throughout the comparison.

**Best-of-5 greedy** repeats single-pass greedy with 5 independent random orderings and returns the best result. This is a stronger and still very cheap baseline — it frequently matches or exceeds QAOA $p=1$ on well-structured graphs.

**Goemans–Williamson (SDP)** solves the semidefinite relaxation and rounds via random hyperplane projection (200 rounds). Provides the approximation guarantee $\mathbb{E}[C_{\text{GW}}] \geq 0.8786 \cdot C_{\max}$, tight under the Unique Games Conjecture (Khot et al. 2007). GW is the correct upper reference for what polynomial-time classical algorithms can guarantee; any claim that QAOA "beats classical" must be measured against this, not against single-pass greedy.

### 3. QAOA Implementation

The statevector simulation uses the diagonal-phase oracle:

$$U_C(\gamma)|\psi\rangle = \sum_z e^{-i\gamma C(z)}|z\rangle\langle z|\psi\rangle$$

applied in $O(2^n)$ time by pointwise multiplication, and the separable mixer

$$U_B(\beta) = \bigotimes_{k=0}^{n-1} R_X(2\beta)_k$$

applied qubit-by-qubit in $O(n \cdot 2^n)$ time. Optimisation uses COBYLA with 20 random restarts; the best result over all restarts is reported. Exact MaxCut values are computed by brute-force enumeration ($2^n$ bitstrings, feasible for $n = 10$).

Results are reported as approximation ratios $F_p / C_{\max}$ to allow comparison across graphs with different optimal cut values.

### 4. Results and Discussion

**$C_{10}$ (cycle):**
QAOA achieves approximation ratios $0.750 \to 0.833 \to 0.875$ for $p = 1, 2, 3$ — monotonically increasing and consistent with the theoretical $p=1$ lower bound of $\geq 0.6924$ for 2-regular graphs (Farhi et al. 2014). At $p=3$, QAOA surpasses best-of-5 greedy. GW finds the exact optimum on this structured instance.

**$C_{10}$ + 3 chords:**
Adding long-range edges disrupts the local cycle structure. Single-pass greedy drops to $0.726$, reflecting the inability of a purely local heuristic to resolve non-local connectivity. QAOA $p=3$ achieves $0.872$, marginally above best-of-5 greedy ($0.864$) and approaching the GW bound. On this instance, QAOA $p=3$ outperforms best-of-5 greedy, though the margin is narrow and GW remains superior.

**3-regular ($n=10$):**
Results are consistent with the chord graph: QAOA $p=1$ is competitive with single-pass greedy but below best-of-5 greedy; $p=3$ approaches but does not reach GW.

**Overall pattern:**
QAOA $p=1$ reliably beats random assignment and single-pass greedy, but does not beat best-of-5 greedy or GW on any instance tested. QAOA $p=3$ matches or exceeds best-of-5 greedy on the chord graph — the instance where greedy is most disrupted by long-range structure — but at substantially higher cost. On the cycle, where graph structure is most regular and greedy is strong, the advantage of deeper QAOA is smaller. The Goemans–Williamson bound is not approached until $p=3$ and is not matched on any instance.

---

## 06 — Noise Analysis

### 1. Noise Model

Each CX gate is followed by the 2-qubit depolarizing channel with error probability $p_{cx}$:

$$\mathcal{E}(\rho) = (1 - p_{cx})\rho + \frac{p_{cx}}{15} \sum_{P \in \{I,X,Y,Z\}^{\otimes 2} \setminus \{I^{\otimes 2}\}} P\rho P^\dagger$$

Single-qubit gates are assumed noiseless. This is a simplified model; it does not capture coherent errors, crosstalk, or qubit-specific variation present on real hardware. The findings should be interpreted as indicative of trends rather than quantitative predictions for any specific device.

A QAOA circuit at depth $p$ contains $2p|E|$ CX gates. Noise therefore accumulates multiplicatively with both depth and graph size — a deeper circuit gains expressibility at the cost of more error, and the trade-off depends directly on $p_{cx}$.

### 2. Experimental Protocol

The noise sweep evaluates QAOA performance at $p_{cx} \in \{0, 0.002, 0.004, \ldots, 0.025\}$ for $p \in \{1, 2, 3\}$ on all three graphs from Notebook 05. Critically, **noiseless optimal parameters from Notebook 05 are held fixed** throughout the sweep. This isolates the effect of noise on circuit fidelity from the confounding effect of re-optimisation under noise — a design choice that measures how well the noiseless solution transfers to a noisy device, not how well one could optimise directly on hardware.

Circuits are simulated using Qiskit Aer with a depolarizing noise model; results are averaged over 4096 shots per data point.

### 3. Ratio Degradation

Approximation ratio degrades monotonically with $p_{cx}$ for all depths and graphs. The rate of degradation scales with circuit depth: $p=3$ has $3\times$ more CX gates than $p=1$ and therefore accumulates $3\times$ more depolarizing error per layer, leading to faster ratio decay at higher $p_{cx}$.

At low error rates ($p_{cx} \lesssim 0.002$), $p=3$ retains its noiseless advantage over $p=1$ and $p=2$. As $p_{cx}$ increases, this advantage shrinks and eventually reverses.

### 4. Crossover Analysis

The **crossover point** $p_{cx}^*$ is the error rate at which a shallower circuit first outperforms a deeper one. Under the depolarizing model used here, $p=2$ and $p=3$ remain competitive at low error rates, while $p=1$ becomes the preferred depth above approximately $p_{cx} \approx 1\%$.

This has a direct practical implication: the optimal QAOA depth on near-term hardware is not determined by expressibility alone. It is determined by the interplay between the marginal quality gain from an additional layer and the additional noise that layer introduces. For current NISQ devices with CX fidelities in the range $99\text{–}99.5\%$ ($p_{cx} \approx 0.5\text{–}1\%$), these results suggest that $p=2$ or $p=3$ are near the boundary of being beneficial.

### 5. Landscape Flattening

Noise reduces the variance of the energy landscape $F_1(\gamma, \beta)$ across the parameter domain $[0, \pi/2]^2$. The landscape standard deviation

$$\Delta = \mathrm{std}_{(\gamma,\beta) \in [0,\pi/2]^2}\bigl[F_1^{\text{noisy}}(\gamma, \beta)\bigr]$$

decreases with $p_{cx}$: at $p_{cx} = 0$ the landscape has a well-defined peak, while at $p_{cx} = 0.02$ the landscape is nearly flat. This has two consequences. First, the noiseless optimal parameters become increasingly suboptimal as noise grows — the landscape maximum shifts and shrinks. Second, any attempt to re-optimise parameters on hardware faces a flattening objective, which compounds the barren plateau problem identified in Notebook 04. Noise and barren plateaus act in the same direction: both reduce the gradient signal available to the optimiser.

---

## Key Findings

**1. QAOA $p=1$ beats single-pass greedy but not best-of-5 greedy or GW on any instance tested.** The classical comparison baseline matters: characterising QAOA performance relative to single-pass greedy overstates its advantage, since best-of-5 greedy is almost always stronger and far cheaper.

**2. QAOA gains the most over greedy where greedy is weakest.** On the chord graph, where long-range edges disrupt local heuristics, QAOA $p=3$ outperforms best-of-5 greedy. On the cycle, where greedy is stronger, the advantage is smaller. This is consistent with QAOA's locality limitations: shallow QAOA is most useful when the problem has non-local structure that depth-limited classical algorithms cannot exploit.

**3. Deeper circuits are not unconditionally better under noise.** Under depolarizing noise with $p_{cx} \gtrsim 1\%$, $p=1$ outperforms $p=3$ on all three graphs. The optimal depth is hardware-dependent and must be chosen with CX fidelity in mind.

**4. Noise and barren plateaus compound.** Landscape flattening under depolarizing noise reduces the gradient signal in the same direction as the barren plateau effect, making parameter optimisation progressively harder as either circuit depth or error rate increases.

---

## Dependencies

```
numpy, scipy, matplotlib, networkx, qiskit, qiskit-aer, cvxpy
```

---

## References

- Farhi, Goldstone, Gutmann. *A quantum approximate optimization algorithm.* arXiv:1411.4028, 2014.
- Goemans, Williamson. *Improved approximation algorithms for maximum cut and satisfiability problems using semidefinite programming.* JACM 42(6), 1995.
- Khot et al. *Optimal inapproximability results for MAX-CUT and other 2-variable CSPs.* JACM 54(3), 2007.
- Bravyi et al. *Obstacles to variational quantum optimization from symmetry protection.* arXiv:2110.14206, 2021.
- Wang et al. *Noise-induced barren plateaus in variational quantum algorithms.* Nature Commun. 12, 2021.
- Cerezo et al. *Variational quantum algorithms.* Nature Reviews Physics 3, 2021.
