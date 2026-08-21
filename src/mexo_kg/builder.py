from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable

import pandas as pd
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import DCTERMS, PROV, SKOS, XSD

MEXO = Namespace("https://w3id.org/mexo/ontology#")
BASE = Namespace("https://w3id.org/mexo/resource/")

SHEET_HEADER_ROW = 2  # zero-based: actual headers are on Excel row 3


def slug(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "unknown"
    text = str(value).strip()
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "unknown"


def isna(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or str(value).strip() == ""


def lit(value: Any, datatype=None):
    if isna(value):
        return None
    if datatype is not None:
        return Literal(value, datatype=datatype)
    return Literal(value)


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    return df


def read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, header=SHEET_HEADER_ROW)
        return clean_columns(df)
    except Exception:
        return pd.DataFrame()


def first_col(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    cols = list(df.columns)
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in cols:
            return cand
        if cand.lower() in lower:
            return lower[cand.lower()]
    # fuzzy startswith match
    for c in cols:
        lc = c.lower()
        for cand in candidates:
            if lc.startswith(cand.lower()):
                return c
    return None


def add_label(g: Graph, uri: URIRef, label: Any):
    if not isna(label):
        g.add((uri, RDFS.label, Literal(str(label))))


def init_graph() -> Graph:
    g = Graph()
    g.bind("mexo", MEXO)
    g.bind("res", BASE)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("skos", SKOS)
    g.bind("prov", PROV)
    g.bind("dct", DCTERMS)
    return g


def add_algorithms(g: Graph, df: pd.DataFrame):
    if df.empty:
        return
    idc = first_col(df, ["algorithm_config_id", "algorithm_id"])
    labelc = first_col(df, ["skos:prefLabel", "label", "rdfs:label"])
    broaderc = first_col(df, ["skos:broader"])
    paramsc = first_col(df, ["mh:hasParameter --> parameter_id", "hasParameter", "parameter_id"])
    for _, row in df.iterrows():
        if isna(row.get(idc)):
            continue
        cfg = BASE[f"algorithm-configuration/{slug(row[idc])}"]
        g.add((cfg, RDF.type, MEXO.AlgorithmConfiguration))
        add_label(g, cfg, row.get(labelc))
        if broaderc and not isna(row.get(broaderc)):
            alg_id = slug(str(row[broaderc]).split("/")[-1])
            alg = BASE[f"algorithm/{alg_id}"]
            g.add((alg, RDF.type, MEXO.Algorithm))
            add_label(g, alg, alg_id)
            g.add((cfg, MEXO.instantiates, alg))
        if paramsc and not isna(row.get(paramsc)):
            for p in str(row[paramsc]).split(','):
                p = p.strip()
                if p:
                    g.add((cfg, MEXO.hasParameter, BASE[f"parameter/{slug(p)}"]))


def add_parameters(g: Graph, df: pd.DataFrame):
    if df.empty:
        return
    idc = first_col(df, ["parameter_id"])
    namec = first_col(df, ["mh:parameterName", "parameterName"])
    symc = first_col(df, ["mh:parameterSymbol", "parameterSymbol"])
    valc = first_col(df, ["mh:parameterValue", "parameterValue"])
    dtypec = first_col(df, ["parameterValueDatatype"])
    for _, row in df.iterrows():
        if isna(row.get(idc)):
            continue
        p = BASE[f"parameter/{slug(row[idc])}"]
        g.add((p, RDF.type, MEXO.Parameter))
        if namec and not isna(row.get(namec)):
            g.add((p, MEXO.parameterName, Literal(str(row[namec]))))
            add_label(g, p, row[namec])
        if symc and not isna(row.get(symc)):
            g.add((p, MEXO.parameterSymbol, Literal(str(row[symc]))))
        if valc and not isna(row.get(valc)):
            dtype = str(row.get(dtypec, "")).lower() if dtypec else ""
            dt = XSD.integer if "integer" in dtype else XSD.decimal if "decimal" in dtype or "double" in dtype else None
            g.add((p, MEXO.parameterValue, Literal(row[valc], datatype=dt) if dt else Literal(str(row[valc]))))


def add_problems(g: Graph, df: pd.DataFrame):
    if df.empty:
        return
    idc = first_col(df, ["problem_id"])
    labelc = first_col(df, ["rdfs:label", "label"])
    sourcec = first_col(df, ["dct:source", "source"])
    for _, row in df.iterrows():
        if isna(row.get(idc)):
            continue
        prob = BASE[f"problem/{slug(row[idc])}"]
        g.add((prob, RDF.type, MEXO.Problem))
        add_label(g, prob, row.get(labelc))
        if sourcec and not isna(row.get(sourcec)):
            suite = BASE[f"benchmark-suite/{slug(row[sourcec])}"]
            g.add((suite, RDF.type, MEXO.BenchmarkSuite))
            add_label(g, suite, row[sourcec])
            g.add((prob, MEXO.belongsToSuite, suite))


def add_instances(g: Graph, df: pd.DataFrame):
    if df.empty:
        return
    idc = first_col(df, ["instance_id"])
    pc = first_col(df, ["problem_id"])
    namec = first_col(df, ["instance_name"])
    dimc = first_col(df, ["dimension"])
    optc = first_col(df, ["known_optimum"])
    for _, row in df.iterrows():
        if isna(row.get(idc)):
            continue
        inst = BASE[f"problem-instance/{slug(row[idc])}"]
        g.add((inst, RDF.type, MEXO.ProblemInstance))
        add_label(g, inst, row.get(namec))
        if pc and not isna(row.get(pc)):
            g.add((inst, MEXO.instanceOf, BASE[f"problem/{slug(row[pc])}"]))
        if dimc and not isna(row.get(dimc)):
            g.add((inst, MEXO.dimension, Literal(int(row[dimc]), datatype=XSD.integer)))
        if optc and not isna(row.get(optc)):
            g.add((inst, MEXO.knownOptimum, Literal(float(row[optc]), datatype=XSD.decimal)))


def add_stopping(g: Graph, df: pd.DataFrame):
    if df.empty:
        return
    idc = first_col(df, ["stopping_id", "stopping_id (e.g., stop-001)"])
    labelc = first_col(df, ["rdfs:label", "label"])
    maxc = first_col(df, ["mh:maxIterations", "maxIterations"])
    for _, row in df.iterrows():
        if isna(row.get(idc)):
            continue
        s = BASE[f"stopping-criterion/{slug(row[idc])}"]
        g.add((s, RDF.type, MEXO.StoppingCriterion))
        add_label(g, s, row.get(labelc))
        if maxc and not isna(row.get(maxc)):
            g.add((s, MEXO.maxIterations, Literal(int(row[maxc]), datatype=XSD.integer)))


def add_budgets(g: Graph, df: pd.DataFrame):
    if df.empty:
        return
    idc = first_col(df, ["budget_id"])
    labelc = first_col(df, ["label"])
    itc = first_col(df, ["max_iterations"])
    evalc = first_col(df, ["max_evaluations"])
    timec = first_col(df, ["runtime_limit_sec"])
    for _, row in df.iterrows():
        if isna(row.get(idc)):
            continue
        b = BASE[f"budget/{slug(row[idc])}"]
        g.add((b, RDF.type, MEXO.ComputationalBudget))
        add_label(g, b, row.get(labelc))
        if itc and not isna(row.get(itc)):
            g.add((b, MEXO.maxIterations, Literal(int(row[itc]), datatype=XSD.integer)))
        if evalc and not isna(row.get(evalc)):
            g.add((b, MEXO.maxEvaluations, Literal(int(row[evalc]), datatype=XSD.integer)))
        if timec and not isna(row.get(timec)):
            g.add((b, MEXO.runtimeLimitSec, Literal(float(row[timec]), datatype=XSD.decimal)))


def add_experiments(g: Graph, df: pd.DataFrame):
    if df.empty:
        return
    idc = first_col(df, ["experiment_id", "experiment_id (e.g., exp-001)"])
    labelc = first_col(df, ["rdfs:label", "label"])
    algc = first_col(df, ["mh:usesAlgorithm -> algorithm_config_id", "usesAlgorithm", "algorithm_config_id"])
    probc = first_col(df, ["mh:targetsProblem -> problem_id", "targetsProblem", "problem_id"])
    stopc = first_col(df, ["mh:hasStoppingCriterion -> stopping_id", "hasStoppingCriterion", "stopping_id"])
    seedc = first_col(df, ["mh:randomSeed", "randomSeed"])
    runsc = first_col(df, ["mh:numberOfRuns", "numberOfRuns"])
    sourcec = first_col(df, ["dct:source", "source"])
    for _, row in df.iterrows():
        if isna(row.get(idc)):
            continue
        e = BASE[f"experiment/{slug(row[idc])}"]
        g.add((e, RDF.type, MEXO.Experiment))
        add_label(g, e, row.get(labelc))
        if algc and not isna(row.get(algc)):
            g.add((e, MEXO.usesAlgorithm, BASE[f"algorithm-configuration/{slug(row[algc])}"]))
        if probc and not isna(row.get(probc)):
            g.add((e, MEXO.targetsProblem, BASE[f"problem/{slug(row[probc])}"]))
        if stopc and not isna(row.get(stopc)):
            g.add((e, MEXO.hasStoppingCriterion, BASE[f"stopping-criterion/{slug(row[stopc])}"]))
        if seedc and not isna(row.get(seedc)):
            g.add((e, MEXO.randomSeed, Literal(int(row[seedc]), datatype=XSD.integer)))
        if runsc and not isna(row.get(runsc)):
            g.add((e, MEXO.numberOfRuns, Literal(int(row[runsc]), datatype=XSD.integer)))
        if sourcec and not isna(row.get(sourcec)):
            study = BASE[f"study/{slug(row[sourcec])}"]
            g.add((study, RDF.type, MEXO.Study))
            add_label(g, study, row[sourcec])
            g.add((e, PROV.wasDerivedFrom, study))


def add_results(g: Graph, df: pd.DataFrame):
    if df.empty:
        return
    idc = first_col(df, ["result_id"])
    expc = first_col(df, ["experiment_id"])
    fields = {
        "best_fitness": MEXO.bestFitness,
        "mean_fitness": MEXO.meanFitness,
        "std_fitness": MEXO.stdFitness,
        "worst_fitness": MEXO.worstFitness,
        "runtime_sec": MEXO.runTime,
        "evaluations": MEXO.numberOfEvaluations,
        "success_rate": MEXO.successRate,
        "rank": MEXO.rank,
    }
    for _, row in df.iterrows():
        if isna(row.get(idc)):
            continue
        r = BASE[f"performance-result/{slug(row[idc])}"]
        g.add((r, RDF.type, MEXO.PerformanceResult))
        if expc and not isna(row.get(expc)):
            e = BASE[f"experiment/{slug(row[expc])}"]
            g.add((e, MEXO.produces, r))
        for col, prop in fields.items():
            if col in df.columns and not isna(row.get(col)):
                dt = XSD.integer if col in ["evaluations", "rank"] else XSD.decimal
                val = int(row[col]) if dt == XSD.integer else float(row[col])
                g.add((r, prop, Literal(val, datatype=dt)))


def build_graph(excel_path: str | Path) -> Graph:
    excel_path = Path(excel_path)
    g = init_graph()
    add_algorithms(g, read_sheet(excel_path, "Algorithms"))
    add_parameters(g, read_sheet(excel_path, "Parameters"))
    add_problems(g, read_sheet(excel_path, "Problems"))
    add_instances(g, read_sheet(excel_path, "ProblemInstances"))
    add_stopping(g, read_sheet(excel_path, "StoppingCriteria"))
    add_budgets(g, read_sheet(excel_path, "ComputationalBudgets"))
    add_experiments(g, read_sheet(excel_path, "Experiments"))
    add_results(g, read_sheet(excel_path, "PerformanceResults"))
    return g


def class_counts(g: Graph) -> Dict[str, int]:
    q = """
    SELECT ?class (COUNT(?s) AS ?n) WHERE { ?s a ?class . }
    GROUP BY ?class ORDER BY DESC(?n)
    """
    return {str(row[0]).split('#')[-1].split('/')[-1]: int(row[1]) for row in g.query(q)}


def property_counts(g: Graph) -> Dict[str, int]:
    q = """
    SELECT ?p (COUNT(*) AS ?n) WHERE { ?s ?p ?o . }
    GROUP BY ?p ORDER BY DESC(?n)
    """
    return {str(row[0]).split('#')[-1].split('/')[-1]: int(row[1]) for row in g.query(q)}


def graph_metrics(g: Graph) -> Dict[str, Any]:
    return {
        "triples": len(g),
        "subjects": len(set(g.subjects())),
        "predicates": len(set(g.predicates())),
        "objects": len(set(g.objects())),
        "class_counts": class_counts(g),
        "property_counts": property_counts(g),
    }


def export_graph_json(g: Graph, path: str | Path, limit: int = 5000):
    nodes = {}
    edges = []
    for i, (s, p, o) in enumerate(g):
        if i >= limit:
            break
        if isinstance(s, URIRef):
            sid = str(s)
            nodes[sid] = {"id": sid, "label": sid.split('/')[-1].split('#')[-1], "type": "uri"}
        if isinstance(o, URIRef):
            oid = str(o)
            nodes[oid] = {"id": oid, "label": oid.split('/')[-1].split('#')[-1], "type": "uri"}
            edges.append({"from": str(s), "to": oid, "label": str(p).split('/')[-1].split('#')[-1]})
    Path(path).write_text(json.dumps({"nodes": list(nodes.values()), "edges": edges}, indent=2), encoding="utf-8")
