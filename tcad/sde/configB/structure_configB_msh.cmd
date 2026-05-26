Title "Untitled"

Controls {
}

IOControls {
	EnableSections
}

Definitions {
	Refinement "Ref.CNT" {
		MaxElementSize = ( 0.00015 0.002 )
		MinElementSize = ( 1e-05 1e-05 )
	}
	Refinement "Ref.GateHfO2" {
		MaxElementSize = ( 0.001 0.002 )
		MinElementSize = ( 1e-05 1e-05 )
	}
	Refinement "Ref.TiN" {
		MaxElementSize = ( 0.002 0.005 )
		MinElementSize = ( 0.0005 0.0005 )
	}
	Refinement "Ref.Sub" {
		MaxElementSize = ( 0.05 0.01 )
		MinElementSize = ( 0.001 0.001 )
	}
	Refinement "Ref.GateEdgeS" {
		MaxElementSize = ( 0.0002 0.0005 )
		MinElementSize = ( 1e-05 1e-05 )
	}
	Refinement "Ref.GateEdgeD" {
		MaxElementSize = ( 0.0002 0.0005 )
		MinElementSize = ( 1e-05 1e-05 )
	}
}

Placements {
	Refinement "Place.CNT" {
		Reference = "Ref.CNT"
		RefineWindow = region ["R.CNTChannel"]
	}
	Refinement "Place.GateHfO2" {
		Reference = "Ref.GateHfO2"
		RefineWindow = region ["R.GateHfO2"]
	}
	Refinement "Place.TiN" {
		Reference = "Ref.TiN"
		RefineWindow = region ["R.GateMetal"]
	}
	Refinement "Place.Sub" {
		Reference = "Ref.Sub"
		RefineWindow = region ["R.Substrate"]
	}
	Refinement "Place.GateEdgeS" {
		Reference = "Ref.GateEdgeS"
		RefineWindow = Rectangle [(0 -0.018) (0.008745 -0.014)]
	}
	Refinement "Place.GateEdgeD" {
		Reference = "Ref.GateEdgeD"
		RefineWindow = Rectangle [(0 0.014) (0.008745 0.018)]
	}
}

AxisAligned {
	xCuts=(0.000745, 0.008745, 0.013745)
	yCuts=(-0.016, 0.016, -0.021, 0.021, -0.071, 0.071)
}
