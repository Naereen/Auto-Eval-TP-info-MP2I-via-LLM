module CR = Code_rendu

let pp_entier_etendu fmt = function
  | CR.Moins_Inf -> Format.pp_print_string fmt "Moins_Inf"
  | CR.Entier n -> Format.fprintf fmt "Entier %d" n
  | CR.Plus_Inf -> Format.pp_print_string fmt "Plus_Inf"

let testable_entier_etendu = Alcotest.testable pp_entier_etendu ( = )

let pp_couleur fmt = function
  | CR.Pique -> Format.pp_print_string fmt "Pique"
  | CR.Trefle -> Format.pp_print_string fmt "Trefle"
  | CR.Coeur -> Format.pp_print_string fmt "Coeur"
  | CR.Carreau -> Format.pp_print_string fmt "Carreau"

let pp_carte fmt (valeur, couleur) =
  Format.fprintf fmt "(%d, %a)" valeur pp_couleur couleur

let testable_carte = Alcotest.testable pp_carte ( = )

let pp_point2d fmt (x, y) =
  Format.fprintf fmt "(%.12g, %.12g)" x y

let pp_sous_ensemble_2d fmt (value : CR.sous_ensemble_2D) =
  match value with
  | CR.Zero2D -> Format.pp_print_string fmt "Zero2D"
  | CR.Plan -> Format.pp_print_string fmt "Plan"
  | CR.Droite point -> Format.fprintf fmt "Droite %a" pp_point2d point

let testable_sous_ensemble_2d = Alcotest.testable pp_sous_ensemble_2d ( = )

let rec pp_entier_unaire fmt (value : CR.entier_unaire) =
  match value with
  | CR.Zero -> Format.pp_print_string fmt "Zero"
  | CR.Successeur n -> Format.fprintf fmt "Successeur (%a)" pp_entier_unaire n

let testable_entier_unaire = Alcotest.testable pp_entier_unaire ( = )

let string_of_entier_etendu value =
  Format.asprintf "%a" pp_entier_etendu value

let string_of_sous_ensemble_2d set =
  Format.asprintf "%a" pp_sous_ensemble_2d set

let safe_ajoute_etendu left right =
  try Some (CR.ajoute_etendu left right) with Failure _ -> None

let label_of_carte_mieux (valeur, _) =
  match valeur with
  | 1 -> "as"
  | 11 -> "valet"
  | 12 -> "dame"
  | 13 -> "roi"
  | n -> string_of_int n

let expected_affiche_carte (valeur, couleur) =
  Printf.sprintf "%d de %s\n" valeur (CR.string_of_couleur couleur)

let expected_affiche_carte_mieux ((_, couleur) as carte) =
  Printf.sprintf "%s de %s\n" (label_of_carte_mieux carte) (CR.string_of_couleur couleur)

let with_captured_stdout f =
  let temp_file = Filename.temp_file "code_rendu" ".stdout" in
  let stdout_fd = Unix.descr_of_out_channel stdout in
  let saved_stdout = Unix.dup stdout_fd in
  let cleanup () =
    flush stdout;
    Unix.dup2 saved_stdout stdout_fd;
    Unix.close saved_stdout;
    if Sys.file_exists temp_file then Sys.remove temp_file
  in
  Fun.protect
    ~finally:cleanup
    (fun () ->
      let temp_fd = Unix.openfile temp_file [ Unix.O_RDWR; Unix.O_TRUNC ] 0o600 in
      Unix.dup2 temp_fd stdout_fd;
      Unix.close temp_fd;
      f ();
      flush stdout;
      let ic = open_in_bin temp_file in
      Fun.protect
        ~finally:(fun () -> close_in ic)
        (fun () ->
          let len = in_channel_length ic in
          really_input_string ic len))

let is_colinear (x1, y1) (x2, y2) =
  (x1 *. y2) -. (x2 *. y1) = 0.

let equivalent_sous_ensemble (a : CR.sous_ensemble_2D) (b : CR.sous_ensemble_2D) =
  match a, b with
  | CR.Zero2D, CR.Zero2D -> true
  | CR.Plan, CR.Plan -> true
  | CR.Droite direction1, CR.Droite direction2 ->
      is_colinear direction1 direction2
  | _ -> false

let zero_set : CR.sous_ensemble_2D = CR.Zero2D
let plan_set : CR.sous_ensemble_2D = CR.Plan
let zero_unary : CR.entier_unaire = CR.Zero

let non_zero_direction_gen =
  let open QCheck.Gen in
  let rec gen () =
    let* x = -20 -- 20 in
    let* y = -20 -- 20 in
    if x = 0 && y = 0 then gen () else return (float_of_int x, float_of_int y)
  in
  gen ()

let non_colinear_directions_gen =
  let open QCheck.Gen in
  let rec gen () =
    let* direction1 = non_zero_direction_gen in
    let* direction2 = non_zero_direction_gen in
    if is_colinear direction1 direction2 then gen () else return (direction1, direction2)
  in
  gen ()

let arb_entier_etendu =
  let open QCheck.Gen in
  QCheck.make
    ~print:string_of_entier_etendu
    (oneof_weighted
       [
         (1, return CR.Moins_Inf);
         (1, return CR.Plus_Inf);
         (8, map (fun n -> CR.Entier n) int_small);
       ])

let arb_couleur =
  QCheck.make
    ~print:(Format.asprintf "%a" pp_couleur)
    QCheck.Gen.(oneof_list [ CR.Pique; CR.Trefle; CR.Coeur; CR.Carreau ])

let arb_carte =
  let open QCheck.Gen in
  QCheck.make
    ~print:(Format.asprintf "%a" pp_carte)
    (let* valeur = 1 -- 13 in
     let* couleur = QCheck.Gen.oneof_list [ CR.Pique; CR.Trefle; CR.Coeur; CR.Carreau ] in
     return (valeur, couleur))

let arb_sous_ensemble_2d =
  let open QCheck.Gen in
  QCheck.make
    ~print:string_of_sous_ensemble_2d
    (oneof_weighted
       [
         (1, return (CR.Zero2D : CR.sous_ensemble_2D));
         (1, return (CR.Plan : CR.sous_ensemble_2D));
         (6, map (fun direction -> CR.Droite direction) non_zero_direction_gen);
       ])

let arb_entier_unaire =
  QCheck.make
    ~print:(Format.asprintf "%a" pp_entier_unaire)
    QCheck.Gen.(map CR.entier_unaire_of_int nat_small)

let arb_non_zero_int =
  QCheck.make
    ~print:string_of_int
    QCheck.Gen.(oneof_weighted [ (1, -100 -- -1); (1, 1 -- 100) ])

let arb_non_colinear_direction_pair =
  QCheck.make
    ~print:(fun (direction1, direction2) ->
      Printf.sprintf "%s ; %s"
        (Format.asprintf "%a" pp_point2d direction1)
        (Format.asprintf "%a" pp_point2d direction2))
    non_colinear_directions_gen

let unit_tests =
  [
    ( "entiers_etendus",
      [
        Alcotest.test_case "constantes globales" `Quick (fun () ->
            Alcotest.check testable_entier_etendu "age" (CR.Entier 18) CR.age;
            Alcotest.check testable_entier_etendu "annee" (CR.Entier 2026) CR.annee;
            Alcotest.check testable_entier_etendu "pos_inf" CR.Plus_Inf CR.pos_inf;
            Alcotest.check testable_entier_etendu "neg_inf" CR.Moins_Inf CR.neg_inf);
        Alcotest.test_case "addition cas elementaires" `Quick (fun () ->
            Alcotest.check testable_entier_etendu "fini + fini" (CR.Entier 7)
              (CR.ajoute_etendu (CR.Entier 3) (CR.Entier 4));
            Alcotest.check testable_entier_etendu "fini + +inf" CR.Plus_Inf
              (CR.ajoute_etendu (CR.Entier 3) CR.Plus_Inf);
            Alcotest.check testable_entier_etendu "fini + -inf" CR.Moins_Inf
              (CR.ajoute_etendu (CR.Entier 3) CR.Moins_Inf));
        Alcotest.test_case "addition indeterminee" `Quick (fun () ->
            Alcotest.check_raises "(+oo) + (-oo) echoue"
              (Failure "Cas indetermine +oo + -oo")
              (fun () -> ignore (CR.ajoute_etendu CR.Plus_Inf CR.Moins_Inf));
            Alcotest.check_raises "(-oo) + (+oo) echoue"
              (Failure "Cas indetermine +oo + -oo")
              (fun () -> ignore (CR.ajoute_etendu CR.Moins_Inf CR.Plus_Inf)));
        Alcotest.test_case "produit cas elementaires" `Quick (fun () ->
            Alcotest.check testable_entier_etendu "fini * fini" (CR.Entier 42)
              (CR.produit_etendu (CR.Entier 6) (CR.Entier 7));
            Alcotest.check testable_entier_etendu "zero * +inf" (CR.Entier 0)
              (CR.produit_etendu (CR.Entier 0) CR.Plus_Inf);
            Alcotest.check testable_entier_etendu "+inf * negatif" CR.Moins_Inf
              (CR.produit_etendu CR.Plus_Inf (CR.Entier (-2)));
            Alcotest.check testable_entier_etendu "-inf * negatif" CR.Plus_Inf
              (CR.produit_etendu CR.Moins_Inf (CR.Entier (-2))));
      ] );
    ( "cartes",
      [
        Alcotest.test_case "constantes et cartes exemples" `Quick (fun () ->
            Alcotest.check Alcotest.int "ace" 1 CR.ace;
            Alcotest.check Alcotest.int "valet" 11 CR.valet;
            Alcotest.check Alcotest.int "dame" 12 CR.dame;
            Alcotest.check Alcotest.int "roi" 13 CR.roi;
            Alcotest.check testable_carte "cesar" (13, CR.Carreau) CR.cesar;
            Alcotest.check testable_carte "judith" (12, CR.Coeur) CR.judith;
            Alcotest.check testable_carte "lancelot" (11, CR.Trefle) CR.lancelot;
            Alcotest.check testable_carte "as_de_pique" (1, CR.Pique) CR.as_de_pique;
            Alcotest.check testable_carte "sept_qui_prend" (7, CR.Carreau)
              CR.sept_qui_prend);
        Alcotest.test_case "string_of_couleur" `Quick (fun () ->
            Alcotest.check Alcotest.string "pique" "Pique" (CR.string_of_couleur CR.Pique);
            Alcotest.check Alcotest.string "trefle" "Trefle" (CR.string_of_couleur CR.Trefle);
            Alcotest.check Alcotest.string "coeur" "Coeur" (CR.string_of_couleur CR.Coeur);
            Alcotest.check Alcotest.string "carreau" "Carreau"
              (CR.string_of_couleur CR.Carreau));
        Alcotest.test_case "affiche_carte" `Quick (fun () ->
            let output = with_captured_stdout (fun () -> CR.affiche_carte CR.cesar) in
            Alcotest.check Alcotest.string "affichage brut" "13 de Carreau\n" output);
        Alcotest.test_case "affiche_carte_mieux" `Quick (fun () ->
            let output_as =
              with_captured_stdout (fun () -> CR.affiche_carte_mieux CR.as_de_pique)
            in
            let output_roi =
              with_captured_stdout (fun () -> CR.affiche_carte_mieux CR.cesar)
            in
            let output_nombre =
              with_captured_stdout (fun () -> CR.affiche_carte_mieux CR.sept_qui_prend)
            in
            Alcotest.check Alcotest.string "as" "as de Pique\n" output_as;
            Alcotest.check Alcotest.string "roi" "roi de Carreau\n" output_roi;
            Alcotest.check Alcotest.string "nombre" "7 de Carreau\n" output_nombre);
        Alcotest.test_case "valeur_point" `Quick (fun () ->
            Alcotest.check Alcotest.int "as de trefle" 50 (CR.valeur_point (1, CR.Trefle));
            Alcotest.check Alcotest.int "roi" 25 (CR.valeur_point CR.cesar);
            Alcotest.check Alcotest.int "dame" 20 (CR.valeur_point CR.judith);
            Alcotest.check Alcotest.int "valet" 15 (CR.valeur_point CR.lancelot);
            Alcotest.check Alcotest.int "autre carte" 7 (CR.valeur_point CR.sept_qui_prend));
      ] );
    ( "sous_ensembles_du_plan",
      [
        Alcotest.test_case "inter2D cas de base" `Quick (fun () ->
            Alcotest.check testable_sous_ensemble_2d "plan neutre" CR.axe_x
              (CR.inter2D CR.plan CR.axe_x);
            Alcotest.check testable_sous_ensemble_2d "zero absorbant" zero_set
              (CR.inter2D zero_set CR.axe_y);
            Alcotest.check testable_sous_ensemble_2d "droites colineaires" CR.axe_x
              (CR.inter2D CR.axe_x CR.axe_moins_x);
            Alcotest.check testable_sous_ensemble_2d "droites non colineaires" zero_set
              (CR.inter2D CR.axe_x CR.axe_y));
        Alcotest.test_case "appartient" `Quick (fun () ->
            Alcotest.check Alcotest.bool "origine dans zero" true
              (CR.appartient zero_set (0., 0.));
            Alcotest.check Alcotest.bool "hors zero" false
              (CR.appartient zero_set (1., 0.));
            Alcotest.check Alcotest.bool "plan contient tout" true
              (CR.appartient plan_set (3.5, -2.));
            Alcotest.check Alcotest.bool "point sur axe x" true
              (CR.appartient CR.axe_x (4., 0.));
            Alcotest.check Alcotest.bool "point hors axe x" false
              (CR.appartient CR.axe_x (4., 1.));
            Alcotest.check Alcotest.bool "point sur bissectrice" true
              (CR.appartient CR.premiere_bissectrice (3., 3.)));
      ] );
    ( "entiers_unaires",
      [
        Alcotest.test_case "constantes unaires" `Quick (fun () ->
            Alcotest.check testable_entier_unaire "zero" zero_unary CR.zero;
            Alcotest.check Alcotest.int "un" 1 (CR.int_of_entier_unaire CR.un);
            Alcotest.check Alcotest.int "deux" 2 (CR.int_of_entier_unaire CR.deux);
            Alcotest.check Alcotest.int "trois" 3 (CR.int_of_entier_unaire CR.trois));
        Alcotest.test_case "conversions" `Quick (fun () ->
            Alcotest.check Alcotest.int "zero" 0 (CR.int_of_entier_unaire zero_unary);
            Alcotest.check testable_entier_unaire "4 vers unaire"
              (CR.Successeur (CR.Successeur (CR.Successeur (CR.Successeur CR.Zero))))
              (CR.entier_unaire_of_int 4);
            Alcotest.check_raises "negatif interdit"
              (Invalid_argument "L'entier doit etre naturel (positif ou nul)")
              (fun () -> ignore (CR.entier_unaire_of_int (-1))));
        Alcotest.test_case "somme_unaire" `Quick (fun () ->
            let resultat = CR.somme_unaire (CR.entier_unaire_of_int 2) (CR.entier_unaire_of_int 3) in
          Alcotest.check Alcotest.int "2 + 3" 5 (CR.int_of_entier_unaire resultat));
        Alcotest.test_case "produit_unaire" `Quick (fun () ->
            let resultat = CR.produit_unaire (CR.entier_unaire_of_int 4) (CR.entier_unaire_of_int 3) in
          Alcotest.check Alcotest.int "4 * 3" 12 (CR.int_of_entier_unaire resultat));
      ] );
  ]

let property_tests =
  let open QCheck in
  [
    Test.make ~count:500 ~name:"ajoute_etendu est commutative hors cas indetermines"
      (pair arb_entier_etendu arb_entier_etendu) (fun (a, b) ->
        safe_ajoute_etendu a b = safe_ajoute_etendu b a);
    Test.make ~count:500 ~name:"ajoute_etendu admet 0 comme element neutre"
      arb_entier_etendu (fun value ->
        CR.ajoute_etendu value (CR.Entier 0) = value
        && CR.ajoute_etendu (CR.Entier 0) value = value);
    Test.make ~count:500 ~name:"ajoute_etendu reproduit l'addition des entiers finis"
      (pair int_small int_small) (fun (a, b) ->
        CR.ajoute_etendu (CR.Entier a) (CR.Entier b) = CR.Entier (a + b));
    Test.make ~count:500 ~name:"ajoute_etendu est associative sur les entiers finis"
      (triple int_small int_small int_small) (fun (a, b, c) ->
        CR.ajoute_etendu (CR.Entier a)
          (CR.ajoute_etendu (CR.Entier b) (CR.Entier c))
        = CR.ajoute_etendu
            (CR.ajoute_etendu (CR.Entier a) (CR.Entier b))
            (CR.Entier c));
    Test.make ~count:500 ~name:"produit_etendu reproduit le produit des entiers finis"
      (pair int_small int_small) (fun (a, b) ->
        CR.produit_etendu (CR.Entier a) (CR.Entier b) = CR.Entier (a * b));
    Test.make ~count:500 ~name:"produit_etendu est commutatif"
      (pair arb_entier_etendu arb_entier_etendu) (fun (a, b) ->
        CR.produit_etendu a b = CR.produit_etendu b a);
    Test.make ~count:500 ~name:"produit_etendu admet 1 comme element neutre"
      arb_entier_etendu (fun value ->
        CR.produit_etendu value (CR.Entier 1) = value
        && CR.produit_etendu (CR.Entier 1) value = value);
    Test.make ~count:500 ~name:"zero annule le produit_etendu"
      arb_entier_etendu (fun value ->
        CR.produit_etendu (CR.Entier 0) value = CR.Entier 0
        && CR.produit_etendu value (CR.Entier 0) = CR.Entier 0);
    Test.make ~count:300
      ~name:"produit_etendu avec +inf respecte le signe d'un entier non nul"
      arb_non_zero_int (fun n ->
        let expected = if n > 0 then CR.Plus_Inf else CR.Moins_Inf in
        CR.produit_etendu CR.Plus_Inf (CR.Entier n) = expected
        && CR.produit_etendu (CR.Entier n) CR.Plus_Inf = expected);
    Test.make ~count:200 ~name:"string_of_couleur n'est jamais vide" arb_couleur
      (fun couleur -> String.length (CR.string_of_couleur couleur) > 0);
    Test.make ~count:120 ~name:"affiche_carte respecte le format exact"
      arb_carte (fun carte ->
        with_captured_stdout (fun () -> CR.affiche_carte carte) = expected_affiche_carte carte);
    Test.make ~count:120 ~name:"affiche_carte_mieux respecte le format exact"
      arb_carte (fun carte ->
        with_captured_stdout (fun () -> CR.affiche_carte_mieux carte)
        = expected_affiche_carte_mieux carte);
    Test.make ~count:300
      ~name:"valeur_point conserve les cartes numeriques ordinaires"
      (pair (int_range 2 10) arb_couleur) (fun (n, couleur) ->
        CR.valeur_point (n, couleur) = n);
    Test.make ~count:300 ~name:"valeur_point des figures depend seulement de la valeur"
      (pair (oneof_list [ 11; 12; 13 ]) arb_couleur) (fun (valeur, couleur) ->
        let expected = match valeur with 11 -> 15 | 12 -> 20 | 13 -> 25 | _ -> assert false in
        CR.valeur_point (valeur, couleur) = expected);
    Test.make ~count:300 ~name:"valeur_point reste dans l'intervalle attendu"
      arb_carte (fun carte ->
        let points = CR.valeur_point carte in
        points >= 1 && points <= 50);
    Test.make ~count:300 ~name:"inter2D est idempotente au sens ensembliste"
      arb_sous_ensemble_2d (fun ensemble ->
        equivalent_sous_ensemble (CR.inter2D ensemble ensemble) ensemble);
    Test.make ~count:300 ~name:"inter2D est commutative au sens ensembliste"
      (pair arb_sous_ensemble_2d arb_sous_ensemble_2d) (fun (a, b) ->
        equivalent_sous_ensemble (CR.inter2D a b) (CR.inter2D b a));
    Test.make ~count:300 ~name:"inter2D est associative au sens ensembliste"
      (triple arb_sous_ensemble_2d arb_sous_ensemble_2d arb_sous_ensemble_2d)
      (fun (a, b, c) ->
        equivalent_sous_ensemble
          (CR.inter2D a (CR.inter2D b c))
          (CR.inter2D (CR.inter2D a b) c));
    Test.make ~count:300 ~name:"inter2D avec le plan laisse l'ensemble inchange"
      arb_sous_ensemble_2d (fun ensemble ->
        equivalent_sous_ensemble (CR.inter2D CR.Plan ensemble) ensemble);
    Test.make ~count:400
      ~name:"appartenance a inter2D equivaut a l'intersection logique"
      (triple arb_sous_ensemble_2d arb_sous_ensemble_2d (pair int_small int_small))
      (fun (a, b, (x, y)) ->
        let point = (float_of_int x, float_of_int y) in
        CR.appartient (CR.inter2D a b) point
        = (CR.appartient a point && CR.appartient b point));
    Test.make ~count:250 ~name:"deux droites non colineaires s'intersectent en Zero2D"
      arb_non_colinear_direction_pair (fun (direction1, direction2) ->
        CR.inter2D (CR.Droite direction1) (CR.Droite direction2) = CR.Zero2D);
    Test.make ~count:300 ~name:"un multiple du directeur appartient a la droite"
      (pair arb_sous_ensemble_2d int_small) (fun ((ensemble : CR.sous_ensemble_2D), k) ->
        match ensemble with
        | CR.Zero2D -> CR.appartient ensemble (0., 0.)
        | CR.Plan -> CR.appartient ensemble (float_of_int k, float_of_int (-k))
        | CR.Droite (dx, dy) ->
            let point = (float_of_int k *. dx, float_of_int k *. dy) in
            CR.appartient ensemble point);
    Test.make ~count:300 ~name:"conversion unaire -> int -> unaire est stable"
      QCheck.nat_small (fun n ->
        CR.int_of_entier_unaire (CR.entier_unaire_of_int n) = n);
    Test.make ~count:300 ~name:"somme_unaire admet zero comme element neutre"
      arb_entier_unaire (fun n ->
        CR.somme_unaire n CR.Zero = n && CR.somme_unaire CR.Zero n = n);
    Test.make ~count:300 ~name:"somme_unaire correspond a l'addition entiere"
      (pair arb_entier_unaire arb_entier_unaire) (fun (a, b) ->
        CR.int_of_entier_unaire (CR.somme_unaire a b)
        = CR.int_of_entier_unaire a + CR.int_of_entier_unaire b);
    Test.make ~count:250 ~name:"somme_unaire est associative"
      (triple arb_entier_unaire arb_entier_unaire arb_entier_unaire)
      (fun (a, b, c) ->
        CR.somme_unaire a (CR.somme_unaire b c)
        = CR.somme_unaire (CR.somme_unaire a b) c);
    Test.make ~count:300 ~name:"produit_unaire est absorbe par zero"
      arb_entier_unaire (fun n ->
        CR.produit_unaire n CR.Zero = CR.Zero && CR.produit_unaire CR.Zero n = CR.Zero);
    Test.make ~count:300 ~name:"produit_unaire correspond au produit entier"
      (pair arb_entier_unaire arb_entier_unaire) (fun (a, b) ->
        CR.int_of_entier_unaire (CR.produit_unaire a b)
        = CR.int_of_entier_unaire a * CR.int_of_entier_unaire b);
    Test.make ~count:250 ~name:"produit_unaire est distributif sur somme_unaire"
      (triple arb_entier_unaire arb_entier_unaire arb_entier_unaire)
      (fun (a, b, c) ->
        CR.produit_unaire a (CR.somme_unaire b c)
        = CR.somme_unaire (CR.produit_unaire a b) (CR.produit_unaire a c));
    Test.make ~count:250 ~name:"produit_unaire est associatif"
      (triple arb_entier_unaire arb_entier_unaire arb_entier_unaire)
      (fun (a, b, c) ->
        CR.produit_unaire a (CR.produit_unaire b c)
        = CR.produit_unaire (CR.produit_unaire a b) c);
  ]

let () =
  Alcotest.run "Tests de code_rendu.ml"
    (unit_tests
    @ [ ("proprietes_qcheck", List.map QCheck_alcotest.to_alcotest property_tests) ])
