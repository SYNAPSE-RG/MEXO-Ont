from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, Query
from mexo_kg.builder import build_graph, graph_metrics
from mexo_kg.graph_exports import rdf_to_networkx, graph_analytics
from mexo_kg.queries import QUERIES, query_to_dataframe

app = FastAPI(title="MEXO-KG API", version="0.2.0")
GRAPH = None

@app.on_event("startup")
def startup():
    global GRAPH
    path = Path("data/MEXO_Optimization.xlsx")
    GRAPH = build_graph(path)

@app.get("/metrics")
def metrics():
    return graph_metrics(GRAPH)

@app.get("/network-metrics")
def network_metrics(include_literals: bool = False):
    nxg = rdf_to_networkx(GRAPH, include_literals=include_literals)
    metrics, top_nodes, top_edges = graph_analytics(nxg)
    return {
        "metrics": metrics,
        "top_nodes": top_nodes.to_dict(orient="records"),
        "top_edges": top_edges.to_dict(orient="records"),
    }

@app.get("/queries")
def list_queries():
    return list(QUERIES.keys())

@app.get("/query/{name}")
def run_named_query(name: str):
    if name not in QUERIES:
        return {"error": "Unknown query", "available": list(QUERIES.keys())}
    df = query_to_dataframe(GRAPH, QUERIES[name])
    return {"rows": len(df), "data": df.to_dict(orient="records")}

@app.get("/sparql")
def run_sparql(q: str = Query(..., description="SPARQL query body without prefixes")):
    df = query_to_dataframe(GRAPH, q)
    return {"rows": len(df), "data": df.to_dict(orient="records")}
