# TODO

## Fonctionnalités supplémentaires

- TODO: Je veux pouvoir supporter des TP qui demanderaient des rendus de code source en *plusieurs fichiers*.

- TODO: amélioration du mode barème : calcul automatique d'un barème question par question, par un/des appels à un LLM/IA, depuis la lecture automatique du sujet (LaTeX ou PDF) ;

- TODO: l'analyse du code et du compte-rendu (Markdown ou PDF) de chaque étudiant, pour l'évaluer semi-automatiquement par des appels à un LLM/IA,

- TODO: l'ajout de vues des notes de la classe et de statistiques de progression individuelles au fil des TP, ou de la cohorte classe au fil de l'année.

-----------------------------------------------------

## Tester le mode Barème

- Vérifier le rechargement automatique de `bareme.json` au redémarrage du dashboard.
- Vérifier l'ajustement du nombre de questions sans perdre les points déjà saisis.
- Vérifier la mise à jour globale du barème avec une valeur unique pour toutes les questions.
- Vérifier l'ergonomie de la zone défilable quand le barème contient beaucoup de questions.

## Tester le mode Évaluation des rendus

- Vérifier que chaque question reprend bien le maximum défini dans le barème du TP.
- Vérifier que le total obtenu et la note sur 20 se mettent à jour après chaque saisie.
- Vérifier que le changement d'étudiant conserve une saisie indépendante pour chaque rendu.
- Vérifier la sauvegarde de `notes.json` dans le dossier de rendu de l'étudiant.
- Vérifier le rechargement automatique de `notes.json` lors du retour sur un rendu déjà évalué.

-----------------------------------------------------

## Maintenir la documentation

- Garder les commentaires et docstrings Python en anglais.
- Mettre à jour `README.md` et `TODO.md` en même temps que les évolutions fonctionnelles.
- Conserver les textes visibles dans l'interface en français correct et accentué.
