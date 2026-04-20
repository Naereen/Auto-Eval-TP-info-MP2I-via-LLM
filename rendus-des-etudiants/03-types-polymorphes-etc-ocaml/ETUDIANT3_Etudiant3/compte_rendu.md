# TP3 - Compte Rendu

## Exercice 1

On veut faire un type avec des infinis et des entiers. J'ai défini le type `entier_etendu` pour mettre les deux ensemble mais Caml dit que c'est pas possible de mettre `int` directement.

Pour l'addition j'ai essayé de regarder si c'est l'infini. Si on ajoute un chiffre à l'infini ça fait l'infini. Par contre j'ai pas réussi à faire marcher le match sur les deux variables en même temps. La comparaison utilise les signes `<` normaux parce que l'infini est plus grand que les nombres.

## Exercice 2

L'unaire c'est pour compter avec des `Successeur`.

### Question 3

Ma fonction `int_of_entier_unaire` doit normalement renvoyer un entier. Elle regarde si c'est zéro, sinon elle rajoute 1 et elle recommence. J'ai une erreur de type "This expression has type entier_unaire but an expression was expected of type int".

### Question 4

Pour faire l'inverse on prend un nombre et on enlève 1 à chaque fois pour mettre un `Successeur` à la place.

### Question 5

La boucle `for` permet de tester les nombres de 0 à 10. Si les deux fonctions marchent bien, on doit trouver le même résultat au début et à la fin.

### Question 6

L'addition c'est juste ajouter `n` et `m`. Mais comme c'est des types `entier_unaire`, le signe `+` ne marche pas, il faudrait transformer en `int` d'abord je pense.

## Conclusion

Le TP était difficile car OCaml est très strict sur les types et les fonctions récursives. Je n'ai pas eu le temps de finir la multiplication et les fonctions de conversion ne compilent pas encore toutes.