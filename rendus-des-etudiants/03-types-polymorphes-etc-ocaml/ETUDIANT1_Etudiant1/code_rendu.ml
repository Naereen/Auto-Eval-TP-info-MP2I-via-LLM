(* Fichier : code_rendu.ml *)
(* Étudiant : [Anonymisé pour la correction] *)
(* Classe : MP2I - Lycée Kléber *)

(* ========================================================================== *)
(* EXERCICE 1 - Types paramétriques                                           *)
(* ========================================================================== *)

(* 1. Définition du type permettant de représenter l'ensemble Z étendu. *)
(* Ce type union nécessite d'enrober les int avec un constructeur paramétrique. *)
type entier_etendu =
  | Moins_Inf       (* *)
  | Entier of int   (* *)
  | Plus_Inf        (* *)
;;

(* 2. Définition des variables globales (âge et année actuelle). *)
let age = Entier 18 ;;
let annee = Entier 2026 ;;

(* 4. Constantes représentant les infinis. *)
let pos_inf = Plus_Inf ;; (* *)
let neg_inf = Moins_Inf ;; (* *)

(* 6. Fonction d'addition pour les entiers étendus. *)
(* On regroupe les cas pour simplifier le filtrage de motifs (pattern matching). *)
let ajoute_etendu x y =
  match x, y with
  | Plus_Inf, Moins_Inf
  | Moins_Inf, Plus_Inf -> failwith "Cas indetermine +oo + -oo" (* *)
  | Plus_Inf, _
  | _, Plus_Inf         -> Plus_Inf
  | Moins_Inf, _
  | _, Moins_Inf        -> Moins_Inf
  | Entier n, Entier m  -> Entier (n + m) (* Seul cas nécessitant l'opérateur + classique *)
;;

(* 7. & 8. Vérifications (évaluées lors de l'exécution du fichier) *)
let () =
  assert (ajoute_etendu age annee = Entier 2044);
  assert (ajoute_etendu age Moins_Inf = Moins_Inf);
  assert (ajoute_etendu age Plus_Inf = Plus_Inf);
  assert (ajoute_etendu Moins_Inf Moins_Inf = Moins_Inf);
  assert (ajoute_etendu Plus_Inf Plus_Inf = Plus_Inf)
;;

(* 9. Produit de deux entiers étendus. *)
let produit_etendu x y =
  match x, y with
  | Entier 0, _
  | _, Entier 0         -> Entier 0 (* Convention 0 * inf = 0 *)
  | Plus_Inf, Plus_Inf
  | Moins_Inf, Moins_Inf-> Plus_Inf
  | Plus_Inf, Moins_Inf
  | Moins_Inf, Plus_Inf -> Moins_Inf
  | Plus_Inf, Entier n
  | Entier n, Plus_Inf  -> if n > 0 then Plus_Inf else Moins_Inf
  | Moins_Inf, Entier n
  | Entier n, Moins_Inf -> if n > 0 then Moins_Inf else Plus_Inf
  | Entier n, Entier m  -> Entier (n * m)
;;

(* 10. Tests exhaustifs avec assert *)
let () =
  assert( produit_etendu (Entier (-10)) (Entier 2023) = (Entier (-20230)) ); (* *)
  assert( produit_etendu (Entier 10) (Entier 2023) = (Entier 20230) );       (* *)
  assert( produit_etendu Plus_Inf (Entier 0) = (Entier 0) );                 (* *)
  assert( produit_etendu Moins_Inf (Entier 0) = (Entier 0) );                (* *)
  assert( produit_etendu Plus_Inf Plus_Inf = Plus_Inf );                     (* *)
  assert( produit_etendu Moins_Inf Plus_Inf = Moins_Inf );                   (* *)
  assert( produit_etendu Plus_Inf Moins_Inf = Moins_Inf );                   (* *)
  assert( produit_etendu Moins_Inf Moins_Inf = Plus_Inf );                   (* *)
;;

(* ========================================================================== *)
(* EXERCICE 2 - Cartes à jouer                                                *)
(* ========================================================================== *)

(* 1. Type énumération pour les couleurs. *)
type couleur = Pique | Trefle | Coeur | Carreau ;; (* *)

(* 2. Type alias pour la carte. *)
type carte = int * couleur ;; (* *)

(* 3. Définition des constantes et de quelques cartes. *)
let ace, valet, dame, roi = 1, 11, 12, 13 ;; (* *)

let cesar : carte    = (roi, Carreau) ;;      (* *)
let judith : carte   = (dame, Coeur) ;;       (* *)
let lancelot : carte = (valet, Trefle) ;;     (* *)
let as_de_pique : carte    = (ace, Pique) ;;  (* *)
let sept_qui_prend : carte = (7, Carreau) ;;  (* *)

(* Fonction utilitaire pour extraire la chaîne de caractères d'une couleur *)
let string_of_couleur = function
  | Pique -> "Pique"
  | Trefle -> "Trefle"
  | Coeur -> "Coeur"
  | Carreau -> "Carreau"
;;

(* 4. Affichage brut de la carte *)
let affiche_carte ((v, c) : carte) : unit =
  Printf.printf "%d de %s\n" v (string_of_couleur c)
;;

(* 5. Affichage amélioré (remplacement des figures et de l'as) *)
let affiche_carte_mieux ((v, c) : carte) : unit =
  let v_str = match v with
    | 1 -> "as"     (* *)
    | 11 -> "valet" (* *)
    | 12 -> "dame"  (* *)
    | 13 -> "roi"   (* *)
    | n -> string_of_int n
  in
  Printf.printf "%s de %s\n" v_str (string_of_couleur c)
;;

(* 6. Calcul des points d'une carte *)
let valeur_point ((v, c) : carte) : int =
  match v, c with
  | 1, Trefle -> 50 (* L'as de trèfle vaut 50 points *)
  | 13, _ -> 25     (* Un roi vaut 25 points *)
  | 12, _ -> 20     (* Une dame vaut 20 points *)
  | 11, _ -> 15     (* Un valet vaut 15 points *)
  | n, _ -> n       (* Les autres cartes valent leur valeur numérique *)
;;

(* ========================================================================== *)
(* EXERCICE 3 - Sous-ensembles du plan                                        *)
(* ========================================================================== *)

type point2D = float * float ;; (* *)

type sous_ensemble_2D =
  | Zero              (* singleton {(0,0)} *)
  | Droite of point2D (* vecteur directeur de la droite *)
  | Plan              (* le plan R² entier *)
;;

(* 1. Exemples de valeurs *)
let zero = Zero ;;
let plan = Plan ;;
let axe_x = Droite (1., 0.) ;;              (* *)
let axe_moins_x = Droite (-1., 0.) ;;       (* *)
let axe_y = Droite (0., 1.) ;;              (* *)
let premiere_bissectrice = Droite (1., 1.) ;;

(* 2. Intersection de deux sous-ensembles du plan *)
let inter2D e1 e2 =
  match e1, e2 with
  | Zero, _ | _, Zero -> Zero
  | Plan, e | e, Plan -> e
  | Droite (x1, y1), Droite (x2, y2) ->
      (* Le déterminant permet de tester la colinéarité des vecteurs directeurs *)
      if x1 *. y2 -. x2 *. y1 = 0. then Droite (x1, y1)
      else Zero
;;

(* 3. Tests de l'intersection *)
let () =
  assert( inter2D axe_x axe_moins_x = axe_x ); (* *)
  assert( inter2D axe_x axe_y = Zero );
  assert( inter2D plan axe_x = axe_x );
  assert( inter2D zero axe_y = Zero )
;;

(* 4. Test d'appartenance d'un point à un ensemble *)
let appartient (ensemble : sous_ensemble_2D) ((px, py) : point2D) : bool =
  match ensemble with
  | Zero -> px = 0. && py = 0.  (* Seul le point (0,0) appartient à Zero *)
  | Plan -> true                (* Tous les points appartiennent à Plan *)
  | Droite (dx, dy) ->
      (* On réutilise l'astuce de la question 2 : on vérifie si
         le vecteur directeur (dx, dy) et le point (px, py) sont colinéaires. *)
      dx *. py -. dy *. px = 0.
;;

(* ========================================================================== *)
(* EXERCICE 4 - Types récursifs                                               *)
(* ========================================================================== *)

(* 1. Représentation des entiers naturels en unaire *)
type entier_unaire =
  | Zero                          (* *)
  | Successeur of entier_unaire   (* *)
;;

(* 2. Constantes unaires *)
let zero = Zero ;;                         (* *)
let un = Successeur zero ;;                (* *)
let deux = Successeur un ;;                (* *)
let trois = Successeur deux ;;             (* *)

(* 3. Conversion unaire -> int *)
let rec int_of_entier_unaire = function
  | Zero -> 0
  | Successeur n -> 1 + int_of_entier_unaire n  (* n+1 si n = int_of_entier_unaire x *)
;;

(* 4. Conversion int -> unaire *)
let rec entier_unaire_of_int = function
  | 0 -> Zero
  | n when n > 0 -> Successeur (entier_unaire_of_int (n - 1))
  | _ -> invalid_arg "L'entier doit etre naturel (positif ou nul)"
;;

(* 5. Boucle de validation sur les conversions *)
let () =
  for n = 0 to 10 do (* *)
    assert( int_of_entier_unaire (entier_unaire_of_int n) = n )
  done
;;

(* 6. Addition d'entiers unaires *)
let rec somme_unaire n m =
  match n with
  | Zero -> m
  | Successeur n_prec -> Successeur (somme_unaire n_prec m)
;;

(* 7. Produit d'entiers unaires *)
(* Repose sur la définition récursive n * m = m + ((n-1) * m) *)
let rec produit_unaire n m =
  match n with
  | Zero -> Zero
  | Successeur n_prec -> somme_unaire m (produit_unaire n_prec m)
;;
