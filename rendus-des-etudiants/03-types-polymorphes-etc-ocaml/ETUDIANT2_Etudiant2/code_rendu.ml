(* TP3 : Types maison *)

(* Exercice 1 *)

type infinis = Plus_Inf | Moins_Inf ;;

type entier_etendu =
  | Inf of infinis
  | Reel of int
;;

let add_etendu x y =
  match x, y with
  | Reel a, Reel b -> Reel (a + b)
  | Inf Plus_Inf, Inf Moins_Inf -> failwith "indéterminé"
  | Inf Moins_Inf, Inf Plus_Inf -> failwith "indéterminé"
  | Inf Plus_Inf, _ -> Inf Plus_Inf
  | _, Inf Plus_Inf -> Inf Plus_Inf
  | Inf Moins_Inf, _ -> Inf Moins_Inf
  | _, Inf Moins_Inf -> Inf Moins_Inf
;;

let compare_etendu x y =
  match x, y with
  | Reel a, Reel b -> compare a b
  | Inf Moins_Inf, Reel _ -> -1
  | Inf Plus_Inf, Reel _ -> 1
  | Reel _, Inf Moins_Inf -> 1
  | Reel _, Inf Plus_Inf -> -1
  | Inf Moins_Inf, Inf Moins_Inf -> 0
  | Inf Plus_Inf, Inf Plus_Inf -> 0
  | Inf Moins_Inf, Inf Plus_Inf -> -1
  | Inf Plus_Inf, Inf Moins_Inf -> 1
;;

(* Exercice 2 *)

type entier_unaire =
  | Zero
  | Successeur of entier_unaire
;;

let zero = Zero ;;
let un = Successeur Zero ;;
let deux = Successeur (Successeur Zero) ;;
let trois = Successeur deux ;;

let int_of_entier_unaire x =
  match x with
  | Zero -> 0
  | Successeur n -> 1 + int_of_entier_unaire n
;;

let rec entier_unaire_of_int n =
  if n = 0 then Zero
  else Successeur (entier_unaire_of_int (n - 1))
;;

let test_reciprocite =
  for n = 0 to 10 do
    assert (int_of_entier_unaire (entier_unaire_of_int n) = n)
  done
;;

let rec addition_unaire n m =
  match n with
  | Zero -> m
  | Successeur n' -> Successeur (addition_unaire n' m)
;;

(* multiplication non finie par manque de temps *)
