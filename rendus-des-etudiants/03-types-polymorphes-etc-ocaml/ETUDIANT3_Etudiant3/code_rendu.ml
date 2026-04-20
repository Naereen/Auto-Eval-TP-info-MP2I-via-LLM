(* TP 3 informatique *)

type infinis = Plus_Inf | Moins_Inf ;;

(* Exercice 1 *)
type entier_etendu = infinis | int ;;

let add_etendu x y =
  match x with
  | Plus_Inf -> Plus_Inf
  | Moins_Inf -> Moins_Inf
  | x -> x + y
;;

let compare_etendu x y =
  if x < y then -1 else 1
;;

(* Exercice 2 *)
type entier_unaire =
  | Zero
  | Successeur of entier_unaire
;;

let zero = Zero ;;
let un = Successeur zero ;;
let deux = Successeur un ;;
let trois = Successeur deux ;;

let int_of_entier_unaire x =
  if x = Zero then 0
  else 1 + int_of_entier_unaire x
;;

let rec entier_unaire_of_int n =
  if n = 0 then Zero
  else Successeur (n - 1)
;;

let test =
  for n = 0 to 10 do
    if int_of_entier_unaire (entier_unaire_of_int n) = n then print_string "ok"
  done
;;

let addition_unaire n m =
  n + m
;;