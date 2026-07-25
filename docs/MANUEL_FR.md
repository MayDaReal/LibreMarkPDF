# LibreMark PDF — Manuel utilisateur

LibreMark PDF convertit un ou plusieurs fichiers Markdown en PDF A4 mis en
forme, directement sur votre ordinateur. Il propose une interface graphique et
une ligne de commande non interactive.

> **Version préliminaire :** aucun téléchargement officiellement validé n’est
> encore publié. L’application actuelle doit être lancée depuis les sources ou
> construite localement.

Depuis un clone, lancez `bootstrap-windows.ps1` sous Windows ou
`bootstrap-linux.sh` sous Linux. Ces scripts préparent l’environnement Python
3.9 verrouillé et le navigateur Chromium local requis. Un clone partagé garde
les payloads natifs séparés dans `browser-win/` et `browser-linux/`. Sous
Windows, `bootstrap-windows.ps1 -InstallPython -InstallMake` peut installer
explicitement les outils recommandés manquants. Sous Linux, utilisez
`bootstrap-linux.sh --install-python --install-make`. Sans ces options, un
terminal interactif demande confirmation avant toute installation.
Sur Ubuntu 24.04 et les distributions qui ne proposent plus de paquet CPython
3.9 natif, installez d’abord CPython 3.9 avec pyenv ; le bootstrap Linux détecte
automatiquement une version pyenv `3.9.x` déjà installée.

## Utilisation de l’interface graphique

1. Ouvrez LibreMark PDF.
2. Sélectionnez **Ajouter des fichiers**, ou déposez des fichiers `.md` ou
   `.markdown` lorsque la prise en charge facultative du glisser-déposer est
   disponible. Sans celle-ci, la zone vide indique **Sélectionner des fichiers
   Markdown** et ouvre le sélecteur natif par un clic, Entrée ou Espace.
   Les fichiers valides conservent leur ordre d’ajout. Une sélection mixte
   ajoute quand même les fichiers valides et indique dans la zone d’état les
   nombres exacts d’ajouts, de doublons et d’éléments non pris en charge.
   Sélectionnez une ligne pour choisir le fichier d’aperçu actif sans modifier
   l’ordre du lot. La ligne active porte le badge **Aperçu actif** ; toutes les
   autres lignes restent incluses dans le lot. Le menu **Actions** de chaque
   ligne permet d’afficher le dossier source, de copier le chemin ou de retirer
   le fichier. Lorsqu’une ligne a le focus, utilisez Haut/Bas pour vous
   déplacer, Entrée ou Espace pour activer son aperçu, Suppr pour la retirer,
   et Menu ou Maj+F10 pour ouvrir ses actions. L’ajout et le retrait sont
   indisponibles pendant la conversion, et le panneau Fichiers en indique la
   raison. Dans la disposition large à deux colonnes, faites glisser le
   séparateur entre le panneau gauche et l’aperçu pour régler sa largeur de
   360 à 440 px ; cette valeur est conservée uniquement pendant la session.
   Les chemins parents longs sont élidés au milieu, tandis que leur valeur
   complète reste accessible dans l’infobulle et par **Copier le chemin**.
3. Facultatif : ouvrez **Style PDF** et choisissez un thème local validé, ou
   sélectionnez **CSS personnalisé** puis **Choisir un CSS**. Ces choix sont
   incompatibles ; **Revenir au thème sélectionné** retire le CSS personnel
   sans oublier le thème choisi pour cette session.
4. Facultatif : ouvrez **En-têtes et pieds de page** et modifiez les positions
   Gauche, Centre et Droite explicitement libellées. **Rétablir les valeurs par
   défaut** ne modifie que ces six champs et restaure le pied central par défaut.
5. L’aperçu du fichier actif est actualisé après un court délai
   lorsqu’un réglage compatible change. L’ancienne image reste visible pendant
   la mise à jour et les états vide, mise à jour et indisponible sont indiqués
   explicitement. Sélectionnez le bouton ↻ pour actualiser immédiatement.
   Utilisez **‹ Page n sur total ›** pour rasteriser chaque page depuis le même
   PDF temporaire d’aperçu, sans modifier le PDF final. Une nouvelle version du
   document revient à la page 1 ; le zoom conserve la page courante. Lorsque
   l’aperçu a le focus, les flèches Gauche et Droite changent de page.
   Utilisez **− 100 % +**, `Ctrl+-`, `Ctrl++` ou `Ctrl+0` pour régler le zoom de
   50 % à 200 %. Lorsque l’aperçu a le focus, la molette le fait défiler,
   `Ctrl+molette` zoome autour du pointeur et le glisser avec le bouton central
   déplace la page. Les barres de défilement n’apparaissent que si nécessaire.
   Une erreur d’aperçu peut être relancée ou copiée et n’empêche pas de tenter
   une génération PDF valide.
6. Facultatif : ouvrez **Destination** et choisissez un dossier de sortie.
   Sinon, chaque PDF est créé à côté de sa source Markdown.
   **Autres options avancées** contient la date de rendu et le HTML statique de
   confiance. Son activation demande une confirmation lors de sa première
   utilisation dans chaque session de l’application.
7. Sélectionnez **Générer le PDF** pour un fichier, ou **Générer n PDF**
   pour un lot. Le libellé suit le nombre de fichiers sans abréviation de
   pluriel.

L’application présente les collisions de sortie et les PDF existants avant la
conversion. Les choix sont explicites : une collision peut être ignorée pendant
que les fichiers indépendants continuent, et un PDF existant peut être remplacé
uniquement après un rendu réussi ou conservé et signalé comme un échec. Pendant
un lot, la barre d’action persistante indique la progression et permet une
annulation sûre après le fichier en cours. Fermer la fenêtre demande de
**Continuer la conversion** (choix sûr par défaut, également utilisé par Échap)
ou d’**Annuler la conversion et fermer** ; le fichier actif peut se terminer
avant l’annulation des fichiers restants. La liste finale conserve une ligne
par entrée dans l’ordre des sources, y compris les réussites, échecs et
annulations. Les codes d’erreur peuvent être dépliés et copiés. Les actions
**Ouvrir le PDF** et **Ouvrir le dossier** ne sont proposées que pour les
sorties réussies.

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

Utilisez le menu de langue de l’en-tête fixe et sélectionnez **Français** ou
**English**. Le choix coché est enregistré localement dans
`~/.libremark-pdf/config.json`. Un échec d’enregistrement n’empêche pas la
conversion. Le changement de langue retraduit immédiatement les libellés
visibles et leurs noms accessibles sans vider les fichiers sélectionnés, le
fichier d’aperçu actif ni les réglages PDF.

Appuyez sur `F1` pour afficher les raccourcis clavier disponibles.
**Aide → Manuel utilisateur** ouvre ce guide local dans l’application système.

La version compacte à côté du nom LibreMark PDF ouvre **À propos de LibreMark
PDF**. Le même dialogue est disponible par **Aide → À propos de LibreMark
PDF**. Il affiche les identités de l’application, du profil de rendu, de
Playwright, de Chromium, de Python, du système et de l’architecture. **Copier
les informations techniques** copie uniquement ces valeurs : ni fichiers
sélectionnés, ni contenu des documents, ni chemins privés, variables
d’environnement ou journaux ne sont inclus, et rien n’est envoyé sur le
réseau.

**Aide → Signaler un problème** ouvre un rapport entièrement local et
modifiable. Décrivez le problème ; les étapes de reproduction et le résultat
attendu sont facultatifs. Si le dialogue est ouvert depuis l’échec d’un
fichier, son code d’erreur est prérempli. **Inclure un diagnostic technique
anonymisé** est décoché par défaut. Une fois activé, il ajoute les identités de
l’application et du moteur, le système, la présence des ressources,
l’identifiant du thème sélectionné, le nombre de fichiers, l’état du
glisser-déposer et une erreur anonymisée. Il n’ajoute jamais les noms ou
chemins des fichiers sélectionnés, les contenus Markdown, PDF, HTML ou CSS, les
noms de compte ou de machine, les variables d’environnement, le presse-papiers
ou les journaux globaux. Vérifiez et modifiez le rapport complet avant
d’utiliser **Copier le rapport** ou **Enregistrer le rapport…**. Rien n’est
téléversé ni envoyé.

Aucune page d’assistance officielle n’est configurée dans cette version : le
dialogue affiche donc des instructions hors ligne au lieu d’inventer un lien.
Copiez ou enregistrez le rapport vérifié et ne le partagez que par un canal
officiel auquel vous faites confiance. Relisez-le vous-même avant tout partage :
la suppression automatique des chemins est une protection, pas un remplacement
de cette vérification.

## Fichiers et sécurité

- Utilisez des fichiers Markdown encodés en UTF-8.
- Un CSS personnalisé s’applique à tout le document, mais ne peut pas utiliser
  de ressources `@import` ou `url(...)`.
- Un PDF existant est refusé sauf si l’appel CLI passe `--overwrite` ; le
  remplacement n’est publié qu’après un rendu réussi.
- Par défaut, le HTML brut est rendu comme texte. **Autres options avancées**
  dans l’interface et l’option de compatibilité CLI `--trusted-html`
  autorisent le même sous-ensemble statique : jamais de scripts, gestionnaires
  d’événements, cadres, chargeurs de ressources ou URL réseau/`file:`.
  L’interface demande une confirmation à la première activation de chaque
  session.
- Les images Markdown doivent être des PNG, JPEG, GIF ou SVG statiques locaux
  approuvés ; elles sont validées et intégrées avant le rendu.
- Les paquets de thèmes doivent être locaux, hachés, accompagnés de leurs
  licences, compatibles avec `default@1` et dépourvus de scripts, d’URL
  distantes, de traversée de chemin et de ressources actives.
- Utilisez `--date AAAA-MM-JJ` pour rendre `{date}` reproductible ; sans
  cette option, la date UTC courante est utilisée.

## Résolution des problèmes

- **Un élément sélectionné ou déposé est ignoré :** consultez les comptes non
  modaux dans la zone d’état. Seuls les fichiers `.md` et `.markdown` sont pris
  en charge ; un fichier déjà présent dans la liste est traité comme doublon.
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
