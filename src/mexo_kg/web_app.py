from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from rdflib import Graph

from mexo_kg.builder import build_graph, graph_metrics
from mexo_kg.graph_exports import rdf_to_networkx, graph_analytics
from mexo_kg.graph_viz import build_interactive_network_html
from mexo_kg.queries import QUERIES, query_to_dataframe

st.set_page_config(page_title="MEXO-KG Explorer", layout="wide")
st.title("MEXO-KG Explorer")
st.caption("Semantic exploration of metaheuristic optimization experiments using MEXO, RDF, SPARQL and graph analytics.")

excel_file = st.sidebar.file_uploader("Upload MEXO Excel workbook", type=["xlsx"])
default_path = Path("data/MEXO_Optimization.xlsx")

@st.cache_data(show_spinner=True)
def load_graph_from_path(path: str):
    g = build_graph(path)
    return g.serialize(format="turtle")

if excel_file is not None:
    temp_path = Path("outputs/uploaded_mexo.xlsx")
    temp_path.parent.mkdir(exist_ok=True)
    temp_path.write_bytes(excel_file.getbuffer())
    ttl = load_graph_from_path(str(temp_path))
elif default_path.exists():
    ttl = load_graph_from_path(str(default_path))
else:
    st.error("No default workbook found. Upload a MEXO Excel workbook.")
    st.stop()

g = Graph()
g.parse(data=ttl, format="turtle")
metrics = graph_metrics(g)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Triples", metrics["triples"])
c2.metric("Subjects", metrics["subjects"])
c3.metric("Predicates", metrics["predicates"])
c4.metric("Objects", metrics["objects"])

st.sidebar.subheader("Network view settings")
include_literals = st.sidebar.toggle("Include literal values as nodes", value=False)
max_nodes = st.sidebar.slider("Max nodes to draw", min_value=30, max_value=500, value=180, step=10)
min_degree = st.sidebar.slider("Minimum degree", min_value=1, max_value=20, value=1, step=1)
physics = st.sidebar.toggle("Physics layout", value=True)

nxg = rdf_to_networkx(g, include_literals=include_literals)
net_metrics, top_nodes, top_edges = graph_analytics(nxg, top_n=30)

tab_overview, tab_network, tab_queries, tab_rdf = st.tabs([
    "Overview", "Network visualization", "SPARQL queries", "RDF preview"
])

with tab_overview:
    st.subheader("Class coverage")
    st.dataframe(pd.DataFrame([{"Class": k, "Individuals": v} for k, v in metrics["class_counts"].items()]), use_container_width=True)

    st.subheader("Network analytics")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Graph nodes", net_metrics.get("nodes", 0))
    mc2.metric("Graph edges", net_metrics.get("edges", 0))
    mc3.metric("Weak components", net_metrics.get("weak_components", 0))
    mc4.metric("Avg. degree", round(net_metrics.get("average_degree", 0), 3))

    st.markdown("**Top central nodes**")
    st.dataframe(top_nodes, use_container_width=True)
    st.markdown("**Top collapsed edges**")
    st.dataframe(top_edges, use_container_width=True)

with tab_network:
    st.subheader("Interactive MEXO-KG network")
    st.caption("The drawing shows the highest-degree subgraph so that the visualization stays readable. Use the sidebar to change node limits or include literal values.")
    html = build_interactive_network_html(
        nxg,
        max_nodes=max_nodes,
        min_degree=min_degree,
        height="760px",
        width="100%",
        physics=physics,
    )
    components.html(html, height=790, scrolling=True)

with tab_queries:
    st.subheader("Competency-question query runner")
    query_name = st.selectbox("Query", list(QUERIES.keys()))
    query_text = st.text_area("SPARQL", QUERIES[query_name], height=240)
    if st.button("Run query"):
        try:
            df = query_to_dataframe(g, query_text)
            st.success(f"Returned {len(df)} rows")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(str(e))

with tab_rdf:
    st.subheader("RDF preview")
    st.code(ttl[:7000], language="turtle")
