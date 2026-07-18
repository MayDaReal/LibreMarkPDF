# LibreMark PDF — Manuel utilisateur

LibreMark PDF convertit un ou plusieurs fichiers Markdown en PDF A4 mis en
forme, directement sur votre ordinateur. Il propose une interface graphique et
une ligne de commande non interactive.

> **Version préliminaire :** aucun téléchargement officiellement validé n’est
> encore publié. L’application actuelle doit être lancée depuis les sources ou
> construite localement.

## Utilisation de l’interface graphique

1. Ouvrez LibreMark PDF.
2. Déposez des fichiers `.md` ou `.markdown` dans la fenêtre, ou sélectionnez
   **Parcourir les fichiers**.
3. Facultatif : choisissez un thème local validé, ou sélectionnez **Changer**
   pour utiliser un fichier CSS personnel. Ces choix sont incompatibles.
4. Facultatif : ouvrez **En-tête et pied de page (avancé)** et modifiez les six
   positions.
5. Sélectionnez **Actualiser l’aperçu** pour afficher la première page. Faites
   défiler l’aperçu ou réglez son zoom de 50 % à 200 %.
6. Facultatif : choisissez un dossier de sortie. Sinon, chaque PDF est créé à
   côté de sa source Markdown.
7. Sélectionnez **Générer le PDF**.

L’application présente les collisions de sortie et les PDF existants avant la
conversion. Pendant un lot, elle affiche la progression et permet une
annulation sûre après le fichier en cours. En cas d’échec, le résultat précise
la source et l’erreur ; les autres fichiers indépendants continuent d’être
traités. Les actions **Ouvrir le PDF** et **Ouvrir le dossier** ne sont proposées
que pour les sorties réussies.

## Jetons d’en-tête et de pied de page

Le pied de page central par défaut est `Page {page} / {total}`. Un champ vide
n’affiche rien.

| Jeton | Valeur |
| --- | --- |
| `{titre}` ou `{title}` | Premier titre de niveau 1 (`#`) |
| `{date}` | Date UTC du rendu au format `AAAA-MM-JJ` (ou `--date`) |
| `{page}` | Numéro de la page courante |
| `{total}` | Nombre total de pages |

Vous pouvez associer du texte aux jetons, par exemple :

```text
{titre} — Page {page} / {total}
```

## Ligne de commande

Depuis les sources, utilisez `python -m libremark_pdf`. Avec un exécutable
construit en mode console, remplacez ce préfixe par le chemin de l’exécutable
(`LibreMarkPDF-cli.exe` sous Windows ou `LibreMarkPDF-cli` dans le dossier du
candidat Linux).

```bash
# Créer report.pdf à côté de report.md
python -m libremark_pdf convert report.md

# Choisir un fichier de sortie
python -m libremark_pdf convert report.md -o exported/report.pdf

# Convertir plusieurs fichiers dans un dossier
python -m libremark_pdf convert a.md b.md --out-dir exported --json

# Appliquer un CSS et une pagination personnalisés
python -m libremark_pdf convert report.md --css print.css \
  --footer-center "Page {page} / {total}"

# Choisir un thème local et une date fixe
python -m libremark_pdf convert report.md --theme default@1 \
  --date 2026-07-14 --json

# Vérifier les identités et ressources sans lancer Chromium
python -m libremark_pdf --version
python -m libremark_pdf doctor --json
```

La CLI ne pose aucune question. Le code de sortie `0` signifie que toutes les
conversions demandées ont réussi. Avec `--json`, stdout contient exactement un objet pour
un fichier ou un objet `{"results": [...]}` pour un lot. Chaque résultat contient
`input`, `output`, `status`, `error` et `error_code` ; une demande de conversion
valide indique aussi la date, le profil, son empreinte, le thème et les identités
Playwright/Chromium. Les erreurs destinées aux humains utilisent stderr. Le
schéma est décrit dans [`CLI_JSON_SCHEMA.json`](CLI_JSON_SCHEMA.json).

Pour afficher toutes les options :

```bash
python -m libremark_pdf convert --help
```

Gérez les thèmes locaux avec `theme list`, `theme show`, `theme install` et
`theme remove`. L’installation et le remplacement sont validés et atomiques.
`default@1` est le thème compatible immuable. L’ancienne option
`--render-date` reste un alias de `--date`.

## Préférence de langue

Sélectionnez **EN** ou **FR** dans la fenêtre. Le choix est enregistré localement
dans `~/.libremark-pdf/config.json`. Un échec d’enregistrement n’empêche pas la
conversion.

## Fichiers et sécurité

- Utilisez des fichiers Markdown encodés en UTF-8.
- Un CSS personnalisé s’applique à tout le document, mais ne peut pas utiliser
  de ressources `@import` ou `url(...)`.
- Un PDF existant est refusé sauf si l’appel CLI passe `--overwrite` ; le
  remplacement n’est publié qu’après un rendu réussi.
- Par défaut, le HTML brut est rendu comme texte. L’option de compatibilité CLI
  `--trusted-html` n’autorise qu’un sous-ensemble statique : jamais de scripts,
  gestionnaires d’événements, cadres, chargeurs de ressources ou URL réseau/
  `file:`.
- Les images Markdown doivent être des PNG, JPEG, GIF ou SVG statiques locaux
  approuvés ; elles sont validées et intégrées avant le rendu.
- Les paquets de thèmes doivent être locaux, hachés, accompagnés de leurs
  licences, compatibles avec `default@1` et dépourvus de scripts, d’URL
  distantes, de traversée de chemin et de ressources actives.
- Utilisez `--date AAAA-MM-JJ` pour rendre `{date}` reproductible ; sans
  cette option, la date UTC courante est utilisée.

## Résolution des problèmes

- **Un fichier déposé est ignoré :** vérifiez son extension `.md` ou
  `.markdown`.
- **L’aperçu échoue :** vérifiez l’installation de Chromium et de `pypdfium2`,
  puis consultez l’erreur complète dans la zone d’état.
- **Le CSS est introuvable :** choisissez un fichier `.css` existant ou
  rétablissez le style intégré.
- **L’application se ferme sous Windows :** lancez
  `dist\LibreMarkPDF\LibreMarkPDF-debug.exe` pour conserver le diagnostic.
- **Le candidat Linux ne démarre pas :** conservez tout son dossier
  `_internal`, lancez `LibreMarkPDF-debug` depuis un terminal et gardez la
  liste des bibliothèques manquantes produite par `ldd`. L’archive n’utilise
  pas FUSE, mais dépend toujours d’une glibc et de bibliothèques de bureau
  compatibles avec Chromium.
- **Un tableau revient à la ligne de manière inattendue :** le style par défaut
  utilise une mise en page fixe ; un contenu long peut augmenter la pagination.

Pour signaler un bug, conservez la commande exacte, le code de sortie, le texte
de l’erreur, le système d’exploitation, la version de Python et le mode
d’exécution (sources ou artefact). N’incluez pas de contenu confidentiel sans
nécessité.
