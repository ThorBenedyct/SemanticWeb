import os
from rdflib import Graph, URIRef, Literal, Namespace, RDFS, Node
from rdflib.namespace import RDF, XSD
import sys
from collections import deque
#from sklearn.metrics import roc_auc_score

REFERENCE_FILE = "reference-kg.nt"
HIERARCHY_FILE = "classHierarchy.nt"
INPUT_FILE = "fokg-sw-train-2024.nt"
OUTPUT_FILE = "result.ttl"

# Namespaces
HAS_TRUTH = URIRef("http://swc2017.aksw.org/hasTruthValue")

PLACE_OF_BIRTH = URIRef("http://rdf.freebase.com/ns/people.person.place_of_birth")
NATIONALITY = URIRef("http://rdf.freebase.com/ns/people.person.nationality")
LOCATION_PART_OF = URIRef("http://rdf.freebase.com/ns/location.location.part_of")
LOCATION_CONTAINS = URIRef("http://rdf.freebase.com/ns/location.location.contains")
PLACE_LIVED = URIRef("http://rdf.freebase.com/ns/people.person.places_lived..people.place_lived.location")
PERSON = URIRef("http://rdf.freebase.com/ns/people.person")
MUSIC_GROUP_MEMBER = URIRef("http://rdf.freebase.com/ns/music_group_member")
MUSIC_ARTIST = URIRef("http://rdf.freebase.com/ns/music_artist")
MUSIC_ARTIST2 = URIRef("http://rdf.freebase.com/ns/music.artist")

MUSIC_GENRE_ARTIST = URIRef("http://rdf.freebase.com/ns/music.artist.genre")
MUSIC_GENRE_TYPE = URIRef('http://rdf.freebase.com/ns/music.genre')
FILM_GENRE = URIRef("http://rdf.freebase.com/ns/film.film.genre")
FILE_GENRE_TYPE = URIRef('http://rdf.freebase.com/ns/film.film_genre')
FILM = URIRef("http://rdf.freebase.com/ns/film.film")

SEQUEL = URIRef("http://rdf.freebase.com/ns/film.film.sequel")
PREQUEL = URIRef("http://rdf.freebase.com/ns/film.film.prequel")

PROFESSION = URIRef("http://rdf.freebase.com/ns/people.person.profession")
MUSICIAN = URIRef("http://rdf.freebase.com/ns/m.09jwl")

GENDER_MALE = URIRef("http://rdf.freebase.com/ns/m.05zppz")
GENDER_FEMALE = URIRef("http://rdf.freebase.com/ns/m.02zsn")

ROMANTIC_RELATIONSHIP_CELEBRITY = URIRef(
    "http://rdf.freebase.com/ns/celebrities.celebrity.sexual_relationships..celebrities.romantic_relationship.celebrity")
DATED_CELEBRITY = URIRef("http://rdf.freebase.com/ns/base.popstra.celebrity.dated..base.popstra.dated.participant")

TIMEZONE = URIRef("http://rdf.freebase.com/ns/time.time_zone")
TIMEZONE_PREDICATE = URIRef("http://rdf.freebase.com/ns/location.location.time_zones")


def load_graph(path):
    print(f"Lade Graph von {path} ... ")

    g = Graph()
    if not os.path.exists(path):
        print(f"Datei {path} fehlt!")
        return g

    if path.endswith(".ttl"):
        g.parse(path, format="turtle")
    else:
        g.parse(path, format="nt")
    print(f"Graph geladen mit {len(g)} Tripeln")
    return g


class FactChecker:
    def __init__(self):
        self.ref_kg = load_graph(REFERENCE_FILE)
        self.class_kg = load_graph(HIERARCHY_FILE)
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
            for parent in self.query_objects(current, LOCATION_PART_OF):
                if parent not in locations:
                    locations.add(parent)
                    stack.append(parent)
            for parent in self.query_subjects(LOCATION_CONTAINS, current):
                if parent not in locations:
                    locations.add(parent)
                    stack.append(parent)
        return locations

    def get_all_sub_locations(self, location):
        locations = set()
        stack = [location]

        while stack:
            current = stack.pop()
            for parent in self.query_subjects(LOCATION_PART_OF, current):
                if parent not in locations:
                    locations.add(parent)
                    stack.append(parent)
            for parent in self.query_objects(current, LOCATION_CONTAINS):
                if parent not in locations:
                    locations.add(parent)
                    stack.append(parent)
        return locations

    def is_location(self, entity):
        return (self.has_type(entity, URIRef("http://rdf.freebase.com/ns/base.locations.countries"))
                or self.has_type(entity, URIRef("http://rdf.freebase.com/ns/locations.country"))
                or self.has_type(entity, URIRef("http://rdf.freebase.com/ns/location.location")))

    def is_instrument(self, entity):
        return (self.has_type(entity, URIRef("http://rdf.freebase.com/ns/music.performance_role"))
                or self.has_type(entity, URIRef("http://rdf.freebase.com/ns/music.instrument")))

    def is_musician(self, entity):
        return (self.has_type(entity, MUSIC_GROUP_MEMBER)
                or self.has_type(entity, MUSIC_ARTIST)
                or self.has_type(entity, MUSIC_ARTIST2)
                or MUSICIAN in self.query_objects(entity, PROFESSION))

    def get_partners(self, person):
        partners = []
        partners += self.query_objects(person, ROMANTIC_RELATIONSHIP_CELEBRITY)
        partners += self.query_subjects(ROMANTIC_RELATIONSHIP_CELEBRITY, person)
        partners += self.query_objects(person, DATED_CELEBRITY)
        partners += self.query_objects(DATED_CELEBRITY, person)
        return set(partners)

    def query_objects(self, subj, pre=None):
        return list(set(self.ref_kg.objects(subj, pre)))

    def query_subjects(self, pre, obj):
        return list(set(self.ref_kg.subjects(pre, obj)))

    def get_types(self, entity):
        return self.query_objects(entity, RDF.type)

    def has_type(self, entity, target_cls):
        for t in self.get_types(entity):
            if t == target_cls:
                return True
            if target_cls in self.get_all_superclasses(t):
                return True
        return False

    def get_labels(self, entity):
        return self.query_objects(entity, RDFS.label)

    def check_path_score(self, start, end, max_depth=2):
        if start == end: return 1.0

        q_fwd = deque([start]);
        visited_fwd = {start: 0}
        q_bwd = deque([end]);
        visited_bwd = {end: 0}

        while q_fwd and q_bwd:
            if len(visited_fwd) >= 500 or len(visited_bwd) >= 500: break

            if len(q_fwd) <= len(q_bwd):
                curr = q_fwd.popleft()
                current_dist = visited_fwd[curr]

                if current_dist >= max_depth:
                    continue

                for n in self.query_objects(curr, None):
                    if n in visited_bwd:
                        dist = current_dist + 1 + visited_bwd[n]
                        return 1.0 / (dist + 1)

                    if n not in visited_fwd:
                        visited_fwd[n] = visited_fwd[curr] + 1
                        q_fwd.append(n)

            else:
                curr = q_bwd.popleft()
                current_dist = visited_bwd[curr]

                if current_dist >= max_depth:
                    continue

                for n in self.query_subjects(None, curr):
                    if n in visited_fwd:
                        dist = current_dist + 1 + visited_fwd[n]
                        return 1.0 / (dist + 1)

                    if n not in visited_bwd:
                        visited_bwd[n] = visited_bwd[curr] + 1
                        q_bwd.append(n)

        return 0.0

    # Rules based on different predicate cases
    def nationality_heuristic(self, subj, pre, obj):
        if not self.has_type(subj, PERSON):
            return 0.0
        if not self.is_location(obj):
            return 0.0

        score = 0.1

        for loc in self.query_objects(subj, PLACE_OF_BIRTH):
            if obj in self.get_all_super_locations(loc):
                score += 0.4

        for loc in self.query_objects(subj, PLACE_LIVED):
            if obj in self.get_all_super_locations(loc):
                score += 0.2

        return min(score, 0.9)

    def place_of_birth_heuristic(self, subj, pre, obj):
        if not self.has_type(subj, PERSON):
            return 0.0
        if not self.is_location(obj):
            return 0.0

        score = 0.1

        for loc in self.query_objects(subj, NATIONALITY):
            if obj in self.get_all_super_locations(loc):
                score += 0.4
            if obj in self.get_all_sub_locations(loc):
                score += 0.1

        for loc in self.query_objects(subj, PLACE_LIVED):
            if obj in self.get_all_super_locations(loc):
                score += 0.2
            if obj in self.get_all_sub_locations(loc):
                score += 0.1

        return min(score, 0.9)

    def time_zone_heuristic(self, subj, pre, obj):
        if not self.is_location(subj):
            return 0.0
        if not self.has_type(obj, TIMEZONE):
            return 0.0

        score = 0.1

        for loc in self.get_all_sub_locations(subj):
            timezones = self.query_objects(loc, TIMEZONE_PREDICATE)
            if obj in timezones:
                score += 0.8
            elif len(timezones) > 0:
                # It has a timezone, but is the wrong one
                score -= 0.4

        for loc in self.get_all_super_locations(subj):
            timezones = self.query_objects(loc, TIMEZONE_PREDICATE)
            if obj in timezones:
                score += 0.1
            elif len(timezones) > 0:
                # It has a timezone, but is the wrong one
                score -= 0.05

        return max(0.0, min(score, 1.0))

    def instrument_heuristic(self, subj, pre, obj):
        if not self.is_instrument(subj):
            return 0.0
        if not self.has_type(obj, PERSON):
            return 0.0

        score = 0.1

        if self.is_musician(obj):
            score += 0.2

        return min(score, 0.9)

    def location_contains_heuristic(self, subj, pre, obj):
        if not self.is_location(subj):
            return 0.0

        if subj in self.get_all_super_locations(obj):
            return 1.0

        score = 0.05
        if self.is_location(obj):
            score += 0.05

        return score

    def gender_heuristic(self, subj, pre, obj):
        if not self.has_type(subj, PERSON):
            return 0.0
        if obj != GENDER_MALE and obj != GENDER_FEMALE:
            return 0.0

        known_gender = self.query_objects(subj, pre)
        if len(known_gender) > 0:
            if obj == known_gender[0]:
                return 1.0
            else:
                return 0.0
        for partner in self.get_partners(subj):
            partner_gender = self.query_objects(partner, pre)
            if len(partner_gender) > 0:
                # Assume hetero
                if obj != partner_gender[0]:
                    return 0.95
                else:
                    return 0.05
        for object in self.query_objects(subj):
            for label in self.get_labels(object):
                if "female" in str(label).lower():
                    if subj == GENDER_FEMALE:
                        return 0.9
                    else:
                        return 0.1
        return 0.5

    def music_genre_heuristic(self, subj, obj):
        if not self.has_type(subj, MUSIC_GENRE_TYPE):
            return 0.0

        score = 0.05

        if self.is_musician(obj):
            score += 0.2

        if (subj, MUSIC_GENRE_ARTIST, obj) in self.ref_kg:
            return 1.0

        for neighbor in self.ref_kg.objects(subj, None):
            if (neighbor, MUSIC_GENRE_ARTIST, obj) in self.ref_kg:
                return 0.8

        for member in self.ref_kg.objects(None, subj):
            if (member, MUSIC_GENRE_ARTIST, obj) in self.ref_kg:
                return 0.6

        return score

    def film_genre_heuristic(self, subj, obj):
        if not self.has_type(subj, FILM):
            return 0.0
        if not self.has_type(obj, FILE_GENRE_TYPE):
            return 0.0

        related_films = []
        for seq in self.ref_kg.objects(subj, SEQUEL):
            related_films.append(seq)
        for pre in self.ref_kg.objects(subj, PREQUEL):
            related_films.append(pre)

        for film in related_films:
            if (film, FILM_GENRE, obj) in self.ref_kg:
                return 0.9

        return 0.1

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
        elif str(pre).endswith("people.person.place_of_birth"):
            score = self.place_of_birth_heuristic(subj, pre, obj)
        elif str(pre).endswith("music.instrument.instrumentalists"):
            score = self.instrument_heuristic(subj, pre, obj)
        elif str(pre).endswith("location.location.contains"):
            score = self.location_contains_heuristic(subj, pre, obj)
        elif str(pre).endswith("people.person.gender"):
            score = self.gender_heuristic(subj, pre, obj)
        elif str(pre).endswith("location.location.time_zones"):
            score = self.time_zone_heuristic(subj, pre, obj)
        # elif str(pre).endswith("music.genre.artists"):
        #     score = self.music_genre_heuristic(subj, obj)
        elif "film" in str(pre) and "genre" in str(pre):
            score = self.film_genre_heuristic(subj, obj)
        else:
            score = self.check_path_score(subj, obj) * 0.4

        # real_score = self.get_real_score(fact)
        #
        # print(f"Calculated score: {score}, \t Real score: {real_score}")

        return score

    def run(self):
        y_true = []
        y_scores = []
        amount_facts = 0

        for fact in self.facts.subjects(RDF.type, RDF.Statement):
            score = self.check_truth(fact)
            real_score = self.get_real_score(fact)

            if real_score is not None:
                y_true.append(real_score)
                y_scores.append(score)

            self.resultGraph.add((
                fact,
                HAS_TRUTH,
                Literal(score, datatype=XSD.double)
            ))

            amount_facts += 1
            if amount_facts % 100 == 0:
                print(f"{amount_facts}...")

        if len(set(y_true)) > 1:
            try:
                auc = roc_auc_score(y_true, y_scores)
                print(f"\n === AUC SCORE: {auc:.4f} ===")
            except:
                pass

        else:
            print("Keine validen labels")

        print("Schreibe Ergebnisdatei")
        self.resultGraph.serialize(destination=OUTPUT_FILE, format="nt")

        print("Fertig.")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        if os.path.exists(sys.argv[1]):
            INPUT_FILE = sys.argv[1]
    fact_checker = FactChecker()
    fact_checker.run()
