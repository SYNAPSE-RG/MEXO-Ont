from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import networkx as nx
import pandas as pd
from rdflib import Graph, URIRef, Literal, RDF, RDFS


def _safe_attr(value: Any) -> str:
    """GraphML/GEXF-friendly string attribute."""
    if value is None:
        return ""
    text = str(value)
    return text.replace("\n", " ").replace("\r", " ").strip()


def _local_name(uri: Any) -> str:
    text = str(uri)
    if "#" in text:
        return text.rsplit("#", 1)[-1]
    return text.rstrip("/").rsplit("/", 1)[-1]


def _uri_label(g: Graph, node: URIRef) -> str:
    for label in g.objects(node, RDFS.label):
        return _safe_attr(label)
    return _local_name(node)


def _type_labels(g: Graph, node: URIRef) -> str:
    labels = []
    for cls in g.objects(node, RDF.type):
        labels.append(_local_name(cls))
    return ";".join(sorted(set(labels)))


def rdf_to_networkx(g: Graph, include_literals: bool = False) -> nx.MultiDiGraph:
    """
    Convert an RDF graph into a NetworkX MultiDiGraph.

    Parameters
    ----------
    g:
        rdflib Graph.
    include_literals:
        If False, only URIRef-to-URIRef triples are exported as edges. This is usually
        best for ontology/KG structural analysis. If True, literal objects are also
        represented as terminal nodes.
    """
    nxg = nx.MultiDiGraph()
    literal_index: Dict[Tuple[str, str | None], str] = {}

    def add_uri_node(u: URIRef):
        uid = str(u)
        if uid not in nxg:
            nxg.add_node(
                uid,
                uri=uid,
                label=_uri_label(g, u),
                kind="uri",
                rdf_types=_type_labels(g, u),
            )

    for s, p, o in g:
        if not isinstance(s, URIRef):
            continue
        add_uri_node(s)
        pred_uri = str(p)
        pred_label = _local_name(p)

        if isinstance(o, URIRef):
            add_uri_node(o)
            nxg.add_edge(str(s), str(o), predicate=pred_uri, predicate_label=pred_label)
        elif include_literals and isinstance(o, Literal):
            key = (_safe_attr(o), str(o.datatype) if o.datatype else None)
            if key not in literal_index:
                literal_index[key] = f"literal:{len(literal_index) + 1}"
            oid = literal_index[key]
            if oid not in nxg:
                nxg.add_node(
                    oid,
                    uri="",
                    label=_safe_attr(o),
                    kind="literal",
                    rdf_types="Literal",
                    datatype=str(o.datatype) if o.datatype else "",
                    language=str(o.language) if o.language else "",
                )
            nxg.add_edge(str(s), oid, predicate=pred_uri, predicate_label=pred_label)
    return nxg


def collapsed_digraph(nxg: nx.MultiDiGraph) -> nx.DiGraph:
    """Collapse a MultiDiGraph into a simple DiGraph for centrality measures."""
    dg = nx.DiGraph()
    for n, data in nxg.nodes(data=True):
        dg.add_node(n, **data)
    for u, v, data in nxg.edges(data=True):
        if dg.has_edge(u, v):
            dg[u][v]["weight"] += 1
            labels = set(dg[u][v].get("predicate_labels", "").split(";"))
            labels.add(data.get("predicate_label", ""))
            dg[u][v]["predicate_labels"] = ";".join(sorted(x for x in labels if x))
        else:
            dg.add_edge(u, v, weight=1, predicate_labels=data.get("predicate_label", ""))
    return dg


def graph_analytics(nxg: nx.MultiDiGraph, top_n: int = 20) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Compute graph-level metrics and node centrality summaries."""
    dg = collapsed_digraph(nxg)
    ug = dg.to_undirected()

    if dg.number_of_nodes() == 0:
        metrics = {"nodes": 0, "edges": 0}
        return metrics, pd.DataFrame(), pd.DataFrame()

    degree = dict(dg.degree())
    in_degree = dict(dg.in_degree())
    out_degree = dict(dg.out_degree())
    degree_centrality = nx.degree_centrality(dg)
    betweenness = nx.betweenness_centrality(dg, normalized=True) if dg.number_of_nodes() <= 5000 else {}
    closeness = nx.closeness_centrality(dg) if dg.number_of_nodes() <= 5000 else {}

    try:
        pagerank = nx.pagerank(dg, weight="weight")
    except Exception:
        pagerank = {}

    rows = []
    for n, data in dg.nodes(data=True):
        rows.append({
            "node": n,
            "label": data.get("label", _local_name(n)),
            "kind": data.get("kind", ""),
            "rdf_types": data.get("rdf_types", ""),
            "degree": degree.get(n, 0),
            "in_degree": in_degree.get(n, 0),
            "out_degree": out_degree.get(n, 0),
            "degree_centrality": degree_centrality.get(n, 0.0),
            "betweenness_centrality": betweenness.get(n, 0.0),
            "closeness_centrality": closeness.get(n, 0.0),
            "pagerank": pagerank.get(n, 0.0),
        })
    node_metrics = pd.DataFrame(rows).sort_values(["degree", "pagerank"], ascending=False)

    edge_rows = []
    for u, v, data in dg.edges(data=True):
        edge_rows.append({
            "source": u,
            "source_label": dg.nodes[u].get("label", _local_name(u)),
            "target": v,
            "target_label": dg.nodes[v].get("label", _local_name(v)),
            "weight": data.get("weight", 1),
            "predicate_labels": data.get("predicate_labels", ""),
        })
    edge_table = pd.DataFrame(edge_rows).sort_values("weight", ascending=False) if edge_rows else pd.DataFrame()

    weak_components = list(nx.weakly_connected_components(dg)) if dg.number_of_nodes() else []
    largest_weak = max((len(c) for c in weak_components), default=0)
    metrics = {
        "nodes": dg.number_of_nodes(),
        "edges": dg.number_of_edges(),
        "multi_edges": nxg.number_of_edges(),
        "density_directed": nx.density(dg),
        "weak_components": len(weak_components),
        "largest_weak_component_nodes": largest_weak,
        "average_degree": sum(degree.values()) / dg.number_of_nodes(),
        "uri_nodes": sum(1 for _, d in dg.nodes(data=True) if d.get("kind") == "uri"),
        "literal_nodes": sum(1 for _, d in dg.nodes(data=True) if d.get("kind") == "literal"),
    }
    return metrics, node_metrics.head(top_n), edge_table.head(top_n)


def export_network_files(g: Graph, output_dir: str | Path, include_literals: bool = False, prefix: str = "mexo_kg") -> dict[str, str]:
    """Export RDF graph into network-analysis formats."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = "full" if include_literals else "uri"
    stem = f"{prefix}_{suffix}"

    nxg = rdf_to_networkx(g, include_literals=include_literals)
    metrics, top_nodes, top_edges = graph_analytics(nxg)

    paths = {
        "graphml": output_dir / f"{stem}.graphml",
        "gexf": output_dir / f"{stem}.gexf",
        "node_link_json": output_dir / f"{stem}_node_link.json",
        "network_metrics_json": output_dir / f"{stem}_network_metrics.json",
        "top_nodes_csv": output_dir / f"{stem}_top_nodes.csv",
        "top_edges_csv": output_dir / f"{stem}_top_edges.csv",
    }

    nx.write_graphml(nxg, paths["graphml"])
    nx.write_gexf(nxg, paths["gexf"])
    with paths["node_link_json"].open("w", encoding="utf-8") as f:
        json.dump(nx.node_link_data(nxg, edges="links"), f, indent=2)
    paths["network_metrics_json"].write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    top_nodes.to_csv(paths["top_nodes_csv"], index=False)
    top_edges.to_csv(paths["top_edges_csv"], index=False)

    return {k: str(v) for k, v in paths.items()}
