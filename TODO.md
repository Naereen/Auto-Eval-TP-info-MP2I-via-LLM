# TODO

Ce document ne décrit pas les fonctionnalités déjà livrées. Il recense uniquement ce qu'il reste à implémenter, fiabiliser, tester ou clarifier.

## À implémenter

- [ ] Supporter des TP qui demandent des rendus de code source en plusieurs fichiers (exemple : `graph.c` + `graph.h`, et `stack.c` + `stack.h`, et `euler.c` pour le TP38).

----

## Tester *automatiquement* toutes les questions de programmation d'un TP donné ?

### 1) Exécuter "dans une sandbox safe" un programme après l'avoir compilé localement

Je peux isoler les exécution via [`nsjail`](https://nsjail.dev/), et utiliser les modules sus-nommés pour écrire des tests d'un TP en OCaml ou en C.

#### Pour OCaml ?

```bash
ocamlopt -ccopt -static -o /tmp/test_ocaml.exe ./code_rendu.ml
nsjail --config ./nsjail_config.cfg -- /tmp/test_ocaml.exe
```

- [ ] faire aussi la compilation `ocamlopt` derrière la "safe sandbox" de nsjail ?
- [ ] faire aussi la compilation `ocamlc` derrière la "safe sandbox" de nsjail ?
- [ ] faire aussi l'interprértation (terminal `ocaml`) derrière la "safe sandbox" de nsjail ?

#### Pour le C ?

```bash
gcc -Wall -Wextra -Wvla -fsanitize=address,undefined -o /tmp/test_c.exe ./code_rendu.c -lm
nsjail --config ./nsjail_config.cfg -- /tmp/test_c.exe
```

TODO: faire aussi la compilation `gcc` derrière la "safe sandbox" de nsjail ?

### 2) Supporter des fichiers de tests, fournis préalablement et écrits à la main (par AlcoTesT/QCheck en OCaml, et AFL++ et Criterion en C)

#### Pour OCaml ?

Un premier exemple est maintenant présent pour `rendus-des-etudiants/03-types-polymorphes-etc-ocaml/dune_tests/`, avec `dune`, `alcotest`, `qcheck` et `qcheck-alcotest`.

Le dashboard permet déjà, pour un rendu OCaml sélectionné (un étudiant fixé), de compiler le fichier, de l'exécuter dans [NsJail](https://nsjail.dev/) (un outil de "sandbox sécurisée"), et de lancer les tests OCaml (qui fonctionnent avec Dune, Alcotest et QCheck) préparés à la main, tout en conservant et en affichant joliment les logs.

- [ ] Généraliser cette infrastructure de tests OCaml aux autres rendus et autres TP.

```bash
ocamlopt -ccopt -static -o /tmp/test_ocaml.exe ./code_rendu.ml
nsjail --config ./nsjail_config.cfg -- ./test_ocaml.exe
```

#### Pour le C ?

TODO: intégrer Criterion et AFL++

```bash
gcc -Wall -Wextra -Wvla -fsanitize=address,undefined -o /tmp/test_c.exe ./code_rendu.c -lm
nsjail --config ./nsjail_config.cfg -- ./test_c.exe
```

----

## À fiabiliser ou corriger (pas urgent)

- [ ] Affiner la génération automatique du barème par LLM/IA à partir du sujet LaTeX, Markdown ou PDF.
- [ ] Affiner la notation automatique par LLM/IA à partir du sujet, du barème, du code rendu et du compte-rendu étudiant.
- [ ] Vérifier la robustesse des réponses JSON retournées par l'IA quand certaines pièces jointes sont absentes.
- [ ] Mieux gérer les cas limites où un TP existe sans sujet PDF, sans sources complémentaires, ou avec des rendus partiels.

## À corriger (bugs urgents)

Rien ?

------

## Tests manuels à faire

## Tester le mode Documentation

- [ ] Vérifier que le mode `0 - Documentation` reste accessible même si aucun TP n'est détecté.
- [ ] Vérifier que les explications sur les modes, les fichiers attendus et les fichiers générés sont cohérentes avec le comportement réel du dashboard.

## Tester le mode Génération automatisée de tests OCaml

- [ ] Vérifier que le mode `2 - Génération automatisée de tests OCaml` reste accessible pour un TP OCaml même si aucun `test_code_rendu.ml` n'existe encore.
- [ ] Vérifier que la génération IA écrit bien `dune_tests/test_code_rendu.ml` sans écraser un fichier existant.
- [ ] Vérifier que les fichiers `dune` et `dune-project` sont créés ou conservés correctement dans `dune_tests/`.
- [ ] Vérifier que la prévisualisation du fichier de tests généré reste lisible après sauvegarde.
- [ ] Vérifier que le mode refuse de réécrire un banc de tests déjà préparé à la main.

## Tester le mode Barème

- [ ] Vérifier le rechargement automatique de `bareme.json` au redémarrage du dashboard.
- [ ] Vérifier l'ajustement du nombre de questions sans perdre les points déjà saisis.
- [ ] Vérifier que le renommage manuel des questions est bien conservé dans l'éditeur puis dans `bareme.json`.
- [ ] Vérifier la mise à jour globale du barème avec une valeur unique pour toutes les questions.
- [ ] Vérifier que le bouton de proposition automatique par IA injecte bien le JSON renvoyé dans l'éditeur du barème courant.
- [ ] Vérifier l'ergonomie de la zone défilable quand le barème contient beaucoup de questions.

## Tester le mode Évaluation des rendus

- [ ] Vérifier que chaque question reprend bien le maximum défini dans le barème du TP.
- [ ] Vérifier qu'à l'ouverture initiale du mode `Évaluation des rendus`, le premier étudiant affiché recharge immédiatement ses valeurs depuis `notes.json`.
- [ ] Vérifier que le bouton de proposition automatique par IA injecte bien le JSON renvoyé dans l'éditeur de notation courant.
- [ ] Vérifier que le total obtenu et la note sur 20 se mettent à jour après chaque saisie.
- [ ] Vérifier que le changement d'étudiant conserve une saisie indépendante pour chaque rendu.
- [ ] Vérifier la sauvegarde de `notes.json` dans le dossier de rendu de l'étudiant.
- [ ] Vérifier le rechargement automatique de `notes.json` lors du retour sur un rendu déjà évalué.

## Tester le mode Vue de la classe par TP

- [ ] Vérifier que la vue n'agrège que les rendus disposant d'un `notes.json`.
- [ ] Vérifier que les statistiques globales (moyenne, médiane, min, max, écart-type) sont cohérentes avec les notes sauvegardées.
- [ ] Vérifier que les statistiques par question respectent bien le barème du TP courant.
- [ ] Vérifier que les graphiques restent lisibles quand le nombre d'étudiants ou de questions augmente.

## Tester le mode Progression annuelle individuelle

- [ ] Vérifier que la vue n'agrège que les TP disposant d'un `notes.json` pour l'étudiant choisi.
- [ ] Vérifier que la moyenne annuelle est bien une moyenne non pondérée des notes par TP.
- [ ] Vérifier la cohérence des statistiques globales de l'étudiant : min, max, médiane, écart-type.
- [ ] Vérifier que la pente de tendance affichée est cohérente avec les notes observées.
- [ ] Vérifier que les graphiques restent lisibles quand un étudiant a beaucoup de TP notés sur l'année.

## Dette documentaire et conventions

- [ ] Garder les commentaires et docstrings Python en anglais.
- [ ] Mettre à jour `README.md` et `TODO.md` en même temps que les évolutions fonctionnelles.
- [ ] Réserver `README.md` aux fonctionnalités effectivement présentes dans le projet.
- [ ] Réserver `TODO.md` aux travaux restants, validations manuelles et points de robustesse.
- [ ] Conserver les textes visibles dans l'interface en français correct et accentué.
