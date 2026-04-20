# TP3 : Types maison (non polymorphes)

## Ex.1 - Types paramétriques

On sait manipuler des entiers relatifs ($n \in \mathbb{Z}$) en Caml, avec le type `int`.
On s'intéresse ici à étendre les opérations usuelles (`+`, `*`, etc) aux deux valeurs infinies $-\infty$ et $+\infty$.

### Présentation de cet ensemble $\overline{\mathbb{Z}}$

Mathématiquement, on s'intéresse à l'ensemble noté $\overline{\mathbb{Z}}$, défini comme $\overline{\mathbb{Z}} = \{-\infty\} \cup \mathbb{Z} \cup \{\infty\}$.

Avec Caml, on veut définir un type maison qui permette de représenter une valeur $n \in \overline{\mathbb{Z}}$ : elle peut être un infini, ou un entier.

- On sait déjà manipuler des valeurs constantes (ici, les deux infinis) avec des types énumération (comme en cours : les signes d'entiers, ou en évaluation : les booléens).
- On sait aussi manipuler les entiers (`int`).

### Vers un type union ?

Dans certains langages, on pourrait faire simplement l'union du type `int` et d'un type énumération `infinis` (qui a deux constructeurs), qui serait par exemple définit ainsi :

```ocaml
type infinis = Plus_Inf | Moins_Inf ;; (* ça, ça marche *)

(* mais ça, NON /!\ c'est un code qui ne fonctionne PAS *)
type entier_etendu = infinis | int ;;
```

Mais dans Caml, pour faire cette "union" de types, il faut **forcément** enrober (on dira aussi décorer, ou entourer) les valeurs `int` par un constructeur : par exemple `let zero = Entier 0` sera un nombre de $\overline{\mathbb{Z}}$ qui vaut $0$.
Ce constructeur `Entier` demande une valeur associée, pas comme le constructeurs constant `Plus_Inf` par exemple.
Ce constructeur est donc dit **paramétrique**.

Voici donc comment on peut définir un type `entier_etendu` qui représente les valeurs dans l'ensemble $\overline{\mathbb{Z}} = \{-\infty\} \cup \mathbb{Z} \cup \{\infty\}$ :

```ocaml
type entier_etendu =
  | Moins_Inf       (* la constante -oo *)
  | Entier of int   (* valeur entière finie : Entier n : n dans Z *)
  | Plus_Inf        (* la constante +oo *)
;;
```

Ces valeurs sont soit la constante $-\infty$, représentée par le constructeur constant `Moins_Inf` , soit un entier $n \in \mathbb{Z}$, représenté par le constructeur paramétrique `Entier` appliqué à `n` (un `int`), soit enfin la constante $+\infty$, représentée aussi par le constructeur constant `Plus_Inf` .

### Premières manipulations de ce type

1. Définir ce type. (le recopier suffit).

2. Définir deux constantes (des variables globales) `age` et `annee`, de type `entier_etendu`, qui représentent votre âge et l'année actuelle.

3. Que donnera le calcul de `let dans_le_futur = annee + age ;;` ?

4. Définir deux constants `pos_inf` et `neg_inf`, qui représentent respectivement $+\infty$ et $-\infty$.

    - **Attention** ces noms n'ont rien à voir avec les infinis chez les flottants, qui existent déjà dans OCaml et s'appellent `infinity` et `neg_infinity`.

5. Que donnera le calcul de `pos_inf + age`, ou `annee - neg_inf` par exemple ?

### Somme de deux entiers étendus

On remarque que Caml ne sait pas ajouter (`x + y`) deux valeurs de type `entier_etendu`, et c'est normal !
En effet, la signature de cet opérateur `+` est `int -> int -> int` : il n'est **pas** polymorphe ! (contrairement aux comparaisons `>`, `<`, `>=`, `<=`, `=`, `<>`)
Comme tous les opérateurs sur les entiers `+`, `-`, `*`, `/` et `mod` (ou leurs cousins sur les flottants), ils n'acceptent que des arguments entiers (ou flottants).

On va définir notre propre fonction `ajoute_etendu : entier_etendu -> entier_etendu -> entier_etendu` qui saura ajouter des valeurs de types `entier_etendu`, en prenant en compte les $-\infty$ et $+\infty$.

6. Programmer cette fonction `ajoute_etendu x y`, en écrivant un `match x,y with ...`, sur la paire `(x,y)` et en examinant tous les cas possibles.

   - Il y a trois cas pour `x`, trois cas pour `y`, donc 9 cas en tout, que l'on doit regrouper autant que possible.
   - Normalement, il n'y a qu'un seul cas dans lequel on a besoin d'appeler l'opérateur `+` sur deux `int`.
   - Le seul cas indéterminé sera l'ajout de `Plus_Inf` et `Moins_Inf`, pour lequel on déclenchera une erreur, en écrivant `failwith "Cas indetermine +oo + -oo"` en fin du match.

7. Vérifier que `ajoute_etendu age annee` fonctionne comme on l'espérait.

8. Vérifier les autres cas corrects : `ajoute_etendu age Moins_Inf`, `ajoute_etendu age Plus_Inf`, `ajoute_etendu Moins_Inf Moins_Inf`, `ajoute_etendu Plus_Inf Plus_Inf`.

### Produit de deux entiers étendus

9. Définir une fonction `produit_etendu : entier_etendu -> entier_etendu -> entier_etendu`, en examinant tous les cas selon le signe de ses arguments et savoir si ses arguments sont des infinis ou non.

   - Ici, on prendra comme convention que $0 \times \infty = 0$ et $0 \times -\infty = 0$, pour simplifier.

10. Vérifier tous les cas avec les exemples suivants (on abusera des copier-coller pour gagner du temps) :

```ocaml
(* Ce test assert( un booléen );; permet de vérifier
   si le booléen est évalué à true, et échoue avec une erreur sinon. *)

assert( produit_etendu (Entier (-10)) (Entier 2023) = (Entier (-20230)) );;
assert( produit_etendu (Entier 10) (Entier 2023) = (Entier 20230) );;

assert( produit_etendu Plus_Inf (Entier 0) = (Entier 0) );;
assert( produit_etendu Moins_Inf (Entier 0) = (Entier 0) );;

assert( produit_etendu Plus_Inf Plus_Inf = Plus_Inf );;
assert( produit_etendu Moins_Inf Plus_Inf = Moins_Inf );;
assert( produit_etendu Plus_Inf Moins_Inf = Moins_Inf );;
assert( produit_etendu Moins_Inf Moins_Inf = Plus_Inf );;
```

----

<!-- \newpage -->

## Ex.2 - Combiner les types énumération et types alias - des cartes à jouer

On cherche à représenter des cartes à jouer traditionnelles, sans les jokers.
Une telle carte peut être le 7 de pique, le 9 de carreau, la dame de cœur, etc.
Une carte est la donnée d'une valeur numérique (entre 1 et 13, avec 11 = valet, 12 = dame et 13 = roi), et d'une couleur (pique, trèfle, cœur et carreau).

1. Définir un type énumération `couleur`, qui permet de représenter ces couleurs, avec quatre constructeurs constants.

2. Définir un type alias `carte` qui n'est rien d'autre qu'un couple `(v, c)`, avec `v` la valeur de la carte qui est un un entier (qui sera toujours entre 1 et 13, mais le type n'a pas besoin de savoir ça), et `c` la couleur de la carte qui est de type `couleur`.

3. Définir les exemples suivants :

```ocaml
let ace, valet, dame, roi = 1, 11, 12, 13;;  (* juste esthétique *)

let cesar : carte    = (roi, Carreau);;
let judith : carte   = (dame, Coeur);;  (* c'est la Dame dans Alice *)
let lancelot : carte = (valet, Trefle);;

let as_de_pique : carte    = (ace, Pique);;
let sept_qui_prend : carte = (7, Carreau);;
```

<!-- https://jaimelesmots.com/les-vrais-noms-des-figures-des-cartes-a-jouer/ -->

Ces *décorations de type*, ici par exemple `let cesar : carte = ...`, au lieu de simplement `let cesar = ...`, servent à demander à Caml d'afficher le type de la constante `cesar` à `carte`, et non `int * couleur`.
En effet les types alias étant des types **déjà connus** de Caml (d'où le nom : alias = *aka* = *"also known as"*), le système de type reconnaîtra `cesar` comme un `int * couleur`, et pas un `carte`, sauf si on lui demande, ou si c'est le résultat d'une fonction pour laquelle on avait précisé son type de retour.

4. Écrire une fonction `affiche_carte : carte -> unit`, qui affiche les cartes ainsi :

```ocaml
# affiche_carte cesar ;;
13 de Carreau
# affiche_carte judith ;;
12 de Coeur
# affiche_carte lancelot ;;
11 de Trefle
# affiche_carte as_de_pique ;;
1 de Pique
# affiche_carte sept_qui_prend ;;
7 de Carreau
```

5. Améliorer un peu la fonction précédente pour afficher `roi` au lieu de `13`, `dame` au lieu de `12`, `valet` au lieu de `11`, et `as` au lieu de `1`, dans les exemples précédents.

```ocaml
# affiche_carte_mieux cesar ;;
roi de Carreau
# affiche_carte_mieux sept_qui_prend ;;  (* pas changé pour le reste *)
7 de Carreau
```

On veut compter les points, dans un certain jeu de cartes. Un roi vaudra 25 points, une dame 20 points, un valet 15 points, et les autres cartes valent leur valeur numérique, *sauf* l'as de trèfle qui vaut 50 points.

6. En déduire une fonction `valeur_point : carte -> int`, qui calcule cette valeur de points d'une carte donnée.

Nous reviendrons sur cet exemple, quand nous étudierons les types enregistrements (*records*).

----

<!-- \newpage -->

## Ex.3 - Constructeurs paramétriques - exemple des sous-ensembles du plan

Si l'on veut définir un type contenant une infinité de valeurs, il faut pouvoir paramétrer les constructeurs par des valeurs d'un type préexistant (ou avoir un type récursif - cf Ex.4 TP3).

Par exemple, définissons un type permettant de représenter certains sous-ensembles du plan (ce seront les *sous-espaces vectoriels* du plan, comme vous le verrez cette année en mathématiques).

Les sous-ensembles du plan $\mathbb{R}^2$ que nous considérerons ici sont :

- l'ensemble réduit à l'origine $\{(0,0)\}$ (qui ne contient donc qu'un seul point, le zéro de $\mathbb{R}^2$) ;
- les droites passant par l'origine ;
- le plan $\mathbb{R}^2$ en entier.

Pour le premier et troisième cas, on aura un simple constructeur (nommés `Zero` et `Plan`), puisqu'à chaque fois il n'y a qu'un seul ensemble possible.
En revanche, pour le deuxième cas, il faut préciser de quelle droite on parle : pour cela, on peut par exemple donner un vecteur directeur sous la forme d'un couple de flottants `(x,y)`.
On aura donc un **constructeur paramétrique** : `Droite (x,y)` (un constructeur paramétré par un couple de flottants).

On obtient le type suivant :

```ocaml
type point2D = (float * float);;  (* type alias *)

type sous_ensemble_2D =   (* type énumération + constructeur paramétrique *)
    | Zero                (* singleton {0}, pas l'ensemble vide ! *)
    | Droite of point2D   (* constructeur paramétrique *)
    | Plan                (* le plan R² entier *)
;;
```

1. Définir des exemples de valeurs du type `sous_ensemble_2D` : `zero`, `plan`, puis `axe_x` sera la droite de vecteur directeur `(1., 0.)`, `axe_moins_x = Droite (-1., 0.)`, `axe_y` pour l'axe $y$, et une autre droite de votre choix.

2. Définir une fonction `inter2D : sous_ensemble_2D -> sous_ensemble_2D -> sous_ensemble_2D`, calculant l'intersection de deux de ces sous-ensembles.
   - On ne cherchera pas à être malin sur le test d'intersection des droites.
     Si on a deux droites données par `Droite (x1, y1)` et `Droite (x2, y2)`, on pourra tester `x1 *. y2 -. x2 *. y1 = 0.`.
   - Quelle est la limitation d'un tel test ?
   - En pratique, on ne fera JAMAIS ça pour du vrai code.

3. Tester cette fonction `inter2D` avec vos exemples de la question 1. On pensera à tester au moins une fois l'intersection de deux droites, avec par exemple `assert( inter2D axe_x axe_moins_x = axe_x );;`.

4. Définir une fonction `appartient (ensemble : sous_ensemble_2D) (point : point2D)` qui permet de tester si un point donné de $\mathbb{R}^2$ appartient à un ensemble $E$ donné.
   - Tous les points appartiennent à `Plan` (le plan entier), un seul point appartient à `Zero` ;
   - Le cas compliqué est le test d'appartenance à une droite. On essaiera d'être malin, et de réutiliser la fonction précédente...

5. Si on souhaitait passer en 3D, que faudrait-il changer depuis `sous_ensemble_2D` et que faudrait-il rajouter pour définir un type `sous_ensemble_3D` ?

6. Que faudrait-il savoir faire entre deux droites, entre une droite et un plan, et entre deux plan, pour écrire `inter3D` qui calcule l'intersection de deux sous-ensembles de l'espace $\mathbb{R}^3$ ?

----

<!-- \newpage -->

## Ex.4 - Types récursifs (mais pas encore polymorphe)

Là où on comprend toute la richesse de ces types, c'est quand on utilise la récursivité : en effet,
un type peut figurer dans sa définition.

### Des entiers représentés en unaire

Le premier exemple que l'on propose est le suivant :
on souhaite représenter les entiers naturels ($\mathbb{N}$) en unaire :
un entier naturel, c'est soit zéro ($0$), soit le successeur $n+1$ d'un entier naturel $n$.

```ocaml
type entier_unaire =
  | Zero
  | Successeur of entier_unaire
;;
```

1. Définir ce type.
2. Définir les constantes suivantes : `zero = Zero`, `un = Successeur zero`, puis `deux` et `trois`.

On souhaite pouvoir convertir des `int` (positifs ou nuls) en `entier_unaire`, et inversement.

3. Écrire une fonction (récursive) `int_of_entier_unaire : entier_unaire -> int`, qui associe `0` à `Zero`, et `n+1` à `Successeur x`, si `n = int_of_entier_unaire x` (récursivement).

4. Faire l'inverse en écrivant une fonction récursive `entier_unaire_of_int : int -> entier_unaire`.

5. A l'aide d'une boucle `for n = 0 to 10 do ... done`, vérifier que ces fonctions sont bien réciproques l'une de l'autre.

On pourra écrire ces tests avec des `assert( condition booléenne );;`, par exemple :

```ocaml
assert( int_of_entier_unaire (entier_unaire_of_int 20) = 20 );;
```

6. Écrire une fonction d'addition, `somme_unaire : entier_unaire -> entier_unaire -> entier_unaire`, qui ne repassera **pas** par les `int`, pour calculer la somme de deux entiers `n` et `m` représentés en unaire.

7. Faire de même pour une fonction produit, `produit_unaire : entier_unaire -> entier_unaire -> entier_unaire`.
