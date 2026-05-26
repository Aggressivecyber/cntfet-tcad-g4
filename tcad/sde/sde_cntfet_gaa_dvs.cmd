;;=============================================================================
;; SDE Script: Quasi-GAA CNTFET with HfO2/Al2O3 Bilayer Gate Dielectric
;;=============================================================================
;; Run ID:  20260427-065553-cntfet-quasi-gaa-tid-radiation
;; Purpose: Build 2D axisymmetric CNTFET structure for TID radiation study
;; Approach: 2D cross-section (x=radial r, y=axial z)
;;           SDevice uses Cylindrical(xAxis=0) in Math section for 3D rotation
;;
;; Material stack (inside to outside):
;;   CNT_thin_film -> Al2O3 (2nm) -> HfO2 (6nm) -> TiN (5nm) -> SiO2 sub (300nm)
;;
;; Reference: final_plan.md Section 4.1, memory preflight validated parameters
;;=============================================================================

;;--- Clear and setup ---------------------------------------------------------
(sde:clear)
(sde:set-process-up-direction "+y")

;;--- Parameter definitions ---------------------------------------------------
;; All lengths in MICROMETERS (um) as required by Sentaurus

(define Lg      0.032)    ; Gate length = 32 nm
(define r_cnt   7.45e-4)  ; CNT radius = 0.745 nm (diameter 1.49 nm for (19,0))
(define t_al2o3 2.0e-3)   ; Al2O3 thickness = 2 nm
(define t_hfo2  6.0e-3)   ; HfO2 thickness = 6 nm
(define t_tin   5.0e-3)   ; TiN thickness = 5 nm
(define Lsd     0.05)     ; Source/Drain extension length = 50 nm
(define Lu      5.0e-3)   ; Underlap length = 5 nm
(define t_sub   0.3)      ; SiO2 substrate thickness = 300 nm

;;--- Derived coordinates -----------------------------------------------------
(define r_al2o3 (+ r_cnt t_al2o3))
(define r_hfo2  (+ r_al2o3 t_hfo2))
(define r_tin   (+ r_hfo2 t_tin))
(define r_sub   (+ r_tin t_sub))

(define y_gate_top    (/ Lg 2.0))
(define y_gate_bot    (- 0 (/ Lg 2.0)))
(define y_ul_top      (+ y_gate_top Lu))
(define y_ul_bot      (- y_gate_bot Lu))
(define y_sd_top      (+ y_ul_top Lsd))
(define y_sd_bot      (- y_ul_bot Lsd))

;;--- Display parameters ------------------------------------------------------
(display "========================================")
(display "Quasi-GAA CNTFET SDE Construction")
(display "========================================")
(display (string-append "  Lg         = " (number->string (* Lg 1e3)) " nm"))
(display (string-append "  r_cnt      = " (number->string (* r_cnt 1e6)) " nm"))
(display (string-append "  t_al2o3    = " (number->string (* t_al2o3 1e3)) " nm"))
(display (string-append "  t_hfo2     = " (number->string (* t_hfo2 1e3)) " nm"))
(display (string-append "  t_tin      = " (number->string (* t_tin 1e3)) " nm"))
(display (string-append "  t_sub      = " (number->string (* t_sub 1e3)) " nm"))
(display (string-append "  Lu         = " (number->string (* Lu 1e3)) " nm"))
(display (string-append "  Lsd        = " (number->string (* Lsd 1e3)) " nm"))
(display (string-append "  EOT        = " (number->string (* (+ (* t_al2o3 (/ 3.9 9.0)) (* t_hfo2 (/ 3.9 25.0))) 1e3)) " nm"))
(display (string-append "  y_sd_top   = " (number->string (* y_sd_top 1e3)) " nm"))
(display (string-append "  y_sd_bot   = " (number->string (* y_sd_bot 1e3)) " nm"))
(display (string-append "  y_gate_top = " (number->string (* y_gate_top 1e3)) " nm"))
(display (string-append "  y_gate_bot = " (number->string (* y_gate_bot 1e3)) " nm"))
(display "========================================")

;;--- Boolean mode: ABA (new region replaces old at overlap) -------------------
(sdegeo:set-default-boolean "ABA")

;;=============================================================================
;; GEOMETRY CONSTRUCTION (outside-in, each inner layer overwrites substrate)
;;=============================================================================

;;--- 1. SiO2 Substrate (full background) -------------------------------------
(sdegeo:create-rectangle
  (position 0.0 y_sd_bot 0.0)
  (position r_sub y_sd_top 0.0)
  "SiO2" "R.Substrate"
)

;;--- 2. TiN Gate Metal (gate region only) ------------------------------------
(sdegeo:create-rectangle
  (position r_hfo2 y_gate_bot 0.0)
  (position r_tin  y_gate_top 0.0)
  "TiN" "R.GateMetal"
)

;;--- 3. HfO2 Main Dielectric (gate region only) ------------------------------
(sdegeo:create-rectangle
  (position r_al2o3 y_gate_bot 0.0)
  (position r_hfo2  y_gate_top 0.0)
  "HfO2" "R.HfO2"
)

;;--- 4. Al2O3 Interlayer (gate region only) ----------------------------------
(sdegeo:create-rectangle
  (position r_cnt    y_gate_bot 0.0)
  (position r_al2o3  y_gate_top 0.0)
  "Al2O3" "R.Al2O3"
)

;;--- 5. CNT Channel (full axial extent) --------------------------------------
(sdegeo:create-rectangle
  (position 0.0   y_sd_bot 0.0)
  (position r_cnt y_sd_top 0.0)
  "CNT_thin_film" "R.CNTChannel"
)

;;=============================================================================
;; CONTACT DEFINITIONS
;; Using create-contact-set / set-current-contact-set / set-contact pattern
;;=============================================================================

;;--- Define contact sets -----------------------------------------------------
(sdegeo:define-contact-set "source"    4.0 0.25  "yellow")
(sdegeo:define-contact-set "drain"     4.0 0.25  "red")
(sdegeo:define-contact-set "gate"      4.0 0.25  "green")
(sdegeo:define-contact-set "substrate" 4.0 0.25  "gray")

;;--- Source Contact (top edge of CNT at y = y_sd_top) ------------------------
(sdegeo:set-current-contact-set "source")
(sdegeo:set-contact
  (find-edge-id (position (* r_cnt 0.5) y_sd_top 0.0))
)

;;--- Drain Contact (bottom edge of CNT at y = y_sd_bot) ----------------------
(sdegeo:set-current-contact-set "drain")
(sdegeo:set-contact
  (find-edge-id (position (* r_cnt 0.5) y_sd_bot 0.0))
)

;;--- Gate Contact (right edge of TiN at x = r_tin) ---------------------------
(sdegeo:set-current-contact-set "gate")
(sdegeo:set-contact
  (find-edge-id (position r_tin 0.0 0.0))
)

;;--- Substrate Contact (right edge of SiO2 at x = r_sub) ---------------------
(sdegeo:set-current-contact-set "substrate")
(sdegeo:set-contact
  (find-edge-id (position r_sub 0.0 0.0))
)

;;=============================================================================
;; MESH DEFINITION
;;=============================================================================

;;--- CNT Channel (finest mesh) -----------------------------------------------
;; ~5 nodes across r_cnt = 0.745 nm, max radial size = 0.15 nm
(sdedr:define-refinement-size "Ref.CNT"
  1.5e-4   ; max-x (radial)
  2.0e-3   ; max-y (axial)
  1.0e-5   ; min-x
  1.0e-5   ; min-y
)
(sdedr:define-refinement-region "Place.CNT" "Ref.CNT" "R.CNTChannel")

;;--- Al2O3 interlayer (fine mesh across 2 nm) --------------------------------
(sdedr:define-refinement-size "Ref.Al2O3"
  5.0e-4   ; max-x = 0.5 nm
  1.0e-3   ; max-y = 1.0 nm
  1.0e-5   ; min-x
  1.0e-5   ; min-y
)
(sdedr:define-refinement-region "Place.Al2O3" "Ref.Al2O3" "R.Al2O3")

;;--- HfO2 dielectric (moderate mesh across 6 nm) ----------------------------
(sdedr:define-refinement-size "Ref.HfO2"
  1.0e-3   ; max-x = 1.0 nm
  2.0e-3   ; max-y = 2.0 nm
  1.0e-5   ; min-x
  1.0e-5   ; min-y
)
(sdedr:define-refinement-region "Place.HfO2" "Ref.HfO2" "R.HfO2")

;;--- TiN gate metal (coarse mesh) --------------------------------------------
(sdedr:define-refinement-size "Ref.TiN"
  2.0e-3   ; max-x = 2.0 nm
  5.0e-3   ; max-y = 5.0 nm
  5.0e-4   ; min-x
  5.0e-4   ; min-y
)
(sdedr:define-refinement-region "Place.TiN" "Ref.TiN" "R.GateMetal")

;;--- Substrate (very coarse) -------------------------------------------------
(sdedr:define-refinement-size "Ref.Sub"
  0.05     ; max-x = 50 nm
  0.01     ; max-y = 10 nm
  1.0e-3   ; min-x
  1.0e-3   ; min-y
)
(sdedr:define-refinement-region "Place.Sub" "Ref.Sub" "R.Substrate")

;;--- Gate-edge refinement windows (critical for underlap field) ---------------
(define y_edge_w 2.0e-3)  ; 2 nm band

(sdedr:define-refinement-size "Ref.GateEdgeS"
  2.0e-4 5.0e-4 1.0e-5 1.0e-5
)
(sdedr:define-refeval-window "Win.GateEdgeS" "Rectangle"
  (position 0.0 (- y_gate_bot y_edge_w) 0.0)
  (position r_al2o3 (+ y_gate_bot y_edge_w) 0.0)
)
(sdedr:define-refinement-placement "Place.GateEdgeS" "Ref.GateEdgeS" "Win.GateEdgeS")

(sdedr:define-refinement-size "Ref.GateEdgeD"
  2.0e-4 5.0e-4 1.0e-5 1.0e-5
)
(sdedr:define-refeval-window "Win.GateEdgeD" "Rectangle"
  (position 0.0 (- y_gate_top y_edge_w) 0.0)
  (position r_al2o3 (+ y_gate_top y_edge_w) 0.0)
)
(sdedr:define-refinement-placement "Place.GateEdgeD" "Ref.GateEdgeD" "Win.GateEdgeD")

;;--- Axial cuts at critical y-positions --------------------------------------
(sdesnmesh:axisaligned "yCuts"
  (list
    y_gate_bot
    y_gate_top
    y_ul_bot
    y_ul_top
    y_sd_bot
    y_sd_top
  )
)

;;--- Radial cuts at material interfaces --------------------------------------
(sdesnmesh:axisaligned "xCuts"
  (list
    r_cnt
    r_al2o3
    r_hfo2
    r_tin
  )
)

;;=============================================================================
;; SAVE AND BUILD
;;=============================================================================

;; sde:build-mesh does everything:
;;   1. Saves boundary as <basename>_bnd.tdr
;;   2. Generates mesh command file <basename>_msh.cmd
;;   3. Calls Snmesh -> outputs <basename>_msh.tdr
;; Single argument: file-basename (STRING)
(sde:build-mesh "structure")

;; Also save the geometric model for reference/debugging
(sde:save-model "sde_cntfet_gaa")

(display "\n========================================")
(display "SDE construction COMPLETE")
(display "========================================")
(display "  Meshed structure: structure_msh.tdr")
(display "  Boundary file:    structure_bnd.tdr")
(display "========================================")
