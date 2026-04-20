# Auto Évaluation de TP d'informatique (en MP2I), via LLM

> **Expérimentation** : peut-on construire rapidement un outil d'aide à l'évaluation de rendus (code + md/PDF) de TP notés, en classe de MP2I, qui évaluerait une partie du code via des appels à LLM ? Via le service [ILASS](https://www.ilaas.fr/) et des modèles open-weight tels que [gpt-oss-120b](https://huggingface.co/openai/gpt-oss-120b), ou via Google AI's Gemini.

## Fonctionnalités

Premier jet disponible : un dashboard Streamlit en Python 3 permet de

- sélectionner un TP parmi ceux présents dans `sujets-de-travaux-pratiques` ;
- choisir un mode de travail dans la navigation latérale ;
- utiliser le mode `Barème` pour définir le nombre de questions, attribuer jusqu'à 100 points par question, voir le total et sauvegarder le résultat dans `sujets-de-travaux-pratiques/<tp>/bareme.json` ;
- renommer manuellement chaque question du barème pour faire apparaître un libellé métier ou la numérotation exacte du sujet ;
- profiter de valeurs par défaut adaptées aux TP courants, avec 10 questions initiales et 5 points par question ;
- appliquer rapidement une même valeur à toutes les questions du barème à l'aide d'un bouton dédié et d'un unique champ numérique ;
- proposer un barème automatique par IA à partir du sujet, puis injecter directement le JSON renvoyé dans l'éditeur courant avant une éventuelle sauvegarde manuelle ;
- faire défiler la liste des questions du barème dans une zone dédiée, tout en gardant le sujet PDF visible dans la colonne de gauche ;
- utiliser le mode `Évaluation des rendus` pour sélectionner un rendu étudiant dans `rendus-des-etudiants/<tp>/` ;
- utiliser le barème défini dans le mode `Barème` pour saisir, question par question, les points attribués à un rendu étudiant ;
- calculer automatiquement le total obtenu et afficher une note sur 20 dans la colonne d'évaluation, ainsi que dans les indicateurs affichés en haut de la vue ;
- sauvegarder la notation d'un étudiant dans `rendus-des-etudiants/<tp>/<rendu>/notes.json` et la recharger automatiquement lors d'une réouverture ;
- utiliser le mode `Vue de la classe par TP` pour synthétiser les notes déjà sauvegardées de toute la classe sur un TP donné ;
- visualiser la moyenne générale, la médiane, le minimum, le maximum, l'écart-type, ainsi que les statistiques détaillées question par question ;
- afficher plusieurs graphiques Streamlit directement dans le dashboard pour comparer les notes par étudiant, avec un dégradé rouge-bleu sur les notes globales, la moyenne par question et la dispersion des résultats ;
- utiliser le mode `Progression annuelle individuelle` pour suivre, TP après TP, la trajectoire d'un étudiant sur l'ensemble de l'année ;
- afficher pour cet étudiant sa moyenne annuelle non pondérée, ses notes minimale et maximale, sa médiane, son écart-type et une visualisation de sa tendance ;
- afficher le code source rendu (`code_rendu.c` ou `code_rendu.ml`) avec coloration syntaxique ;
- afficher le compte-rendu PDF de l'étudiant, avec repli sur le Markdown si le PDF n'existe pas encore.

## Documentation du projet

- Les commentaires et docstrings dans le code Python sont rédigés en anglais, afin de garder une documentation technique homogène.
- Les textes destinés à l'utilisateur final restent en français correct et accentué.
- Toute évolution fonctionnelle du projet doit s'accompagner d'une mise à jour de la documentation pertinente dans ce dépôt, en particulier dans `README.md`, `TODO.md` et dans les commentaires utiles du code.

## Lancement local

Depuis la racine du dépôt :

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Le dashboard découvre automatiquement les dossiers de TP et les rendus disponibles.

----

## TODO et idées

La liste des idées et des choses à faire pour ce projet se trouve ici : [TODO.md](./TODO.md).

----

## :scroll: License ? [![GitHub license](https://img.shields.io/github/license/Naereen/Auto-Eval-TP-info-MP2I-via-LLM.svg)](https://github.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM/blob/master/LICENSE)

[MIT Licensed](https://lbesson.mit-license.org/) (file [LICENSE](LICENSE)).
© [Lilian Besson](https://GitHub.com/Naereen), 2026.

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM/graphs/commit-activity)
[![Ask Me Anything !](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](https://GitHub.com/Naereen/ama)

[![ForTheBadge built-with-swag](http://ForTheBadge.com/images/badges/built-with-swag.svg)](https://GitHub.com/Naereen/)
[![ForTheBadge uses-badges](http://ForTheBadge.com/images/badges/uses-badges.svg)](http://ForTheBadge.com)
[![ForTheBadge uses-git](http://ForTheBadge.com/images/badges/uses-git.svg)](https://GitHub.com/)

