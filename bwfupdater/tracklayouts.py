
tracklayouts = {"MS_ENCODING" : {"trackNames":["M MID_SIDE", "S MID_SIDE"], "trackFunctions":["M-MID_SIDE", "S-MID_SIDE"]},
"XY_ENCODING" : {"trackNames":["X X_Y", "Y X_Y"], "trackFunctions":["X-X_Y", "Y-X_Y"]},
"STEREO_MIX" : {"trackNames":["LEFT", "RIGHT"], "trackFunctions":["L-MIX", "R-MIX"]},
"STEREO" : {"trackNames":["LEFT", "RIGHT"], "trackFunctions":["LEFT", "RIGHT"]},
"LCR" : {"trackNames":["LEFT", "CENTER", "RIGHT"], "trackFunctions":["L-LCR", "C-LCR", "R-LCR"]},
"LCRS" : {"trackNames":["LEFT", "CENTER", "RIGHT", "SUB"], "trackFunctions":["L-LCRS", "C-LCRS", "R-LCRS", "S-LCRS"]},
"MIX_5_1" : {"trackNames":["LEFT", "CENTER", "RIGHT", "LEFT SURROUND", "RIGHT SURROUND", "LFE"], "trackFunctions":["L-5.1", "C-5.1", "R-5.1", "Ls-5.1", "Rs-5.1", "LFE-5.1"]},
"MIX_5_1_W" : {"trackNames":["LEFT", "LEFT SURROUND", "CENTER", "RIGHT SURROUND","RIGHT", "LFE"], "trackFunctions":["L-5.1", "Ls-5.1", "C-5.1", "Rs-5.1", "R-5.1", "LFE-5.1"]},
"MIX_5_1_SMPTE" : {"trackNames":["LEFT", "RIGHT", "CENTER", "BOOM", "LEFT SURROUND", "RIGHT SURROUND"], "trackFunctions":["L-5.1", "R-5.1", "C-5.1",  "LFE-5.1", "Ls-5.1", "Rs-5.1"]},
"MIX_7_1" : {"trackNames":["LEFT", "LEFT CENTER", "CENTER", "RIGHT CENTER", "RIGHT", "LEFT SURROUND", "RIGHT SURROUND", "BOOM"], "trackFunctions":["L-7.1", "Lc-7.1", "C-7.1", "Rc-7.1", "R-7.1", "Ls-7.1", "Rs-7.1", "LFE-7.1"]}}

def tracklayoutRepresentation():
	trackLists = []
	for name in tracklayouts.keys():
		trackLists.append(name)

	return trackLists







