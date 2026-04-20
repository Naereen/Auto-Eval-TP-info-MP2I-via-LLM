# TODO

Ce document ne décrit pas les fonctionnalités déjà livrées. Il recense uniquement ce qu'il reste à implémenter, fiabiliser, tester ou clarifier.

## À implémenter

- Supporter des TP qui demandent des rendus de code source en plusieurs fichiers.
- Ajouter une vue de statistiques de cohorte à l'échelle de l'année.

## À fiabiliser ou corriger

- Affiner la génération automatique du barème par LLM/IA à partir du sujet LaTeX, Markdown ou PDF.
- Affiner la notation automatique par LLM/IA à partir du sujet, du barème, du code rendu et du compte-rendu étudiant.
- Vérifier la robustesse des réponses JSON retournées par l'IA quand certaines pièces jointes sont absentes.
- Mieux gérer les cas limites où un TP existe sans sujet PDF, sans sources complémentaires, ou avec des rendus partiels.

## Tests manuels à faire

## Tester le mode Barème

- Vérifier le rechargement automatique de `bareme.json` au redémarrage du dashboard.
- Vérifier l'ajustement du nombre de questions sans perdre les points déjà saisis.
- Vérifier que le renommage manuel des questions est bien conservé dans l'éditeur puis dans `bareme.json`.
- Vérifier la mise à jour globale du barème avec une valeur unique pour toutes les questions.
- Vérifier que le bouton de proposition automatique par IA injecte bien le JSON renvoyé dans l'éditeur du barème courant.
- Vérifier l'ergonomie de la zone défilable quand le barème contient beaucoup de questions.

## Tester le mode Évaluation des rendus

- Vérifier que chaque question reprend bien le maximum défini dans le barème du TP.
- Vérifier que le bouton de proposition automatique par IA injecte bien le JSON renvoyé dans l'éditeur de notation courant.
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
- Vérifier la cohérence des statistiques globales de l'étudiant : min, max, médiane, écart-type.
- Vérifier que la pente de tendance affichée est cohérente avec les notes observées.
- Vérifier que les graphiques restent lisibles quand un étudiant a beaucoup de TP notés sur l'année.

## Dette documentaire et conventions

- Garder les commentaires et docstrings Python en anglais.
- Mettre à jour `README.md` et `TODO.md` en même temps que les évolutions fonctionnelles.
- Réserver `README.md` aux fonctionnalités effectivement présentes dans le projet.
- Réserver `TODO.md` aux travaux restants, validations manuelles et points de robustesse.
- Conserver les textes visibles dans l'interface en français correct et accentué.
