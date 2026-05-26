;;=============================================================================
;; SDE Script: Quasi-GAA CNTFET - Config B: HfO2 Single Layer Dielectric
;;=============================================================================
;; Config: B - HfO2 single layer, 8nm thick
;;   eps_r=25.0, bandgap=5.8eV, electron_affinity=2.5eV
;;
;; Material stack (inside to outside):
;;   CNT_thin_film -> HfO2 (8nm) -> TiN (5nm) -> SiO2 sub (300nm)
;;
;; 2D axisymmetric: x=radial r, y=axial z
;; SDevice uses Cylindrical(xAxis=0) for 3D rotation
;;=============================================================================

;;--- Clear and setup ---------------------------------------------------------
(sde:clear)
(sde:set-process-up-direction "+y")

;;--- Parameter definitions ---------------------------------------------------
;; All lengths in MICROMETERS (um) as required by Sentaurus

(define Lg      0.032)    ; Gate length = 32 nm
(define r_cnt   7.45e-4)  ; CNT radius = 0.745 nm (diameter 1.49 nm for (19,0))
(define t_hfo2  8.0e-3)   ; HfO2 dielectric thickness = 8 nm
(define t_tin   5.0e-3)   ; TiN thickness = 5 nm
(define Lsd     0.05)     ; Source/Drain extension length = 50 nm
(define Lu      5.0e-3)   ; Underlap length = 5 nm
(define t_sub   0.3)      ; SiO2 substrate thickness = 300 nm

;;--- Derived coordinates -----------------------------------------------------
(define r_dielectric (+ r_cnt t_hfo2))
(define r_tin        (+ r_dielectric t_tin))
(define r_sub        (+ r_tin t_sub))

(define y_gate_top    (/ Lg 2.0))
(define y_gate_bot    (- 0 (/ Lg 2.0)))
(define y_ul_top      (+ y_gate_top Lu))
(define y_ul_bot      (- y_gate_bot Lu))
(define y_sd_top      (+ y_ul_top Lsd))
(define y_sd_bot      (- y_ul_bot Lsd))

;;--- Display parameters ------------------------------------------------------
(display "========================================")
(display "Config B: HfO2 Single Layer CNTFET SDE")
(display "========================================")
(display (string-append "  Lg         = " (number->string (* Lg 1e3)) " nm"))
(display (string-append "  r_cnt      = " (number->string (* r_cnt 1e6)) " nm"))
(display (string-append "  t_HfO2     = " (number->string (* t_hfo2 1e3)) " nm"))
(display (string-append "  t_tin      = " (number->string (* t_tin 1e3)) " nm"))
(display (string-append "  t_sub      = " (number->string (* t_sub 1e3)) " nm"))
(display (string-append "  Lu         = " (number->string (* Lu 1e3)) " nm"))
(display (string-append "  Lsd        = " (number->string (* Lsd 1e3)) " nm"))
(display (string-append "  EOT        = " (number->string (* t_hfo2 (/ 3.9 25.0) 1e3)) " nm (HfO2, eps=25.0)"))
(display (string-append "  y_sd_top   = " (number->string (* y_sd_top 1e3)) " nm"))
(display (string-append "  y_sd_bot   = " (number->string (* y_sd_bot 1e3)) " nm"))
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
  (position r_dielectric y_gate_bot 0.0)
  (position r_tin        y_gate_top 0.0)
  "TiN" "R.GateMetal"
)

;;--- 3. HfO2 Gate Dielectric (gate region only) ------------------------------
(sdegeo:create-rectangle
  (position r_cnt        y_gate_bot 0.0)
  (position r_dielectric y_gate_top 0.0)
  "HfO2" "R.GateHfO2"
)

;;--- 4. CNT Channel (full axial extent) --------------------------------------
(sdegeo:create-rectangle
  (position 0.0   y_sd_bot 0.0)
  (position r_cnt y_sd_top 0.0)
  "CNT_thin_film" "R.CNTChannel"
)

;;=============================================================================
;; CONTACT DEFINITIONS
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
(sdedr:define-refinement-size "Ref.CNT"
  1.5e-4   ; max-x (radial)
  2.0e-3   ; max-y (axial)
  1.0e-5   ; min-x
  1.0e-5   ; min-y
)
(sdedr:define-refinement-region "Place.CNT" "Ref.CNT" "R.CNTChannel")

;;--- HfO2 gate dielectric (moderate mesh across 8 nm) ------------------------
(sdedr:define-refinement-size "Ref.GateHfO2"
  1.0e-3   ; max-x = 1.0 nm
  2.0e-3   ; max-y = 2.0 nm
  1.0e-5   ; min-x
  1.0e-5   ; min-y
)
(sdedr:define-refinement-region "Place.GateHfO2" "Ref.GateHfO2" "R.GateHfO2")

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
(sdedr:define-refinement-window "Win.GateEdgeS" "Rectangle"
  (position 0.0 (- y_gate_bot y_edge_w) 0.0)
  (position r_dielectric (+ y_gate_bot y_edge_w) 0.0)
)
(sdedr:define-refinement-placement "Place.GateEdgeS" "Ref.GateEdgeS" "Win.GateEdgeS")

(sdedr:define-refinement-size "Ref.GateEdgeD"
  2.0e-4 5.0e-4 1.0e-5 1.0e-5
)
(sdedr:define-refinement-window "Win.GateEdgeD" "Rectangle"
  (position 0.0 (- y_gate_top y_edge_w) 0.0)
  (position r_dielectric (+ y_gate_top y_edge_w) 0.0)
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
    r_dielectric
    r_tin
  )
)

;;=============================================================================
;; SAVE AND BUILD
;;=============================================================================

(sde:build-mesh "structure_configB")
(sde:save-model "sde_cntfet_configB")

(display "\n========================================")
(display "Config B SDE construction COMPLETE")
(display "========================================")
(display "  Meshed structure: structure_configB_msh.tdr")
(display "  Boundary file:    structure_configB_bnd.tdr")
(display "========================================")
