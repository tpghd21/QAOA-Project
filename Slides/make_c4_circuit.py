"""Generate a clean C_4 QAOA circuit diagram for the slides."""
import os
import matplotlib
matplotlib.use("Agg")
from qiskit import QuantumCircuit

OUT = "figs_from_pdf"
os.makedirs(OUT, exist_ok=True)

n = 4
edges = [(0, 1), (1, 2), (2, 3), (0, 3)]
gamma, beta = 0.79, 0.39  # representative optimum for C_4 at p=1

qc = QuantumCircuit(n)

# Initial superposition
qc.h(range(n))
qc.barrier()

# U_C(gamma): per-edge CX - RZ(-gamma) - CX
for i, j in edges:
    qc.cx(i, j)
    qc.rz(-gamma, j)
    qc.cx(i, j)
qc.barrier()

# U_B(beta): RX(2*beta) on every qubit
for q in range(n):
    qc.rx(2 * beta, q)

# Render using matplotlib backend
fig = qc.draw(output="mpl", fold=-1, style="iqp")
fig.savefig(f"{OUT}/c4_qaoa_circuit.png", dpi=200, bbox_inches="tight")
print(f"saved {OUT}/c4_qaoa_circuit.png  ({qc.num_qubits} qubits, depth {qc.depth()})")
