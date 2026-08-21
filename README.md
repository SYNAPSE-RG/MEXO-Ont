# MEXO-KG Graph Package

Builds a MEXO RDF knowledge graph from Excel and exports ontology/KG graph formats for analysis in Gephi, Cytoscape, yEd, NetworkX and web dashboards.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

## Build everything

```bash
python -m mexo_kg.cli --excel data/MEXO_Optimization.xlsx --out outputs --graph-mode both
```

## Main outputs

- `outputs/mexo_kg.ttl`: RDF/Turtle KG.
- `outputs/mexo_kg.nt`: RDF/N-Triples KG.
- `outputs/mexo_kg_uri.graphml`: URI-resource graph for Gephi/Cytoscape/yEd.
- `outputs/mexo_kg_full.graphml`: graph including literal value nodes.
- `outputs/mexo_kg_uri.gexf`: Gephi-native graph.
- `outputs/mexo_kg_full.gexf`: Gephi-native graph including literals.
- `outputs/mexo_kg_uri_network_metrics.json`: graph metrics.
- `outputs/mexo_kg_uri_top_nodes.csv`: centrality ranking.
- `outputs/mexo_kg_uri_top_edges.csv`: most frequent collapsed relations.
- `outputs/query_results/*.csv`: SPARQL competency-question outputs.

## App

```bash
streamlit run src/mexo_kg/web_app.py
```

## API

```bash
uvicorn mexo_kg.api:app --reload
```

Open `http://127.0.0.1:8000/network-metrics` for centrality and graph-level metrics.
