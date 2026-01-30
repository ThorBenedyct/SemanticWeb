
# Fact Checking Tool - Introduction to the Semantic Web

Authors: 
Thorben Hoppe (Matrikel-Nummer: 7232127), 
Florian Ernst (Matrikel-Nummer: )

# Description

This repository contains the source code for our Fact Checking Tool, which we created for the course “Introduction to the Semantic Web”. 
The tool validates RDF-triples based on a reference knowledge graph and some heuristics.

The approach to fact checking combines exact matching in the reference graph with a series of predicate specific heuristics. 
In addition to that a fallback strategy, using path finding in the knowledge graph was also implemented.

## 1. The tool relies on three sources of data:
- `reference-kg.nt` - The reference knowledge graph. This knowledge graph acts as our base truth.
- `classHierarchy.nt` - Class Hierarchy. An ontology which defines relations between subclasses. 
- `fokg-sw-###-2024.nt` - Input facts. The facts which are to be checked.

## 2. The strategy
For every triple (Subjekt, Predicate, Object) a score between 0.0 and 1.0 will be calculated by the following rules:

If a triple exists exactly in the reference knowledge graph an exact match has been found. An exact match equals to 1.0.

If no exact match is found, the tool checks the predicate for specific rules through the implemented heuristics.
These are: 

- **Nationality** and **place of birth**. This heuristic follows a transitivity approach, through which e.g. a person born in Berlin will also be born in Germany.
Hierarchies like ‘part_of’ and ‘contains’ can be accessed for this.

- **Gender**. Checks if there exists a known gender to a person. 
Otherwise, it checks for possible romantic partners of the person and determines gender based on the assumption, that the person is likely heterosexual. 
Lastly it checks if connected nodes have labels, such as ‘female actor’ to determine gender.

- **Location Containment** Validates the connection between time zones and geography through a location-tree.

- **Time Zones**. Validates the connection between time zones and geography through a location-tree.

- **Instruments**. Checks if subject and objects have appropriate types (instrument and person). 
If the object is a musician, it is considered likely, that the statement is true.

- **Film Genre**. Analyzes sequels and prequels of a movie to deduce its possible genre.

## 3. Fallback: BFS
If neither the exact match, nor the heuristics find a sufficient answer, a bi-directional BFS will take place. 

Here the shortest path between the subject and object will be found. The shorter the path is, the more likely it is, that the two are related.

The score is then calculated through: 1.0 / (distance + 1).

# Requirements:
- Python 3.8 or higher 
- Pip (Python Package Manager)
- Access to the “Introduction to the Semantic Web” course material on Panda

To use the tool yourself, follow the steps. When bash is required, use your systems terminal.

1. Clone repository
Download the repository and navigate to the folder by using bash:
```
cd ~/Desktop
Git clone https://github.com/ThorBenedyct/SemanticWeb.git fact-checking-tool
cd fact-checking-tool
```

2. Install dependencies using bash

`pip install rdflib` (WINDOWS)

`python3 -m pip install rdflib` (MACOS)

3. Download the correct data sources

In the project folder you need to have the following files:

- `main.py`
- `reference-kg.nt`
- `classHierarchy.nt`
- `fokg-sw-train-2024.nt` or `fokg-sw-test-2024.nt`

Of which most should already be there.

The reference-kg.nt file is too big for GitHub and needs to be downloaded manually from the related course material on Panda.

In the course go to the “mini-project” tab and download the reference knowledge graph as a dump file.

If you have downloaded the file from Panda, just move it manually into the fact-checking-tool folder.


4. Start the tool from the fact-checking-tool directory through your terminal:
(IF NOT ALREADY IN THE RIGHT DIRECTORY: `cd ~/Desktop/fact-checking-tool` )

`python main.py` (WINDOWS)

`python3 main.py` (MACOS)

5. The result will be the newly created `result.ttl` file in the fact-checking-tool directory located on your desktop

Thanks for using our fact-checking tool :-)