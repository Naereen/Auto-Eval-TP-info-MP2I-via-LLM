# Auto Évaluation de TP d'informatique (en MP2I), via LLM

> **Expérimentation** : peut-on construire rapidement un outil d'aide à l'évaluation de rendus (code + md/PDF) de TP notés, en classe de MP2I, qui évaluerait une partie du code via des appels à LLM ? Via le service [ILASS](https://www.ilaas.fr/) et des modèles open-weight tels que [gpt-oss-120b](https://huggingface.co/openai/gpt-oss-120b), ou via Google AI's Gemini.

## Objectif

Ce dépôt contient un dashboard Streamlit destiné à aider un enseignant à :

- parcourir les sujets de TP disponibles ;
- consulter les rendus étudiants ;
- construire un barème par TP ;
- saisir ou pré-remplir une notation ;
- sauvegarder les évaluations ;
- visualiser des statistiques à l'échelle d'un TP ou d'un étudiant.

## Fonctionnalités actuellement disponibles

### Navigation générale

Le dashboard permet de :

- ouvrir un mode `0 - Documentation` directement dans l'application pour relire son fonctionnement ;
- sélectionner un TP parmi ceux présents dans `sujets-de-travaux-pratiques` ;
- choisir un mode de travail dans la navigation latérale ;

### Mode `0 - Documentation`

Le mode Documentation permet de :

- expliquer l'ordre conseillé d'utilisation du dashboard ;
- rappeler le rôle de chaque mode ;
- documenter les fichiers attendus dans le dépôt ;
- préciser où sont sauvegardés `bareme.json` et `notes.json` ;
- résumer la place des fonctionnalités d'assistance par IA dans le flux de travail.

### Mode `1 - Barème`

Le mode Barème permet de :

- définir le nombre de questions pour le TP courant ;
- attribuer jusqu'à 100 points par question ;
- renommer manuellement chaque question ;
- partir d'une configuration par défaut adaptée aux TP courants : 10 questions, 5 points chacune ;
- appliquer rapidement une même valeur à toutes les questions ;
- proposer un barème automatique par IA à partir du sujet ;
- injecter directement le JSON renvoyé dans l'éditeur courant ;
- sauvegarder le résultat dans `sujets-de-travaux-pratiques/<tp>/bareme.json` ;
- conserver le sujet PDF visible pendant l'édition grâce à une zone défilable dédiée au barème.

### Mode `2 - Évaluation des rendus`

Le mode Évaluation des rendus permet de :

- sélectionner un rendu étudiant dans `rendus-des-etudiants/<tp>/` ;
- afficher le code source rendu (`code_rendu.c` ou `code_rendu.ml`) avec coloration syntaxique ;
- afficher le compte-rendu PDF de l'étudiant, avec repli sur le Markdown si le PDF n'existe pas encore ;
- utiliser le barème du TP pour saisir, question par question, les points attribués ;
- calculer automatiquement le total obtenu et la note sur 20 ;
- proposer une notation automatique par IA à partir du sujet, de ses sources, du `bareme.json`, du code rendu et du compte-rendu étudiant ;
- injecter directement le JSON renvoyé dans l'éditeur courant ;
- sauvegarder la notation dans `rendus-des-etudiants/<tp>/<rendu>/notes.json` ;
- recharger automatiquement cette notation lors d'une réouverture du rendu.

### Mode `3 - Vue de la classe par TP`

Le mode Vue de la classe par TP permet de :

- agréger les `notes.json` déjà sauvegardés pour le TP courant ;
- afficher le nombre de rendus détectés, le nombre d'évaluations sauvegardées et les rendus encore en attente ;
- calculer la moyenne, la médiane, le minimum, le maximum et l'écart-type des notes ;
- détailler les statistiques question par question ;
- visualiser la répartition des notes et la dispersion des résultats avec des graphiques intégrés.

### Mode `4 - Progression annuelle individuelle`

Le mode Progression annuelle individuelle permet de :

- sélectionner un étudiant parmi tous les rendus détectés ;
- agréger ses `notes.json` sur l'ensemble des TP ;
- afficher sa moyenne annuelle non pondérée, ses notes extrêmes, sa médiane et son écart-type ;
- calculer une pente de tendance par régression linéaire simple ;
- visualiser l'évolution de ses notes et de son taux de réussite au fil de l'année.

## Fichiers persistés par le dashboard

- `sujets-de-travaux-pratiques/<tp>/bareme.json` : barème normalisé du TP ;
- `rendus-des-etudiants/<tp>/<rendu>/notes.json` : notation normalisée d'un rendu étudiant.

## Documentation du projet

- Les commentaires et docstrings dans le code Python sont rédigés en anglais, afin de garder une documentation technique homogène.
- Les textes destinés à l'utilisateur final restent en français correct et accentué.
- `README.md` documente uniquement les fonctionnalités déjà présentes dans le projet.
- `TODO.md` recense ce qu'il reste à implémenter, tester, fiabiliser ou corriger.
- Toute évolution fonctionnelle du projet doit s'accompagner d'une mise à jour de la documentation pertinente dans ce dépôt.

## Lancement local

Depuis la racine du dépôt :

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Le dashboard découvre automatiquement les dossiers de TP et les rendus disponibles.

## Feuille de route et vérifications restantes

La liste des développements, tests et points de fiabilisation encore ouverts se trouve dans [TODO.md](./TODO.md).

----

## :scroll: License ? [![GitHub license](https://img.shields.io/github/license/Naereen/Auto-Eval-TP-info-MP2I-via-LLM.svg)](https://github.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM/blob/master/LICENSE)

[MIT Licensed](https://lbesson.mit-license.org/) (file [LICENSE](LICENSE)).
© [Lilian Besson](https://GitHub.com/Naereen), 2026.

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM/graphs/commit-activity)
[![Ask Me Anything !](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](https://GitHub.com/Naereen/ama)

[![ForTheBadge built-with-swag](http://ForTheBadge.com/images/badges/built-with-swag.svg)](https://GitHub.com/Naereen/)
[![ForTheBadge uses-badges](http://ForTheBadge.com/images/badges/uses-badges.svg)](http://ForTheBadge.com)
[![ForTheBadge uses-git](http://ForTheBadge.com/images/badges/uses-git.svg)](https://GitHub.com/)

