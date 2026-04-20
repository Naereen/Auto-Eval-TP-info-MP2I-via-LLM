# Compte-rendu de TP 3 - MP2I

## Exercice 1 : Type Z barre

On a défini un type `entier_etendu` qui permet de stocker soit un entier normal, soit un des deux infinis. Comme OCaml ne permet pas de faire l'union directe des types, on a utilisé des constructeurs `Inf` et `Reel`.

Pour l'addition, on a traité tous les cas avec un `match`. Pour les cas où on ajoute plus l'infini et moins l'infini, le résultat n'existe pas donc on a mis un `failwith` pour arrêter le programme avec une erreur. La fonction de comparaison utilise la fonction `compare` de base d'OCaml pour les entiers et gère manuellement les cas avec l'infini.

## Exercice 2 : Entiers unaires

On a créé un type récursif pour représenter les entiers naturels. C'est la définition mathématique de Peano.

### Questions 3, 4 et 5

On a écrit les deux fonctions de conversion. La fonction `int_of_entier_unaire` parcourt la structure jusqu'au `Zero` pour compter le nombre de successeurs. On a vérifié avec une boucle et des `assert` que si on fait la conversion dans les deux sens, on retrouve bien le même nombre pour les entiers entre 0 et 10.

### Question 6 : Addition

L'addition se fait en ajoutant les successeurs du premier nombre un par un au-dessus du deuxième nombre.

### Complexité

- Pour la conversion, la complexité est $O(n)$ car on doit parcourir tout l'entier unaire.
- Pour l'addition `addition_unaire n m`, on fait $n$ appels récursifs, donc la complexité dépend de la taille du premier argument, c'est du $O(n)$.
- Si on avait fait la multiplication, ce serait sûrement du $O(n \times m)$ car on appellerait l'addition plusieurs fois.

## Conclusion

Le TP a permis de voir comment manipuler des types que l'on définit nous-mêmes. C'est assez pratique pour représenter des objets mathématiques mais il faut faire attention aux fonctions récursives pour ne pas oublier de cas.
