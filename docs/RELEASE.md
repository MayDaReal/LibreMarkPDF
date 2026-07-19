# Release

Le fichier racine `VERSION` est l'unique source de version pour l'application,
la CLI et les candidats. Le format suit PEP 440 : `0.1.0.dev1` pour le
développement, `0.1.0b1` pour une bêta, `0.1.0rc1` pour une release candidate
et `0.1.0` pour une version stable.

Chaque candidat est produit nativement et placé sous
`dist/<version>/<platform>/`. Il doit contenir le candidat, ses checksums, son
SBOM, son manifeste, les rapports automatisés et la checklist humaine.

Une bêta publique requiert la validation automatisée complète de sa plateforme.
Une stable requiert aussi la checklist humaine complète, la comparaison du
corpus canonique et les signatures applicables. Un build réussi seul ne rend
jamais une release officielle.

Les archives lourdes, navigateurs, environnements virtuels et PDF générés ne
sont pas versionnés. Les rapports synthétiques, manifests et checksums d'une
release publiée peuvent l'être.
