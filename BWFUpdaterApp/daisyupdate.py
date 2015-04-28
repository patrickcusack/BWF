import requests
import json
import types
import re

def daisyAssetUpdatePath():
	return 'http://daisy.inbcu.com/daisy/assetupdate/'

def daisyAssetUpdatePathDev():
	return 'http://qa.daisy.nbcuni.ge.com/daisy/assetupdate/'

def updateStatusAsNeedsAttention(daNumber, isDev=True):
	updateStatusWithInfo(daNumber,'Needs Attention',isDev=isDev)

def updateStatusAsAvailable(daNumber, isDev=True):
	updateStatusWithInfo(daNumber,'Available', isDev=isDev)

def updateStatusWithInfo(daNumber, info, isDev=True):

	if isDev == True:
		url = daisyAssetUpdatePathDev() + "updateEnumeratedField/"
	else:
		url = daisyAssetUpdatePath() + "updateEnumeratedField/"

	payload = {'classname':'AssetStatus', 'fieldDescription':info}
	headers = {'content-type':'application/x-www-form-urlencoded'}
	
	r = requests.put('{}{}'.format(url, daNumber), data=payload, headers=headers)
	if r.status_code == 200:
		return True
	else:
		return False

def updateComments(daNumber, comments, isDev=True):

	if isDev == True:
		url = daisyAssetUpdatePathDev() + "updateField/"
	else:
		url = daisyAssetUpdatePath() + "updateField/"

	url = 'http://qa.daisy.nbcuni.ge.com/daisy/assetupdate/updateField/'
	payload = {'fieldName':'comments', 'fieldValue':'New Comments'}
	headers = {'content-type':'application/x-www-form-urlencoded'}

	r = requests.put('{}{}'.format(url, daNumber), data=payload, headers=headers)
	if r.status_code == 200:
		return True
	else:
		return False

def testNames():
		return ["DA000149611_08C19_FTR_TRK_audio_51D.wav",
				"DA000142914_08C19_FTR_ITA_audio_ST20.wav",
				"DA000149650_08C19_FTR_ARA_audio_ST20.wav",
				"DA000142921_08C19_FTR_LAS_audio_51D.wav",
				"DA000149614_08C19_FTR_THA_audio_ST20.wav",
				"DA000142922_08C19_FTR_LAS_audio_ST12.wav",
				"DA000149625_08C19_FTR_NOR_audio_51D.wav",
				"DA000149616_08C19_FTR_SWD_audio_ST12.wav",
				"DA000142853_04041_FTR_ENG_audio_51D.wav",
				"DA000149609_08C19_FTR_TRK_audio_ST12.wav",
				"DA000149635_08C19_FTR_HUN_audio_ST12.wav",
				"DA000149624_08C19_FTR_NOR_audio_ST20.wav",
				"DA000142844_04041_FTR_GER_audio_51D.wav",
				"DA000149633_08C19_FTR_GRK_audio_ST12.wav",
				"DA000149638_08C19_FTR_FIN_audio_51D.wav",
				"DA000142842_04041_FTR_ITA_audio_51D.wav",
				"DA000149439_04041_FTR_FRC_audio_ST12.wav",
				"DA000142916_08C19_FTR_ITA_audio_ST12.wav",
				"DA000149629_08C19_FTR_ME_audio_51D.wav",
				"DA000142836_04041_FTR_BPO_audio_51D.wav",
				"DA000149622_08C19_FTR_POL_audio_ST12.wav",
				"DA000142846_04041_FTR_FRT_audio_51D.wav",
				"DA000149648_08C19_FTR_DUT_audio_51D.wav",
				"DA000149619_08C19_FTR_SWD_audio_51D.wav",
				"DA000149623_08C19_FTR_POL_audio_51D.wav",
				"DA000142917_08C19_FTR_FRT_audio_51D.wav",
				"DA000142839_04041_FTR_CSP_audio_51D.wav",
				"DA000142911_08C19_FTR_CSP_audio_51D.wav",
				"DA000142909_08C19_FTR_RUS_audio_51D.wav",
				"DA000149620_08C19_FTR_POL_audio_ST20.wav",
				"DA000142910_08C19_FTR_CSP_audio_ST20.wav",
				"DA000142925_08C19_FTR_ENG_audio_ST12.wav",
				"DA000142845_04041_FTR_FRT_audio_ST12.wav",
				"DA000142849_04041_FTR_LAS_audio_51D.wav",
				"DA000142912_08C19_FTR_ITA_audio_51D.wav",
				"DA000149630_08C19_FTR_MAN_audio_ST20.wav",
				"DA000149642_08C19_FTR_GRK_audio_51D.wav",
				"DA000149644_08C19_FTR_CZC_audio_ST20.wav",
				"DA000149649_08C19_FTR_DAN_audio_ST12.wav",
				"DA000142905_08C19_FTR_BPO_audio_ST20.wav",
				"DA000149653_08C19_FTR_ARA_audio_51D.wav",
				"DA000149639_08C19_FTR_FIN_audio_ST20.wav",
				"DA000149615_08C19_FTR_THA_audio_51D.wav",
				"DA000142851_04041_FTR_ENG_audio_ST20.wav",
				"DA000149646_08C19_FTR_DAN_audio_51D.wav",
				"DA000142843_04041_FTR_GER_audio_ST20.wav",
				"DA000142906_08C19_FTR_BPO_audio_51D.wav",
				"DA000142904_08C19_FTR_RUS_audio_ST20.wav",
				"DA000149621_08C19_FTR_POR_audio_ST12.wav",
				"DA000149636_08C19_FTR_HUN_audio_51D.wav",
				"DA000546138_08267_FTR_CSP_audio_51D.wav",
				"DA000544027_02428_FTR_ENG_audio_71D.wav",
				"DA000545885_G4101_EPS_ENG_audio_51D.wav",
				"DA000533271_05417_FTR_ENG_audio_ST12.wav",
				"DA000543991_VM432_FTR_LAS_audio_51D.wav",
				"DA000544235_89076_FTR_FIN_audio_51D.wav",
				"DA000547764_Q3901_FTR_CSP_audio_ST12.wav",
				"DA000549483_02373_FTR_RUS_audio_ST20.wav",
				"DA000548288_08J94_FTR_LAS_audio_51D.wav",
				"DA000547549_VM222_FTR_BPO_audio_ST12.wav",
				"DA000545886_G4101_EPS_ENG_audio_ST12.wav",
				"DA000547547_VM222_FTR_BPO_audio_51D.wav",
				"DA000549001_F8501_FTR_BPO_audio_51D.wav",
				"DA000546687_88428_FTR_CSP_audio_51D.wav",
				"DA000549192_G4202_EPS_ENG_audio_ST12.wav",
				"DA000548903_F8501_FTR_LAS_audio_51D.wav",
				"DA000544236_89076_FTR_FIN_audio_ST12.wav",
				"DA000544170_06G82_FTR_ITA_audio_51D.wav",
				"DA000548766_08334_FTR_LAS_audio_ST20.wav",
				"DA000544115_08D68_FTR_ITA_audio_ST12.wav",
				"DA000547512_F8501_FTR_LAS_audio_ST20.wav",
				"DA000547763_Q3901_FTR_CSP_audio_51D.wav",
				"DA000545413_UYS03_EPS_ENG_audio_ST12.wav",
				"DA000533264_05417_FTR_ENG_audio_51D.wav",
				"DA000546693_88572_FTR_CSP_audio_ST12.wav",
				"DA000544238_89076_FTR_NOR_audio_51D.wav",
				"DA000548341_G4002_EPS_ENG_audio_51D.wav",
				"DA000536953_UYS02_EPS_ENG_audio_ST12.wav",
				"DA000547234_08305_FTR_BPO_audio_51D.wav",
				"DA000547127_G3802_EPS_ENG_audio_51D.wav",
				"DA000545381_T8910_EPS_ENG_audio_51D.wav",
				"DA000550531_02149_FTR_TRK_audio_ST20.wav",
				"DA000549841_89076_FTR_DUT_audio_51D.wav",
				"DA000552115_08G35_FTR_LAS_audio_51D.wav",
				"DA000550174_G3403_EPS_ENG_audio_51D.wav",
				"DA000550548_08534_FTR_TRK_audio_ST20.wav",
				"DA000552165_G3704_EPS_ENG_audio_ST12.wav",
				"DA000550336_UYS05_EPS_ENG_audio_ST12.wav",
				"DA000551117_G3404_EPS_ENG_audio_51D.wav",
				"DA000551165_G4003_EPS_ENG_audio_ST12.wav",
				"DA000549613_08K08_FTR_ITA_audio_ST12.wav",
				"DA000552681_88627_FTR_CSP_audio_ST12.wav",
				"DA000552677_08K08_FTR_GER_audio_ST12.wav",
				"DA000552118_08G35_FTR_BPO_audio_51D.wav",
				"DA000552119_08G35_FTR_BPO_audio_ST12.wav",
				"DA000549579_05421_FTR_CSP_audio_ST12.wav",
				"DA000550618_G3703_EPS_ENG_audio_51D.wav",
				"DA000551704_VM432_FTR_BPO_audio_51D.wav",
				"DA000551703_VM432_FTR_BPO_audio_ST20.wav",
				"DA000552680_88627_FTR_CSP_audio_51D.wav",
				"DA000456975_02305_FTR_SWD_audio_51D.wav",
				"DA000490054_CML09_EPS_ENG_audio_51D.wav",
				"DA000395744_T8302_EPS_ENG_audio_ST12.wav",
				"DA000411507_T8204_EPS_ENG_audio_51D.wav",
				"DA000544082_08F89_FTR_ITA_audio_ST12.wav",
				"DA000530075_08J61_FTR_ITA_audio_ST20.wav",
				"DA000530258_F9907_EPS_ENG_audio_51D.wav",
				"DA000526983_88624_FTR_GER_audio_ST20.wav",
				"DA000495432_F7809_EPS_ENG_audio_ST12.wav",
				"DA000533735_G0670_EPS_ENG_audio_ST12.wav",
				"DA000528312_88623_FTR_LAS_audio_ST20.wav",
				"DA000507270_CML14_EPS_ENG_audio_51D.wav",
				"DA000140243_T7501_EPS_ENG_audio_51D.wav",
				"DA000469642_05556_FTR_BPO_audio_51D.wav",
				"DA000474255_08E91_FTR_BPO_audio_ST12.wav",
				"DA000465385_E1309_EPS_CSP_audio_ST12.wav",
				"DA000519683_08J12_FTR_GER_audio_51D.wav",
				"DA000441762_88430_FTR_GER_audio_ST12.wav",
				"DA000455853_08781_FTR_HUN_audio_ST20.wav",
				"DA000502535_08G95_FTR_POL_audio_ST20.wav",
				"DA000420650_T8210_EPS_ENG_audio_ST12.wav",
				"DA000537864_08F46_FTR_GER_audio_ST12.wav",
				"DA000402121_T8304_EPS_ENG_audio_51D.wav",
				"DA000508728_AA818_EPS_BPO_audio_ST12.wav",
				"DA000420655_F6903_EPS_ENG_audio_51D.wav",
				"DA000490257_02387_FTR_CZC_audio_51D.wav",
				"DA000526733_08J27_FTR_BPO_audio_51D.wav",
				"DA000488514_04533_FTR_LAS_audio_ST12.wav",
				"DA000443272_CHX06_EPS_GER_audio_51D.wav",
				"DA000141794_T7611_EPS_ENG_audio_ST12.wav",
				"DA000494973_CMG07_EPS_ENG_audio_51D.wav",
				"DA000544251_08334_FTR_CSP_audio_51D.wav",
				"DA000543293_88429_FTR_POL_audio_ST12.wav",
				"DA000432459_UYL02_EPS_ENG_audio_ST12.wav",
				"DA000512743_T8710_EPS_ENG_audio_51D.wav",
				"DA000411767_T8307_EPS_ENG_audio_ST12.wav",
				"DA000407899_T8306_EPS_ENG_audio_ST12.wav",
				"DA000510227_UWZ24_FTR_POL_audio_ST20.wav",
				"DA000395748_T8302_EPS_ENG_audio_51D.wav",
				"DA000463522_F8910_EPS_ENG_audio_51D.wav",
				"DA000146927_T7570_EPS_ENG_audio_51D.wav",
				"DA000432460_UYL02_EPS_ENG_audio_51D.wav",
				"DA000543085_T8909_EPS_ENG_audio_51D.wav",
				"DA000471648_T3309_EPS_LAS_audio_51D.wav",
				"DA000499192_CMG09_EPS_ENG_audio_51D.wav",
				"DA000533397_T9109_EPS_ENG_audio_51D.wav",
				"DA000476150_08224_FTR_BPO_audio_51D.wav",
				"DA000140713_T7604_EPS_ENG_audio_ST12.wav",
				"DA000452580_02244_FTR_RUS_audio_ST12.wav",
				"DA000455357_08012_FTR_GER_audio_51D.wav",
				"DA000455417_05570_FTR_BPO_audio_51D.wav",
				"DA000469219_E7905_EPS_LAS_audio_51D.wav",
				"DA000455636_02352_FTR_ITA_audio_ST12.wav",
				"DA000452761_05591_FTR_BPO_audio_ST12.wav",
				"DA000469214_E7910_EPS_LAS_audio_51D.wav",
				"DA000452588_02244_FTR_FRT_audio_ST20.wav",
				"DA000469223_E7902_EPS_LAS_audio_51D.wav",
				"DA000452609_02304_FTR_GER_audio_ST12.wav",
				"DA000452742_05484_FTR_BPO_audio_51D.wav",
				"DA000455648_02352_FTR_ENG_audio_51D.wav",
				"DA000452589_02244_FTR_ITA_audio_ST12.wav",
				"DA000452730_05484_FTR_GER_audio_51D.wav",
				"DA000452724_05484_FTR_CSP_audio_ST20.wav",
				"DA000469218_E7904_EPS_LAS_audio_51D.wav",
				"DA000455424_05570_FTR_CSP_audio_ST20.wav",
				"DA000469197_E7905_EPS_LAS_audio_ST12.wav",
				"DA000456352_05647_FTR_LAS_audio_51D.wav",
				"DA000469412_T1101_EPS_LAS_audio_ST12.wav",
				"DA000452578_08A15_FTR_ENG_audio_51D.wav",
				"DA000452662_02371_FTR_ENG_audio_ST12.wav",
				"DA000132931_AA211_EPS_LAS_audio_ST12.wav",
				"DA000485614_E6722_EPS_LAS_audio_ST12.wav",
				"DA000132057_CHH13_EPS_CSP_audio_ST12.wav",
				"DA000471479_F0716_EPS_LAS_audio_ST12.wav",
				"DA000471499_F0772_EPS_LAS_audio_51D.wav",
				"DA000452571_08A15_FTR_CSP_audio_51D.wav",
				"DA000452529_T0A0D_FTR_FRT_audio_51D.wav",
				"DA000132852_AA112_EPS_LAS_audio_ST12.wav",
				"DA000484986_E7410_EPS_LAS_audio_51D.wav",
				"DA000477423_AA214_EPS_GER_audio_ST12.wav",
				"DA000485086_E7810_EPS_LAS_audio_51D.wav",
				"DA000484981_E7417_EPS_LAS_audio_51D.wav",
				"DA000399181_CHI20_EPS_CSP_audio_51D.wav",
				"DA000484967_E7412_EPS_LAS_audio_ST12.wav",
				"DA000485083_E7816_EPS_LAS_audio_51D.wav",
				"DA000471501_F0770_EPS_LAS_audio_51D.wav",
				"DA000129974_UXX01_EPS_CSP_audio_ST12.wav",
				"DA000399168_CHI10_EPS_CSP_audio_ST12.wav",
				"DA000133058_AA306_EPS_LAS_audio_ST12.wav",
				"DA000471496_F0702_EPS_LAS_audio_ST12.wav",
				"DA000477608_AA402_EPS_GER_audio_ST12.wav",
				"DA000452515_T0A0D_FTR_RUS_audio_51D.wav",
				"DA000485437_E5902_EPS_LAS_audio_ST12.wav",
				"DA000399192_CHI07_EPS_CSP_audio_51D.wav",
				"DA000485060_E7816_EPS_LAS_audio_ST12.wav",
				"DA000471514_F0714_EPS_LAS_audio_51D.wav",
				"DA000485088_E7809_EPS_LAS_audio_51D.wav",
				"DA000399198_CHI04_EPS_CSP_audio_51D.wav"]

def showDetailsTest():
	fileName = testNames()[0]
	dLookup = DaisyMetadataLookup(getDaisyNumber(fileName),isDevMode=True)
	if dLookup.isValid == True:
		print dLookup.comments(), dLookup.vendor(), dLookup.statusForFile(fileName)

def markAsNeedsAttentionTest():
	fileName = testNames()[0]
	dLookup = DaisyMetadataLookup(getDaisyNumber(fileName),isDevMode=True)
	if dLookup.isValid == True:
		print dLookup.comments(), dLookup.vendor(), dLookup.statusForFile(fileName)
		updateStatusAsNeedsAttention(getDaisyNumber(fileName))

def markAsAvailableTest():
	fileName = testNames()[0]
	dLookup = DaisyMetadataLookup(getDaisyNumber(fileName),isDevMode=True)
	if dLookup.isValid == True:
		print dLookup.comments(), dLookup.vendor(), dLookup.statusForFile(fileName)
		updateStatusAsAvailable(getDaisyNumber(fileName))

if __name__ == '__main__':
	markAsNeedsAttentionTest()