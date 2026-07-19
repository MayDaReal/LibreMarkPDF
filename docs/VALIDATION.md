# Validation

LibreMark PDF distingue les contrôles rapides des validations d'artefact. Les
tests normaux ne modifient jamais le corpus canonique ni les données attendues.

## Commandes

Après `bootstrap-windows.ps1` ou `bootstrap-linux.sh` :

```text
make test-pure     # contrôles unitaires sans navigateur
make test          # suite complète avec Chromium verrouillé
make test-ui       # orchestration Tk et actions IHM stables
make test-visual   # contrat du corpus canonique
```

Les validations natives `make validate-windows` et `make validate-linux`
produisent un candidat, des diagnostics et une checklist dans
`dist/<version>/<plateforme>/`.

Sous Windows, l'appel direct ne demande aucun paramètre :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-windows-artifact.ps1
```

Il utilise par défaut `.venv-windows-py39`, `browser-win` et
`dist/<version>/windows-x64`. Les valeurs peuvent toujours être remplacées avec
`-Python` et `-EvidenceRoot`.

Les bootstraps sont interactifs lorsqu'un terminal est disponible : ils
demandent confirmation avant d'installer Python 3.9 ou GNU Make. Les options
Windows `-InstallPython`, `-InstallMake`, `-NonInteractive` et leurs équivalents
Linux `--install-python`, `--install-make`, `--non-interactive` permettent une
exécution automatisée. Le mode hors ligne n'installe et ne télécharge rien.

## Corpus canonique

`tests/fixtures/canonical/manifest.json` et
`tests/goldens/canonical/expected.json` forment le corpus canonique actuel.
Ils couvrent Markdown, pagination, ressources, Unicode, thèmes, collisions et
chemins. Les outils actifs sont `tools/visual_regression.py`,
`tools/artifact_visual_regression.py`, `tools/validate-windows-artifact.ps1`
et `tools/validate-linux-artifact.sh`.

La commande normale de comparaison est en lecture seule. Toute mise à jour des
goldens utilise l'outil de mise à jour dédié, exige un ticket, une justification,
une revue humaine et des comparaisons avant/après conservées avec la release.

## IHM

Les tests IHM ciblent des actions métier stables telles que `files.add`,
`advanced.toggle`, `preview.refresh` et `convert.start`. Ils ne reposent ni
sur les coordonnées, ni sur les couleurs, ni sur les textes EN/FR. La checklist
native conserve les vérifications humaines de contraste, focus, DPI et
intégration bureau.
