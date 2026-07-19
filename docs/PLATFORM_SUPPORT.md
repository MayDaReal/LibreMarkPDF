# Platform support

Windows x64 est la première plateforme candidate obligatoire. Un artefact
Windows doit être construit et validé sur Windows natif, hors du checkout,
avec son navigateur embarqué et sans Python ni cache Playwright disponibles au
runtime.

Linux x86_64 est une lane candidate séparée. Le tarball portable est testé sur
une matrice explicitement déclarée ; aucune compatibilité Linux générale n'est
promise tant que cette matrice n'est pas validée. macOS reste hors périmètre.

Les payloads Playwright sont eux aussi natifs. Un checkout partagé conserve
donc les ressources générées Windows dans `browser-win/` et Linux dans
`browser-linux/`. Ces deux répertoires sont ignorés par Git.

Les artefacts de plateformes différentes ne sont pas interchangeables. La
comparaison canonique vérifie l'équivalence structurelle et visuelle ; elle ne
promet pas une identité binaire des PDF.
