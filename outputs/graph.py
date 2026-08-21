import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
import math
import re

GRAPH_PATH = "mexo_kg_uri.graphml"
OUT_DIR = Path("figures")
OUT_DIR.mkdir(exist_ok=True)

G = nx.read_graphml(GRAPH_PATH)

# -------------------------
# Helpers
# -------------------------
def clean_uri(x):
    x = str(x)
    x = x.split("/")[-1]
    x = x.split("#")[-1]
    return x

def infer_class(node):
    s = str(node).lower()

    if "experiment" in s and "performance" not in s:
        return "Experiment"
    if "performanceresult" in s or "performance-result" in s or "result" in s:
        return "PerformanceResult"
    if "algorithmconfiguration" in s or "configuration" in s or "ga-" in s or "pso-" in s or "de-" in s or "abc-" in s:
        return "AlgorithmConfiguration"
    if "algorithm" in s:
        return "Algorithm"
    if "probleminstance" in s or "instance" in s:
        return "ProblemInstance"
    if "problem" in s:
        return "Problem"
    if "benchmark" in s or "suite" in s:
        return "BenchmarkSuite"
    if "parameter" in s:
        return "Parameter"
    if "budget" in s:
        return "ComputationalBudget"
    if "stopping" in s or "maxfes" in s:
        return "StoppingCriterion"
    if "environment" in s:
        return "ExecutionEnvironment"
    if "study" in s or "karaboga" in s:
        return "Study"
    return "Other"

# -------------------------
# Build class interaction graph
# -------------------------
edge_weights = defaultdict(int)
class_counts = defaultdict(int)

for n in G.nodes():
    class_counts[infer_class(n)] += 1

for u, v in G.edges():
    cu = infer_class(u)
    cv = infer_class(v)

    if cu == "Other" or cv == "Other":
        continue

    if cu == cv:
        continue

    # undirected class-level interaction
    a, b = sorted([cu, cv])
    edge_weights[(a, b)] += 1

CG = nx.Graph()

for c, count in class_counts.items():
    if c != "Other":
        CG.add_node(c, count=count)

for (a, b), w in edge_weights.items():
    CG.add_edge(a, b, weight=w)

# Remove isolated nodes if any
isolates = list(nx.isolates(CG))
CG.remove_nodes_from(isolates)

# -------------------------
# Manual layout for clean paper figure
# -------------------------
pos = {
    "Study": (-2.2, 1.2),
    "BenchmarkSuite": (2.2, 1.2),
    "Problem": (2.2, 0.35),
    "ProblemInstance": (1.35, -0.45),
    "Experiment": (0.0, 0.0),
    "PerformanceResult": (0.0, -1.35),
    "AlgorithmConfiguration": (-1.35, -0.45),
    "Algorithm": (-2.2, 0.35),
    "Parameter": (-2.2, -1.25),
    "ComputationalBudget": (1.35, -1.55),
    "StoppingCriterion": (2.2, -1.25),
    "ExecutionEnvironment": (0.0, 1.25),
}

# Keep only positions that exist
pos = {n: pos[n] for n in CG.nodes() if n in pos}

# fallback layout if some node has no manual position
missing = [n for n in CG.nodes() if n not in pos]
if missing:
    auto_pos = nx.spring_layout(CG.subgraph(missing), seed=42)
    pos.update(auto_pos)

# -------------------------
# Styling
# -------------------------
node_sizes = [
    900 + 90 * math.sqrt(CG.nodes[n]["count"])
    for n in CG.nodes()
]

weights = [CG[u][v]["weight"] for u, v in CG.edges()]
max_w = max(weights) if weights else 1

edge_widths = [
    0.8 + 5.0 * (CG[u][v]["weight"] / max_w)
    for u, v in CG.edges()
]

edge_labels = {
    (u, v): CG[u][v]["weight"]
    for u, v in CG.edges()
    if CG[u][v]["weight"] >= 5
}

labels = {
    n: f"{n}\n(n={CG.nodes[n]['count']})"
    for n in CG.nodes()
}

plt.figure(figsize=(11, 7.5), dpi=400)

nx.draw_networkx_edges(
    CG,
    pos,
    width=edge_widths,
    edge_color="gray",
    alpha=0.45
)

nx.draw_networkx_nodes(
    CG,
    pos,
    node_size=node_sizes,
    node_color="white",
    edgecolors="black",
    linewidths=1.6
)

nx.draw_networkx_labels(
    CG,
    pos,
    labels=labels,
    font_size=9,
    font_weight="bold"
)

nx.draw_networkx_edge_labels(
    CG,
    pos,
    edge_labels=edge_labels,
    font_size=8,
    font_color="dimgray",
    rotate=False,
    bbox=dict(facecolor="white", edgecolor="none", alpha=0.75)
)

plt.title(
    "Ontology Class Interaction Graph of MEXO-KG",
    fontsize=15,
    fontweight="bold",
    pad=14
)

plt.axis("off")
plt.tight_layout()

plt.savefig(OUT_DIR / "mexo_kg_class_interaction_graph.png", dpi=400, bbox_inches="tight")
plt.savefig(OUT_DIR / "mexo_kg_class_interaction_graph.pdf", bbox_inches="tight")
plt.show()

print("Class graph nodes:", CG.number_of_nodes())
print("Class graph edges:", CG.number_of_edges())
print("\nClass counts:")
for n, data in sorted(CG.nodes(data=True), key=lambda x: x[0]):
    print(f"{n}: {data['count']}")

print("\nClass interactions:")
for u, v, data in sorted(CG.edges(data=True), key=lambda x: x[2]["weight"], reverse=True):
    print(f"{u} -- {v}: {data['weight']}")
