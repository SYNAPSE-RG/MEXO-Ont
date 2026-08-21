from __future__ import annotations

import argparse
import json
from pathlib import Path

from mexo_kg.builder import build_graph, graph_metrics, export_graph_json
from mexo_kg.graph_exports import export_network_files
from mexo_kg.queries import run_all_queries


def main():
    parser = argparse.ArgumentParser(
        description="Build MEXO-KG from Excel and export RDF, SPARQL outputs, JSON, GraphML, GEXF and network metrics."
    )
    parser.add_argument("--excel", default="data/MEXO_Optimization.xlsx")
    parser.add_argument("--out", default="outputs")
    parser.add_argument(
        "--graph-mode",
        choices=["uri", "full", "both"],
        default="both",
        help="uri = only URI resource graph; full = include literal values as nodes; both = export both variants.",
    )
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    g = build_graph(args.excel)

    ttl_path = out / "mexo_kg.ttl"
    nt_path = out / "mexo_kg.nt"
    g.serialize(destination=ttl_path, format="turtle")
    g.serialize(destination=nt_path, format="nt")

    metrics = graph_metrics(g)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    export_graph_json(g, out / "graph.json")

    query_summary = run_all_queries(g, out / "query_results")
    (out / "query_summary.json").write_text(json.dumps(query_summary, indent=2), encoding="utf-8")

    network_exports = {}
    if args.graph_mode in ["uri", "both"]:
        network_exports["uri"] = export_network_files(g, out, include_literals=False, prefix="mexo_kg")
    if args.graph_mode in ["full", "both"]:
        network_exports["full"] = export_network_files(g, out, include_literals=True, prefix="mexo_kg")
    (out / "network_exports.json").write_text(json.dumps(network_exports, indent=2), encoding="utf-8")

    print(f"Wrote RDF: {ttl_path}")
    print(f"Wrote GraphML/GEXF exports to: {out}")
    print(json.dumps({"rdf_metrics": metrics, "network_exports": network_exports}, indent=2))


if __name__ == "__main__":
    main()
