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
3. Facultatif : sélectionnez **Changer** pour utiliser un fichier CSS personnel.
4. Facultatif : ouvrez **En-tête et pied de page (avancé)** et modifiez les six
   positions.
5. Sélectionnez **Actualiser l’aperçu** pour afficher la première page.
6. Facultatif : choisissez un dossier de sortie. Sinon, chaque PDF est créé à
   côté de sa source Markdown.
7. Sélectionnez **Générer le PDF**.

La zone d’état indique le nombre de conversions réussies et échouées. En cas
d’échec, la boîte de dialogue précise le fichier source et l’erreur rencontrée.
Les autres fichiers du lot continuent d’être traités.

## Jetons d’en-tête et de pied de page

Le pied de page central par défaut est `Page {page} / {total}`. Un champ vide
n’affiche rien.

| Jeton | Valeur |
| --- | --- |
| `{titre}` ou `{title}` | Premier titre de niveau 1 (`#`) |
| `{date}` | Date locale du rendu au format `AAAA-MM-JJ` |
| `{page}` | Numéro de la page courante |
| `{total}` | Nombre total de pages |

Vous pouvez associer du texte aux jetons, par exemple :

```text
{titre} — Page {page} / {total}
```

## Ligne de commande

Depuis les sources, utilisez `python -m libremark_pdf`. Avec un exécutable
construit en mode console, remplacez ce préfixe par le chemin de l’exécutable.

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
```

La CLI ne pose aucune question. Le code de sortie `0` signifie que toutes les
conversions demandées ont réussi. Avec `--json`, stdout contient un objet pour
un fichier ou un objet `{"results": [...]}` pour un lot. Chaque résultat contient
`input`, `output`, `status` et `error`.

Pour afficher toutes les options :

```bash
python -m libremark_pdf convert --help
```

## Préférence de langue

Sélectionnez **EN** ou **FR** dans la fenêtre. Le choix est enregistré localement
dans `~/.libremark-pdf/config.json`. Un échec d’enregistrement n’empêche pas la
conversion.

## Fichiers et sécurité

- Utilisez des fichiers Markdown encodés en UTF-8.
- Un CSS personnalisé s’applique à tout le document : utilisez une source de
  confiance.
- Le prototype actuel peut remplacer un PDF existant portant le nom de sortie.
  Conservez une sauvegarde tant que la protection contre l’écrasement n’est pas
  implémentée.
- La sécurisation du rendu n’est pas terminée. Considérez pour le moment le
  HTML brut, les ressources liées et le Markdown tiers comme du contenu fiable.
- La construction télécharge les paquets Python et Chromium. La conversion est
  conçue pour employer des ressources locales, mais le blocage strict du réseau
  n’est pas encore validé dans ce prototype.

## Résolution des problèmes

- **Un fichier déposé est ignoré :** vérifiez son extension `.md` ou
  `.markdown`.
- **L’aperçu échoue :** vérifiez l’installation de Chromium et de `pypdfium2`,
  puis consultez l’erreur complète dans la zone d’état.
- **Le CSS est introuvable :** choisissez un fichier `.css` existant ou
  rétablissez le style intégré.
- **L’application se ferme sous Windows :** exécutez `build.bat --console`, puis
  lancez `dist\LibreMarkPDF.exe` depuis cette console pour obtenir le traceback.
- **Un tableau revient à la ligne de manière inattendue :** le style par défaut
  utilise une mise en page fixe ; un contenu long peut augmenter la pagination.

Pour signaler un bug, conservez la commande exacte, le code de sortie, le texte
de l’erreur, le système d’exploitation, la version de Python et le mode
d’exécution (sources ou artefact). N’incluez pas de contenu confidentiel sans
nécessité.
