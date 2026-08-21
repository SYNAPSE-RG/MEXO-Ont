from __future__ import annotations

from typing import Iterable

import networkx as nx
from pyvis.network import Network


def _short(text: str, max_len: int = 42) -> str:
    text = str(text)
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def build_interactive_network_html(
    nxg: nx.MultiDiGraph,
    max_nodes: int = 180,
    min_degree: int = 1,
    height: str = "720px",
    width: str = "100%",
    physics: bool = True,
) -> str:
    """
    Build an interactive HTML network visualization from the MEXO-KG NetworkX graph.

    The visualization intentionally limits the displayed subgraph because complete RDF
    graphs can become visually unreadable. Nodes are selected by degree centrality.
    """
    if nxg.number_of_nodes() == 0:
        return "<p>No graph data available.</p>"

    degree = dict(nxg.degree())
    selected = [n for n, d in sorted(degree.items(), key=lambda item: item[1], reverse=True) if d >= min_degree]
    selected = selected[:max_nodes]

    if not selected:
        selected = [n for n, _ in sorted(degree.items(), key=lambda item: item[1], reverse=True)[:max_nodes]]

    sub = nxg.subgraph(selected).copy()

    net = Network(height=height, width=width, directed=True, notebook=False, cdn_resources="in_line")
    net.barnes_hut(
        gravity=-22000,
        central_gravity=0.22,
        spring_length=130,
        spring_strength=0.045,
        damping=0.72,
        overlap=0.15,
    )
    net.toggle_physics(physics)

    for node, data in sub.nodes(data=True):
        label = data.get("label") or str(node).rstrip("/").split("/")[-1]
        rdf_types = data.get("rdf_types", "")
        kind = data.get("kind", "uri")
        title = (
            f"<b>{label}</b><br>"
            f"Kind: {kind}<br>"
            f"Types: {rdf_types or '-'}<br>"
            f"Degree: {degree.get(node, 0)}<br>"
            f"URI: {node}"
        )
        group = rdf_types.split(";")[0] if rdf_types else kind
        size = min(55, 12 + degree.get(node, 0) * 1.4)
        net.add_node(str(node), label=_short(label), title=title, group=group, size=size)

    # Collapse duplicated edges visually to avoid unreadable parallel edge clouds.
    collapsed_edges: dict[tuple[str, str, str], int] = {}
    for u, v, data in sub.edges(data=True):
        pred = data.get("predicate_label", "relatedTo")
        key = (str(u), str(v), pred)
        collapsed_edges[key] = collapsed_edges.get(key, 0) + 1

    for (u, v, pred), weight in collapsed_edges.items():
        title = f"{pred}" + (f" × {weight}" if weight > 1 else "")
        net.add_edge(u, v, label=_short(pred, 24), title=title, value=max(1, weight))

    net.set_options(
        """
        const options = {
          "nodes": {
            "borderWidth": 1,
            "font": {"size": 18, "face": "Arial"},
            "shape": "dot"
          },
          "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.55}},
            "font": {"size": 11, "align": "middle"},
            "smooth": {"type": "dynamic"}
          },
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true,
            "tooltipDelay": 120
          },
          "physics": {
            "stabilization": {"enabled": true, "iterations": 250}
          }
        }
        """
    )
    return net.generate_html(notebook=False)
