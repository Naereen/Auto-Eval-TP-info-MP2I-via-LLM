# Auto Évaluation de TP d'informatique (en MP2I), via LLM

> **Expérimentation** : peut-on construire rapidement un outil d'aide à l'évaluation de rendus (code + md/PDF) de TP notés, en classe de MP2I, qui évaluerait une partie du code via des appels à LLM ? Via le service [ILASS](https://www.ilaas.fr/) et des modèles open-weight tels que [gpt-oss-120b](https://huggingface.co/openai/gpt-oss-120b).

## Fonctionnalités

Premier jet disponible : un dashboard Streamlit en Python 3 permet de

- sélectionner un TP parmi ceux présents dans `sujets-de-travaux-pratiques` ;
- afficher le PDF du sujet de TP dans le navigateur ;
- sélectionner un rendu étudiant dans `rendus-des-etudiants/<tp>/` ;
- afficher le code source rendu (`code_rendu.c` ou `code_rendu.ml`) avec coloration syntaxique ;
- afficher le compte-rendu PDF de l'étudiant, avec repli sur le Markdown si le PDF n'existe pas encore.

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

