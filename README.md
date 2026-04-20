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

## Quel genre de sujets de TP et de rendus par étudiants ?

J'ai intégré un seul exemple d'un de mes petits sujets de TP, et de trois (faux) rendus d'étudiants, dans ces dossiers :

- [sujets-de-travaux-pratiques/03-types-polymorphes-etc-ocaml/](sujets-de-travaux-pratiques/03-types-polymorphes-etc-ocaml/) : [TP3.md](sujets-de-travaux-pratiques/03-types-polymorphes-etc-ocaml/TP3.md), [TP3.pdf](sujets-de-travaux-pratiques/03-types-polymorphes-etc-ocaml/TP3.pdf), et son [bareme.json](sujets-de-travaux-pratiques/03-types-polymorphes-etc-ocaml/bareme.json) qui a été généré automatiquement par Google Gemini (et un prompt bien choisi) ;

- [rendus-des-etudiants/03-types-polymorphes-etc-ocaml/](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/) qui contient des rendus synthétiques de trois faux étudiants : un étudiant excellent qui produit quasiment un corrigé, un étudiant plutôt moyen et un étudiant au niveau très bas :

  1. [Étudiant excellent](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT1_Etudiant1/) : [son rendu en Markdown](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT1_Etudiant1/compte_rendu.md), [et compilé en PDF](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT1_Etudiant1/compte_rendu.pdf), [son code (en OCaml sur cet exemple)](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT1_Etudiant1/compte_rendu.md), et [ses notes (encore générées automatiquement par IA !)](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT1_Etudiant1/notes.json) 
  2. [Étudiant moyen](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT2_Etudiant2/) : [son rendu en Markdown](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT2_Etudiant2/compte_rendu.md), [et compilé en PDF](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT2_Etudiant2/compte_rendu.pdf), [son code (en OCaml sur cet exemple)](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT2_Etudiant2/compte_rendu.md), et [ses notes (encore générées automatiquement par IA !)](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT2_Etudiant2/notes.json) 
  3. [Étudiant plutôt faible](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT3_Etudiant3/) : [son rendu en Markdown](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT3_Etudiant3/compte_rendu.md), [et compilé en PDF](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT3_Etudiant3/compte_rendu.pdf), [son code (en OCaml sur cet exemple)](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT3_Etudiant3/compte_rendu.md), et [ses notes (encore générées automatiquement par IA !)](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT3_Etudiant3/notes.json) 

--------

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

![documentation-screenshotsdocumentation-mode-0-documentation-intégrée-1.png](documentation-screenshotsdocumentation-mode-0-documentation-intégrée-1.png)
![documentation-screenshotsdocumentation-mode-0-documentation-intégrée-2.png](documentation-screenshotsdocumentation-mode-0-documentation-intégrée-2.png)

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

![documentation-mode-1-conception-barème-assisté-par-IA-1.png](documentation-mode-1-conception-barème-assisté-par-IA-1.png)
![documentation-mode-1-conception-barème-assisté-par-IA-3.png](documentation-mode-1-conception-barème-assisté-par-IA-3.png)

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

![documentation-mode-2-évaluation-rendus-par-étudiant-1.png](documentation-mode-2-évaluation-rendus-par-étudiant-1.png)
![documentation-mode-2-évaluation-rendus-par-étudiant-2.png](documentation-mode-2-évaluation-rendus-par-étudiant-2.png)

### Mode `3 - Vue de la classe par TP`

Le mode Vue de la classe par TP permet de :

- agréger les `notes.json` déjà sauvegardés pour le TP courant ;
- afficher le nombre de rendus détectés, le nombre d'évaluations sauvegardées et les rendus encore en attente ;
- calculer la moyenne, la médiane, le minimum, le maximum et l'écart-type des notes ;
- détailler les statistiques question par question ;
- visualiser la répartition des notes et la dispersion des résultats avec des graphiques intégrés.

![documentation-mode-3-vue-classe-par-TP-1.png](documentation-mode-3-vue-classe-par-TP-1.png)

### Mode `4 - Progression annuelle individuelle`

Le mode Progression annuelle individuelle permet de :

- sélectionner un étudiant parmi tous les rendus détectés ;
- agréger ses `notes.json` sur l'ensemble des TP ;
- afficher sa moyenne annuelle non pondérée, ses notes extrêmes, sa médiane et son écart-type ;
- calculer une pente de tendance par régression linéaire simple ;
- visualiser l'évolution de ses notes et de son taux de réussite au fil de l'année.

![documentation-mode-4-progression-individuelle-annuelle-1.png](documentation-mode-4-progression-individuelle-annuelle-1.png)

------

## Fichiers persistés par le dashboard

- `sujets-de-travaux-pratiques/<tp>/bareme.json` : barème normalisé du TP. Cf. [cet exemple si besoin](sujets-de-travaux-pratiques/03-types-polymorphes-etc-ocaml/bareme.json) (généré par IA via Google Gemini !) ;


```json
{
  "format_version": 1,
  "tp_name": "03-types-polymorphes-etc-ocaml",
  "question_count": 29,
  "total_points": 100,
  "questions": [
    {
      "index": 1,
      "label": "Question 1.1",
      "points": 1
    },
    {
      "index": 11,
      "label": "Question 2.1",
      "points": 1
    },
    ...
    {
      "index": 29,
      "label": "Question 4.7",
      "points": 10
    }
  ]
}

```

- `rendus-des-etudiants/<tp>/<rendu>/notes.json` : notation normalisée d'un rendu étudiant. Cf. [cet exemple si besoin](rendus-des-etudiants/03-types-polymorphes-etc-ocaml/ETUDIANT1_Etudiant1/notes.json) (généré semi-automatiquement par IA via Google Gemini !) ;

```json
{
  "format_version": 1,
  "tp_name": "03-types-polymorphes-etc-ocaml",
  "student_name": "ETUDIANT1_Etudiant1",
  "question_count": 29,
  "total_points_awarded": 92,
  "total_points_bareme": 100,
  "note_sur_20": 18.4,
  "questions": [
    {
      "index": 1,
      "label": "Question 1.1",
      "max_points": 1,
      "points_awarded": 1
    },
    ...
    {
      "index": 29,
      "label": "Question 4.7",
      "max_points": 10,
      "points_awarded": 8
    }
  ]
}
```

## Documentation du projet

- Les commentaires et docstrings dans le code Python sont rédigés en anglais, afin de garder une documentation technique homogène.
- Les textes destinés à l'utilisateur final restent en français correct et accentué.
- `README.md` documente uniquement les fonctionnalités déjà présentes dans le projet.
- `TODO.md` recense ce qu'il reste à implémenter, tester, fiabiliser ou corriger.
- Toute évolution fonctionnelle du projet doit s'accompagner d'une mise à jour de la documentation pertinente dans ce dépôt.

## Lancement local

Depuis la racine du dépôt, il devrait suffire de faire :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py --server.port 8765
```

Le dashboard s'ouvre tout seul, sur l'adresse http://localhost:8765/, puis découvre automatiquement les dossiers de TP et les rendus disponibles.

------

## Feuille de route et vérifications restantes

La liste des développements, tests et points de fiabilisation encore ouverts se trouve dans [`TODO.md`](./TODO.md).

----

## :scroll: License ? [![GitHub license](https://img.shields.io/github/license/Naereen/Auto-Eval-TP-info-MP2I-via-LLM.svg)](https://github.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM/blob/master/LICENSE)

[MIT Licensed](https://lbesson.mit-license.org/) (file [LICENSE](LICENSE)).
© [Lilian Besson](https://GitHub.com/Naereen), 2026.

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/Auto-Eval-TP-info-MP2I-via-LLM/graphs/commit-activity)
[![Ask Me Anything !](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](https://GitHub.com/Naereen/ama)

[![ForTheBadge built-with-swag](http://ForTheBadge.com/images/badges/built-with-swag.svg)](https://GitHub.com/Naereen/)
[![ForTheBadge uses-badges](http://ForTheBadge.com/images/badges/uses-badges.svg)](http://ForTheBadge.com)
[![ForTheBadge uses-git](http://ForTheBadge.com/images/badges/uses-git.svg)](https://GitHub.com/)

