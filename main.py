import os
from rdflib import Graph, URIRef, Literal, Namespace, RDFS, Node
from rdflib.namespace import RDF, XSD
import sys
REFERENCE_FILE = "reference-kg.nt"
HIERARCHY_FILE = "classHierarchy.nt"
INPUT_FILE = "fokg-sw-train-2024.nt"
OUTPUT_FILE = "result.ttl"

# Namespaces
HAS_TRUTH = URIRef("http://swc2017.aksw.org/hasTruthValue")

PLACE_OF_BIRTH = URIRef("http://rdf.freebase.com/ns/people.person.place_of_birth")
PLACE_LIVED = URIRef("http://rdf.freebase.com/ns/people.person.places_lived..people.place_lived.location")
PERSON = URIRef("http://rdf.freebase.com/ns/people.person")

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

    def get_all_super_locations(self, location):
        locations = set()
        stack = [location]

        while stack:
            current = stack.pop()
            for parent in self.ref_kg.objects(current, URIRef("http://rdf.freebase.com/ns/location.location.part_of")):
                if parent not in locations:
                    locations.add(parent)
                    stack.append(parent)
            for parent in self.ref_kg.subjects(URIRef("http://rdf.freebase.com/ns/location.location.contains"), current):
                if parent not in locations:
                    locations.add(parent)
                    stack.append(parent)
        return locations

    def is_location(self, entity):
        return (self.has_type(entity, URIRef("http://rdf.freebase.com/ns/base.locations.countries"))
                or self.has_type(entity, URIRef("http://rdf.freebase.com/ns/locations.country"))
                or self.has_type(entity, URIRef("http://rdf.freebase.com/ns/location.location")))

    def query(self, subj, pre=None):
        return list(set(self.ref_kg.objects(subj, pre)))

    def get_types(self, entity):
        return list(set(self.ref_kg.objects(entity, RDF.type)))

    def has_type(self, entity, target_cls):
        for t in self.get_types(entity):
            if t == target_cls:
                return True
            if target_cls in self.get_all_superclasses(t):
                return True
        return False

    def get_labels(self, entity):
        return list(set(self.ref_kg.objects(entity, RDFS.label)))

    def nationality_heuristic(self, subj, pre, obj):
        if not self.has_type(subj, PERSON):
            return 0.0
        if not self.is_location(obj):
            return 0.0

        score = 0.1

        for loc in self.ref_kg.objects(subj, PLACE_OF_BIRTH):
            if obj in self.get_all_super_locations(loc):
                score += 0.4

        for loc in self.ref_kg.objects(subj, PLACE_LIVED):
            if obj in self.get_all_super_locations(loc):
                score += 0.2

        return min(score, 0.9)

    def check_truth(self, fact):
        subj = self.facts.value(fact, RDF.subject)
        pre = self.facts.value(fact, RDF.predicate)
        obj = self.facts.value(fact, RDF.object)

        if subj is None or pre is None or obj is None:
            return 0.0

        print(f"Checking: {self.get_labels(subj)} {pre} {self.get_labels(obj)}")

        # Existenzprüfung im Referenz-KG
        is_true = (subj, pre, obj) in self.ref_kg
        if is_true:
            return 1.0

        # More complex rules:
        score = 0.0

        if str(pre).endswith("people.person.nationality"):
            score = self.nationality_heuristic(subj, pre, obj)

        real_score = self.get_real_score(fact)
        print(f"Calculated score: {score}, \t Real score: {real_score}")
        if score > 0:
            print("halt")
        return score

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
