from __future__ import annotations
from pathlib import Path
from pyshacl import validate


def validate_graph(data_graph_path="outputs/mexo_kg.ttl", shacl_path="ontology/shacl_shapes.ttl"):
    conforms, results_graph, results_text = validate(
        data_graph=str(data_graph_path),
        shacl_graph=str(shacl_path),
        data_graph_format="turtle",
        shacl_graph_format="turtle",
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    )
    return conforms, results_text

if __name__ == "__main__":
    conforms, text = validate_graph()
    print("Conforms:", conforms)
    print(text)
