
;; Defined Parameters:

;; Contact Sets:
(sdegeo:define-contact-set "source" 0.25 (color:rgb 1 0 0 )"##" )
(sdegeo:define-contact-set "drain" 0.25 (color:rgb 1 0 0 )"##" )
(sdegeo:define-contact-set "gate" 0.25 (color:rgb 1 0 0 )"##" )
(sdegeo:define-contact-set "substrate" 0.25 (color:rgb 1 0 0 )"##" )

;; Work Planes:
(sde:workplanes-init-scm-binding)

;; Defined ACIS Refinements:
(sde:refinement-init-scm-binding)

;; Reference/Evaluation Windows:
(sdedr:define-refeval-window "Win.GateEdgeS" "Rectangle" (position 0 -0.018 0) (position 0.008745 -0.014 0))
(sdedr:define-refeval-window "Win.GateEdgeD" "Rectangle" (position 0 0.014 0) (position 0.008745 0.018 0))
