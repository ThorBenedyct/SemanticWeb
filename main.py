import os
from rdflib import Graph, URIRef, Literal, Namespace, RDFS
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


class FactChecker:
    def __init__(self):
        print("Lade Referenz-KG")
        self.ref_kg = load_graph(REFERENCE_FILE)

        print("Lade Klassen-Hierachy")
        self.class_kg = load_graph(HIERARCHY_FILE)

        print("Lade Input-Fakten")
        self.facts = load_graph(INPUT_FILE)

        self.resultGraph = Graph()

    def get_real_score(self, fact):
        """For testing purpose only. Uses veracity in test file to check"""
        real_score_literal = self.facts.value(fact, HAS_TRUTH)
        if real_score_literal is None:
            return 0.0
        return float(real_score_literal[0])

    def get_all_superclasses(self, cls):
        supers = set()
        stack = [cls]

        while stack:
            current = stack.pop()
            for parent in self.class_kg.objects(current, RDFS.subClassOf):
                if parent not in supers:
                    supers.add(parent)
                    stack.append(parent)

        return supers

    def query(self, subj, pre=None):
        return list(set(self.ref_kg.objects(subj, pre)))

    def get_types(self, entity):
        return list(set(self.ref_kg.objects(entity, RDF.type)))

    def get_labels(self, entity):
        return list(set(self.ref_kg.objects(entity, RDFS.label)))

    def check_truth(self, fact):
        sub = self.facts.value(fact, RDF.subject)
        pre = self.facts.value(fact, RDF.predicate)
        obj = self.facts.value(fact, RDF.object)

        if sub is None or pre is None or obj is None:
            return 0.0
        # Existenzprüfung im Referenz-KG
        is_true = (sub, pre, obj) in self.ref_kg
        if is_true:
            return 1.0

        # More complex rules:

        return 0.0

    def main(self):
        test_score = 0.0
        amount_facts = 0

        for fact in self.facts.subjects(RDF.type, RDF.Statement):
            score = self.check_truth(fact)

            real_score = self.get_real_score(fact)
            test_score = test_score + abs(score - real_score)
            amount_facts += 1

            self.resultGraph.add((
                fact,
                HAS_TRUTH,
                Literal(score, datatype=XSD.double)
            ))
        test_score = test_score / amount_facts

        print("Schreibe Ergebnisdatei")
        self.resultGraph.serialize(destination=OUTPUT_FILE, format="nt")

        print(f"Abweichung: {test_score}")
        print("Fertig.")


def main():
    fact_checker = FactChecker()
    fact_checker.main()


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        if os.path.exists(sys.argv[1]):
            INPUT_FILE = sys.argv[1]
    main()
