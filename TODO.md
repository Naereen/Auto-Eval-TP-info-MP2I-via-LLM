# TODO

## Fonctionnalités supplémentaires

- TODO: Je veux pouvoir supporter des TP qui demanderaient des rendus de code source en *plusieurs fichiers*.

- [x] pré-remplissage du mode barème par une proposition JSON issue d'un LLM/IA, avec injection directe dans l'éditeur courant.
- TODO: fiabiliser et affiner la génération automatique du barème par LLM/IA depuis la lecture du sujet (LaTeX ou PDF).

- TODO: l'analyse du code et du compte-rendu (Markdown ou PDF) de chaque étudiant, pour l'évaluer semi-automatiquement par des appels à un LLM/IA,

- [x] l'ajout de vues des notes de la classe pour un TP fixé et donné.

- [x] l'ajout d'une vue de progression annuelle individuelle au fil des TP.
- TODO: l'ajout de statistiques de cohorte classe au fil de l'année.

-----------------------------------------------------

## Tester le mode Barème

- Vérifier le rechargement automatique de `bareme.json` au redémarrage du dashboard.
- Vérifier l'ajustement du nombre de questions sans perdre les points déjà saisis.
- Vérifier la mise à jour globale du barème avec une valeur unique pour toutes les questions.
- Vérifier que le bouton de proposition automatique par IA injecte bien le JSON renvoyé dans l'éditeur du barème courant.
- Vérifier l'ergonomie de la zone défilable quand le barème contient beaucoup de questions.

## Tester le mode Évaluation des rendus

- Vérifier que chaque question reprend bien le maximum défini dans le barème du TP.
- Vérifier que le total obtenu et la note sur 20 se mettent à jour après chaque saisie.
- Vérifier que le changement d'étudiant conserve une saisie indépendante pour chaque rendu.
- Vérifier la sauvegarde de `notes.json` dans le dossier de rendu de l'étudiant.
- Vérifier le rechargement automatique de `notes.json` lors du retour sur un rendu déjà évalué.

## Tester le mode Vue de la classe par TP

- Vérifier que la vue n'agrège que les rendus disposant d'un `notes.json`.
- Vérifier que les statistiques globales (moyenne, médiane, min, max, écart-type) sont cohérentes avec les notes sauvegardées.
- Vérifier que les statistiques par question respectent bien le barème du TP courant.
- Vérifier que les graphiques restent lisibles quand le nombre d'étudiants ou de questions augmente.

## Tester le mode Progression annuelle individuelle

- Vérifier que la vue n'agrège que les TP disposant d'un `notes.json` pour l'étudiant choisi.
- Vérifier que la moyenne annuelle est bien une moyenne non pondérée des notes par TP.
- Vérifier la cohérence des statistiques globale de l'étudiant : min, max, médiane, écart-type.
- Vérifier que les graphiques restent lisibles quand un étudiant a beaucoup de TP notés sur l'année.

-----------------------------------------------------

## Maintenir la documentation

- Garder les commentaires et docstrings Python en anglais.
- Mettre à jour `README.md` et `TODO.md` en même temps que les évolutions fonctionnelles.
- Conserver les textes visibles dans l'interface en français correct et accentué.
