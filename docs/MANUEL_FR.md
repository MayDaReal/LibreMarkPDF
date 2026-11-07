# LibreMark PDF — Manuel utilisateur

LibreMark PDF convertit un ou plusieurs fichiers Markdown en PDF A4 mis en
forme, directement sur votre ordinateur. Il propose une interface graphique et
une ligne de commande non interactive.

> **Version préliminaire :** aucun téléchargement officiellement validé n’est
> encore publié. L’application actuelle doit être lancée depuis les sources ou
> construite localement.

La première version binaire `v0.1.0` prévue prend en charge Windows x64 et les
candidats Ubuntu 24.04 x86_64 validés. Cette portée ne constitue pas une
compatibilité Linux générale : les autres distributions, versions,
architectures, environnements de bureau et serveurs d’affichage restent hors
de la matrice de support. macOS est hors périmètre.

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
   autres lignes restent incluses dans le lot. Quelle que soit la largeur de
   la fenêtre, utilisez les boutons icône dossier, copie et poubelle pour
   afficher le dossier source, copier le chemin ou retirer le fichier.
   Lorsqu’une ligne a le focus, utilisez Haut/Bas pour vous
   déplacer, Entrée ou Espace pour activer son aperçu, Suppr pour la retirer,
   et Menu ou Maj+F10 pour ouvrir ses actions. La poubelle du bandeau retire
   directement tous les fichiers. L’ajout et le retrait sont indisponibles
   pendant la conversion, et le panneau Fichiers en indique la raison. Dans la
   disposition large à deux colonnes, faites glisser le séparateur entre le
   panneau gauche et l’aperçu depuis son minimum de 360 px jusqu’à la limite
   disponible qui conserve un aperçu utilisable ; cette valeur est conservée uniquement pendant la session.
   Les chemins parents longs sont élidés au milieu, tandis que leur valeur
   complète reste accessible dans l’infobulle et par **Copier le chemin**.
   Pour une largeur de fenêtre inférieure ou égale à 759 px, utilisez les
   onglets **Fichiers**, **Aperçu**, **Réglages** et **Résultats**. Un seul
   panneau est visible, l’onglet actif est mémorisé pendant la session et le
   redimensionnement ne vide ni les fichiers, ni la page ou le zoom de
   l’aperçu, ni les réglages, la conversion ou les résultats. La zone de
   génération et de progression reste fixe en bas.
3. Les quatre lignes **Réglages** résument toujours le style PDF, la
   destination, les en-têtes et pieds de page et les options avancées actifs.
   Les valeurs longues restent sur une ligne et leur valeur complète est
   disponible dans une infobulle. Sélectionnez la ligne **Style PDF** pour
   ouvrir son éditeur dédié. Choisissez un thème local validé, ou sélectionnez
   **CSS personnalisé** puis **Choisir un CSS**. Ces choix sont exclusifs, mais
   choisir un CSS n’oublie pas le thème sélectionné. Le brouillon actualise
   l’aperçu après 450 ms ; **Enregistrer** l’applique à la session, tandis que
   **Annuler**, Échap, la fermeture ou **Retour** en mode compact restaurent le
   style et l’aperçu précédents. Sélectionnez la ligne **Destination** pour
   ouvrir son éditeur dédié. Choisissez **Même dossier que chaque fichier
   source** ou **Dossier unique**, puis utilisez **Parcourir** pour sélectionner
   un chemin. Le chemin personnalisé complet reste sélectionnable et copiable ;
   les caractères Unicode et les espaces sont conservés. Le brouillon de
   destination n’actualise ni ne remplace jamais l’aperçu. **Enregistrer**
   applique la destination à la session ; **Annuler**, Échap, la fermeture ou
   **Retour** en mode compact la restaurent exactement. Sélectionnez **En-têtes
   et pieds de page** pour modifier les positions Gauche, Centre et Droite
   explicitement libellées. Un champ vide n’affiche rien. Sélectionnez
   `{titre}`, `{title}`, `{date}`, `{page}` ou `{total}` pour insérer la variable
   à la position du curseur dans le champ actif. Les changements du brouillon
   actualisent l’aperçu après 450 ms. **Rétablir les valeurs par défaut** demande
   confirmation uniquement si des valeurs personnalisées existent, ne modifie
   que ces six champs et restaure `Page {page} / {total}` dans le pied central.
   Enregistrer et Annuler suivent les mêmes règles de session et de restauration
   de l’aperçu que Style PDF. En mode compact, chaque éditeur dédié occupe
   l’onglet Réglages et garde Enregistrer visible. Les champs d’en-tête et de
   pied conservent leurs trois colonnes ; une barre de défilement verticale
   interne apparaît uniquement lorsque la hauteur restante ne permet pas
   d’afficher les variables et l’action de réinitialisation. Sélectionnez
   **Options avancées** pour ouvrir son éditeur dédié. Laissez la date de rendu
   vide pour utiliser
   automatiquement la date du jour, ou saisissez une valeur `AAAA-MM-JJ`
   valide. Une date incorrecte est signalée en ligne. L’activation du HTML
   statique de confiance demande confirmation la première fois de la session ;
   un refus laisse l’interrupteur désactivé. Les scripts, ressources distantes
   et contenus actifs restent bloqués. Le brouillon avancé actualise l’aperçu
   après 450 ms ; Enregistrer et Annuler suivent les mêmes règles exactes de
   session et de restauration de l’aperçu.
4. Facultatif : modifiez **En-têtes et pieds de page** comme décrit ci-dessus.
5. L’aperçu du fichier actif est actualisé après un court délai
   lorsqu’un réglage compatible change. L’ancienne image reste visible pendant
   la mise à jour et les états vide, mise à jour et indisponible sont indiqués
   explicitement. Le premier fichier ajouté à une liste vide s’ouvre en mode
   **Ajuster à la page**. La sélection d’un autre fichier d’aperçu, y compris
   celui sélectionné automatiquement après la suppression du fichier actif,
   revient à la page 1 en mode **Ajuster à la page**. L’ajout ou la suppression
   d’un autre fichier sans changer le fichier actif conserve la vue courante.
   Sélectionnez le bouton ↻, ou appuyez sur `Ctrl+R`, pour
   actualiser immédiatement et réinitialiser la vue sur **Ajuster à la page**.
   Utilisez **‹ Page n sur total ›** pour rasteriser chaque page depuis le même
   PDF temporaire d’aperçu, sans modifier le PDF final. Une nouvelle version du
   document revient à la page 1 ; le zoom conserve la page courante. Lorsque
   l’aperçu a le focus, les flèches Gauche et Droite changent de page.
   Utilisez **− 100 % +**, `Ctrl+-`, `Ctrl++` ou `Ctrl+0` pour régler le zoom de
   10 % à 200 % ; chaque action de zoom avant ou arrière le modifie de 2 points
   de pourcentage. **Ajuster à la page** utilise la largeur et la hauteur
   disponibles, tandis que **Ajuster à la largeur** utilise la largeur
   disponible. Ces deux actions redimensionnent l’image d’aperçu existante sans
   relancer le rendu du document ; redimensionner la fenêtre recalcule le mode
   d’ajustement actif, et un zoom manuel le quitte. Dans une fenêtre compacte,
   les deux actions d’ajustement se trouvent dans le menu de débordement de
   l’aperçu. Lorsque l’aperçu a le focus, la molette le fait défiler,
   `Maj+molette` le fait défiler horizontalement, `Ctrl+molette` zoome autour du
   pointeur et le glisser avec le bouton central déplace la page. Les barres de
   défilement n’apparaissent que si nécessaire. Une erreur d’aperçu peut être
   relancée, copiée ou ouverte dans le parcours local **Signaler un problème**
   et n’empêche pas de tenter une génération PDF valide.
6. Facultatif : modifiez **Destination** et choisissez **Dossier unique**.
   Sinon, chaque PDF est créé à côté de sa source Markdown.
   **Options avancées** contient la date de rendu et le HTML statique de
   confiance comme décrit ci-dessus.
7. Sélectionnez **Générer le PDF** pour un fichier, ou **Générer n PDF**
   pour un lot. Le libellé suit le nombre de fichiers sans abréviation de
   pluriel.

L’application présente les PDF existants et les collisions de sortie directement
dans la barre d’action fixe avant la conversion, sans fenêtre modale. **Retour**
précède le titre de la décision, comme dans les pages de réglages ; Échap produit
le même retour sûr. Le titre et les compteurs partagent une ligne. Les détails
indiquent chaque source, destination, problème court et décision de remplacement
dans un tableau compact. Cochez **Remplacer ?** pour chaque PDF existant qui peut
être remplacé après un rendu réussi ; les PDF non cochés sont conservés avec
un état neutre **Conservé**. La case du titre de colonne modifie toutes les lignes
éligibles et adopte un état intermédiaire pour une sélection mixte. Les lignes en
collision affichent **Bloqué** à la place d’une case et peuvent être signalées
pendant que les fichiers indépendants continuent. Un récapitulatif séparé indique
combien de PDF seront remplacés ou conservés ; le bouton **Continuer** reste fixe.
Survolez une cellule pour afficher sa valeur complète. La molette ne fait défiler
ce tableau que lorsqu’il a le focus ; sinon elle continue de faire défiler
l’interface principale.

Pendant la conversion, la barre indique la destination du lot, l’élément et le
fichier actifs. Le pourcentage numérique repose uniquement sur les fichiers
entièrement terminés, tandis qu’un segment animé et la phase exacte
**Préparation du document**, **Rendu avec Chromium**, **Finalisation du PDF** ou
**Publication sécurisée** montrent l’avancement du fichier actif. Chromium
imprime le PDF complet dans un seul appel bloquant ; aucun pourcentage par page
n’est donc annoncé. Le premier fichier peut être plus long pendant le démarrage
de Chromium et la préparation des ressources et polices locales. **Options
appliquées ⓘ** est un lien informatif, pas un réglage : survolez-le ou donnez-lui
le focus pour l’infobulle, ou activez-le pour garder ouvert un petit résumé non
modal. Il détaille dès le début de la conversion l’instantané immuable transmis
au moteur : style, destination complète, six valeurs d’en-tête/pied, mode de
date et HTML de confiance. La sélection des fichiers, l’aperçu existant (pages,
zoom, ajustement,
défilement et déplacement), les résumés des réglages et les résultats produits
restent consultables. Les mutations et le nouveau rendu de l’aperçu restent
verrouillés jusqu’à l’événement terminal.

**Arrêter après ce fichier** laisse finir le fichier courant et annule ceux qui
n’ont pas démarré. **Annuler maintenant** interrompt au prochain point sûr et
annule tout le reste. Un appel Chromium bloquant peut demander quelques secondes
pour rendre la main ; aucun PDF partiel n’est publié et un PDF de destination
préexistant est conservé. Fermer la fenêtre demande de
**Continuer la conversion** (choix sûr par défaut, également utilisé par Échap)
ou d’**Annuler la conversion et fermer** ; le fichier actif peut se terminer
avant l’annulation des fichiers restants. La liste finale conserve une ligne
par entrée dans l’ordre des sources, y compris les réussites, échecs,
conservations et annulations. Un PDF existant que l’utilisateur a explicitement
choisi de ne pas remplacer est **Conservé**, tandis qu’un refus d’écrasement
inattendu reste un échec. Dans les fenêtres normales et grandes, **Résultats** est un panneau
inférieur transversal de hauteur bornée, sous l’espace Fichiers/Réglages et
Aperçu. Vous pouvez le déployer, le replier ou faire glisser son séparateur
horizontal pour régler sa hauteur ; l’espace principal et la barre d’action
fixe restent disponibles. Réglages conserve une hauteur fixe et Fichiers
utilise toute la hauteur restante, jusqu’à son minimum. Le séparateur vertical permet d’agrandir la
zone de gauche jusqu’à la limite disponible tout en conservant un Aperçu
utilisable. Dans une fenêtre compacte, les mêmes résultats ordonnés utilisent
des cartes verticales condensées dans l’onglet **Résultats**, sans
défilement horizontal. À la fin d’un lot comportant une erreur, l’application
sélectionne automatiquement Résultats. Elle ne change jamais d’onglet pendant
la conversion et conserve l’onglet courant après un lot entièrement réussi.

Le bandeau place le résumé du lot à côté de **Résultats**. Sa poubelle efface
directement les résultats, comme dans la section Fichiers, et le chevron replie
ou déploie le panneau. Les actions des lignes utilisent
des icônes standard avec infobulles localisées et noms accessibles. Une
réussite propose **Ouvrir le PDF** et **Ouvrir le dossier**. Un échec propose
**Copier les détails**, le parcours existant **Signaler un problème** prérempli
avec le code d’erreur, et un bouton d’information direct pour déployer les détails. Une
annulation ne propose jamais d’action d’ouverture ; ses détails éventuels sont
également accessibles par le même bouton d’information. La cellule Sortie
affiche le message d’échec élidé lorsqu’aucun PDF n’a été produit. Les détails
déployés évitent de répéter ce message et affichent le code stable puis les
éventuelles informations techniques supplémentaires en police monospace ; ils restent
déployés pendant les mises à jour suivantes ou un changement de langue.
**Effacer les résultats** est disponible uniquement hors conversion, ne
supprime aucun PDF et restaure l’état prêt lorsque des fichiers sources restent
sélectionnés.

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

Dans une fenêtre compacte, ouvrez le menu image de l’application à côté du
nom du produit. Il contient **Manuel utilisateur**, **Raccourcis clavier**, le
sous-menu **Langue** avec le choix actif coché, **Signaler un problème** et **À
propos de LibreMark PDF**. Le logo, le nom du produit, le menu et les contrôles
natifs de fenêtre restent visibles à la largeur minimale de 560 px. La version
courante reste disponible dans **À propos de LibreMark PDF**.

Appuyez sur `F1` pour afficher les raccourcis clavier disponibles.
Ils sont présentés dans un tableau localisé à deux colonnes action/touche avec
une seule action **Fermer** et restent utilisables au clavier à la taille
minimale de la fenêtre.
**Aide → Manuel utilisateur** ouvre le PDF inclus correspondant à la langue
active dans l’application système. Depuis les sources, en l’absence d’un PDF
préparé, cette action ouvre à la place ce guide Markdown suivi par Git. Les
candidats génèrent le PDF avec LibreMark PDF lui-même et le fichier `style.css`
suivi à la racine ; le PDF généré n’est pas un fichier source suivi.

**À propos de LibreMark PDF** affiche les identités de l’application, du
profil de rendu, de Playwright, de Chromium, de Python, du système et de
l’architecture. **Copier les informations techniques** copie uniquement ces
valeurs : ni fichiers
sélectionnés, ni contenu des documents, ni chemins privés, variables
d’environnement ou journaux ne sont inclus, et rien n’est envoyé sur le
réseau. Le dialogue indique aussi que la conversion de Markdown en PDF est
locale et qu’aucune donnée n’est envoyée sur le réseau. Il identifie le mode
sources ou artefact uniquement lorsque l’application en cours peut le
déterminer de manière fiable.
**Mentions des composants tiers** ouvre le document local inclus dans
l’application système, sans contacter de service réseau.

**Aide → Signaler un problème** ouvre un rapport entièrement local et
modifiable. Décrivez le problème ; les étapes de reproduction et le résultat
attendu sont facultatifs. Si le dialogue est ouvert depuis l’échec d’un
fichier, son contexte et son code d’erreur sont préremplis sans remplir la
description utilisateur. **Inclure un diagnostic technique
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
