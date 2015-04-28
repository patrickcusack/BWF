keys = {
"MS_ENCODING" 		: ["M-MID_SIDE", "S-MID_SIDE"], 
"XY_ENCODING" 		: ["X-X_Y", "Y-X_Y"],
"STEREO_MIX" 		: ["L-MIX", "R-MIX"],
"STEREO" 			: ["LEFT", "RIGHT"],
"DMS" 				: ["F-DMS", "8-DMS", "R-DMS"],
"LCR" 				: ["L-LCR", "C-LCR", "R-LCR"],
"LCRS" 				: ["L-LCRS", "C-LCRS", "R-LCRS", "S-LCRS"],
"RECORDINGS_5_1"	: ["L-5.1", "C-5.1", "R-5.1", "Ls-5.1", "Rs-5.1", "LFE-5.1"],
"RECORDINGS_7_1" 	: ["L-7.1", "Lc-7.1", "C-7.1", "Rc-7.1", "R-7.1", "Ls-7.1", "Rs-7.1", "LFE-7.1"],
"GENERIC_9" 		: ["L-GENERIC", "Lc-GENERIC", "C-GENERIC", "Rc-GENERIC", "R-GENERIC", "Ls-GENERIC", "Cs-GENERIC", "Rs-GENERIC", "LFE-GENERIC"]}

mKeys = {"TEST":[]}

try:
	print mKeys["TEST"][-1]
except:
	print "mKeys[\"TEST\"] doesn't contain any keys"



print keys["MS_ENCODING"]