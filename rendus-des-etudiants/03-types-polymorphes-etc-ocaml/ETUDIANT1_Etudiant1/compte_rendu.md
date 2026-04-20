# Compte-rendu de TP3 : Types de données en OCaml

## Exercice 1 : Types paramétriques

**Question 3**
L'expression `let dans_le_futur = annee + age` provoque une erreur de typage. L'opérateur `+` en OCaml possède la signature `int -> int -> int`. Comme `annee` et `age` sont de type `entier_etendu` (un type somme que nous avons défini) et non de type `int`, le système de types rejette l'opération. En OCaml, les opérateurs ne sont pas surchargés par défaut.

**Question 5**
De la même manière, les expressions `pos_inf + age` et `annee - neg_inf` échouent. Bien que ces concepts soient mathématiquement valides dans $\overline{\mathbb{Z}}$, les types ne correspondent pas aux attentes des primitives de calcul du langage. C'est précisément pour lever cette limitation que nous avons implémenté la fonction `ajoute_etendu`.

---

## Exercice 3 : Sous-ensembles du plan

**Question 2 : Précision numérique**
Le test de colinéarité repose sur le calcul `x1 *. y2 -. x2 *. y1 = 0.`. En informatique, l'utilisation de l'égalité stricte sur des flottants est risquée. À cause de la représentation en virgule flottante (norme IEEE-754), des erreurs d'arrondi peuvent faire qu'un résultat théoriquement nul soit égal à une valeur très petite (ex: $10^{-17}$). Dans un cadre de production, on préférera vérifier si la valeur absolue du résultat est inférieure à un seuil $\epsilon$ arbitrairement petit.

**Question 5 : Extension à la 3D**
Pour passer à un type `sous_ensemble_3D`, nous devrions :

1. Modifier `point` pour être un triplet : `type point3D = float * float * float`.
2. Adapter `Droite of point3D` (vecteur directeur).
3. Ajouter un constructeur `Plan_3D of point3D` (où le paramètre serait le vecteur normal au plan).
4. Ajouter un constructeur `Espace` pour désigner $\mathbb{R}^3$ tout entier.

**Question 6 : Géométrie dans l'espace**
L'implémentation de `inter3D` serait plus complexe car l'intersection de deux plans peut être une droite ou un plan (s'ils sont confondus). Il faudrait utiliser :

* Le **produit scalaire** pour tester l'appartenance ou l'orthogonalité.
* Le **produit vectoriel** pour déterminer le vecteur directeur de la droite d'intersection de deux plans.
* Le **produit mixte** pour vérifier si des vecteurs sont coplanaires.

---

## Exercice 4 : Types récursifs

L'implémentation des entiers unaires montre comment une structure de données peut être définie par induction.

* La fonction `int_of_entier_unaire` parcourt la structure jusqu'à atteindre le constructeur de base `Zero`, en accumulant les unités au retour des appels récursifs.
* La fonction `somme_unaire` ne nécessite pas de conversion en `int` : elle "greffe" simplement le premier entier au sommet du second par récurrence sur le nombre de constructeurs `Successeur`.
* Le produit est défini comme une succession d'additions, illustrant parfaitement la définition axiomatique de l'arithmétique de Peano.