# Spécification UX/UI cible — LibreMark PDF Desktop

## 1. Résumé exécutif

L’IHM cible conserve intégralement les capacités actuelles, mais réorganise le
parcours autour de trois priorités visibles en permanence :

1. les fichiers à convertir ;
2. l’aperçu du fichier actif ;
3. l’état de la conversion et l’action principale.

La proposition remplace la longue colonne de cadres par :

- une barre supérieure compacte : identité, version, langue et aide ;
- un espace de travail redimensionnable : préparation à gauche, aperçu à
  droite ;
- une barre d’action persistante : destination, état, progression, annulation
  et génération ;
- des réglages avancés repliés par défaut ;
- des résultats persistants par fichier, au lieu de limiter les erreurs à une
  boîte de dialogue.

À la taille actuelle par défaut de 820×780, la destination et la génération
sont entièrement sous la ligne de flottaison. C’est la friction prioritaire à
corriger. La cible adopte une taille initiale de référence de 1060×720, ajustée
à l’espace de travail disponible, et garantit à toutes les tailles que le
bouton **⚙ Générer** et sa barre de progression restent visibles hors de la
zone défilante. Elle permet de sélectionner un fichier puis de générer son PDF
en deux actions, tout en gardant les thèmes, le CSS, les six champs
d’en-tête/pied de page, la date, le HTML statique de confiance, l’aperçu, le
zoom, les lots et l’annulation.

Aucun changement de moteur, profil, rendu PDF, CSS par défaut, pagination,
marges, polices ou sécurité n’est proposé.

## 2. Hypothèses et périmètre

### Sources analysées

L’analyse s’appuie sur :

- `README.md` ;
- `docs/MANUAL_EN.md` et `docs/MANUEL_FR.md` ;
- la façade `libremark_pdf/gui.py` ;
- les modules Tk `libremark_pdf/desktop/tk/layout.py`, `inputs.py`,
  `preview.py` et `conversion.py` ;
- les traductions `libremark_pdf/i18n.py` ;
- `tests/test_gui.py`, `tests/test_i18n.py` et
  `tests/test_desktop_services.py` ;
- `SUPPORT.md` ;
- une capture locale de l’état initial obtenue depuis l’IHM du dépôt à
  820×780.

La capture annoncée comme « fournie » dans le brief n’était pas accessible
comme pièce jointe. Les constats visuels ci-dessous proviennent donc de la
capture locale et de la structure Tk effectivement exécutée.

### Périmètre

Inclus :

- modernisation visuelle et réorganisation de l’IHM desktop Tk ;
- comportements responsives jusqu’à la taille minimale actuelle 560×520 ;
- hiérarchie, navigation clavier, états et retours d’erreur ;
- affichage de la version ;
- signalement local et respectueux de la vie privée ;
- préparation conceptuelle à de petits écrans.

Exclus :

- implémentation ;
- application Android ;
- modification du moteur Chromium ou des rendus PDF ;
- ajout automatique d’un service, compte, serveur ou télémétrie ;
- installation ou gestion de thèmes depuis l’IHM ;
- mode sombre de l’application ;
- personnalisation de la palette de l’application en version 1.

### Contrats observés à préserver

- fenêtre actuelle : 820×780, minimum 560×520 ;
- `.md` et `.markdown`, sans doublons dans la liste ;
- glisser-déposer optionnel, import et lancement possibles sans
  `tkinterdnd2` ;
- premier fichier actuellement utilisé pour l’aperçu ;
- niveaux de zoom : 50, 75, 100, 125, 150 et 200 % ;
- actualisation explicite et actualisations automatiques temporisées après
  certains changements ;
- aperçu exécuté hors du thread Tk, demandes intermédiaires regroupées et
  réponses obsolètes ignorées ;
- lot poursuivi après l’échec d’un fichier ;
- collisions contrôlées avant écrasements existants ;
- remplacement seulement après rendu réussi ;
- annulation après le fichier en cours ;
- boutons d’ouverture uniquement pour les sorties réussies ;
- EN et FR avec mêmes clés et mêmes placeholders ;
- préférence de langue locale et non bloquante.

### Divergences existantes à résoudre

- La documentation présente le « HTML statique de confiance » comme une option
  CLI, mais l’IHM expose déjà une case correspondante. La cible la conserve
  dans les réglages avancés, conformément à l’exigence de non-suppression, en
  synchronisant les manuels avec ce comportement.
- Les manuels décrivent principalement « Actualiser l’aperçu », alors que
  l’IHM déclenche aussi automatiquement un aperçu après plusieurs changements.
  La cible conserve les deux comportements et demande de documenter
  l’actualisation automatique.
- L’aide sur les jetons n’affiche que `{titre}`, alors que `{title}` est
  également supporté.

## 3. Audit de l’IHM actuelle

Échelle de gravité : critique, élevée, moyenne, faible.

| ID | Gravité | Utilisateur | Preuve observée | Conséquence | Recommandation |
| --- | --- | --- | --- | --- | --- |
| A1 | Critique | Tous | À 820×780, l’aperçu commence vers le bas de l’écran ; destination, génération, progression et résultats sont sous la ligne de flottaison. | L’objectif principal n’est pas visible. L’utilisateur doit parcourir l’écran sans savoir où terminer. | Barre de génération et d’état persistante, indépendante du défilement. |
| A2 | Élevée | Tous, surtout nouveaux | Tous les sujets utilisent des `LabelFrame` de poids visuel proche : fichiers, thèmes, avancé, aperçu, sortie. | Absence de hiérarchie entre indispensable, facultatif et avancé. | Deux zones de travail et divulgation progressive ; supprimer les cadres décoratifs imbriqués. |
| A3 | Élevée | Nouveau | Le bloc fichiers réserve une zone de dépôt, une rangée d’actions et une liste haute de 96 px même vide. | Beaucoup d’espace est consommé avant toute valeur produite. | Grand état vide, puis barre d’ajout compacte et liste dimensionnée au contenu. |
| A4 | Élevée | Installation sans `tkinterdnd2` | Le texte continue d’annoncer le dépôt même lorsque le support DnD n’est pas chargé. La zone reste cliquable pour parcourir. | Promesse trompeuse ; un dépôt peut ne produire aucun effet ni explication. | Libellé fondé sur la capacité réelle : dépôt + parcours si disponible, parcours seul sinon. |
| A5 | Élevée | Tous | Les extensions non valides et doublons sont simplement ignorés dans `_add_files`. | L’utilisateur ne sait pas pourquoi un dépôt semble incomplet. | Retour non modal : nombre ajouté, doublons ignorés et fichiers non pris en charge. |
| A6 | Moyenne | Lot | L’aperçu utilise toujours `self.files[0]`; aucun fichier actif n’est indiqué. | Ambiguïté sur le document prévisualisé. | Rendre une ligne sélectionnable ; identifier le fichier, la page courante et le total. |
| A7 | Élevée | Nouveau | Le canevas d’aperçu est vide et gris au démarrage ; le contenu d’exemple n’est rendu que sur actualisation explicite. | Le vide peut être interprété comme un échec. | État d’aperçu explicite, illustré uniquement par des formes simples et du texte. |
| A8 | Moyenne | Tous | Le titre affiche seulement « Aperçu » et le moteur d’aperçu ne rasterise que la première page. | L’utilisateur ne peut pas vérifier la pagination, les pages suivantes ou leurs en-têtes et pieds. | Navigation multipage à la demande depuis le même PDF d’aperçu, avec page courante et total explicites. |
| A9 | Élevée | Tous | Le bouton Générer est désactivé pendant l’aperçu automatique, sans explication près du bouton. | Une modification peut bloquer brièvement l’action principale et sembler défectueuse. | Afficher « Mise à jour de l’aperçu… » sans masquer l’action ; ne bloquer la génération que pendant la validation nécessaire. |
| A10 | Critique | Lot avec erreur | Après conversion, seuls les succès sont rendus dans la zone de résultats ; les échecs apparaissent dans une boîte modale technique. | Les erreurs ne restent pas consultables par fichier et sont difficiles à corriger. | Liste de résultats persistante pour succès, échec et annulation, avec détail repliable. |
| A11 | Élevée | Tous | L’état et les erreurs en ligne sont sous le bouton et donc hors écran. Les erreurs utilisent aussi des modales. | Feedback tardif ou invisible, particulièrement durant un lot. | État et progression dans la barre persistante ; notifications en ligne proches de leur cause. |
| A12 | Élevée | Utilisateur des options avancées | Les trois champs d’en-tête et trois champs de pied n’ont aucun libellé individuel visible. Les chaînes « Gauche/Centre/Droite » existent mais ne sont pas appliquées. | Positions indéterminables, ordre mémoriel imposé. | Libellés ou intitulés accessibles pour chaque position ; disposition 3 colonnes ou empilée selon largeur. |
| A13 | Élevée | Utilisateur avancé | Le titre du cadre et le bouton répètent tous deux l’idée d’options avancées ; le bouton dit « afficher ou masquer ». | Texte long, peu orienté action, état difficile à lire. | Un seul accordéon nommé « En-têtes et pieds de page », chevron et état exposé. |
| A14 | Critique | Utilisateur du HTML de confiance | Case à cocher sensible sans explication, alors que la documentation la présente comme CLI uniquement. | Mauvaise compréhension du risque et divergence de contrat. | Conserver sous « Sécurité avancée », avec aide courte et confirmation au premier usage ; arbitrage documentaire obligatoire. |
| A15 | Élevée | Thèmes/CSS | Thème et CSS sont affichés côte à côte. « Utiliser le thème sélectionné » sert à réinitialiser le CSS. | L’exclusivité est technique plutôt qu’expliquée ; le sens du bouton est incertain. | Une section « Style PDF » affichant un choix exclusif : thème local ou CSS personnalisé. |
| A16 | Moyenne | Chemins longs, FR | Les chemins sont présentés dans des champs en lecture seule sur une ligne, sans stratégie visible d’élision ni détail. | Débordement et difficulté à distinguer deux chemins similaires. | Nom principal + chemin parent élidé ; chemin complet au focus, infobulle ou copie. |
| A17 | Élevée | Petite fenêtre | Un canevas global scrollable contient un canevas de liste et un canevas d’aperçu, chacun avec son propre défilement. | Conflit de molette et difficulté à savoir quelle zone défile. | Un seul défilement de contenu ; aperçu dans un panneau autonome clairement focalisable. |
| A18 | Moyenne | Clavier et technologies d’assistance | Raccourcis présents mais non découvrables ; peu de raccourcis mnémotechniques ; focus de canevas peu explicite. | Le clavier fonctionne partiellement sans être prévisible. | Menu/aide des raccourcis, ordre de tabulation défini, libellés accessibles et focus très visible. |
| A19 | Moyenne | Linux et pavé tactile | Le gestionnaire global dépend de `<MouseWheel>` et de `event.delta`; aucun comportement Linux bouton 4/5 n’est visible. | Défilement potentiellement incohérent selon plateforme. | Caractériser Windows/Linux et lier les événements par plateforme sans capturer la molette hors zone. |
| A20 | Moyenne | EN/FR | Formes `file(s)`, `fichier(s)`, `PDF(s)` et textes de confirmation très longs ; `{title}` absent de l’aide. | Français peu naturel et risques de coupure. | Clés singulier/pluriel séparées ; phrases courtes ; placeholders identiques. |
| A21 | Élevée | Tous | Version absente de la fenêtre ; aucune entrée de support. | Impossible d’identifier facilement le build ou de produire un rapport utile. | `v1.0.0` discret dans la barre supérieure, dialogue À propos, menu Aide et rapport local. |
| A22 | Élevée | Écrasement/collision | Les choix reposent sur Oui/Non/Annuler avec une explication longue de leur sens. | Risque de choisir « Non » sans comprendre que certains éléments deviendront des échecs. | Dialogue avec boutons nommés : Remplacer, Conserver et signaler, Annuler. |
| A23 | Faible | Langue | EN et FR sont deux boutons identiques sans état sélectionné manifeste. | La langue active n’est pas immédiatement identifiable. | Contrôle segmenté ou menu avec état sélectionné et nom accessible. |
| A24 | Moyenne | Haute densité | Police et couleurs sont essentiellement celles de Tk, avec couleurs fixes sur les canevas. | Aspect daté, contraste dépendant de la plateforme, peu de distinction des niveaux. | Styles `ttk` centralisés, couleurs sémantiques et respect des couleurs système. |

### Éléments qui doivent rester visibles ou immédiatement accessibles

Toujours visibles :

- nombre de fichiers ;
- fichier actif pour l’aperçu ;
- destination résumée ;
- action Générer ;
- état global et progression ;
- Annuler pendant une conversion ;
- accès à la langue, à la version et à l’aide.

Accessibles en une action :

- ajout et suppression de fichiers ;
- style PDF courant ;
- changement de destination ;
- affichage de l’aperçu ;
- réglages avancés ;
- résultats et erreurs par fichier.

## 4. Principes UX retenus

1. **Deux actions pour le cas simple.** Ajouter un fichier, puis générer. Le
   style et la destination par défaut restent explicites mais ne réclament
   aucune confirmation.
2. **Progression du simple vers l’expert.** Fichiers et aperçu d’abord ; style,
   destination et options avancées ensuite.
3. **Action et état persistants.** La génération, l’annulation et le retour
   d’état ne disparaissent jamais au défilement. Le bouton **⚙ Générer** et la
   barre de progression restent présents, y compris lorsque la génération est
   momentanément indisponible ou en cours.
4. **Une cause, un retour local.** Fichier ignoré près de la liste, CSS invalide
   près du style, erreur de rendu sur la ligne du fichier.
5. **Le lot est une liste de tâches.** Chaque fichier possède un état durable :
   prêt, actif, réussi, échoué ou annulé.
6. **L’aperçu est informatif, pas bloquant.** Son indisponibilité ne doit pas
   être confondue avec une impossibilité certaine de convertir.
7. **Aucun réseau implicite.** Copier et enregistrer un rapport sont les
   capacités de base ; ouvrir un canal externe est une option configurée.
8. **Adaptation par priorité, pas par réduction uniforme.** En espace étroit,
   les réglages se replient et l’aperçu devient une section ; l’action
   principale reste fixe.
9. **Texte bref, sens accessible.** Une icône immédiatement reconnaissable
   peut être utilisée seule ; l’action principale et les actions ambiguës
   conservent un texte. Toutes les icônes ont un nom accessible et une
   infobulle ; la couleur n’est jamais le seul indicateur.
10. **Tk progressif.** Styles `ttk`, `PanedWindow`, cadres, dialogues et
    composants existants suffisent ; aucune nouvelle dépendance n’est requise.

## 5. Parcours utilisateurs cibles

### 5.1 Convertir un seul fichier — parcours par défaut

1. Au démarrage, le focus est sur **Ajouter des fichiers**.
2. L’utilisateur sélectionne un Markdown ou clique/dépose dans la zone vide.
3. Le fichier apparaît, devient actif et déclenche l’aperçu temporisé.
4. La barre inférieure indique `1 fichier`, `À côté du fichier source` et
   **⚙ Générer le PDF**, avec une progression à zéro.
5. L’utilisateur sélectionne **⚙ Générer le PDF**.
6. Le précontrôle vérifie destination, options et sortie existante.
7. La progression avance, **⚙ Générer le PDF** reste visible mais désactivé et
   **Annuler après ce fichier** apparaît.
8. À la fin, la ligne passe à **Réussi** et propose **Ouvrir le PDF** et
   **Ouvrir le dossier**.

### 5.2 Convertir plusieurs fichiers

1. L’utilisateur sélectionne plusieurs fichiers en une fois ou en ajoute.
2. La liste indique le compte et conserve l’ordre d’ajout.
3. Le premier fichier devient actif ; cliquer une autre ligne change seulement
   l’aperçu.
4. **⚙ Générer 4 PDF** lance le précontrôle du lot.
5. Les collisions sont présentées avant les sorties existantes.
6. Durant la conversion, l’IHM affiche `2 sur 4`, le fichier actif et les
   résultats déjà terminés.
7. Une erreur marque uniquement le fichier concerné ; le lot continue.
8. Le résumé final indique réussites, échecs et annulations, sans effacer les
   détails.

### 5.3 Glisser-déposer

Avec `tkinterdnd2` :

1. Le survol valide affiche une bordure accentuée et **Déposer pour ajouter**.
2. Un dépôt valide ajoute les fichiers.
3. Les éléments non pris en charge ou déjà présents sont récapitulés dans un
   message non modal.
4. Le focus passe à la première nouvelle ligne.

Sans `tkinterdnd2` :

1. Aucun texte ne promet le dépôt.
2. La zone affiche **Sélectionner des fichiers Markdown**.
3. Clic, Entrée ou Espace ouvre le sélecteur natif.
4. Le reste du parcours est identique.

### 5.4 Changer de thème ou fournir un CSS

1. L’utilisateur ouvre **Style PDF**.
2. Deux options exclusives sont proposées : **Thème local** et
   **CSS personnalisé**.
3. Choisir un CSS désactive visuellement le thème sans perdre la sélection
   mémorisée pour la session.
4. **Revenir au thème** retire le CSS et réactive le thème sélectionné.
5. L’aperçu se met à jour après 450 ms.
6. Une erreur CSS est affichée dans cette section et dans l’état de l’aperçu.

### 5.5 Configurer les options avancées

1. L’utilisateur ouvre **En-têtes et pieds de page**.
2. Les champs Gauche, Centre et Droite sont explicitement libellés.
3. Les jetons autorisés sont affichés dans une aide repliable.
4. La date de rendu et le HTML statique de confiance sont placés dans
   **Autres options avancées**.
5. Une date invalide produit une erreur en ligne.
6. Le HTML de confiance présente une explication et, au premier passage à
   l’état actif, une confirmation.

### 5.6 Consulter, actualiser et zoomer l’aperçu

1. La sélection d’un fichier déclenche son aperçu et affiche sa première page.
2. Le titre identifie le fichier et indique `Page 1 sur n`.
3. Les modifications compatibles déclenchent une actualisation temporisée ;
   seule la demande la plus récente est conservée.
4. **Actualiser** force immédiatement la demande courante.
5. Les commandes suivent l’ordre `− 100 % +`.
6. À 50 ou 200 %, le bouton correspondant est désactivé.
7. `Ctrl+-`, `Ctrl++` et `Ctrl+0` règlent le zoom.
8. Lorsque l’aperçu a le focus, la molette défile, `Ctrl+molette` zoome autour
   du pointeur et le glisser avec le bouton central déplace la page.
9. Les boutons `‹` et `›` rendent la page précédente ou suivante à la demande,
   sans relancer la conversion finale ; ils sont désactivés aux bornes.
10. Les barres de défilement ne sont visibles que lorsque nécessaires.

### 5.7 Choisir une destination

1. Le résumé par défaut indique **À côté de chaque source**.
2. **Changer** ouvre le sélecteur de dossier.
3. Le chemin choisi est élidé au centre mais copiable et exposé intégralement
   au focus ou via infobulle.
4. **Utiliser les dossiers sources** rétablit le comportement par défaut.
5. Le changement de destination ne déclenche pas de nouvel aperçu.

### 5.8 Suivre, gérer une erreur et annuler

- La barre persistante montre le fichier actif, `n sur total` et la progression.
- **Annuler après ce fichier** pose l’événement d’annulation une seule fois,
  désactive le bouton et annonce l’attente.
- Les fichiers non commencés passent à **Annulé**.
- Une erreur par fichier affiche un résumé, un code technique repliable,
  **Copier les détails** et l’accès au signalement.
- Une erreur globale conserve la liste et ne transforme pas les succès en
  échecs.
- Fermer la fenêtre pendant une génération ouvre une confirmation bloquante.
  **Continuer la conversion** est l’action sûre par défaut. **Annuler la
  conversion et fermer** précise que le fichier actif peut terminer son
  traitement et que les fichiers restants seront annulés. Fermer le dialogue
  ou appuyer sur `Échap` poursuit la conversion.

### 5.9 Signaler un problème

1. L’utilisateur ouvre **Aide → Signaler un problème** ou l’action depuis une
   erreur.
2. Un dialogue demande un résumé et des étapes facultatives.
3. L’ajout du diagnostic est optionnel, décoché par défaut et expliqué.
4. Le rapport complet est prévisualisable et modifiable.
5. L’utilisateur peut le copier, l’enregistrer localement ou ouvrir un canal de
   support configuré.
6. Rien n’est envoyé automatiquement.

### 5.10 Changer la langue

1. L’utilisateur ouvre le contrôle `EN` ou `FR`.
2. L’interface est retraduite sans perdre fichiers ni réglages.
3. La préférence est enregistrée localement en mode best effort.
4. Un échec d’enregistrement ne bloque pas la conversion et ne nécessite pas de
   modal.

### 5.11 Consulter la version

1. `v1.0.0` est visible dans la barre supérieure.
2. Un clic ouvre **À propos de LibreMark PDF**.
3. Le dialogue affiche les identités techniques disponibles.
4. **Copier les informations techniques** copie un contenu sans chemins privés.

### États transversaux

| État | Présentation et comportement |
| --- | --- |
| Vide | Zone d’ajout dominante, réglages résumés, aperçu avec instruction ; génération désactivée avec raison accessible. |
| Chargement d’aperçu | Indicateur non bloquant, ancien aperçu conservé avec voile léger et libellé « Mise à jour… ». |
| Absence d’aperçu | Message neutre : ajouter ou sélectionner un fichier. |
| Erreur d’aperçu | Message en ligne, Réessayer, Copier les détails ; génération disponible si les options sont valides. |
| Prêt | Compte, destination, progression à zéro et génération visibles. |
| Conversion | Contrôles de réglage verrouillés, progression déterminée, annulation disponible et bouton Générer visible mais désactivé. |
| Succès | Résumé vert accompagné d’une coche et actions sur chaque sortie. |
| Erreur partielle | Résumé ambre/rouge, lignes réussies conservées, détails par fichier. |
| Annulation demandée | Bouton désactivé, texte indiquant que le fichier courant se termine. |
| Annulé | Fichiers non commencés marqués comme annulés, résultats terminés conservés. |

## 6. Architecture de l’information

### Barre supérieure persistante

Ordre de gauche à droite :

1. logo ;
2. **LibreMark PDF** ;
3. version compacte ;
4. espace flexible ;
5. langue active ;
6. menu **Aide**.

La barre ne porte ni réglage PDF ni action de conversion.

### Zone de préparation

Ordre de lecture :

1. fichiers et ajout ;
2. style PDF ;
3. destination ;
4. réglages avancés.

Les trois dernières sections affichent toujours un résumé sur une ligne. Leur
contenu détaillé est repliable.

### Zone d’aperçu

- fichier actif ;
- pagination `‹ Page n sur total ›` ;
- actualisation, zoom et panoramique ;
- canevas ou état vide/erreur ;
- séparateur redimensionnable en disposition large ou moyenne.

### Barre d’action persistante

- à gauche : état ou résumé final et barre de progression toujours visible ;
- au centre : destination résumée lorsque l’espace le permet ;
- à droite : bouton primaire **⚙ Générer** toujours visible ; pendant une
  conversion il est désactivé et **Annuler après ce fichier** apparaît à ses
  côtés.

La barre n’appartient jamais au contenu défilant. En l’absence de conversion,
la progression reste à zéro avec l’état **Prêt**. Pendant une conversion, elle
indique l’avancement du lot. Après la conversion, elle reste remplie et
accompagne le résumé final jusqu’au prochain lot ou changement de liste.

### Priorités lorsque l’espace manque

1. Générer/Annuler et état global ;
2. ajout et compte de fichiers ;
3. destination ;
4. sélection du fichier d’aperçu ;
5. aperçu ;
6. style PDF ;
7. réglages avancés ;
8. détails techniques.

La version reste visible sous forme compacte ; le reste des informations
techniques demeure dans le dialogue À propos.

### Aperçu indisponible

Le panneau reste présent afin d’éviter un changement brutal de layout. Il
montre :

- le motif de l’indisponibilité ;
- **Réessayer** ;
- **Copier les détails** ;
- une indication explicite si la conversion peut toujours être tentée.

## 7. Wireframes et responsive

### 7.1 Large — largeur ≥ 1100 px

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [logo] LibreMark PDF  v1.0.0                          [FR ▾] [Aide ▾]        │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ Fichiers                 3    │ Aperçu — rapport.md          ‹ Page 1/12 ›   │
│ ┌───────────────────────────┐ │                              [↻] [− 100% +] │
│ │ + Ajouter des fichiers    │ │ ┌──────────────────────────────────────────┐ │
│ ├───────────────────────────┤ │ │                                          │ │
│ │ ● rapport.md         [×]  │ │ │               page A4                    │ │
│ │   notes.md           [×]  │ │ │                                          │ │
│ │   annexe.md          [×]  │ │ └──────────────────────────────────────────┘ │
│ └───────────────────────────┘ │                                              │
│                               │                                              │
│ Style PDF                     │                                              │
│ Thème Default            [›]  │                                              │
│                               │                                              │
│ Destination                   │                                              │
│ À côté de chaque source  [›]  │                                              │
│                               │                                              │
│ En-têtes et pieds        [›]  │                                              │
│ Autres options avancées  [›]  │                                              │
├───────────────────────────────┴──────────────────────────────────────────────┤
│ Prêt · 3 fichiers · À côté des sources          [⚙ Générer 3 PDF]           │
│ [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0/3          │
└──────────────────────────────────────────────────────────────────────────────┘
```

Règles :

- `ttk.PanedWindow` horizontal ;
- panneau gauche : minimum 360 px, cible 38 % ;
- aperçu : minimum 480 px ;
- séparateur utilisable au clavier si le toolkit le permet, sinon ratio
  recalculé au redimensionnement ;
- barre inférieure hors défilement : 72 px cible, 88 px maximum hors
  résultats détaillés.

### 7.2 Moyen — 760 à 1099 px

```text
┌──────────────────────────────────────────────────────────────────┐
│ [logo] LibreMark PDF v1.0.0                   [FR] [Aide]        │
├────────────────────────┬─────────────────────────────────────────┤
│ Fichiers            3  │ rapport.md · ‹ Page 1/12 ›             │
│ [+ Ajouter]             │                         [↻] [− 100% +] │
│ ● rapport.md       [×]  │ ┌─────────────────────────────────────┐ │
│   notes.md         [×]  │ │                                     │ │
│   annexe.md        [×]  │ │             aperçu                 │ │
│                        │ │                                     │ │
│ Style · Default    [›] │ └─────────────────────────────────────┘ │
│ Sortie · Sources   [›] │                                         │
│ Avancé             [›] │                                         │
├────────────────────────┴─────────────────────────────────────────┤
│ Prêt · 3 fichiers                          [⚙ Générer 3 PDF]     │
│ [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0/3     │
└──────────────────────────────────────────────────────────────────┘
```

Règles :

- panneau gauche minimum 300 px ;
- les chemins détaillés sont masqués ;
- « Style », « Sortie » et « Avancé » utilisent des résumés courts ;
- les contrôles d’aperçu restent sur une ligne tant qu’ils tiennent.

### 7.3 Étroit — 560 à 759 px

```text
┌──────────────────────────────────────────────┐
│ [logo] LibreMark PDF  v1.0.0      [FR] [?]  │
├──────────────────────────────────────────────┤
│ Fichiers                                 3  │
│ [+ Ajouter des fichiers]                    │
│ ● rapport.md                           [×]  │
│   notes.md                             [×]  │
│   annexe.md                            [×]  │
│                                            │
│ [▾ Aperçu · rapport.md · page 1/12]        │
│ [↻] [‹ 1/12 ›]              [− 100% +]     │
│ ┌────────────────────────────────────────┐ │
│ │                 aperçu                │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ [› Style PDF · Default]                   │
│ [› Destination · Dossiers sources]        │
│ [› En-têtes et pieds de page]             │
│ [› Autres options avancées]               │
├──────────────────────────────────────────────┤
│ Prêt · 3 fichiers       [⚙ Générer 3 PDF] │
│ [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0/3  │
└──────────────────────────────────────────────┘
```

Règles :

- une seule colonne et un seul défilement du contenu ;
- aperçu repliable, ouvert après ajout d’un premier fichier mais refermable ;
- accordéons exclusifs : ouvrir une section ferme la précédente lorsque la
  hauteur est inférieure à 640 px ;
- barre d’action sur deux lignes ;
- aucun champ en trois colonnes : Gauche, Centre et Droite sont empilés.

### Grille et dimensions

- unité de base : 4 px logiques ;
- espacements usuels : 4, 8, 12, 16 et 24 px ;
- marge extérieure : 16 px large/moyen, 12 px étroit ;
- hauteur de barre supérieure : 52 px ;
- contrôle texte : minimum 32 px de haut ;
- bouton principal : minimum 40 px de haut ;
- bouton icône : minimum 32×32 px, nom accessible obligatoire ;
- zone de dépôt vide : 96 px minimum ;
- ligne de fichier : 44 px minimum ;
- panneau aperçu : 320 px de haut large, 280 px moyen, 240 px étroit ;
- fenêtre minimale conservée : 560×520 ;
- taille initiale cible : 1060×720, plafonnée à l’espace de travail disponible
  sur l’écran courant ;
- le contenu central absorbe toute réduction de hauteur avant la barre
  supérieure ou la barre d’action ;
- le bouton **⚙ Générer** et la progression restent visibles à 560×520, en EN
  comme en FR.

## 8. Catalogue des composants et comportements

### 8.1 Barre supérieure

- Utilise les couleurs système via `ttk`.
- La version est un bouton-lien avec focus visible.
- Le contrôle de langue expose l’état sélectionné.
- **Aide** contient Raccourcis clavier, Signaler un problème et À propos.

#### Politique d’icônes

- Une icône seule est privilégiée pour une action conventionnelle et comprise
  sans phrase : retirer (`×` rouge), choisir ou ouvrir un dossier, aide (`?`),
  actualiser (`↻`), zoom et navigation entre pages.
- **⚙ Générer** conserve l’icône d’engrenage et son libellé, car il s’agit de
  l’action principale et parce que l’engrenage seul pourrait être interprété
  comme un accès aux réglages.
- Une action rare, sensible ou ambiguë conserve un libellé court, avec ou sans
  icône : annuler une conversion, remplacer une sortie, inclure un diagnostic.
- Chaque bouton icône possède un nom accessible localisé, une infobulle
  localisée, un focus visible et une zone active d’au moins 32×32 px.
- La forme, la position et le nom accessible transmettent le sens : le rouge
  de la croix Retirer ne constitue jamais son unique indication.
- Des icônes locales, légères et dont la licence est compatible sont intégrées
  à l’application. Aucun téléchargement, police d’icônes distante ou nouvelle
  dépendance d’exécution n’est autorisé.

### 8.2 Zone d’ajout

États :

- **vide avec DnD** : contour neutre, texte dépôt/parcours ;
- **vide sans DnD** : texte de sélection seulement ;
- **survol valide** : contour accentué, fond légèrement accentué ;
- **survol invalide** : contour erreur et texte « Type non pris en charge » ;
- **occupé** : devient un bouton compact au-dessus de la liste ;
- **désactivé pendant conversion** : reste lisible, sans réaction au clic ni au
  dépôt.

### 8.3 Liste et ligne de fichier

Chaque ligne contient :

- état ou sélection ;
- nom du fichier ;
- chemin parent secondaire si l’espace le permet ;
- état de conversion ;
- bouton Retirer.

Comportements :

- clic ou focus + Entrée : sélection pour l’aperçu ;
- Suppr : retire la ligne si aucune conversion n’est active ;
- aucun dialogue pour retirer une simple entrée ;
- **Vider la liste** est masqué si la liste est vide ;
- après suppression du fichier actif, sélectionner le suivant, sinon le
  précédent ;
- les doublons sont détectés comme aujourd’hui, mais explicitement annoncés.

### 8.4 Style PDF

Résumé fermé :

`Style PDF — Default (default@1)` ou `Style PDF — CSS · print.css`.

Ouvert :

- bouton radio **Thème local** ;
- liste des thèmes installés, nom traduit et référence technique secondaire ;
- bouton radio **CSS personnalisé** ;
- chemin et **Choisir un CSS** ;
- erreur locale et action de rétablissement.

Aucun téléchargement ni recherche distante.

### 8.5 Destination

- valeur par défaut explicite ;
- dossier personnalisé avec chemin élidé ;
- boutons **Changer** et **Utiliser les dossiers sources** ;
- destination verrouillée pendant une conversion ;
- changement appliqué à tout le lot.

### 8.6 En-têtes et pieds de page

Deux sous-sections, chacune avec Gauche, Centre et Droite.

À largeur large/moyenne : trois colonnes égales. À largeur étroite : trois
lignes.

L’aide mentionne exactement `{titre}`, `{title}`, `{date}`, `{page}` et
`{total}`.

Un bouton **Réinitialiser** restaure uniquement les six valeurs par défaut,
dont `Page {page} / {total}` au centre du pied. Il ne modifie aucun autre
réglage.

### 8.7 Autres options avancées

- date de rendu, avec format localisé affiché mais valeur `YYYY-MM-DD`
  inchangée ;
- HTML statique de confiance ;
- texte d’avertissement sans jargon ;
- aucune option de marge, police, format de page ou sécurité réseau.

### 8.8 Aperçu

États :

- pas de fichier ;
- attente temporisée ;
- rendu en cours ;
- réussi ;
- erreur ;
- indisponible faute de composant ;
- obsolète pendant un nouveau rendu.

Règles :

- le rendu initial affiche la page 1 et le nombre total de pages ;
- pages rasterisées à la demande depuis le même PDF d’aperçu via PDFium ;
- boutons précédent/suivant désactivés sur la première/dernière page ;
- changement de page sans nouvelle préparation Markdown ni nouveau rendu
  Chromium tant que le document d’aperçu n’est pas invalidé ;
- nouvelle version du document : retour à la page 1 ; un simple changement de
  zoom conserve la page courante ;
- ancien aperçu conservé pendant le chargement ;
- nouvelle sélection de fichier prioritaire ;
- demandes intermédiaires supprimées comme actuellement ;
- rendu et lecture du fichier hors thread principal ;
- dessin de l’image exclusivement sur le thread Tk ;
- fond neutre contrastant avec la page blanche ;
- zoom sans relancer Chromium ;
- molette : défilement ; `Ctrl+molette` : zoom centré sur le pointeur ;
  glisser avec le bouton central : panoramique ;
- zoom annoncé aux technologies d’assistance ;
- page courante et total annoncés aux technologies d’assistance ;
- échec de rasterisation d’une page affiché dans l’aperçu sans invalider les
  pages déjà consultables ni empêcher la génération.

### 8.9 Barre d’action et progression

Prêt :

`3 fichiers · À côté des sources` + progression `0 sur 3` +
**⚙ Générer 3 PDF**.

Conversion :

`2 sur 3 · notes.md` + progression + **Annuler après ce fichier** +
**⚙ Générer 3 PDF** désactivé.

Annulation demandée :

`Annulation demandée · fin de notes.md…`, bouton désactivé.

Final :

`2 réussis · 1 échec` + **Voir les résultats** si la liste n’est pas visible.

La barre d’action et sa progression restent toujours visibles et hors du
contenu défilant. Le bouton **⚙ Générer** ne disparaît dans aucun état : il est
désactivé lorsque la liste ou les options sont invalides, pendant l’aperçu
strictement bloquant et pendant la conversion. La cause de l’indisponibilité
est annoncée dans l’état adjacent et par l’aide accessible du bouton.

### 8.10 Résultats

Chaque résultat contient :

- nom source ;
- état avec icône et texte ;
- chemin de sortie en cas de succès ;
- résumé et code en cas d’échec ;
- actions appropriées.

Actions :

- succès : Ouvrir le PDF, Ouvrir le dossier ;
- erreur : Copier les détails, Signaler un problème ;
- annulé : aucune action d’ouverture.

### 8.11 Dialogues de précontrôle

Collision :

- liste des sources concernées ;
- raison par fichier ;
- **Continuer avec les autres** ;
- **Annuler**.

Sorties existantes :

- liste ou compte ;
- **Remplacer après rendu réussi** ;
- **Conserver et signaler des échecs** ;
- **Annuler**.

Le bouton sûr est sélectionné par défaut. `Échap` équivaut toujours à Annuler.

### 8.12 Couleur et contraste

La version 1 suit les couleurs système exposées par `ttk`. Elle ne dérive pas
sa palette de l’icône LibreMark PDF. Les styles restent toutefois centralisés
afin qu’une identité personnalisée puisse être ajoutée dans une version
ultérieure sans modifier la structure des composants.

Tokens sémantiques :

- surface principale : couleur système ;
- surface secondaire : contraste léger mais visible ;
- texte principal : contraste ≥ 4,5:1 ;
- texte secondaire : contraste ≥ 4,5:1 pour le petit texte ;
- contour et composants : contraste ≥ 3:1 ;
- accent : action principale et focus ;
- erreur, succès, avertissement : texte + icône + couleur.

États :

- hover : variation de surface et curseur approprié ;
- focus : anneau de 2 px, non masqué par hover ;
- disabled : contraste réduit, mais texte encore lisible ;
- error : bordure, icône et message associé ;
- success : icône et libellé, jamais couleur seule.

### 8.13 Typographie

- police système `TkDefaultFont` ;
- titre produit : 16 px équivalent, semi-gras ;
- titre de section : 11–12 px équivalent, semi-gras ;
- texte courant : 10–11 px équivalent ;
- métadonnées : 9–10 px, sans descendre sous la taille système ;
- pas de majuscules intégrales pour structurer ;
- une ligne maximum pour les actions ; élision seulement pour les données.

### 8.14 Navigation clavier

Ordre principal :

1. Ajouter ;
2. liste de fichiers ;
3. Style ;
4. Destination ;
5. Options avancées ;
6. aperçu et zoom ;
7. action principale.

| Action | Raccourci |
| --- | --- |
| Ajouter des fichiers | `Ctrl+O` |
| Actualiser l’aperçu | `Ctrl+R` |
| Générer | `Ctrl+G` |
| Zoom avant/arrière | `Ctrl++` / `Ctrl+-` |
| Zoom 100 % | `Ctrl+0` |
| Page précédente/suivante, aperçu focalisé | `←` / `→` |
| Annuler le lot actif | `Échap` |
| Aide des raccourcis | `F1` |
| Retirer la ligne focalisée | `Suppr` |

`Échap` ne vide jamais la liste et ne ferme pas la fenêtre principale lorsque
la conversion est active.

La molette conserve le défilement natif. Dans l’aperçu focalisé,
`Ctrl+molette` zoome autour du pointeur et le glisser avec le bouton central
déplace la page. Ces gestes complètent les boutons et raccourcis clavier ; ils
ne sont jamais le seul moyen d’effectuer l’action.

## 9. Spécification EN/FR des textes nouveaux ou modifiés

Les placeholders d’une même clé doivent rester strictement identiques dans les
deux langues. Les pluriels utilisent des clés distinctes.

| Clé proposée | English | Français |
| --- | --- | --- |
| `app_version_compact` | `v{version}` | `v{version}` |
| `help_menu` | `Help` | `Aide` |
| `about_action` | `About LibreMark PDF` | `À propos de LibreMark PDF` |
| `report_issue_action` | `Report a problem` | `Signaler un problème` |
| `keyboard_shortcuts_action` | `Keyboard shortcuts` | `Raccourcis clavier` |
| `language_english_a11y` | `Change language to English` | `Passer l’interface en anglais` |
| `language_french_a11y` | `Change language to French` | `Passer l’interface en français` |
| `files_heading` | `Files` | `Fichiers` |
| `file_count_one` | `1 file` | `1 fichier` |
| `file_count_many` | `{count} files` | `{count} fichiers` |
| `add_files` | `Add files` | `Ajouter des fichiers` |
| `drop_or_browse` | `Drop Markdown files here, or browse` | `Déposez des fichiers Markdown ici, ou parcourez vos fichiers` |
| `browse_without_dnd` | `Select Markdown files` | `Sélectionner des fichiers Markdown` |
| `drop_active` | `Drop to add` | `Déposer pour ajouter` |
| `unsupported_drop` | `Unsupported file type` | `Type de fichier non pris en charge` |
| `files_added_one` | `1 file added.` | `1 fichier ajouté.` |
| `files_added_many` | `{count} files added.` | `{count} fichiers ajoutés.` |
| `files_ignored_one` | `1 item ignored: {reason}` | `1 élément ignoré : {reason}` |
| `files_ignored_many` | `{count} items ignored: {reason}` | `{count} éléments ignorés : {reason}` |
| `duplicate_reason` | `already in the list` | `déjà présent dans la liste` |
| `unsupported_reason` | `only .md and .markdown files are supported` | `seuls les fichiers .md et .markdown sont acceptés` |
| `remove_file_a11y` | `Remove {name}` | `Retirer {name}` |
| `clear_files` | `Clear list` | `Vider la liste` |
| `style_heading` | `PDF style` | `Style PDF` |
| `local_theme` | `Local theme` | `Thème local` |
| `custom_css` | `Custom CSS` | `CSS personnalisé` |
| `choose_css` | `Choose CSS` | `Choisir un CSS` |
| `return_to_theme` | `Use the selected theme` | `Revenir au thème sélectionné` |
| `destination_heading` | `Destination` | `Destination` |
| `source_destination_one` | `Next to the source file` | `À côté du fichier source` |
| `source_destination_many` | `Next to each source file` | `À côté de chaque fichier source` |
| `change_destination` | `Change` | `Changer` |
| `reset_destination` | `Use source folders` | `Utiliser les dossiers sources` |
| `header_footer_heading` | `Headers and footers` | `En-têtes et pieds de page` |
| `other_advanced_heading` | `Other advanced options` | `Autres options avancées` |
| `position_left` | `Left` | `Gauche` |
| `position_center` | `Center` | `Centre` |
| `position_right` | `Right` | `Droite` |
| `tokens_help` | `Tokens: {titre}, {title}, {date}, {page}, {total}` | `Jetons : {titre}, {title}, {date}, {page}, {total}` |
| `reset_header_footer` | `Restore defaults` | `Rétablir les valeurs par défaut` |
| `render_date` | `Render date (YYYY-MM-DD)` | `Date de rendu (AAAA-MM-JJ)` |
| `trusted_html` | `Allow trusted static HTML` | `Autoriser le HTML statique de confiance` |
| `trusted_html_help` | `Use only for content you trust. Scripts, remote resources and active content remain blocked.` | `À utiliser uniquement avec un contenu de confiance. Les scripts, ressources distantes et contenus actifs restent bloqués.` |
| `trusted_html_confirm_title` | `Allow trusted HTML?` | `Autoriser le HTML de confiance ?` |
| `trusted_html_confirm` | `This changes how raw HTML in the Markdown is interpreted. Continue only if you trust the file.` | `Cette option modifie l’interprétation du HTML brut dans le Markdown. Continuez uniquement si le fichier est fiable.` |
| `preview_heading` | `Preview` | `Aperçu` |
| `refresh_preview` | `Refresh` | `Actualiser` |
| `refresh_preview_a11y` | `Refresh preview` | `Actualiser l’aperçu` |
| `preview_empty` | `Add or select a file to preview it.` | `Ajoutez ou sélectionnez un fichier pour le prévisualiser.` |
| `preview_loading` | `Updating preview…` | `Mise à jour de l’aperçu…` |
| `preview_unavailable` | `Preview unavailable` | `Aperçu indisponible` |
| `preview_retry` | `Try again` | `Réessayer` |
| `preview_conversion_possible` | `You can still try to generate the PDF.` | `Vous pouvez tout de même essayer de générer le PDF.` |
| `preview_page` | `Page {current} of {total}` | `Page {current} sur {total}` |
| `previous_page_a11y` | `Previous page` | `Page précédente` |
| `next_page_a11y` | `Next page` | `Page suivante` |
| `zoom_out_a11y` | `Zoom out` | `Réduire le zoom` |
| `zoom_in_a11y` | `Zoom in` | `Augmenter le zoom` |
| `zoom_value` | `{percent}%` | `{percent} %` |
| `generate_one` | `Generate PDF` | `Générer le PDF` |
| `generate_many` | `Generate {count} PDFs` | `Générer {count} PDF` |
| `generating_progress` | `{current} of {total} · {name}` | `{current} sur {total} · {name}` |
| `cancel_after_current` | `Cancel after this file` | `Annuler après ce fichier` |
| `cancelling_current` | `Cancellation requested · finishing {name}…` | `Annulation demandée · fin de {name}…` |
| `close_during_conversion_title` | `Conversion in progress` | `Conversion en cours` |
| `close_during_conversion_message` | `A conversion is in progress. If you close, the active file may finish processing and the remaining files will be cancelled.` | `Une conversion est en cours. Si vous fermez, le fichier actif peut terminer son traitement et les fichiers restants seront annulés.` |
| `continue_conversion` | `Continue conversion` | `Continuer la conversion` |
| `cancel_conversion_and_close` | `Cancel conversion and close` | `Annuler la conversion et fermer` |
| `result_success` | `Succeeded` | `Réussi` |
| `result_error` | `Failed` | `Échec` |
| `result_cancelled` | `Cancelled` | `Annulé` |
| `summary_complete` | `{ok} succeeded · {failed} failed · {cancelled} cancelled` | `{ok} réussis · {failed} échecs · {cancelled} annulés` |
| `open_pdf` | `Open PDF` | `Ouvrir le PDF` |
| `open_folder` | `Open folder` | `Ouvrir le dossier` |
| `copy_details` | `Copy details` | `Copier les détails` |
| `view_results` | `View results` | `Voir les résultats` |
| `collision_title` | `Output conflicts` | `Conflits de sortie` |
| `continue_independent` | `Continue with other files` | `Continuer avec les autres fichiers` |
| `existing_outputs_title` | `Existing PDFs` | `PDF existants` |
| `replace_after_success` | `Replace after successful rendering` | `Remplacer après un rendu réussi` |
| `keep_and_report` | `Keep existing PDFs and report failures` | `Conserver les PDF et signaler les échecs` |
| `cancel_action` | `Cancel` | `Annuler` |
| `about_version` | `LibreMark PDF {version}` | `LibreMark PDF {version}` |
| `technical_information` | `Technical information` | `Informations techniques` |
| `copy_technical_information` | `Copy technical information` | `Copier les informations techniques` |
| `report_title` | `Report a problem` | `Signaler un problème` |
| `report_summary` | `What happened?` | `Que s’est-il passé ?` |
| `report_steps` | `Steps to reproduce (optional)` | `Étapes pour reproduire le problème (facultatif)` |
| `include_diagnostics` | `Include anonymized technical diagnostics` | `Inclure un diagnostic technique anonymisé` |
| `diagnostics_consent` | `Nothing is sent automatically. Review the report before copying or saving it.` | `Rien n’est envoyé automatiquement. Vérifiez le rapport avant de le copier ou de l’enregistrer.` |
| `preview_report` | `Review report` | `Vérifier le rapport` |
| `copy_report` | `Copy report` | `Copier le rapport` |
| `save_report` | `Save report…` | `Enregistrer le rapport…` |
| `open_support_channel` | `Open support page` | `Ouvrir la page d’assistance` |
| `support_not_configured` | `No support page is configured. Copy or save the report instead.` | `Aucune page d’assistance n’est configurée. Copiez ou enregistrez le rapport.` |
| `report_copied` | `Report copied.` | `Rapport copié.` |
| `report_saved` | `Report saved to {path}.` | `Rapport enregistré dans {path}.` |
| `report_copy_error` | `Could not copy the report: {error}` | `Impossible de copier le rapport : {error}` |
| `report_save_error` | `Could not save the report: {error}` | `Impossible d’enregistrer le rapport : {error}` |
| `support_open_error` | `Could not open the support page: {error}` | `Impossible d’ouvrir la page d’assistance : {error}` |

## 10. Version et signalement de problème

### 10.1 Version

#### Emplacement

- barre supérieure : `v1.0.0` après le nom ;
- dialogue À propos accessible par la version ou le menu Aide.

#### Détail

Le dialogue peut afficher, à partir des informations déjà disponibles :

- LibreMark PDF `1.0.0` ;
- profil de rendu `default@1` ;
- Playwright `1.60.0` ;
- Chromium `148.0.7778.96`, révision `1223` ;
- version Python ;
- système et architecture ;
- mode source ou artefact, si une détection fiable est définie.

#### Copie technique

Format stable, texte UTF-8 ou JSON lisible. À exclure :

- chemins vers le navigateur ;
- nom du compte système ;
- dossier personnel ;
- fichiers sélectionnés ;
- contenu Markdown/PDF/CSS ;
- variables d’environnement ;
- journaux arbitraires.

### 10.2 Signaler un problème

#### Point d’entrée

- **Aide → Signaler un problème** ;
- action secondaire sur une erreur de fichier ;
- jamais une bannière promotionnelle ni un envoi automatique.

#### Données demandées

- résumé obligatoire ;
- étapes facultatives ;
- résultat attendu facultatif ;
- code d’erreur prérempli lorsqu’ouvert depuis une erreur ;
- diagnostic optionnel.

#### Diagnostic proposé

Données raisonnables :

- version de l’application ;
- OS, version et architecture ;
- Python ;
- langue de l’IHM ;
- mode source/artefact si fiable ;
- profil de rendu ;
- identités Playwright/Chromium ;
- présence/absence des ressources contrôlées par `doctor` ;
- thème sélectionné par identifiant ;
- code d’erreur ;
- nombre de fichiers, sans noms ni chemins ;
- état du DnD ;
- date/heure locale, avec fuseau si accepté.

Données exclues par défaut :

- contenu Markdown ou HTML ;
- PDF ;
- contenu du CSS ;
- nom complet des fichiers ;
- chemins d’entrée, sortie, navigateur et profil utilisateur ;
- nom de machine ou utilisateur ;
- presse-papiers ;
- journaux globaux ;
- identifiants ou données personnelles.

Si le texte d’erreur contient un chemin, le rapport doit le remplacer par un
alias tel que `<source-1.md>` ou `<output-folder>`. Le rapport doit rester
éditable avant copie/enregistrement.

#### Fonctionnement hors ligne

Fonctions garanties :

- construire le rapport ;
- prévisualiser ;
- copier ;
- enregistrer comme fichier local.

Fonction conditionnelle :

- ouvrir une URL de support configurée dans le navigateur système.

Aucune requête HTTP ne doit être effectuée par LibreMark PDF lui-même.

#### Canal non défini

`SUPPORT.md` mentionne GitHub Issues, mais le dépôt inspecté ne possède pas de
remote permettant de déduire une URL fiable. Tant qu’une URL officielle n’est
pas décidée :

- ne pas afficher un faux lien ;
- conserver **Copier** et **Enregistrer** ;
- afficher « Aucune page d’assistance n’est configurée » ;
- embarquer des instructions de support locales et bilingues dans les
  artefacts, consultables sans réseau.

Une future URL doit être fournie explicitement par le propriétaire et intégrée
comme constante packagée ; elle ne doit jamais être déduite du dépôt ou de Git.

## 11. Découpage en lots d’implémentation

### Lot 0 — Caractérisation de la baseline

- **Objectif :** verrouiller les comportements actuels avant toute modification
  visible.
- **Domaines :** `tests/test_gui.py`, `tests/test_i18n.py`,
  `tests/test_desktop_services.py`.
- **Avant/après :** aucun changement utilisateur.
- **Tests :** options transmises au core, ordre collision/écrasement,
  annulation, fermeture, erreurs par fichier, sélection du premier fichier,
  zoom, DnD absent, focus initial.
- **Acceptation :** baseline documentée et tests verts sans toucher au moteur.
- **Risques :** tester la structure source plutôt que le comportement.
- **Dépendances/décisions :** aucune.
- **i18n/accessibilité :** caractériser clés et ordre de focus actuels.

### Lot 1 — Fondations techniques UI

- **Objectif :** centraliser espacements, typographie, couleurs sémantiques,
  tailles et états `ttk`.
- **Domaines :** nouveau module possible `desktop/tk/styles.py`, initialisation
  dans `app.py`.
- **Avant/après :** hiérarchie visuelle plus nette, layout encore identique.
- **Tests :** import sans affichage, création des styles, variantes
  disabled/focus/error.
- **Acceptation :** aucune couleur métier dispersée ; aucun changement des
  ressources PDF.
- **Risques :** différences de thème Tk entre Windows et Linux.
- **Dépendances/décisions :** couleurs système en version 1 ; architecture des
  styles compatible avec une personnalisation future.
- **i18n/accessibilité :** contraste contrôlé, taille système respectée.

### Lot 2 — Réorganisation du layout

- **Objectif :** barre supérieure, zone de travail redimensionnable et barre
  d’action persistante.
- **Domaines :** `desktop/tk/layout.py`, éventuellement `responsive.py`,
  `app.py`.
- **Avant/après :** génération et état passent de sous la ligne de flottaison à
  toujours visibles.
- **Tests :** transitions large/moyen/étroit, `minsize`, aucun widget
  inaccessible, focus conservé lors du changement de mode.
- **Acceptation :** bouton **⚙ Générer** et barre de progression visibles aux
  sept tailles de référence et dans tous les états ; un seul défilement global
  en mode étroit.
- **Risques :** mélange `pack`/`grid`, reconstruction de widgets et perte de
  focus.
- **Dépendances/décisions :** seuils responsives et ratio initial du séparateur.
- **i18n/accessibilité :** aucun libellé FR coupé à 560 px.

### Lot 3 — Composants communs, fichiers et dépôt

- **Objectif :** politique d’icônes cohérente, zone vide adaptative, liste
  compacte, fichier actif et feedback des éléments ignorés.
- **Domaines :** `inputs.py`, `layout.py`, registre d’icônes UI local éventuel,
  actifs UI dédiés et tests GUI. Ne pas remplacer les icônes de statut PDF
  compatibility-sensitives.
- **Avant/après :** les éléments invalides ne sont plus ignorés silencieusement
  ; le fichier aperçu est explicite ; les actions conventionnelles emploient
  une icône reconnaissable.
- **Tests :** DnD présent/absent, doublons, extensions invalides, suppression
  active, ordre du lot, nom accessible et infobulle EN/FR de chaque bouton
  icône.
- **Acceptation :** un dépôt mixte produit un résumé exact sans empêcher les
  fichiers valides ; **⚙ Générer** conserve son texte ; aucune icône n’est
  téléchargée à l’exécution.
- **Risques :** modifier involontairement l’ordre transmis au core, pictogramme
  ambigu, licence ou rendu différent selon l’échelle.
- **Dépendances/décisions :** sélection d’aperçu libre validée.
- **i18n/accessibilité :** nom accessible du bouton Retirer avec `{name}`.

### Lot 4 — Réglages et destination

- **Objectif :** créer les accordéons Style, Destination, En-têtes/pieds et
  Autres options.
- **Domaines :** `inputs.py`, `layout.py`, `i18n.py`.
- **Avant/après :** mêmes options, résumées et mieux hiérarchisées.
- **Tests :** exclusivité thème/CSS, six positions exactes, pied par défaut,
  date, `trusted_html`, destination.
- **Acceptation :** `_render_options()` produit des valeurs strictement
  équivalentes à la baseline.
- **Risques :** remise à zéro trop large ou changement du pied par défaut.
- **Dépendances/décisions :** HTML de confiance placé sous Sécurité avancée et
  confirmation au premier usage de la session.
- **i18n/accessibilité :** chaque champ possède un nom distinct ; chevrons
  exposent ouvert/fermé.

### Lot 5 — Aperçu

- **Objectif :** états explicites, fichier actif, entête compacte et zoom
  cohérent sur la première page, avant extension multipage.
- **Domaines :** `preview.py`, `layout.py`, services inchangés sauf événement
  strictement nécessaire.
- **Avant/après :** canevas vide remplacé par un état compréhensible ; aperçu
  identifié.
- **Tests :** debounce 450 ms, regroupement, réponse obsolète, erreur, absence de
  PDFium, zoom 50–200, `Ctrl+molette` centré sur le pointeur, panoramique au
  bouton central, changement de fichier actif.
- **Acceptation :** toutes les opérations Tk restent sur le thread principal ;
  aucune seconde voie de rendu.
- **Risques :** régression de concurrence ou charge Chromium.
- **Dépendances/décisions :** `Ctrl+0`, `F1` et gestes de souris validés.
- **i18n/accessibilité :** progression et zoom annoncés sans dépendre du
  canevas.

### Lot 6 — Navigation multipage de l’aperçu

- **Objectif :** consulter chaque page du PDF d’aperçu avec `‹`, `Page n sur
  total`, `›`, sans changer le document PDF produit.
- **Domaines :** frontière canonique d’aperçu dans `libremark_pdf/engine/preview.py`
  et réexport de `core.py`, contrats/services desktop, `desktop/tk/preview.py`,
  tests d’aperçu et GUI.
- **Avant/après :** page 1 seulement, puis rasterisation à la demande de toute
  page disponible depuis le même PDF temporaire.
- **Tests :** total de pages, bornes précédent/suivant, cache par page,
  invalidation au changement de contenu, retour page 1 après nouveau rendu,
  conservation de la page au zoom, réponse obsolète, fermeture et nettoyage du
  fichier temporaire.
- **Acceptation :** aucune seconde voie de génération PDF ; un seul rendu
  Chromium par version d’aperçu ; PDFium rasterise la page demandée hors du
  thread Tk ; le PDF final et ses options restent strictement inchangés.
- **Risques :** durée de vie du PDF temporaire, mémoire du cache PNG, navigation
  sur un aperçu devenu obsolète et évolution de la frontière `core.py`.
- **Dépendances/décisions :** aucun nouveau moteur ni dépendance ; utiliser le
  PDFium déjà employé pour la première page.
- **i18n/accessibilité :** page courante/total annoncés ; boutons aux bornes
  désactivés ; flèches clavier limitées à l’aperçu focalisé.

### Lot 7 — Progression, annulation et résultats

- **Objectif :** afficher l’état global et chaque résultat de façon persistante.
- **Domaines :** `conversion.py`, `layout.py`, dialogues, tests.
- **Avant/après :** erreurs modales techniques remplacées ou complétées par des
  lignes durables.
- **Tests :** lot mixte, annulation avant/durant, succès seulement ouvrable,
  fermeture pendant opération, choix **Continuer la conversion**, choix
  **Annuler la conversion et fermer**, `Échap` dans le dialogue, erreur globale.
- **Acceptation :** une ligne par entrée ; nombre final identique aux résultats
  du core.
- **Risques :** réactiver trop tôt les contrôles ou masquer une erreur.
- **Dépendances/décisions :** dialogues de collision et de fermeture
  personnalisés validés.
- **i18n/accessibilité :** progression accessible, focus envoyé au résumé final
  sans saut intrusif.

### Lot 8 — Localisation

- **Objectif :** intégrer les textes cibles et supprimer les pseudo-pluriels.
- **Domaines :** `i18n.py`, manuels EN/FR, tests i18n.
- **Avant/après :** libellés plus courts et français naturel.
- **Tests :** égalité des clés/placeholders, singulier/pluriel, largeur et
  retranslation à chaud.
- **Acceptation :** aucun texte utilisateur codé en dur hors `i18n.py`, excepté
  EN/FR et symboles indépendants.
- **Risques :** régression de placeholders avec accolades des jetons.
- **Dépendances/décisions :** règle de pluralisation limitée à deux formes.
- **Accessibilité :** noms accessibles traduits avec les textes visibles.

### Lot 9 — Version et dialogue À propos

- **Objectif :** rendre la version visible et copiable.
- **Domaines :** `app.py`, `layout.py`, nouveau dialogue possible,
  `__version__` en lecture.
- **Avant/après :** version absente puis visible et détaillée.
- **Tests :** valeur égale à `libremark_pdf.__version__`, identité technique,
  copie sans chemins.
- **Acceptation :** `v1.0.0` visible à 560 px ; aucune collecte réseau.
- **Risques :** divergence entre version packagée et source.
- **Dépendances/décisions :** liste exacte des identités exposées.
- **i18n/accessibilité :** dialogue entièrement navigable au clavier.

### Lot 10 — Signalement de problème

- **Objectif :** produire, vérifier, copier et enregistrer un rapport anonymisé.
- **Domaines :** nouveau service toolkit-neutre possible
  `desktop/reporting.py`, dialogue Tk, `SUPPORT.md`, packaging si document
  embarqué.
- **Avant/après :** aucune action dans l’IHM puis rapport local utilisable.
- **Tests :** anonymisation des chemins, consentement décoché, copie,
  sauvegarde, canal absent, ouverture via service injecté.
- **Acceptation :** aucun document, chemin privé ou contenu CSS dans le
  diagnostic par défaut ; aucun réseau.
- **Risques :** fuite par texte d’erreur libre ou faux sentiment d’anonymat.
- **Dépendances/décisions :** rapport texte et JSON optionnel, diagnostic
  minimal et aide bilingue embarquée validés ; URL officielle encore à
  fournir.
- **i18n/accessibilité :** ordre de focus logique et consentement explicite.

### Lot 11 — Validation visuelle et responsive

- **Objectif :** qualifier la cible sur les OS et tailles annoncés.
- **Domaines :** tests, captures de référence, manuels, éventuellement guide
  Windows.
- **Avant/après :** validation ad hoc puis matrice reproductible.
- **Tests :** scénarios de la section suivante, suite complète et artefacts
  natifs.
- **Acceptation :** aucune coupure, chevauchement, action perdue ou régression
  métier.
- **Risques :** captures produites uniquement sous Xvfb et non sur Windows
  natif.
- **Dépendances/décisions :** seuil final des breakpoints après essais natifs.
- **i18n/accessibilité :** matrice clavier et EN/FR obligatoire.

## 12. Plan de tests et validation visuelle

### Scénarios manuels reproductibles

1. Démarrer en EN, sans DnD, sans fichier.
2. Ajouter un Markdown UTF-8 puis générer dans le dossier source.
3. Ajouter huit fichiers, sélectionner chaque ligne pour l’aperçu.
4. Déposer un mélange de `.md`, `.txt` et doublons.
5. Choisir un thème local puis un CSS personnalisé, puis revenir au thème.
6. Remplir les six champs avec tous les jetons supportés.
7. Tester date valide et invalide.
8. Activer le HTML de confiance après confirmation.
9. Tester chaque zoom, les deux axes de défilement, `Ctrl+molette` centré sur le
   pointeur et le panoramique avec le bouton central.
10. Ouvrir un document multipage, parcourir la première, une page intermédiaire
    et la dernière, puis modifier le document et vérifier le retour à la page 1.
11. Simuler une erreur d’aperçu avec conversion encore disponible.
12. Choisir un dossier contenant des espaces et des caractères non ASCII.
13. Présenter une collision et des sorties existantes.
14. Exécuter un lot avec succès, erreur et annulation.
15. Fermer pendant une conversion et choisir **Continuer la conversion** ;
    recommencer et choisir **Annuler la conversion et fermer**.
16. Ouvrir un PDF et un dossier réussis ; simuler une ouverture indisponible.
17. Passer EN → FR → EN sans perdre l’état.
18. Ouvrir À propos et copier les informations.
19. Construire un rapport, examiner l’anonymisation, copier et enregistrer hors
    ligne.
20. Tester le canal absent puis une URL configurée en validation.
21. Redémarrer et vérifier la langue persistée.
22. Répéter les états vide, prêt, conversion, annulation et résultat à 560×520
    et vérifier que **⚙ Générer** et la progression restent visibles.

### Tests automatisables

- égalité EN/FR et placeholders ;
- calcul des modes large/moyen/étroit ;
- ordre de tabulation déclaré ;
- maintien du focus après suppression/reconstruction ;
- capacité DnD injectée ;
- filtrage et compte des fichiers ignorés ;
- options exactes transmises au core ;
- sélection d’aperçu sans modification de l’ordre de conversion ;
- coalescence des demandes d’aperçu ;
- total des pages, bornes précédent/suivant, cache et invalidation multipage ;
- zoom centré sur le pointeur et panoramique sans modifier le zoom ;
- absence d’appel Tk depuis les workers ;
- progression et état terminal ;
- présence de la barre d’action et de progression dans chaque mode responsive ;
- fermeture pendant conversion sans annulation implicite ;
- anonymisation des chemins Windows, POSIX, UNC et Unicode ;
- absence de socket, HTTP ou envoi dans le reporting ;
- version égale à la version du package.

### Captures visuelles de référence

Pour EN et FR :

- vide avec et sans DnD ;
- un fichier, aperçu réussi ;
- lot de huit fichiers et chemins longs ;
- réglages avancés ouverts ;
- aperçu en chargement, erreur et indisponible ;
- aperçu pages 1, intermédiaire et dernière ;
- zoom 50, 100 et 200 % ;
- conversion en cours ;
- annulation demandée ;
- résultats mixtes ;
- dialogues collision et écrasement ;
- À propos ;
- signalement avec et sans diagnostic.

Les captures ne sont pas des goldens de rendu PDF et ne doivent pas modifier
les goldens canoniques.

### Tailles à vérifier

- 1440×900 ;
- 1280×800 ;
- 1100×700 ;
- 1024×768 ;
- 820×780, pour comparaison avec l’existant ;
- 720×640 ;
- 560×520.

À vérifier sous Windows : mise à l’échelle 100 %, 125 % et 150 %. Sous Linux :
au moins un thème Tk natif de l’environnement candidat.

### Tests clavier

- parcours complet sans souris ;
- Tab et Maj+Tab sans boucle ni widget fantôme ;
- Entrée/Espace sur dépôt, accordéons et boutons ;
- flèches sur sélection de thème et langue ;
- focus visible sur canevas et lignes ;
- `Ctrl+O`, `Ctrl+R`, `Ctrl+G`, zoom, pages précédente/suivante, `F1`,
  `Suppr`, `Échap` ;
- retour de focus après fermeture des dialogues ;
- aucun raccourci déclenché dans un champ texte lorsqu’il modifierait le
  contenu.

### Critères de non-régression métier

- mêmes entrées acceptées ;
- mêmes options transmises à `core.py` ;
- même pied par défaut ;
- mêmes thèmes et CSS ;
- mêmes restrictions HTML/CSS/réseau ;
- même moteur Chromium ;
- une sortie par entrée ;
- poursuite après erreur ;
- écrasement atomique ;
- annulation après le fichier courant ;
- aucun appel réseau ;
- fonctionnement sans `tkinterdnd2` ;
- CLI et skill inchangés.

Commandes finales minimales :

```bash
python3 -m unittest discover -s tests -v
python3 -m libremark_pdf convert --help
python3 -m libremark_pdf convert README.md --json
```

### Critères de qualité visuelle

- bouton **⚙ Générer** et barre de progression visibles à toutes les tailles et
  dans tous les états ;
- aucun texte tronqué sans mécanisme de consultation ;
- aucun chevauchement en FR ;
- contraste conforme aux seuils définis ;
- état de focus visible partout ;
- pas plus de deux niveaux d’encadrement ;
- une seule action primaire par état ;
- erreurs compréhensibles sans lire le code technique ;
- hiérarchie perceptible en niveaux de gris.

Baseline contrôlée durant l’analyse :

```text
PYTHONDONTWRITEBYTECODE=1 venv-linux/bin/python -m unittest \
  tests.test_gui tests.test_i18n tests.test_desktop_services -v
```

Résultat : code 0, 40 tests réussis. Aucun test de rendu Chromium n’était
requis pour cette spécification non implémentée.

## 13. Décisions validées et validations restantes

Les décisions produit suivantes sont validées pour la cible. Les mentions
« validation requise » désignent une preuve à produire pendant
l’implémentation ; elles ne rouvrent pas le choix produit.

| ID | Décision validée | Validation restante |
| --- | --- | --- |
| D1 | Conserver le HTML statique de confiance sous **Sécurité avancée** et synchroniser les manuels. | Non-régression sécurité et documentation EN/FR. |
| D2 | Utiliser uniquement une URL de support fournie explicitement et packagée ; tant qu’elle manque, garantir Copier, Enregistrer et l’aide locale. | Le propriétaire doit encore fournir l’URL officielle s’il souhaite activer ce bouton. |
| D3 | Rapport texte lisible et éditable avec bloc JSON technique optionnel. | Tests EN/FR, copie et enregistrement UTF-8. |
| D4 | Diagnostic minimal de la section 10 avec anonymisation des chemins et noms. | Revue sécurité de l’anonymisation avant livraison. |
| D5 | Confirmer le HTML de confiance au premier usage de chaque session. | Test du retour arrière et du focus clavier. |
| D6 | Toute ligne peut devenir le fichier actif d’aperçu sans modifier l’ordre du lot. | Tests de sélection, suppression et ordre transmis au core. |
| D7 | Conserver l’actualisation automatique avec debounce de 450 ms et l’action d’actualisation immédiate. | Tests de regroupement et documentation EN/FR. |
| D8 | En mode étroit, ouvrir l’aperçu après le premier ajout puis mémoriser son état pendant la session. | Validation à 560×520 et avec huit fichiers. |
| D9 | Sous 640 px de hauteur, un seul accordéon avancé reste ouvert. | Validation du focus lors de la fermeture automatique. |
| D10 | Utiliser un dialogue personnalisé pour les sorties existantes et ses trois choix explicites. | Tests d’écrasement atomique et d’annulation. |
| D11 | Taille initiale cible 1060×720, plafonnée à l’espace de travail, minimum 560×520. **⚙ Générer** et sa barre de progression restent toujours visibles hors défilement. | Validation native Windows/Linux, EN/FR et mise à l’échelle 100–150 %. |
| D12 | Afficher le mode source/artefact uniquement si sa détection est fiable et testée. | Omettre l’information si cette preuve n’est pas disponible. |
| D13 | Embarquer des instructions de support locales et bilingues dans les artefacts. | Revue du packaging Windows et fonctionnement hors ligne. |
| D14 | Ajouter `Ctrl+0` et `F1` sans retirer les raccourcis existants. | Tests de conflits dans les champs texte. |
| D15 | Mémoriser séparateur et accordéons seulement pendant la session dans les premiers lots. | Une persistance entre lancements pourra être réévaluée après tests utilisateurs. |
| D16 | Molette pour défiler ; `Ctrl+molette` pour zoomer autour du pointeur ; glisser avec le bouton central pour déplacer la page. | Validation Windows/Linux, souris et pavé tactile, sans retirer les commandes clavier. |
| D17 | Icône seule pour les actions immédiatement reconnaissables ; icône + texte pour l’action principale ou ambiguë. Le bouton principal est **⚙ Générer**. | Choix d’icônes locales sous licence compatible, infobulles et noms accessibles EN/FR. |
| D18 | Confirmer toute fermeture pendant conversion ; **Continuer la conversion** est le choix sûr, **Annuler la conversion et fermer** explicite le traitement du fichier actif. | Tests de fermeture de dialogue, `Échap`, annulation et terminaison du fichier actif. |
| D19 | Ajouter une navigation multipage à la demande avec `‹`, `Page n sur total`, `›`, dans un lot technique séparé. | Tests de performance, cache, nettoyage temporaire et non-régression du PDF final. |
| D20 | Pour la version 1, utiliser les couleurs système sans dériver la palette de l’icône ; centraliser les styles pour permettre une personnalisation future. | Contraste et validation visuelle sur les thèmes Tk natifs ciblés. |

Aucune décision validée n’introduit de service externe. L’ajout futur d’un SDK
de support, d’une télémétrie, d’un service de collecte ou d’une palette
personnalisée constitue une nouvelle décision produit et sécurité.

## 14. Hors périmètre

- développement ou prototype de l’IHM ;
- changement de toolkit ;
- portage Android ;
- synchronisation cloud ;
- compte utilisateur ;
- télémétrie ;
- envoi automatique de rapports ;
- éditeur Markdown ou CSS intégré ;
- options de marges, polices ou format PDF ;
- modification des thèmes PDF ;
- téléchargement ou marketplace de thèmes ;
- changement du rendu Chromium ;
- changement de la CLI ou de `SKILL.md` ;
- mode sombre de l’application ;
- refonte du logo ou de l’identité visuelle ;
- modification des fichiers golden de rendu.

## Vue synthétique de l’IHM cible

### Visible au premier écran

- logo, nom, `v1.0.0`, langue et aide ;
- ajout et liste des fichiers ;
- fichier actif, page courante et navigation de l’aperçu ;
- résumés du style et de la destination ;
- état global ;
- bouton **⚙ Générer** et barre de progression toujours visibles.

### Présenté progressivement

- choix thème/CSS ;
- six champs d’en-tête et de pied ;
- date et HTML statique de confiance ;
- détails des erreurs ;
- diagnostics ;
- informations techniques complètes.

### Accomplissable en moins de trois actions

- sélectionner un fichier puis générer son PDF ;
- déposer un fichier puis générer ;
- changer le fichier prévisualisé ;
- actualiser ou ajuster le zoom ;
- choisir une destination ;
- changer la langue ;
- consulter la version ;
- ouvrir le signalement et copier un rapport prérempli.
