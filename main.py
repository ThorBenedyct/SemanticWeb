import os

from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD
import sys

REFERENCE_FILE = "reference-kg.nt"
HIERARCHY_FILE = "classHierarchy.nt"
INPUT_FILE = "fokg-sw-test-2024.nt"
OUTPUT_FILE = "result.ttl"

# Namespace für das Ergebnis
HAS_TRUTH = URIRef("http://swc2017.aksw.org/hasTruthValue")


def load_graph(path):
    g = Graph()
    g.parse(path, format="nt")
    return g


def get_real_score(facts, fact):
    real_score_literal = facts.value(fact, HAS_TRUTH)
    if real_score_literal is None:
        return 0.0
    return float(real_score_literal[0])

def check_truth(ref_kg, facts, fact):
    sub = facts.value(fact, RDF.subject)
    pre = facts.value(fact, RDF.predicate)
    obj = facts.value(fact, RDF.object)

    if sub is None or pre is None or obj is None:
        return 0.0

    # Existenzprüfung im Referenz-KG
    is_true = (sub, pre, obj) in ref_kg

    if is_true:
        return 1.0
    return 0.0


def main():
    test_score = 0.0
    amount_facts = 0

    print("Lade Referenz-KG")
    ref_kg = load_graph(REFERENCE_FILE)

    print("Lade Input-Fakten")
    facts = load_graph(INPUT_FILE)

    resultGraph = Graph()

    for fact in facts.subjects(RDF.type, RDF.Statement):
        score = check_truth(ref_kg, facts, fact)

        real_score = get_real_score(facts, fact)
        test_score = test_score + abs(score-real_score)
        amount_facts += 1

        resultGraph.add((
            fact,
            HAS_TRUTH,
            Literal(score, datatype=XSD.double)
        ))
    test_score = test_score / amount_facts

    print("Schreibe Ergebnisdatei")
    resultGraph.serialize(destination=OUTPUT_FILE, format="nt")

    print(f"Abweichung: {test_score}")
    print("Fertig.")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        if os.path.exists(sys.argv[1]):
            INPUT_FILE = sys.argv[1]
    main()
