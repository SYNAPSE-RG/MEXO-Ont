from __future__ import annotations
from pathlib import Path
import pandas as pd
from rdflib import Graph

PREFIX = """
PREFIX mexo: <https://w3id.org/mexo/ontology#>
PREFIX res: <https://w3id.org/mexo/resource/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX prov: <http://www.w3.org/ns/prov#>
"""

QUERIES = {
    "cq1_algorithm_ranking": """
SELECT ?alg (MIN(?fit) AS ?bestFit)
WHERE {
  ?e a mexo:Experiment ;
     mexo:usesAlgorithm ?cfg ;
     mexo:produces ?r .
  ?cfg mexo:instantiates ?alg .
  ?r mexo:bestFitness ?fit .
}
GROUP BY ?alg
ORDER BY ASC(?bestFit)
""",
    "cq4_stopping_criterion_tradeoff": """
SELECT ?criterion (AVG(?fit) AS ?avgFit) (AVG(?runtime) AS ?avgRuntime)
WHERE {
  ?e a mexo:Experiment ;
     mexo:hasStoppingCriterion ?criterion ;
     mexo:produces ?r .
  ?r mexo:bestFitness ?fit .
  OPTIONAL { ?r mexo:runTime ?runtime . }
}
GROUP BY ?criterion
ORDER BY ASC(?avgFit) ASC(?avgRuntime)
""",
    "cq7_provenance_trace": """
SELECT ?experiment ?study
WHERE {
  ?experiment a mexo:Experiment .
  OPTIONAL { ?experiment prov:wasDerivedFrom ?study . }
}
ORDER BY ?experiment
""",
    "cq9_missing_results": """
SELECT ?experiment
WHERE {
  ?experiment a mexo:Experiment .
  FILTER NOT EXISTS { ?experiment mexo:produces ?result . }
}
ORDER BY ?experiment
""",
    "cq10_robust_configurations": """
SELECT ?cfg (AVG(?fit) AS ?avgFit) (AVG(?std) AS ?avgStdFit)
WHERE {
  ?e a mexo:Experiment ;
     mexo:usesAlgorithm ?cfg ;
     mexo:produces ?r .
  ?r mexo:bestFitness ?fit .
  OPTIONAL { ?r mexo:stdFitness ?std . }
}
GROUP BY ?cfg
ORDER BY ASC(?avgFit) ASC(?avgStdFit)
""",
}


def query_to_dataframe(g: Graph, query: str) -> pd.DataFrame:
    rows = []
    result = g.query(PREFIX + query)
    vars_ = [str(v) for v in result.vars]
    for row in result:
        rows.append({vars_[i]: str(row[i]) if row[i] is not None else "" for i in range(len(vars_))})
    return pd.DataFrame(rows, columns=vars_)


def run_all_queries(g: Graph, output_dir: str | Path):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, query in QUERIES.items():
        df = query_to_dataframe(g, query)
        df.to_csv(output_dir / f"{name}.csv", index=False)
        summary[name] = len(df)
    return summary
