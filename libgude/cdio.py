from .cdio_base import *

class ARExpansionGoodsDef(CompoundObject):
	_OBJECT_ID = 112

	TYPE_PLACE_GUDETAMA = 0
	TYPE_PLACE_STAMP = 1
	GUDETAMA_OFFSET = 10
	STAMP_OFFSET = 100

	def __init__(self,
		id: Short,
		type: Short,
		price: Object
	):
		self.id = id
		self.type = type
		self.price = price


class AbilityParam(CompoundObject):
	_OBJECT_ID = 90

	KIND_HEAVEN = 0
	KIND_TOUCH = 1
	KIND_ROULETTE_SPEED = 2
	KIND_SUCCESS_PROB = 3
	KIND_HAPPENING_PROB = 4
	KIND_VOICE_PROB = 5
	KIND_HIDDEN_PROB = 6
	KIND_HURRY = 7
	KIND_GET_PTS_COOK = 8
	KIND_REVIVAL_HELPCHARA = 9
	FLAGMASK_TOUCH_INFO = 256
	FLAGMASK_UNIQUE = 512
	FLAGMASK_OVERWRITE = 1024
	TYPE_HEAVEN = 256
	TYPE_TOUCH = 257
	TYPE_ROULETTE_SPEED = 2
	TYPE_SUCCESS_PROB = 515
	TYPE_HAPPENING_PROB = 516
	TYPE_VOICE_PROB = 261
	TYPE_HIDDEN_PROB = 6
	TYPE_HURRY = 7
	TYPE_GET_PTS_COOK = 1032
	TYPE_REVIVAL_HELPCHARA = 521

	def __init__(self,
		type: Int,
		values: Object,
		secs: Int
	):
		self.type = type
		self.values = values
		self.secs = secs


class AssistInfo(CompoundObject):
	_OBJECT_ID = 82

	def __init__(self,
		aid: Double,
		encodedUid: Int,
		playerName: String,
		playerRank: Int,
		kitchenwareType: Int,
		gudetamaId: Int,
		finishTimeSecs: Int,
		usefulId: Int,
		assistTimeSecs: Int,
		avatar: Int,
		snsProfileImage: Object,
		snsType: Byte
	):
		self.aid = aid
		self.encodedUid = encodedUid
		self.playerName = playerName
		self.playerRank = playerRank
		self.kitchenwareType = kitchenwareType
		self.gudetamaId = gudetamaId
		self.finishTimeSecs = finishTimeSecs
		self.usefulId = usefulId
		self.assistTimeSecs = assistTimeSecs
		self.avatar = avatar
		self.snsProfileImage = snsProfileImage
		self.snsType = snsType


class AvatarData(CompoundObject):
	_OBJECT_ID = 96

	def __init__(self,
		id: Int,
		acquired: Boolean,
		available: Boolean
	):
		self.id = id
		self.acquired = acquired
		self.available = available


class AvatarDef(CompoundObject):
	_OBJECT_ID = 79

	def __init__(self,
		id: Int,
		rsrc: Int,
		name: String,
		desc: String,
		conditionDesc: String,
		price: Object,
		isNew: Boolean
	):
		self.id = id
		self.rsrc = rsrc
		self.name = name
		self.desc = desc
		self.conditionDesc = conditionDesc
		self.price = price
		self.isNew = isNew


class AvatarInfo(CompoundObject):
	_OBJECT_ID = 103

	def __init__(self,
		updateAvatars: Object,
		removeAvatarIds: Object
	):
		self.updateAvatars = updateAvatars
		self.removeAvatarIds = removeAvatarIds


class CheckedMessageInfo(CompoundObject):
	_OBJECT_ID = 42

	def __init__(self,
		seq: Object,
		type: Int,
		target: Int
	):
		self.seq = seq
		self.type = type
		self.target = target


class ComicDef(CompoundObject):
	_OBJECT_ID = 126

	def __init__(self,
		id: Int,
		rsrcs: Object,
		comicSpine: Object
	):
		self.id = id
		self.rsrcs = rsrcs
		self.comicSpine = comicSpine


class ComicSpineDef(CompoundObject):
	_OBJECT_ID = 139

	def __init__(self,
		id: Int,
		spainMap: HashMap,
		spainAnimeMap: HashMap,
		spainScaleMap: HashMap,
		spainDelayMap: HashMap
	):
		self.id = id
		self.spainMap = spainMap
		self.spainAnimeMap = spainAnimeMap
		self.spainScaleMap = spainScaleMap
		self.spainDelayMap = spainDelayMap


class CommentDef(CompoundObject):
	_OBJECT_ID = 115

	def __init__(self,
		id: Int,
		name: String
	):
		self.id = id
		self.name = name


class CommonConstants(CompoundObject):
	_OBJECT_ID = 12

	PLATFORM_UNKNOWN = -1
	PLATFORM_IOS = 0
	PLATFORM_ANDROID = 1
	PLATFORM_WINDOWS = 2
	PLATFORM_OTHER = 3
	PLATFORM_ONESTORE = 4
	GENDER_MALE = 0
	GENDER_FEMALE = 1
	LOCALE_ALL = "all"
	LOCALE_JA = "ja"
	LOCALE_EN = "en"
	LOCALE_KO = "ko"
	LOCALE_CN = "cn"
	LOCALE_TW = "tw"
	LOCALE_PT = "pt"
	LOCALE_ID = "id"
	LOCALE_TH = "th"
	LOCALE_VI = "vi"
	COUNTRY_CODE_ALL = 0
	COUNTRY_CODE_JA = 1
	COUNTRY_CODE_US = 2

	def __init__(self,
	):
		pass


class ConvertParam(CompoundObject):
	_OBJECT_ID = 30

	KIND_MONEY = 0
	KIND_FREE_METAL = 1
	KIND_CHARGE_METAL = 2
	KIND_SUB_METAL = 3
	KIND_KITCHENWARE = 4
	KIND_RECIPE_NOTE = 5
	KIND_RECIPE = 6
	KIND_GUDETAMA = 7
	KIND_USEFUL = 8
	KIND_DECORATION = 9
	KIND_UTENSIL = 10
	KIND_STAMP = 11
	KIND_AVATAR = 12
	KIND_COMMENT = 13
	KIND_CHARGE_MONEY = 14
	KIND_RANKING_POINT = 15
	KIND_MONTHLY_BONUS = 16
	KIND_ONLY_SHOW = 17
	KIND_SET_ITEM = 18
	KIND_CUP_GACHA = 19
	KIND_FRAME = 20
	KIND_NUM = 21

	def __init__(self,
		originalItem: Object,
		convertedItem: Object,
		convertedParam: Object,
		kind: Int,
		id: Int,
		num: Int
	):
		self.originalItem = originalItem
		self.convertedItem = convertedItem
		self.convertedParam = convertedParam
		self.kind = kind
		self.id = id
		self.num = num


class CupGachaData(CompoundObject):
	_OBJECT_ID = 132

	SLOT_NUM = 4

	def __init__(self,
		cookIndex: Byte,
		cupGachaIds: Object,
		restSec: Int,
		showAdNum: Byte
	):
		self.cookIndex = cookIndex
		self.cupGachaIds = cupGachaIds
		self.restSec = restSec
		self.showAdNum = showAdNum


class CupGachaDef(CompoundObject):
	_OBJECT_ID = 131

	def __init__(self,
		id: Int,
		rsrc: Int,
		name: String,
		desc: String,
		rarity: Byte,
		prizes: Object,
		oddses: Object,
		cookMin: Int,
		price: Object,
		isNew: Boolean,
		conditionDesc: String,
		sortIndex: Int,
		enableCountryFlags: Object,
		missionCommonID: Int
	):
		self.id = id
		self.rsrc = rsrc
		self.name = name
		self.desc = desc
		self.rarity = rarity
		self.prizes = prizes
		self.oddses = oddses
		self.cookMin = cookMin
		self.price = price
		self.isNew = isNew
		self.conditionDesc = conditionDesc
		self.sortIndex = sortIndex
		self.enableCountryFlags = enableCountryFlags
		self.missionCommonID = missionCommonID


class CupGachaResult(CompoundObject):
	_OBJECT_ID = 133

	def __init__(self,
		id: Int,
		results: ArrayList
	):
		self.id = id
		self.results = results


class DecorationData(CompoundObject):
	_OBJECT_ID = 74

	def __init__(self,
		id: Int,
		acquired: Boolean,
		available: Boolean
	):
		self.id = id
		self.acquired = acquired
		self.available = available


class DecorationDef(CompoundObject):
	_OBJECT_ID = 73

	def __init__(self,
		id: Int,
		rsrc: Int,
		name: String,
		desc: String,
		conditionDesc: String,
		price: Object,
		isNew: Boolean
	):
		self.id = id
		self.rsrc = rsrc
		self.name = name
		self.desc = desc
		self.conditionDesc = conditionDesc
		self.price = price
		self.isNew = isNew


class DecorationInfo(CompoundObject):
	_OBJECT_ID = 75

	def __init__(self,
		updateDecorations: Object,
		removeDecorationIds: Object
	):
		self.updateDecorations = updateDecorations
		self.removeDecorationIds = removeDecorationIds


class DeliverPointTableDef(CompoundObject):
	_OBJECT_ID = 123

	def __init__(self,
		id: Int,
		gudePointMap: IntHashMap
	):
		self.id = id
		self.gudePointMap = gudePointMap


class DelusionDef(CompoundObject):
	_OBJECT_ID = 86

	def __init__(self,
		param: Object
	):
		self.param = param


class DelusionParam(CompoundObject):
	_OBJECT_ID = 87

	def __init__(self,
		pastMinutes: Int
	):
		self.pastMinutes = pastMinutes


class DictDef(CompoundObject):
	_OBJECT_ID = 19

	def __init__(self,
		uitext: HashMap,
		message: HashMap,
		textplain: HashMap,
		others: HashMap,
		voice: HashMap,
		guide: HashMap,
		inviteRewardRobos: Object,
		guideLocalizeImages: Object,
		noticeLocalizeImages: Object,
		notice: Object,
		hintNum: Int
	):
		self.uitext = uitext
		self.message = message
		self.textplain = textplain
		self.others = others
		self.voice = voice
		self.guide = guide
		self.inviteRewardRobos = inviteRewardRobos
		self.guideLocalizeImages = guideLocalizeImages
		self.noticeLocalizeImages = noticeLocalizeImages
		self.notice = notice
		self.hintNum = hintNum


class EventData(CompoundObject):
	_OBJECT_ID = 118

	def __init__(self,
		id: Int,
		endRestTimeSecs: Int,
		background: String,
		buttonImage: String,
		title: String,
		message: String,
		url: String,
		decorationId: Int,
		endTallyRestTimeSecs: Int,
		rankingId: Int,
		noticeIconRsrc: Int,
		gudetamaIds: Object,
		chBGM: Object,
		rentalDecorations: Object,
		noticeTextKey: String,
		attendable: Boolean
	):
		self.id = id
		self.endRestTimeSecs = endRestTimeSecs
		self.background = background
		self.buttonImage = buttonImage
		self.title = title
		self.message = message
		self.url = url
		self.decorationId = decorationId
		self.endTallyRestTimeSecs = endTallyRestTimeSecs
		self.rankingId = rankingId
		self.noticeIconRsrc = noticeIconRsrc
		self.gudetamaIds = gudetamaIds
		self.chBGM = chBGM
		self.rentalDecorations = rentalDecorations
		self.noticeTextKey = noticeTextKey
		self.attendable = attendable


class EventPreset(CompoundObject):
	_OBJECT_ID = 27

	def __init__(self,
	):
		pass


class FeatureDef(CompoundObject):
	_OBJECT_ID = 92

	TYPE_COLLECTION = 0
	TYPE_AR = 1
	TYPE_MANUAL_STOP = 2
	TYPE_OVEN = 3
	TYPE_PLACE = 4
	TYPE_RARE_VOICE = 5
	TYPE_DELUSION = 6
	TYPE_ROULETTE_SPEED = 7
	TYPE_MISSION = 8
	TYPE_USEFUL = 9
	TYPE_GACHA = 10
	TYPE_MISSION_DAILY = 11
	TYPE_FRIEND = 12
	TYPE_SNS_ICON = 13
	TYPE_ROOM_DECO = 14
	TYPE_CUP_GACHA = 15
	TYPE_HOME_DECO = 16

	def __init__(self,
		paramMap: IntHashMap
	):
		self.paramMap = paramMap


class FeatureParam(CompoundObject):
	_OBJECT_ID = 93

	def __init__(self,
		type: Int,
		value: Int
	):
		self.type = type
		self.value = value


class FileInfoDef(CompoundObject):
	_OBJECT_ID = 16

	def __init__(self,
		path: String,
		size: Int,
		hash: Int,
		hasLocale: Boolean
	):
		self.path = path
		self.size = size
		self.hash = hash
		self.hasLocale = hasLocale


class FirstLoginInfo(CompoundObject):
	_OBJECT_ID = 28

	def __init__(self,
		name: String,
		gender: Int,
		area: Int,
		timeZone: String,
		locale: String,
		deckIndex: Int,
		comment: Int,
		avatar: Int
	):
		self.name = name
		self.gender = gender
		self.area = area
		self.timeZone = timeZone
		self.locale = locale
		self.deckIndex = deckIndex
		self.comment = comment
		self.avatar = avatar


class FriendAssistResult(CompoundObject):
	_OBJECT_ID = 53

	def __init__(self,
		userRoomInfo: Object,
		lastFriendly: Int,
		addFriendly: Int,
		lastFriendlyLevel: Int
	):
		self.userRoomInfo = userRoomInfo
		self.lastFriendly = lastFriendly
		self.addFriendly = addFriendly
		self.lastFriendlyLevel = lastFriendlyLevel


class FriendInfo(CompoundObject):
	_OBJECT_ID = 51

	def __init__(self,
		friendlyData: Object,
		wantedGudetamas: Object,
		friendPresentLogDiff: Object,
		lastFriendlyLevel: Int
	):
		self.friendlyData = friendlyData
		self.wantedGudetamas = wantedGudetamas
		self.friendPresentLogDiff = friendPresentLogDiff
		self.lastFriendlyLevel = lastFriendlyLevel


class FriendPresentResult(CompoundObject):
	_OBJECT_ID = 52

	def __init__(self,
		friendlyData: Object,
		consumedGudetama: Object,
		lastFriendly: Int,
		addFriendly: Int,
		friendPresentLogDiff: Object,
		lastFriendlyLevel: Int,
		deliveredEventIds: Object
	):
		self.friendlyData = friendlyData
		self.consumedGudetama = consumedGudetama
		self.lastFriendly = lastFriendly
		self.addFriendly = addFriendly
		self.friendPresentLogDiff = friendPresentLogDiff
		self.lastFriendlyLevel = lastFriendlyLevel
		self.deliveredEventIds = deliveredEventIds


class FriendlyData(CompoundObject):
	_OBJECT_ID = 111

	def __init__(self,
		encodedUid: Int,
		friendly: Int,
		friendlyLevel: Int
	):
		self.encodedUid = encodedUid
		self.friendly = friendly
		self.friendlyLevel = friendlyLevel


class FriendlyDef(CompoundObject):
	_OBJECT_ID = 109

	def __init__(self,
		params: Object,
		heartBorders: Object
	):
		self.params = params
		self.heartBorders = heartBorders


class FriendlyParam(CompoundObject):
	_OBJECT_ID = 110

	def __init__(self,
		index: Int,
		max: Int,
		rewards: Object
	):
		self.index = index
		self.max = max
		self.rewards = rewards


class GachaData(CompoundObject):
	_OBJECT_ID = 66

	def __init__(self,
		id: Int,
		existsPickup: Boolean
	):
		self.id = id
		self.existsPickup = existsPickup


class GachaDef(CompoundObject):
	_OBJECT_ID = 64

	RARITY_COMMON = 0
	RARITY_UNCOMMON = 1
	RARITY_RARE = 2

	def __init__(self,
		id: Int,
		rsrc: Int,
		sortIndex: Int,
		name: String,
		desc: String,
		lineupDesc: String,
		prices: Object,
		numFree: Int,
		numOnceMore: Int,
		screeningItems: Object,
		ratesAtKind: Object,
		hasRareStamp: Boolean,
		gachaLineupPrioritizedKinds: Object
	):
		self.id = id
		self.rsrc = rsrc
		self.sortIndex = sortIndex
		self.name = name
		self.desc = desc
		self.lineupDesc = lineupDesc
		self.prices = prices
		self.numFree = numFree
		self.numOnceMore = numOnceMore
		self.screeningItems = screeningItems
		self.ratesAtKind = ratesAtKind
		self.hasRareStamp = hasRareStamp
		self.gachaLineupPrioritizedKinds = gachaLineupPrioritizedKinds


class GachaPriceDef(CompoundObject):
	_OBJECT_ID = 65

	def __init__(self,
		num: Int,
		prices: Object,
		numDaily: Int,
		enabledCollect: Boolean
	):
		self.num = num
		self.prices = prices
		self.numDaily = numDaily
		self.enabledCollect = enabledCollect


class GachaResult(CompoundObject):
	_OBJECT_ID = 69

	def __init__(self,
		userGachaData: Object,
		items: Object,
		params: Object,
		convertedItems: Object,
		rarities: Object,
		worthFlags: Object,
		onceMore: Boolean,
		useItem: Object
	):
		self.userGachaData = userGachaData
		self.items = items
		self.params = params
		self.convertedItems = convertedItems
		self.rarities = rarities
		self.worthFlags = worthFlags
		self.onceMore = onceMore
		self.useItem = useItem


class GameDef(CompoundObject):
	_OBJECT_ID = 18

	def __init__(self,
		version: Int,
		dict: Object,
		initDict: Object,
		rule: Object,
		screening: Object,
		kitchenwareMap: IntHashMap,
		recipeNoteMap: IntHashMap,
		gudetamaMap: IntHashMap,
		voiceMap: IntHashMap,
		gachaMap: IntHashMap,
		usefulMap: IntHashMap,
		decorationMap: IntHashMap,
		utensilMap: IntHashMap,
		stampMap: IntHashMap,
		avatarMap: IntHashMap,
		missionMap: IntHashMap,
		touch: Object,
		delusion: Object,
		feature: Object,
		friendly: Object,
		videoAdReward: Object,
		linkageMap: IntHashMap,
		questionMap: IntHashMap,
		arExpansionGoodsMap: IntHashMap,
		hideGudeMap: IntHashMap,
		commentMap: IntHashMap,
		promotionVideoMap: IntHashMap,
		identifiedPresentMap: IntHashMap,
		shareBonusMap: IntHashMap,
		quizGenreIdMax: Int,
		battleItemIdMax: Int,
		metalShopTable: IntHashMap,
		monthlyPremiumBonusTable: IntHashMap,
		guideTalkTable: IntHashMap,
		rankingMap: IntHashMap,
		rankingRewardMap: IntHashMap,
		fileInfos: Object,
		locale: String,
		resourceUrl: String,
		purchasePresentTable: IntHashMap,
		bannerTable: IntHashMap,
		interTable: IntHashMap,
		deliverPointTableMap: IntHashMap,
		setItemMap: IntHashMap,
		comicMap: IntHashMap,
		onlyShowMap: IntHashMap,
		cupGachaMap: IntHashMap,
		homeExpansionGoodsMap: IntHashMap,
		homeStampSettingMap: IntHashMap,
		kitchenwareConditionMap: IntHashMap,
		helperSettingMap: IntHashMap,
		helperComicDef: Object
	):
		self.version = version
		self.dict = dict
		self.initDict = initDict
		self.rule = rule
		self.screening = screening
		self.kitchenwareMap = kitchenwareMap
		self.recipeNoteMap = recipeNoteMap
		self.gudetamaMap = gudetamaMap
		self.voiceMap = voiceMap
		self.gachaMap = gachaMap
		self.usefulMap = usefulMap
		self.decorationMap = decorationMap
		self.utensilMap = utensilMap
		self.stampMap = stampMap
		self.avatarMap = avatarMap
		self.missionMap = missionMap
		self.touch = touch
		self.delusion = delusion
		self.feature = feature
		self.friendly = friendly
		self.videoAdReward = videoAdReward
		self.linkageMap = linkageMap
		self.questionMap = questionMap
		self.arExpansionGoodsMap = arExpansionGoodsMap
		self.hideGudeMap = hideGudeMap
		self.commentMap = commentMap
		self.promotionVideoMap = promotionVideoMap
		self.identifiedPresentMap = identifiedPresentMap
		self.shareBonusMap = shareBonusMap
		self.quizGenreIdMax = quizGenreIdMax
		self.battleItemIdMax = battleItemIdMax
		self.metalShopTable = metalShopTable
		self.monthlyPremiumBonusTable = monthlyPremiumBonusTable
		self.guideTalkTable = guideTalkTable
		self.rankingMap = rankingMap
		self.rankingRewardMap = rankingRewardMap
		self.fileInfos = fileInfos
		self.locale = locale
		self.resourceUrl = resourceUrl
		self.purchasePresentTable = purchasePresentTable
		self.bannerTable = bannerTable
		self.interTable = interTable
		self.deliverPointTableMap = deliverPointTableMap
		self.setItemMap = setItemMap
		self.comicMap = comicMap
		self.onlyShowMap = onlyShowMap
		self.cupGachaMap = cupGachaMap
		self.homeExpansionGoodsMap = homeExpansionGoodsMap
		self.homeStampSettingMap = homeStampSettingMap
		self.kitchenwareConditionMap = kitchenwareConditionMap
		self.helperSettingMap = helperSettingMap
		self.helperComicDef = helperComicDef


class GetItemResult(CompoundObject):
	_OBJECT_ID = 116

	def __init__(self,
		item: Object,
		param: Object,
		toMail: Boolean
	):
		self.item = item
		self.param = param
		self.toMail = toMail


class GudetamaConstants(CompoundObject):
	_OBJECT_ID = 47

	NUM_PREFECTURES = 47
	NUM_COMMENTS = 1
	NUM_WANTED = 3
	MAX_LOGS = 20
	MAX_OTHERS_LOGS = 5
	MAX_KEEP_LOG_DAYS = 7
	TOUCH_INDEX_GUDETAMA = 0
	TOUCH_INDEX_VOICE = 1
	TOUCH_INDEX_REMOTE = 2
	TOUCH_INDEX_PHONE = 3
	TOUCH_INDEX_SAUCE = 4
	TOUCH_INDEX_SOY_SAUCE = 5
	TOUCH_INDEX_SOY_SAUCE_FISH = 6
	TOUCH_INDEX_SOY_SAUCE_FISH_GOLD = 7
	TOUCH_INDEX_HEAVEN = 8
	NUM_TOUCH_TEXT = 3
	MENU_LINKAGE = 0
	MENU_WATCHWORD = 1
	MENU_HELP = 2
	MENU_INQUIRY = 3
	MENU_OPTION = 4
	MENU_TITLE = 5
	MENU_INFO = 6
	MENU_BLOCK = 7
	SHOP_PURCHASE_METAL = 0
	SHOP_PURCHASE_MONEY = 1
	SHOP_UTENSIL = 2
	SHOP_USEFUL = 3
	SHOP_DECORATION = 4
	SHOP_AVATAR = 5
	SHOP_STAMP = 6
	SHOP_SET_ITEM = 7
	SHOP_CUP_GACHA = 8
	MAX_GACHA_COLLECT = 10
	USEFUL_ID_HURRY_GOLD = 62
	USEFUL_ID_HURRY_SILVER = 63
	USEFUL_ID_HURRY_15MIN = 64
	COLLECTION_NUMBER = 0
	COLLECTION_CATEGORY = 1
	COLLECTION_AREA = 2
	COLLECTION_EVENT = 3
	SNS_TWITTER = 0
	SNS_INSTAGRAM = 1
	SNS_LINE = 2
	SNS_FACEBOOK = 3
	SNS_KAKAO = 4
	SNS_PLURK = 5
	SNS_WEIBO = 6
	SNS_WEIXIN = 7
	SHARE_AR_IMAGE = 0
	SHARE_AR_VIDEO = 1
	SHARE_HIDE_GUDE = 2
	SHARE_WANTED = 3
	SHARE_GUDE_IMAGE = 4
	SHARE_DIALOG = 5
	SHARE_HONEDECO = 6
	PUSH_PERMIT_INFO = 1
	PUSH_PERMIT_COOK = 2
	PUSH_PERMIT_FRIEND_PRESENT_GUDE = 4
	PUSH_PERMIT_FRIEND_PRESENT_GP = 8
	PUSH_PERMIT_DELUSION = 16
	PUSH_PERMIT_CUP_GACHA = 32
	PUSH_PERMIT_ALL = 63

	def __init__(self,
	):
		pass


class GudetamaData(CompoundObject):
	_OBJECT_ID = 61

	GUDETAMA_MAX = 999

	def __init__(self,
		id: Int,
		count: Short,
		num: Short,
		unlockedVoiceIndex: Byte,
		available: Boolean,
		unlocked: Boolean,
		alreadyChallenge: Boolean,
		cookedHappening: Boolean,
		cookedFailure: Boolean,
		targetValue: Int,
		currentValue: Int,
		currentTarget: Int
	):
		self.id = id
		self.count = count
		self.num = num
		self.unlockedVoiceIndex = unlockedVoiceIndex
		self.available = available
		self.unlocked = unlocked
		self.alreadyChallenge = alreadyChallenge
		self.cookedHappening = cookedHappening
		self.cookedFailure = cookedFailure
		self.targetValue = targetValue
		self.currentValue = currentValue
		self.currentTarget = currentTarget


class GudetamaDef(CompoundObject):
	_OBJECT_ID = 60

	TYPE_PRIVATELY = 0
	TYPE_NUMBERING = 1
	TYPE_EVENT = 2
	TYPE_EVENT_ONLY_RECIPE = 3
	RARE_0 = 0
	RARE_1 = 1
	RARE_2 = 2
	RARE_3 = 3
	RARE_4 = 4
	CATEGORY_NATURAL = 0
	CATEGORY_CONFECTIONERY = 1
	CATEGORY_BOIL = 2
	CATEGORY_WONDER = 3
	CATEGORY_SOLID = 4
	CATEGORY_SIMPLE = 5
	CATEGORY_DRESS_UP = 6
	CATEGORY_PLENTIFULLY = 7
	CATEGORY_NOODLE = 8
	CATEGORY_RICE = 9
	CATEGORY_MORNING = 10
	CATEGORY_SOBER = 11
	CATEGORY_PSEUDO = 12
	CATEGORY_XMAS = 13
	CATEGORY_SEVEN_GODS = 14
	CATEGORY_CUP = 15
	COUNTRY_JAPAN = 0
	COUNTRY_NONE = 127
	AREA_HOKKAIDO = 0
	AREA_AOMORI = 1
	AREA_IWATE = 2
	AREA_MIYAGI = 3
	AREA_AKITA = 4
	AREA_YAMAGATA = 5
	AREA_FUKUSHIMA = 6
	AREA_IBARAKI = 7
	AREA_TOCHIGI = 8
	AREA_GUMMA = 9
	AREA_SAITAMA = 10
	AREA_CHIBA = 11
	AREA_TOKYO = 12
	AREA_KANAGAWA = 13
	AREA_NIIGATA = 14
	AREA_TOYAMA = 15
	AREA_ISHIKAWA = 16
	AREA_FUKUI = 17
	AREA_YAMANASHI = 18
	AREA_NAGANO = 19
	AREA_GIFU = 20
	AREA_SHIZUOKA = 21
	AREA_AICHI = 22
	AREA_MIE = 23
	AREA_SHIGA = 24
	AREA_KYOTO = 25
	AREA_OSAKA = 26
	AREA_HYOGO = 27
	AREA_NARA = 28
	AREA_WAKAYAMA = 29
	AREA_TOTTORI = 30
	AREA_SHIMANE = 31
	AREA_OKAYAMA = 32
	AREA_HIROSHIMA = 33
	AREA_YAMAGUCHI = 34
	AREA_TOKUSHIMA = 35
	AREA_KAGAWA = 36
	AREA_EHIME = 37
	AREA_KOCHI = 38
	AREA_FUKUOKA = 39
	AREA_SAGA = 40
	AREA_NAGASAKI = 41
	AREA_KUMAMOTO = 42
	AREA_OITA = 43
	AREA_MIYAZAKI = 44
	AREA_KAGOSHIMA = 45
	AREA_OKINAWA = 46
	AREA_NONE = 999
	MAX_NUM_VOICE = 2
	VOICE_OFFSET = 2
	VOICE_NORMAL_GUDETAMA = 0
	VOICE_GURETAMA = 1
	VOICE_NISETAMA = 2
	VOICE_HARDBOILED = 3
	DROP_ANIME_SWING = 0
	DROP_ANIME_SCALING = 1
	MATERIAL_SOY_SAUCE = 1
	MATERIAL_BACON = 2
	MATERIAL_SUGAR = 4
	MATERIAL_BREAD = 8
	MATERIAL_PASTA = 16
	MATERIAL_VEGETABLE = 32
	MATERIAL_MEAT = 64
	MATERIAL_RICE = 128
	MATERIAL_MILK = 256
	MATERIAL_NUM = 9
	MAX_PERCENT = 100
	ROULETTE_SUCCESS = 0
	ROULETTE_HAPPENING = 1
	ROULETTE_FAILURE = 2

	def __init__(self,
		id: Int,
		rsrc: Int,
		uncountable: Boolean,
		disabledSpine: Boolean,
		imageOffsX: Int,
		imageOffsY: Int,
		kitchenwareId: Int,
		recipeNoteId: Int,
		type: Byte,
		number: Int,
		name: String,
		wrappedName: String,
		desc: String,
		cost: Int,
		reward: Int,
		rarity: Byte,
		category: Byte,
		country: Byte,
		area: Short,
		voices: Object,
		voiceType: Byte,
		dropAnime: Int,
		dish: Boolean,
		materials: Int,
		conditionDesc: String,
		roulettes: Object,
		rouletteTimePerRound: Int,
		cookingResultType: Int,
		isGacha: Boolean,
		requiredGudetamas: Object,
		touchTextParams: Object,
		rubTextParams: Object,
		isCup: Boolean,
		targetType: Int,
		targetId: Int
	):
		self.id = id
		self.rsrc = rsrc
		self.uncountable = uncountable
		self.disabledSpine = disabledSpine
		self.imageOffsX = imageOffsX
		self.imageOffsY = imageOffsY
		self.kitchenwareId = kitchenwareId
		self.recipeNoteId = recipeNoteId
		self.type = type
		self.number = number
		self.name = name
		self.wrappedName = wrappedName
		self.desc = desc
		self.cost = cost
		self.reward = reward
		self.rarity = rarity
		self.category = category
		self.country = country
		self.area = area
		self.voices = voices
		self.voiceType = voiceType
		self.dropAnime = dropAnime
		self.dish = dish
		self.materials = materials
		self.conditionDesc = conditionDesc
		self.roulettes = roulettes
		self.rouletteTimePerRound = rouletteTimePerRound
		self.cookingResultType = cookingResultType
		self.isGacha = isGacha
		self.requiredGudetamas = requiredGudetamas
		self.touchTextParams = touchTextParams
		self.rubTextParams = rubTextParams
		self.isCup = isCup
		self.targetType = targetType
		self.targetId = targetId


class GuideTalkDef(CompoundObject):
	_OBJECT_ID = 24

	NONE = 0
	FRONT = 1
	LEFT = 2
	RIGHT = 3
	CENTER = 4
	WINDOW = 5
	BACKGROUND = 6
	FILL = 7
	SHUTTER = 8
	PICTURE_IMAGE = 9
	EVENT_NONE = -1
	EVENT_CHANGE = 0
	EVENT_ANIMATION = 1
	EVENT_CHOICES = 2
	EVENT_BACKGROUND = 3
	EVENT_DISAPPEAR = 4
	EVENT_TWEEN = 5
	EVENT_MUSIC = 6
	EVENT_EMOTION = 7
	EVENT_PICTURE_IMAGE = 8
	EVENT_OPPONENT_POS = 9
	EVENT_BACKGROUND_POS = 10
	EVENT_SOUND = 11
	EVENT_FOCUS_CHARACTER = 12
	EVENT_MOVIE = 13
	EVENT_BACKGROUND_SPINE = 14
	EVENT_SCREEN_EFFECT = 15
	EVENT_EXTRA = 16
	EVENT_CALLBACK = 17
	EVENT_INTERRUPTION = 18
	EVENT_GUIDE_ARROW = 19
	POS_LEFT = -1
	POS_CENTER = 0
	POS_RIGHT = 1
	EXTRA = -2147483648

	def __init__(self,
		id: Int,
		paragraph: Object,
		cannotSkip: Boolean
	):
		self.id = id
		self.paragraph = paragraph
		self.cannotSkip = cannotSkip


class GuideTalkParagraphParam(CompoundObject):
	_OBJECT_ID = 25

	def __init__(self,
		sentences: Object
	):
		self.sentences = sentences


class GuideTalkSentenceParam(CompoundObject):
	_OBJECT_ID = 26

	def __init__(self,
		word: Boolean,
		event: Byte,
		paramInt: Int,
		paramStr: String,
		waitTime: Float,
		forceTime: Float,
		nextWordsConnect: Boolean,
		forceWordsFinish: Boolean
	):
		self.word = word
		self.event = event
		self.paramInt = paramInt
		self.paramStr = paramStr
		self.waitTime = waitTime
		self.forceTime = forceTime
		self.nextWordsConnect = nextWordsConnect
		self.forceWordsFinish = forceWordsFinish


class HelperCharaDef(CompoundObject):
	_OBJECT_ID = 138

	IDLE = "idle_loop"
	TOUCH = "animation"

	def __init__(self,
		id: Int,
		rsrc: Int,
		showRate: Int,
		massages: HashMap,
		massagePosIndex: HashMap,
		voices: HashMap,
		fixHelperPosX: Int
	):
		self.id = id
		self.rsrc = rsrc
		self.showRate = showRate
		self.massages = massages
		self.massagePosIndex = massagePosIndex
		self.voices = voices
		self.fixHelperPosX = fixHelperPosX


class HideGudetamaDef(CompoundObject):
	_OBJECT_ID = 114

	def __init__(self,
		id: Int,
		name: String
	):
		self.id = id
		self.name = name


class HomeDecoData(CompoundObject):
	_OBJECT_ID = 134

	def __init__(self,
		stampId: Int,
		index: Short,
		x: Double,
		y: Double,
		rotation: Float,
		scale: Float,
		screenPosRateX: Float,
		screenPosRateY: Float,
		isSpain: Boolean
	):
		self.stampId = stampId
		self.index = index
		self.x = x
		self.y = y
		self.rotation = rotation
		self.scale = scale
		self.screenPosRateX = screenPosRateX
		self.screenPosRateY = screenPosRateY
		self.isSpain = isSpain


class HomeExpansionGoodsDef(CompoundObject):
	_OBJECT_ID = 135

	def __init__(self,
		id: Short,
		price: Object
	):
		self.id = id
		self.price = price


class HomeStampSettingDef(CompoundObject):
	_OBJECT_ID = 136

	def __init__(self,
		id: Int,
		animationName: String,
		slotName: String,
		attachmentName: String,
		loop: Boolean,
		touchSetting: Object,
		music: String,
		sound: String
	):
		self.id = id
		self.animationName = animationName
		self.slotName = slotName
		self.attachmentName = attachmentName
		self.loop = loop
		self.touchSetting = touchSetting
		self.music = music
		self.sound = sound


class IdentifiedPresentDef(CompoundObject):
	_OBJECT_ID = 121

	def __init__(self,
		id: Int,
		limit: Int,
		url: String
	):
		self.id = id
		self.limit = limit
		self.url = url


class InitDictDef(CompoundObject):
	_OBJECT_ID = 100

	def __init__(self,
		others: HashMap,
		uitext: HashMap
	):
		self.others = others
		self.uitext = uitext


class ItemParam(CompoundObject):
	_OBJECT_ID = 29

	KIND_MONEY = 0
	KIND_FREE_METAL = 1
	KIND_CHARGE_METAL = 2
	KIND_SUB_METAL = 3
	KIND_KITCHENWARE = 4
	KIND_RECIPE_NOTE = 5
	KIND_RECIPE = 6
	KIND_GUDETAMA = 7
	KIND_USEFUL = 8
	KIND_DECORATION = 9
	KIND_UTENSIL = 10
	KIND_STAMP = 11
	KIND_AVATAR = 12
	KIND_COMMENT = 13
	KIND_CHARGE_MONEY = 14
	KIND_RANKING_POINT = 15
	KIND_MONTHLY_BONUS = 16
	KIND_ONLY_SHOW = 17
	KIND_SET_ITEM = 18
	KIND_CUP_GACHA = 19
	KIND_FRAME = 20
	KIND_NUM = 21

	def __init__(self,
		kind: Int,
		id: Int,
		num: Int
	):
		self.kind = kind
		self.id = id
		self.num = num


class KitchenwareData(CompoundObject):
	_OBJECT_ID = 55

	TARGET_SUCCESS = 0
	TARGET_HAPPENING = 1

	def __init__(self,
		type: Int,
		paramMap: IntHashMap,
		recipeNoteId: Int,
		gudetamaId: Int,
		restTimeSecs: Int,
		assistUsefulIds: Object,
		assistEncodedUids: Object,
		target: Int
	):
		self.type = type
		self.paramMap = paramMap
		self.recipeNoteId = recipeNoteId
		self.gudetamaId = gudetamaId
		self.restTimeSecs = restTimeSecs
		self.assistUsefulIds = assistUsefulIds
		self.assistEncodedUids = assistEncodedUids
		self.target = target


class KitchenwareDef(CompoundObject):
	_OBJECT_ID = 54

	TYPE_BOARD = 0
	TYPE_PAN = 1
	TYPE_POT = 2
	TYPE_OVEN = 3
	TYPE_EVENT = 4
	TYPE_NUM = 5
	LAYER_BACK = 0
	LAYER_FRONT = 1

	def __init__(self,
		id: Int,
		rsrc: Int,
		type: Int,
		grade: Int,
		name: String,
		desc: String,
		recipeNoteIds: Object,
		conditionDesc: String,
		existsImage: Boolean,
		bgPos: Object,
		materialLayer: Int,
		eventIds: Object
	):
		self.id = id
		self.rsrc = rsrc
		self.type = type
		self.grade = grade
		self.name = name
		self.desc = desc
		self.recipeNoteIds = recipeNoteIds
		self.conditionDesc = conditionDesc
		self.existsImage = existsImage
		self.bgPos = bgPos
		self.materialLayer = materialLayer
		self.eventIds = eventIds


class KitchenwareInfo(CompoundObject):
	_OBJECT_ID = 57

	def __init__(self,
		unavailableRecipeNoteIds: Object,
		unavailableGudetamaIds: Object
	):
		self.unavailableRecipeNoteIds = unavailableRecipeNoteIds
		self.unavailableGudetamaIds = unavailableGudetamaIds


class KitchenwareParam(CompoundObject):
	_OBJECT_ID = 56

	def __init__(self,
		id: Int,
		available: Boolean
	):
		self.id = id
		self.available = available


class LinearTable(CompoundObject):
	_OBJECT_ID = 32

	def __init__(self,
		offset: Float,
		rate: Float,
		indexOffset: Int,
		indexes: Object,
		values: Object
	):
		self.offset = offset
		self.rate = rate
		self.indexOffset = indexOffset
		self.indexes = indexes
		self.values = values


class LinkageData(CompoundObject):
	_OBJECT_ID = 95

	def __init__(self,
		id: Int,
		code: String,
		notified: Boolean
	):
		self.id = id
		self.code = code
		self.notified = notified


class LinkageDef(CompoundObject):
	_OBJECT_ID = 94

	def __init__(self,
		id: Int,
		rsrc: Int,
		title: String,
		name: String,
		linkTitle: String,
		linkMessage: String,
		linkUrl: Object,
		conditionDesc: String
	):
		self.id = id
		self.rsrc = rsrc
		self.title = title
		self.name = name
		self.linkTitle = linkTitle
		self.linkMessage = linkMessage
		self.linkUrl = linkUrl
		self.conditionDesc = conditionDesc


class MailPresentResult(CompoundObject):
	_OBJECT_ID = 80

	def __init__(self,
		items: Object,
		params: Object
	):
		self.items = items
		self.params = params


class MessageData(CompoundObject):
	TYPE_UNKNOWN = 0
	TYPE_UNKNOWNS = 1
	TYPE_SOMEONE = 2
	TYPE_SOMEPEOPLE = 3
	TYPE_FRIEND = 4
	TYPE_FRIENDS = 5
	TYPE_CHANNEL_MEMBERS = 9
	TYPE_GUILD_MEMBERS = 11
	TYPE_IMPORTANT_SOMEPEOPLE = 15
	TYPE_BROADCAST = 17
	TYPE_IMPORTANT_BROADCAST = 19
	TYPE_HALT_SOMEPEOPLE = 20
	TYPE_HALT_BROADCAST = 21
	TYPE_ALL = 66
	OPERATOR_ID = 0

	def __init__(self,
		messageVersion: Short,
		seq: Object,
		type: Byte,
		bookId: Short,
		groupId: Int,
		receivers: Object,
		receiverNames: Object,
		sender: Int,
		senderName: String,
		uniqueKey: Int,
		message: String,
		receivedSecs: Int
	):
		self.messageVersion = messageVersion
		self.seq = seq
		self.type = type
		self.bookId = bookId
		self.groupId = groupId
		self.receivers = receivers
		self.receiverNames = receiverNames
		self.sender = sender
		self.senderName = senderName
		self.uniqueKey = uniqueKey
		self.message = message
		self.receivedSecs = receivedSecs


class MetalShopDef(CompoundObject):
	_OBJECT_ID = 40

	TYPE_MONEY = 1
	TYPE_METAL = 2
	TYPE_SETITEM = 3

	def __init__(self,
		id: Int,
		name: String,
		items: Object
	):
		self.id = id
		self.name = name
		self.items = items


class MetalShopItemDef(CompoundObject):
	_OBJECT_ID = 41

	TYPE_WIN = 1
	TYPE_IOS = 2
	TYPE_ANDROID = 4
	TYPE_ONESTORE = 8
	TYPE_ALL = 15

	def __init__(self,
		key: Int,
		rsrc: Byte,
		value: Int,
		bonus: Int,
		campaign: Int,
		price: Int,
		product_id: String,
		items: Object,
		limit: Int,
		overlap: Object,
		ranklimit: Int,
		applimit: Int,
		info: Int
	):
		self.key = key
		self.rsrc = rsrc
		self.value = value
		self.bonus = bonus
		self.campaign = campaign
		self.price = price
		self.product_id = product_id
		self.items = items
		self.limit = limit
		self.overlap = overlap
		self.ranklimit = ranklimit
		self.applimit = applimit
		self.info = info


class MissionConstants(CompoundObject):
	_OBJECT_ID = 23

	TYPE_NONE = 0
	TYPE_RANK = 1
	TYPE_VOICE_NUM = 2
	TYPE_VOICE_RARE1_NUM = 4
	TYPE_VOICE_RARE2_NUM = 8
	TYPE_ACCUMULATION = 1
	TYPE_ONETIME = 2
	TYPE_COUNTER = 3
	CONDITION_COOKING_CATEGORY = "CookingCategory"
	CONDITION_CUP_COOK_TARGET = "CupCookTarget"
	CONDITION_GUDETAMA_CATEGORY = "GudetamaCategory"
	CONDITION_GUDETAMA_TARGET = "GudetamaTarget"
	CONDITION_USE_USEFUL_ITEM = "UseUsefulItem"
	TYPE_CONDITION_GUDETAMA_TARGET = 0
	TYPE_CONDITION_RECIPE_TARGET = 1

	def __init__(self,
	):
		pass


class MissionData(CompoundObject):
	_OBJECT_ID = 39

	def __init__(self,
		key: Int,
		param: Object,
		currentValue: Short,
		id: Short
	):
		self.key = key
		self.param = param
		self.currentValue = currentValue
		self.id = id


class MissionDef(CompoundObject):
	_OBJECT_ID = 21

	TYPE_NONE = 0
	TYPE_RANK = 1
	TYPE_VOICE_NUM = 2
	TYPE_VOICE_RARE1_NUM = 4
	TYPE_VOICE_RARE2_NUM = 8
	TYPE_ACCUMULATION = 1
	TYPE_ONETIME = 2
	TYPE_COUNTER = 3
	CONDITION_COOKING_CATEGORY = "CookingCategory"
	CONDITION_CUP_COOK_TARGET = "CupCookTarget"
	CONDITION_GUDETAMA_CATEGORY = "GudetamaCategory"
	CONDITION_GUDETAMA_TARGET = "GudetamaTarget"
	CONDITION_USE_USEFUL_ITEM = "UseUsefulItem"
	TYPE_CONDITION_GUDETAMA_TARGET = 0
	TYPE_CONDITION_RECIPE_TARGET = 1

	def __init__(self,
		id: Short,
		number: Int,
		counterType: Int,
		eventId: Int,
		eventTypeFlags: Int,
		enableCountryFlags: Object
	):
		self.id = id
		self.number = number
		self.counterType = counterType
		self.eventId = eventId
		self.eventTypeFlags = eventTypeFlags
		self.enableCountryFlags = enableCountryFlags


class MissionParam(CompoundObject):
	_OBJECT_ID = 22

	TYPE_NONE = 0
	TYPE_RANK = 1
	TYPE_VOICE_NUM = 2
	TYPE_VOICE_RARE1_NUM = 4
	TYPE_VOICE_RARE2_NUM = 8
	TYPE_ACCUMULATION = 1
	TYPE_ONETIME = 2
	TYPE_COUNTER = 3
	CONDITION_COOKING_CATEGORY = "CookingCategory"
	CONDITION_CUP_COOK_TARGET = "CupCookTarget"
	CONDITION_GUDETAMA_CATEGORY = "GudetamaCategory"
	CONDITION_GUDETAMA_TARGET = "GudetamaTarget"
	CONDITION_USE_USEFUL_ITEM = "UseUsefulItem"
	TYPE_CONDITION_GUDETAMA_TARGET = 0
	TYPE_CONDITION_RECIPE_TARGET = 1

	def __init__(self,
		number: Int,
		type: Byte,
		category: Byte,
		guide: Short,
		goalValue: Short,
		finishSecs: Int,
		targetDescKey: String,
		titleKey: String,
		nextTitleKey: String,
		rewards: Object,
		titleParam: Object,
		counterType: Int
	):
		self.number = number
		self.type = type
		self.category = category
		self.guide = guide
		self.goalValue = goalValue
		self.finishSecs = finishSecs
		self.targetDescKey = targetDescKey
		self.titleKey = titleKey
		self.nextTitleKey = nextTitleKey
		self.rewards = rewards
		self.titleParam = titleParam
		self.counterType = counterType


class MonthlyPremiumBonusDef(CompoundObject):
	_OBJECT_ID = 117

	def __init__(self,
		id: Short,
		validDays: Short,
		item: Object,
		bonusItems: Object
	):
		self.id = id
		self.validDays = validDays
		self.item = item
		self.bonusItems = bonusItems


class NoticeFlagData(CompoundObject):
	_OBJECT_ID = 34

	FLAG_NOTSET = 0
	FLAG_SET = 1
	FLAG_DONE = 2
	PROGRESS_CHECKED_TERMS_OF_SERVICE = 0
	PROGRESS_GENDER_AND_NAME = 1
	PROGRESS_GUDETAMA_GREETING = 2
	PROGRESS_GUDETAMA_INTRODUCTION = 3
	PROGRESS_FIRST_COOKING = 4
	PROGRESS_FIRST_TAPGUIDE = 5
	PROGRESS_FIRST_PUSH = 6
	PROGRESS_MAX = 7
	PROGRESS_FIRST_LOGIN = 3
	PROGRESS_FIRST_STORY = 4
	PROGRESS_FIRST_DECK_EDIT = 5
	PROGRESS_SECOND_STORY = 6
	PROGRESS_FIRST_GACHA_PLAY = 7
	PROGRESS_SECOND_DECK_EDIT = 8
	PROGRESS_THIRD_STORY = 9
	PROGRESS_RANK_UP4 = 10
	PROGRESS_FOURTH_STORY = 11
	NOTICE_SECOND_COOKING = 0
	NOTICE_FIRST_PROFILE = 1
	NOTICE_FIRST_SHOPPING = 2
	NOTICE_FIRST_PICTURE_BOOK = 3
	NOTICE_GOLD_EGG_INTRO = 4
	NOTICE_FRIEND_LIST = 5
	NOTICE_ROOM_DECORATION = 6
	NOTICE_FIRST_ITEM_INFO = 7
	NOTICE_MISSION_ATTENTION = 8
	NOTICE_MISSION_INFO = 9
	NOTICE_MISSION_DAILY_INFO = 10
	NOTICE_FRIEND_DETAIL = 11
	NOTICE_FRIEND_ROOM = 12
	NOTICE_RECIPE_RELEASE = 13
	NOTICE_AR_CAMERA_INTRO = 14
	NOTICE_COOKING_ITEM_INFO = 15
	NOTICE_COOKING_ITEM_ALREADY = 16
	NOTICE_AR_CAMERA_HOME_INDUCTION = 17
	NOTICE_GACHA_INFO = 18
	NOTICE_SNS_ICON = 19
	NOTICE_RARE_VOICE = 20
	NOTICE_MISSION_EVENT_INFO = 21
	NOTICE_MICROWAVE_ATTENTION = 22
	NOTICE_RANKING_EVENT_INFO = 23
	NOTICE_EVENT_KW_INFO = 24
	NOTICE_HIDE_GUDE_GUIDE = 25
	NOTICE_DECO_GUIDE = 26
	NOTICE_CUP_GACHA_GUIDE = 27
	NOTICE_HOME_DECO_GUIDE = 28
	NOTICE_HELPER1_INFO = 29
	NOTICE_SECOND_PICTURE_BOOK = 30
	NOTICE_GUIDE_TALK_BASE_ID = 1000
	BIT_SNS_LINK_BONUS = 1

	def __init__(self,
		noticeFlags: Object,
		tutorialProgress: Int,
		bitFlags: Int
	):
		self.noticeFlags = noticeFlags
		self.tutorialProgress = tutorialProgress
		self.bitFlags = bitFlags


class OnlyShowItemDef(CompoundObject):
	_OBJECT_ID = 128

	def __init__(self,
		id: Int,
		rsrc: Int,
		name: String,
		desc: String
	):
		self.id = id
		self.rsrc = rsrc
		self.name = name
		self.desc = desc


class Packet(CompoundObject):
	_OBJECT_ID = 14

	HEADER_SIZE = 4

	def __init__(self,
		type: Int,
		time: Int,
		payloadInt: Object,
		payloadObj0: Object,
		payloadObj1: Object,
		payloadExtra: Object,
		sequence: Short,
		relogin: Boolean
	):
		self.type = type
		self.time = time
		self.payloadInt = payloadInt
		self.payloadObj0 = payloadObj0
		self.payloadObj1 = payloadObj1
		self.payloadExtra = payloadExtra
		self.sequence = sequence
		self.relogin = relogin


class PossibleRouletteParam(CompoundObject):
	_OBJECT_ID = 62

	def __init__(self,
		type: Byte,
		percent: Int
	):
		self.type = type
		self.percent = percent


class PresentLogData(CompoundObject):
	_OBJECT_ID = 50

	def __init__(self,
		encodedUid: Int,
		playerRank: Int,
		playerName: String,
		avatar: Int,
		itemId: Int,
		itemNum: Int,
		time: Int,
		snsProfileImage: Object,
		snsType: Byte
	):
		self.encodedUid = encodedUid
		self.playerRank = playerRank
		self.playerName = playerName
		self.avatar = avatar
		self.itemId = itemId
		self.itemNum = itemNum
		self.time = time
		self.snsProfileImage = snsProfileImage
		self.snsType = snsType


class PromotionBannerSettingDef(CompoundObject):
	_OBJECT_ID = 120

	def __init__(self,
		id: Int,
		allowCountriyCodes: Object,
		allowCountryLocales: Object,
		bannerID: String,
		visible: Boolean,
		startTimeSecs: Int,
		limitTimeSecs: Int,
		endTimeStr: String,
		browserType: Byte,
		webURL: Object
	):
		self.id = id
		self.allowCountriyCodes = allowCountriyCodes
		self.allowCountryLocales = allowCountryLocales
		self.bannerID = bannerID
		self.visible = visible
		self.startTimeSecs = startTimeSecs
		self.limitTimeSecs = limitTimeSecs
		self.endTimeStr = endTimeStr
		self.browserType = browserType
		self.webURL = webURL


class PromotionInterstitialSettingDef(CompoundObject):
	_OBJECT_ID = 127

	def __init__(self,
		id: Int,
		allowCountriyCodes: Object,
		allowCountryLocales: Object,
		imageIDs: Object,
		visible: Boolean,
		startTimeSecs: Int,
		limitTimeSecs: Int,
		endTimeStr: String,
		browserType: Byte,
		webURL: Object,
		rate: Int,
		intervalSec: Int
	):
		self.id = id
		self.allowCountriyCodes = allowCountriyCodes
		self.allowCountryLocales = allowCountryLocales
		self.imageIDs = imageIDs
		self.visible = visible
		self.startTimeSecs = startTimeSecs
		self.limitTimeSecs = limitTimeSecs
		self.endTimeStr = endTimeStr
		self.browserType = browserType
		self.webURL = webURL
		self.rate = rate
		self.intervalSec = intervalSec


class PromotionVideoDef(CompoundObject):
	_OBJECT_ID = 119

	def __init__(self,
		id: Int,
		movie: Int,
		endcard: Int,
		landscape: Boolean,
		urlApple: String,
		urlGoogle: String,
		link: String,
		locales: Object
	):
		self.id = id
		self.movie = movie
		self.endcard = endcard
		self.landscape = landscape
		self.urlApple = urlApple
		self.urlGoogle = urlGoogle
		self.link = link
		self.locales = locales


class PurchasePresentDef(CompoundObject):
	_OBJECT_ID = 107

	def __init__(self,
		id: Int,
		presents: Object,
		message: String
	):
		self.id = id
		self.presents = presents
		self.message = message


class PurchasePresentItemDef(CompoundObject):
	_OBJECT_ID = 108

	def __init__(self,
		price: Int,
		message: String,
		items: Object
	):
		self.price = price
		self.message = message
		self.items = items


class QnqConstants(CompoundObject):
	_OBJECT_ID = 13

	ID_CHARA_MAX = 99
	ID_MAIN_STORYGROUP = 1
	NUM_QUIZ_OPTIONS = 4
	NUM_QUIZ_TWO_OPTIONS = 2
	NUM_ELIMINATION_QUIZ_OPTIONS = 5
	NUM_NORMAL_QUIZZES = 4
	NUM_QUEST_MEMBERS = 4
	NUM_JOBS = 4
	NUM_JOB_BOOKS = 7
	NUM_STATUS_BOOKS = 3
	MAX_BATTLE_ENEMIES = 3
	NUM_MISSION_REWARD = 3
	QUIZ_RATING_DECIMAL_DIGIT = 1000
	QUIZ_RATING_MAX = 10000000
	QUIZ_RATING_INITIAL = -3000000
	QUIZ_RATING_OFFSET = 3000
	QUIZ_DIFFICULY_UNKNOWN_RATING = 25
	TIME_ATTACK_PRECISION = 10
	TIME_ATTACK_MAX = 90000
	TYPE_ROOM_PUBLIC = 0
	TYPE_ROOM_SPECIFIC_JOB = 1
	TYPE_ROOM_PRIVATE = 2
	TYPE_ROOM_PROHIBIT = 3
	TYPE_ROOM_RENTAL = 4
	TYPE_ROOM_ALL_RENTAL = 5
	TYPE_ROOM_EVENT = 6
	STATE_MEMBER_ACTIVE = 0
	STATE_MEMBER_READY = 1
	STATE_MEMBER_PREPARE = 2
	STATE_MEMBER_SUSPEND = 3
	STATE_MEMBER_DISCONNECTED = 4
	STATE_MEMBER_LOST = 5
	TYPE_PLAYSTYLE_NONE = 0
	TYPE_PLAYSTYLE_LEVEL = 1
	TYPE_PLAYSTYLE_BEGINNER = 2
	TYPE_PLAYSTYLE_EXPERT = 3
	TYPE_PLAYSTYLE_MATERIAL = 4
	TYPE_PLAYSTYLE_RARE = 5
	TYPE_PLAYSTYLE_NUM = 6
	BATTLERESULT_GIVEUP = -1
	BATTLERESULT_DEFEAT = 0
	BATTLERESULT_VICTORY = 1
	CHAT_MAX_TEXTLINES = 10
	QUIZ_GUILDPOINT_DECIMAL_DIGIT = 1000
	QUIZ_GUILDPOINT_MAX = 10000000
	SNS_NONE = -1
	SNS_TWITTER = 0
	SNS_FACEBOOK = 1

	def __init__(self,
	):
		pass


class QnqServletConstants(CompoundObject):
	_OBJECT_ID = 15

	UIID_LENGTH = 36
	PLAYERNAME_LENGTH_MIN = 2
	PLAYERNAME_LENGTH_MAX = 8
	PLAYERCOMMENT_LENGTH_MIN = 2
	PLAYERCOMMENT_LENGTH_MAX = 30
	MESSAGE_LENGTH_MIN = 2
	MESSAGE_LENGTH_MAX = 120
	TAKEOVER_CODE_LENGTH = 9
	SUPPORTOR_PRENSET_MESSAGE_LENGTH_MIN = 2
	SUPPORTOR_PRENSET_MESSAGE_LENGTH_MAX = 15
	GUILDNAME_LENGTH_MIN = 2
	GUILDNAME_LENGTH_MAX = 10
	GUILDCOMMENT_LENGTH_MIN = 2
	GUILDCOMMENT_LENGTH_MAX = 15
	GUILDKEY_LENGTH_MIN = 2
	GUILDKEY_LENGTH_MAX = 10
	TAKEOVER_PASSWORD_LENGTH_MIN = 4
	TAKEOVER_PASSWORD_LENGTH_MAX = 12
	REQUEST_PARAM_DIRECT = "d"
	REQUEST_PARAM_DIRECT_APPPLATFORM = "a"
	REQUEST_PARAM_DIRECT_APPPVERSION = "va"
	REQUEST_PARAM_UIID = "u"
	REQUEST_PARAM_APP_VERSION = "v"
	REQUEST_PARAM_NO_REDIRECT = "n"
	REQUEST_PARAM_APP_PLATFORM = "p"
	REQUEST_PARAM_COMPATIBLE_VERSION = "c"
	REQUEST_PARAM_IDFV = "i"
	REQUEST_PARAM_LOCALE = "l"
	REQUEST_PARAM_SESSION = "s"
	REQUEST_PARAM = "r"
	REQUEST_PARAM_ENCRYPTED = "e"
	REQUEST_PARAM_UID = "ui"
	REQUEST_PARAM_LOG = "log"
	REQUEST_PARAM_TAKEOVER = "t"
	REQUEST_PARAM_TAKEOVER_PLATFROM = "tp"
	REQUEST_PARAM_TAKEOVER_PASSWORD = "pwt"
	REQUEST_PARAM_APP_ONESTORE = "o"
	RESPONSE_PLAIN = 125
	RESPONSE_ENCRYPTED = 78
	RESPONSE_ENCRYPTED_WITH_SEQUENCE = 64
	RESPONSE_ERROR_OTHERS = -1
	RESPONSE_SESSION_CLOSED = -2
	RESPONSE_MAINTENANCE = -3
	RESPONSE_CONGESTION = -4
	RESPONSE_UNAVAILABLE = -5
	RESPONSE_INVALID_REQUEST = -6
	RESPONSE_NOT_ALLOWED = -7
	RESPONSE_REJECT_WITH_MESSAGE = -8
	RESPONSE_DECRYPT_ERROR = -9
	ENTRANCE_RESPONSE_OK = 14
	ENTRANCE_RESPONSE_REDIRECT = 7
	ENTRANCE_RESPONSE_NEED_UPDATE = 11
	TAKEOVER_RESPONSE_SUCCESS = 25
	TAKEOVER_RESPONSE_INVALID_CODE = 21
	TAKEOVER_RESPONSE_CODE_PUBLISHED_SAME_UIID = 34
	TAKEOVER_RESPONSE_UNKNOWN_ERROR = 42
	RESPONSE_EXTRA_RELOAD_SETTING = "reload_setting:"
	RESPONSE_EXTRA_NUM_PRESENTS = "prs:"
	RESPONSE_EXTRA_BANNERIDS = "bannerids:"
	RESPONSE_EXTRA_NUM_FOLLOWERS = "num_followers:"
	RESPONSE_EXTRA_NUM_FOLLOWS = "num_follows:"
	RESPONSE_EXTRA_UPDATED_DAILY_MISSION = "m_ud:"
	RESPONSE_EXTRA_MODIFIED_MISSION = "m_mod:"
	RESPONSE_EXTRA_PRIMAL_MISSION = "m_prm:"
	RESPONSE_EXTRA_INACTIVE_MISSION = "m_deact:"
	RESPONSE_EXTRA_RECENT_MET_DIRTY = "rm_dirty:"
	RESPONSE_EXTRA_MENU_BALLOON = "m_balloon:"
	RESPONSE_EXTRA_NUM_TASTING_QUIZ = "num_quizzes:"
	RESPONSE_EXTRA_CONTRIBUTE_QUIZ_REWARD = "cont_reward:"
	RESPONSE_EXTRA_ASSIST = "assist:"
	RESPONSE_EXTRA_PRESENT_MONEY = "present_money:"
	RESPONSE_EXTRA_ABILITY = "ability:"
	RESPONSE_EXTRA_FEATURE = "feature:"
	RESPONSE_EXTRA_TOUCH = "touch:"
	RESPONSE_EXTRA_TOUCH_UPDATE = "touch_u:"
	RESPONSE_EXTRA_TOUCH_INFO = "touch_info:"
	RESPONSE_EXTRA_KITCHENWARE = "kitchenware:"
	RESPONSE_EXTRA_RECIPE_NOTE = "recipe_note:"
	RESPONSE_EXTRA_GUDETAMA = "gudetama:"
	RESPONSE_EXTRA_AVATAR = "avatar:"
	RESPONSE_EXTRA_DECORATION = "decoration:"
	RESPONSE_EXTRA_STAMP = "stamp:"
	RESPONSE_EXTRA_USEFUL = "useful:"
	RESPONSE_EXTRA_UTENSIL = "utensil:"
	RESPONSE_EXTRA_VIDEO_AD_REWARD = "video_ad_reward:"
	RESPONSE_EXTRA_LINKAGE = "linkage:"
	RESPONSE_EXTRA_NEW_FRIEND = "new_friend:"
	RESPONSE_EXTRA_HIDE_GUDE = "hidegude:"
	RESPONSE_EXTRA_OFFERWALL = "offerwall:"
	RESPONSE_EXTRA_SNS_LINK_BONUS = "slb:"
	RESPONSE_EXTRA_MONTHLY_PREMIUM_BONUS = "monthly:"
	RESPONSE_EXTRA_MENU_ITEMS = "menu:"
	RESPONSE_EXTRA_EVENT = "event:"
	RESPONSE_EXTRA_ID_PRESENT = "id_present:"
	RESPONSE_EXTRA_RANKING_POINT_ADD = "rpadd:"
	RESPONSE_EXTRA_RANKING_POINT_REWARD = "rpreward:"
	RESPONSE_EXTRA_RANKING_GLOBAL_POINT_REWARD = "rgpreward:"
	RESPONSE_EXTRA_TOUCH_COUNT = "touch_count:"
	RESPONSE_EXTRA_SET_ITEM = "set_item:"
	RESPONSE_EXTRA_NOTICE_PREMIUM = "n_pre:"
	RESPONSE_EXTRA_CUP_GACHA = "cgacha:"
	RESPONSE_SET_PLAYERNAME_CORRECT = 0
	RESPONSE_SET_PLAYERNAME_INVALID = 1
	RESPONSE_SET_PLAYERNAME_OVER = 2
	RESPONSE_SET_PLAYERNAME_NOT_ENOUGH = 3
	RESPONSE_SET_PLAYERNAME_BAD = 4
	SEND_EXTRA_TOUCH = "send_touch:"
	SEND_EXTRA_DROP = "send_drop:"
	SEND_EXTRA_HEAVEN = "send_heaven:"
	SEND_EXTRA_SHOW_CSBANNER = "send_show_csbanner:"
	SEND_EXTRA_SHOW_CSBANNER_IDS = "send_show_csbanner_ids:"
	SEND_EXTRA_SHOW_CSINTERSTITIAL = "send_show_csinter:"
	RESPONSE_EXTRA_RATE_BANNER_ADS = "bannerads:"
	RESPONSE_EXTRA_RATE_VIDEO_ADS = "videoads:"
	RESPONSE_EXTRA_RATE_INTER_ADS = "interstitialads:"
	RESPONSE_EXTRA_PRIORITY_VIDEO_ADS = "priorityvideoads:"
	RESPONSE_EXTRA_HELPER = "helper:"
	TAG_GENERAL = 0
	TAG_HOME = 1
	TAG_RANKING = 2
	TAG_SHOP = 3
	TAG_FRIEND = 4
	TAG_OPENING = 6
	TAG_DEBUG = 7
	TAG_COOKING = 8
	TAG_COLLECTION = 9
	TAG_GACHA = 10
	TAG_MISSION = 11
	TAG_PROFILE = 12
	TAG_DECORATION = 13
	TAG_LINKAGE = 14
	TAG_OPTION = 15
	TAG_AR = 16
	TAGMASK_GENERAL = 0
	TAGMASK_HOME = 16777216
	TAGMASK_RANKING = 33554432
	TAGMASK_SHOP = 50331648
	TAGMASK_FRIEND = 67108864
	TAGMASK_OPENING = 100663296
	TAGMASK_DEBUG = 117440512
	TAGMASK_COOKING = 134217728
	TAGMASK_COLLECTION = 150994944
	TAGMASK_GACHA = 167772160
	TAGMASK_MISSION = 184549376
	TAGMASK_PROFILE = 201326592
	TAGMASK_DECORATION = 218103808
	TAGMASK_LINKAGE = 234881024
	TAGMASK_OPTION = 251658240
	TAGMASK_AR = 268435456
	DEBUG_GENERATE_USERDATA = 117441511
	DEBUG_RELOAD_CONF = 117441501
	DEBUG_USER_NAME = 117441498
	DEBUG_PURCHASE = 117441497
	DEBUG_INPUT_MONEY = 117441496
	DEBUG_HIDE_GUDE = 117441495
	DEBUG_NOTICE_RETRY = 117441494
	DEBUG_LOGOUT = 117441493
	DEBUG_UNLOCK_VOICE = 117441492
	DEBUG_UNLOCK_ALL = 117441491
	DEBUG_UNLOCK_MISSION = 117441490
	DEBUG_CHANGE_NOTICE_BIT_FLAG = 117441489
	DEBUG_FREE_GUDETAMA = 117441488
	DEBUG_CHANGE_METAL = 117441487
	DEBUG_FREE_USEFULITEM = 117441486
	DEBUG_COOK_GUDETAMA = 117441485
	DEBUG_RESET_LOGIN_PRESENT_TIME = 117441484
	DEBUG_RESET_CARNAVI = 117441483
	DEBUG_RESET_SHARE_BONUS = 117441482
	DEBUG_RESET_MONTHLY_PREMIUMBONUS = 117441481
	DEBUG_SEND_PRESENT = 117441480
	DEBUG_RESET_DAILY_MISSION = 117441479
	DEBUG_RESET_NEXT_HIDE_GUDE = 117441478
	DEBUG_CHANGE_AREA = 117441477
	DEBUG_RESET_GUDE_PRESENT_REST = 117441476
	DEBUG_RESET_SETITEM_BUYDATA = 117441475
	DEBUG_COOKING_UNLOCK = 117441474
	GENERAL_CUP_GACHA_PLACE = 1
	GENERAL_INIT_AT_LOGIN = 10
	GENERAL_RELOGIN = 11
	GENERAL_PUSH_PACKET = 19
	GENERAL_PURCHASE = 23
	GENERAL_PUSH_TOKEN = 25
	GENERAL_SEND_MESSAGE = 26
	GENERAL_GET_MESSAGES = 27
	GENERAL_REQUEST_TAKEOVER_CODE = 28
	GENERAL_PURCHASE_CHECK = 29
	GENERAL_PUSH_PERMIT = 38
	GENERAL_RANKING_INFO = 51
	GENERAL_PING = 59
	GENERAL_ENTER_HOME = 60
	GENERAL_ENTER_SHOP = 62
	GENERAL_ENTER_FRIEND = 63
	GENERAL_GET_AVAILABLE_SYSTEM_MAILS = 66
	PACKET_GET_NUM_FOLLOWERS = 69
	GENERAL_GET_PRESENT = 72
	GENERAL_GET_PRESENT_BULK = 73
	GENERAL_ENTER_OPENING = 77
	PACKET_GET_ANDROID_PUBLIC_KEY = 114
	GENERAL_APPSFLYER_UID = 119
	GENERAL_CHECK_TAKEOVER_CODE = 124
	GENERAL_REQUEST_FOLLOW = 127
	GENERAL_ENTER_COOKING = 141
	GENERAL_ENTER_COLLECTION = 142
	GENERAL_ENTER_GACHA = 143
	GENERAL_ENTER_MISSION = 144
	GENERAL_ENTER_PROFILE = 145
	GENERAL_ENTER_DECORATION = 146
	GENERAL_ENTER_LINKAGE = 147
	GENERAL_ENTER_OPTION = 148
	GENERAL_ENTER_AR = 149
	GENERAL_ENTER_RANKING = 150
	GENERAL_CHECK_CLEARED_MISSION = 159
	GENERAL_READ_INFORMATION = 160
	GENERAL_FRIEND_REQUEST_FOLLOW = 162
	GENERAL_FRIEND_REMOVE_FOLLOW = 163
	GENERAL_UPDATE_WANTED = 166
	GENERAL_FRIEND_DETAIL = 167
	GENERAL_PRESENT_TO_FRIEND = 168
	FRIEND_PRESENT_WARN_NOT_MUTUAL = -1
	FRIEND_PRESENT_WARN_NOT_WANTED = -2
	FRIEND_PRESENT_MONEY_WARN_ZERO = -3
	GENERAL_USE_USEFUL = 189
	GENERAL_EXTRA = 190
	PACKET_START_TUTORIAL_GUIDE = 202
	PACKET_CHECK_AND_START_TUTORIAL_GUIDE = 203
	PACKET_CHECK_TUTORIAL_GUIDE = 204
	GENERAL_LINK_SNS = 208
	GENERAL_SEARCH_SNS_PROFILE = 209
	PACKET_DONE_NOTICE_GUIDE = 210
	PACKET_SHARED = 217
	PACKET_GET_SHARE_BONUS_PARAM = 218
	GENERAL_GET_WANTED_FRIENDS = 219
	GENERAL_PROFILE_NAME = 220
	GENERAL_PRESENT_TO_FRIEND_AT_FREE = 221
	GENERAL_UNLINK_SNS = 225
	GENERAL_PRESENT_MONEY_TO_FRIEND = 228
	GENERAL_GET_OFFERWALL_REWARD = 229
	PACKET_TRIED_SHARE = 236
	GENERAL_STARTED_VIDEO = 237
	GENERAL_GET_VIDEO_RATE = 238
	GENERAL_TOUCH_BANNER = 239
	GENERAL_IDENTIFIED_PRESENT = 240
	GENERAL_PRESENT_TO_FRIEND_AT_GP = 241
	GENERAL_CHECK_GUDE_PRESENT = 242
	GENERAL_TOUCH_IINTERSTITIAL = 243
	GENERAL_GET_DIALOG_SHARE_BONUS = 247
	GENERAL_SHARED_DIALOG = 248
	GENERAL_CHECK_KITCHENWARE = 249
	GACHA_GET_AVAILABLE_DATA_LIST = 167772315
	GACHA_PLAY = 167772316
	GACHA_PLAY_FREE = 167772317
	GACHA_PLAY_ONCE_MORE = 167772318
	GACHA_PLAY_ENTRY = 167772373
	GACHA_PLAY_STAMP = 167772409
	GACHA_PLAY_WARN_OUT_OF_TERM = -1
	FRIEND_GET_LIST = 67109025
	FRIEND_SEARCH = 67109028
	FRIEND_ENTER_ROOM = 67109033
	FRIEND_ASSIST = 67109034
	FRIEND_ASSIST_WARN_NOT_COOKING = -1
	FRIEND_ASSIST_WARN_COMPLETED = -2
	FRIEND_ASSIST_WARN_EXISTS_USEFUL = -3
	FRIEND_ANSWER_QUESTION = 67109035
	FRIEND_EXTENSION = 67109036
	FRIEND_REMOVE_FOLLOWER_AUTO = 67109037
	PROFILE_INIT = 201326757
	PROFILE_SET_AVATAR = 201326791
	PROFILE_NAME = 201326792
	PROFILE_SET_COMMENT = 201326793
	COOKING_START = 134217909
	COOKING_START_WARN_OUT_OF_TERM = 0
	COOKING_CANCEL = 134217910
	COOKING_CANCEL_WARN_COMPLETED = 0
	COOKING_HURRY_UP = 134217911
	COOKING_HURRY_UP_WARN_COMPLETED = 0
	COOKING_HURRY_UP_WARN_OUT_OF_TERM = 1
	COOKING_COMPLETE = 134217912
	COOKING_ROULETTE = 134217923
	COOKING_USEFUL = 134217924
	COOKING_UNLOCK = 134217925
	COOKING_PURCHASE_RECIPE = 134217926
	COOKING_FINISH = 134217942
	COOKING_RETRY = 134217943
	COOKING_RETRY_FREE = 134217951
	COOKING_REPAIR = 134217952
	COOKING_PLACE = 134217954
	COOKING_ROULETTE_START = 134217963
	COOKING_HURRY_UP_BY_USEFUL = 134217971
	COOKING_HURRY_UP_BY_USUALLY = 134217976
	COOKING_GET_CUP_GACHA_LIST_RECIPE = 134217977
	COLLECTION_PLACE = 150995129
	HOME_CUP_GACHA_COOK = 16777217
	HOME_CUP_GACHA_SHORT = 16777218
	HOME_CUP_GACHA_DRAW = 16777219
	HOME_CUP_GACHA_GUIDE = 16777220
	HOME_DELUSION = 16777402
	HOME_GET_INFO = 16777403
	HOME_LINKAGE_NOTIFY = 16777408
	HOME_USE_CODE = 16777409
	USE_CODE_FAILED_NOTFOUND = -1
	USE_CODE_FAILED_USED = -2
	USE_CODE_FAILED_LIMIT = -3
	USE_CODE_FAILED_ACQUIRED = -4
	HOME_UNLOCK_VOICE = 16777410
	PACKET_GET_GUDETAMA_VOICE_EVENT_TUTORIAL = 16777421
	PACKET_GET_HEAVEN_EVENT_TUTORIAL = 16777422
	PACKET_FINISHED_TUTORIAL_GUIDE = 16777423
	HOME_VIDEO_AD_REWARD = 16777428
	HOME_ASSIST_FROM_FRIEND = 16777446
	HOME_HIDE_GUDE = 16777447
	HOME_GET_HIDE_GUDE_SHARE_BONUS = 16777448
	HOME_HIDE_GUDE_SHARE = 16777450
	HOME_DECORATION_CHANGE = 16777460
	HOME_DECORATION_CHANGE_WARN_OUT_OF_TERM = -1
	GENERATE_HIDE_GUDE_4GUIDE = 16777461
	HOME_DECORATION_STAMP = 16777462
	HOME_DECORATION_EXTENSION_PLACE = 16777463
	HOME_UNLOCK_VOICE_USE_HELPER = 16777464
	HOME_MANUALDELETION_PRESENT = 16777465
	DECORATION_CHANGE = 218103999
	PURCHASE_ITEM = 50331664
	PACKET_SEND_MONEY_4PICTUREBOOK = 50331859
	PACKET_AR_EXTENSION_PLACE = 268435672
	AR_CAPTURE = 268435683
	RANKING_DELIVER = 33554433
	RANKING_DELIVER_ALL = 33554434
	PACKET_CHECKED_TERMS_OF_SERVICE = 100663307
	PACKET_SET_FIRSTLOGIN_INFO = 100663309
	FAIL_OVER_FRIENDS_SELF = -5
	FAIL_OVER_FRIENDS = -4
	FAIL_OVER_FOLLOWERS_SELF = -3
	FAIL_ALREADY_FOLLOW = -2
	FAIL_OVER_FOLLOWERS = -1
	SUCCESS = 0
	SUCCESS_MUTUAL = 1
	FAIL_RANKING_INVALID = -1
	FAIL_RANKING_NOT_FOUND = -2

	def __init__(self,
	):
		pass


class QuestionDef(CompoundObject):
	_OBJECT_ID = 97

	POSITIVE = 0
	NEGATIVE = 1

	def __init__(self,
		id: Int,
		question: String,
		questionVoiceId: Int,
		params: Object
	):
		self.id = id
		self.question = question
		self.questionVoiceId = questionVoiceId
		self.params = params


class QuestionInfo(CompoundObject):
	_OBJECT_ID = 99

	def __init__(self,
		encodedUid: Int,
		avatar: Int,
		friendName: String,
		questionId: Int,
		choiceIndex: Int,
		snsProfileImage: Object,
		snsType: Byte
	):
		self.encodedUid = encodedUid
		self.avatar = avatar
		self.friendName = friendName
		self.questionId = questionId
		self.choiceIndex = choiceIndex
		self.snsProfileImage = snsProfileImage
		self.snsType = snsType


class QuestionParam(CompoundObject):
	_OBJECT_ID = 98

	def __init__(self,
		choice: String,
		message: String,
		messageVoiceId: Int
	):
		self.choice = choice
		self.message = message
		self.messageVoiceId = messageVoiceId


class RankingContentDef(CompoundObject):
	_OBJECT_ID = 43

	def __init__(self,
		type: Int,
		argi: Int,
		rewardId: Int,
		daily: Boolean,
		guild: Boolean,
		deliverTableId: Int,
		deliverPtsPercentMap: IntHashMap
	):
		self.type = type
		self.argi = argi
		self.rewardId = rewardId
		self.daily = daily
		self.guild = guild
		self.deliverTableId = deliverTableId
		self.deliverPtsPercentMap = deliverPtsPercentMap


class RankingDef(CompoundObject):
	_OBJECT_ID = 37

	TYPE_DELIVER = 5
	GROUP_NONE = 0
	GROUP_AREA = 1

	def __init__(self,
		id: Int,
		title: String,
		desc: String,
		storyComicId: Int,
		howtoComicId: Int,
		content: Object,
		groupType: Int,
		groupIdIndexMap: IntHashMap,
		hasDefaultGroupContent: Boolean,
		rankTextColor: Int,
		pointTextColor: Int,
		balloonTextColor: Int,
		rewardTextColor: Int,
		rankingTitleTextColor: Int,
		topRecordMatColor: Int,
		rankingRewardMatColor: Int,
		pointRewardMatColor: Int,
		levelRewardMatColor: Int,
		topRecordBgMatColor: Int,
		rankingRewardBgMatColor: Int,
		pointRewardBgMatColor: Int,
		levelRewardBgMatColor: Int,
		recordMatColor: Int,
		rankingRewardLineColor: Int,
		pointRewardLineColor: Int,
		levelRewardLineColor: Int
	):
		self.id = id
		self.title = title
		self.desc = desc
		self.storyComicId = storyComicId
		self.howtoComicId = howtoComicId
		self.content = content
		self.groupType = groupType
		self.groupIdIndexMap = groupIdIndexMap
		self.hasDefaultGroupContent = hasDefaultGroupContent
		self.rankTextColor = rankTextColor
		self.pointTextColor = pointTextColor
		self.balloonTextColor = balloonTextColor
		self.rewardTextColor = rewardTextColor
		self.rankingTitleTextColor = rankingTitleTextColor
		self.topRecordMatColor = topRecordMatColor
		self.rankingRewardMatColor = rankingRewardMatColor
		self.pointRewardMatColor = pointRewardMatColor
		self.levelRewardMatColor = levelRewardMatColor
		self.topRecordBgMatColor = topRecordBgMatColor
		self.rankingRewardBgMatColor = rankingRewardBgMatColor
		self.pointRewardBgMatColor = pointRewardBgMatColor
		self.levelRewardBgMatColor = levelRewardBgMatColor
		self.recordMatColor = recordMatColor
		self.rankingRewardLineColor = rankingRewardLineColor
		self.pointRewardLineColor = pointRewardLineColor
		self.levelRewardLineColor = levelRewardLineColor


class RankingInfo(CompoundObject):
	_OBJECT_ID = 38

	def __init__(self,
		contentIndex: Int,
		type: Int,
		contentTitle: String,
		argi: Int,
		showOnly: Boolean,
		guild: Boolean,
		desc: String,
		myPoint: Int,
		myRoughPlace: Int,
		topRecords: Object,
		rewardId: Int,
		rewardPlaceAndPoint: Object,
		topRecordSizeMax: Int,
		totalPoint: Int
	):
		self.contentIndex = contentIndex
		self.type = type
		self.contentTitle = contentTitle
		self.argi = argi
		self.showOnly = showOnly
		self.guild = guild
		self.desc = desc
		self.myPoint = myPoint
		self.myRoughPlace = myRoughPlace
		self.topRecords = topRecords
		self.rewardId = rewardId
		self.rewardPlaceAndPoint = rewardPlaceAndPoint
		self.topRecordSizeMax = topRecordSizeMax
		self.totalPoint = totalPoint


class RankingRecord(CompoundObject):
	_OBJECT_ID = 36

	def __init__(self,
		point: Int,
		encodeUid: Int,
		playerName: String,
		avatar: Int,
		snsType: Int,
		snsProfileImage: Object
	):
		self.point = point
		self.encodeUid = encodeUid
		self.playerName = playerName
		self.avatar = avatar
		self.snsType = snsType
		self.snsProfileImage = snsProfileImage


class RankingRewardDef(CompoundObject):
	_OBJECT_ID = 44

	def __init__(self,
		id: Int,
		rewardIdTable: Object,
		rankingRewards: Object,
		pointRewards: Object,
		globalRewards: Object
	):
		self.id = id
		self.rewardIdTable = rewardIdTable
		self.rankingRewards = rankingRewards
		self.pointRewards = pointRewards
		self.globalRewards = globalRewards


class RankingRewardItemDef(CompoundObject):
	_OBJECT_ID = 45

	def __init__(self,
		sortedIndex: Int,
		last: Boolean,
		argi: Int,
		screeningItems: Object
	):
		self.sortedIndex = sortedIndex
		self.last = last
		self.argi = argi
		self.screeningItems = screeningItems


class RecipeNoteData(CompoundObject):
	_OBJECT_ID = 59

	def __init__(self,
		id: Int,
		visible: Boolean,
		available: Boolean,
		purchased: Boolean,
		targetValue: Int,
		currentValue: Int
	):
		self.id = id
		self.visible = visible
		self.available = available
		self.purchased = purchased
		self.targetValue = targetValue
		self.currentValue = currentValue


class RecipeNoteDef(CompoundObject):
	_OBJECT_ID = 58

	def __init__(self,
		id: Int,
		rsrc: Int,
		kitchenwareId: Int,
		name: String,
		desc: String,
		minutes: Int,
		premises: Object,
		conditionDesc: String,
		eventId: Int,
		price: Int,
		defaults: Object,
		appends: Object,
		happeningIds: Object,
		failureIds: Object,
		hasBonusPrize: Boolean,
		targetType: Int,
		targetId: Int
	):
		self.id = id
		self.rsrc = rsrc
		self.kitchenwareId = kitchenwareId
		self.name = name
		self.desc = desc
		self.minutes = minutes
		self.premises = premises
		self.conditionDesc = conditionDesc
		self.eventId = eventId
		self.price = price
		self.defaults = defaults
		self.appends = appends
		self.happeningIds = happeningIds
		self.failureIds = failureIds
		self.hasBonusPrize = hasBonusPrize
		self.targetType = targetType
		self.targetId = targetId


class RefreshCacheDef(CompoundObject):
	def __init__(self,
		id: Int,
		ability: Object,
		battleitem: Object,
		boost: Object,
		effect: Object,
		emo: Object,
		field: Object,
		gacha: Object,
		image: Object,
		music: Object,
		other: Object,
		planet: Object,
		stage: Object,
		test: Object,
		ui: Object,
		upgrade: Object,
		voice: Object,
		robo: Object,
		dialog: Object
	):
		self.id = id
		self.ability = ability
		self.battleitem = battleitem
		self.boost = boost
		self.effect = effect
		self.emo = emo
		self.field = field
		self.gacha = gacha
		self.image = image
		self.music = music
		self.other = other
		self.planet = planet
		self.stage = stage
		self.test = test
		self.ui = ui
		self.upgrade = upgrade
		self.voice = voice
		self.robo = robo
		self.dialog = dialog


class RuleDef(CompoundObject):
	_OBJECT_ID = 20

	GACHA_RATE_SCREENING_NONE = 0
	GACHA_RATE_SCREENING_KIND = 1
	GACHA_RATE_SCREENING_ALL = 2
	TYPE_SHARE_BONUS_AFTER = 0
	TYPE_SHARE_BONUS_BEFORE = 1

	def __init__(self,
		focusGainedLimitTimeMinites: Byte,
		reloadFollowerTime: Int,
		ruleFlags: Object,
		roundingFollowPastDay: Byte,
		locale: String,
		localeCode: Object,
		titleMusic: Int,
		heavenTimeSecs: Int,
		touchRewards: Object,
		carnaviIds: Object,
		enabledMoneyShop: Boolean,
		menuItems: Object,
		shopItems: Object,
		collectionTypes: Object,
		hurryUpReduceMinutesPerMetal: Int,
		hurryUpMetalBase: Int,
		cookingTooMatchTimeHours: Int,
		lowerLimitPercentForRouletteSpeed: Int,
		hurryUpItemBaseMap: IntHashMap,
		hurryUpReduceMinutesPerItem: IntHashMap,
		gachaRateScreeningLevel: Int,
		missionCommentAchievePercent: Object,
		maxFriendsExtension: Short,
		friendsExtensionValue: Short,
		friendsExtensionPrices: Object,
		updateFollowerTime: Int,
		maximumFriendPresentForGPWhileEvent: Int,
		friendlyValueByAssist: Int,
		gudetamaTeamIds: Object,
		minimumMessageTime: Int,
		messagePercents: Object,
		messageResetHourOffset: Int,
		friendPresentCost: Int,
		friendPresentGp: Int,
		friendPresentGpCountPerDay: Int,
		friendPresentGpGlobalCountPerDay: Int,
		freeFriendPresentCountPerDay: Int,
		placeArGudetamaNumTable: Object,
		placeArStampNumTable: Object,
		placeHomeStampNumTable: Object,
		numScreeningPresentLogs: Int,
		maxFriendPresentMoneyPerRank: Int,
		maxAssistPerDay: Int,
		defStampSpainPath: String,
		imobileAndroidPlacement: Object,
		imobileIOSPlacement: Object,
		fiveAdsAndroidId: String,
		fiveAdsIOSId: String,
		fiveAdsAndroidSlotId: Object,
		fiveAdsIOSSlotId: Object,
		nendAdsAndroidIds: Object,
		nendAdsIOSIds: Object,
		eventBannerUpdateTime: Int,
		bannerCircleSec: Int,
		bannerCircle: Boolean,
		disableBannerOSVersionMap: HashMap,
		maioAdsAndroidId: String,
		maioAdsIOSId: String,
		maioAdsZoneAndroidId: String,
		maioAdsZoneIOSId: String,
		videoTraceErrorSec: Int,
		tapjoyAdsAndroidId: Object,
		tapjoyAdsIOSId: Object,
		vangleAdsAndroidId: String,
		vangleAdsIOSId: String,
		vangleAdsAndroidPlacementIds: Object,
		vangleAdsIOSPlacementIds: Object,
		ironsourceAdsAndroidId: String,
		ironsourceAdsIOSId: String,
		ironSourceGlobalAdsAndroidId: String,
		ironSourceGlobalAdsIOSId: String,
		admobBannerAndroidId: String,
		admobBannerIOSId: String,
		admobVideoAndroidId: String,
		admobVideoIOSId: String,
		nendAndroidIds: Object,
		nendIOSIds: Object,
		chartboosVideoAndroidIds: Object,
		chartboosVideoIOSIds: Object,
		promotionVideoNames: Object,
		promotionVideoIdAndRatio: Object,
		priorityMaxVideoCount: Int,
		preLoadingVideoSecs: Int,
		videoLodingIntervalMillisec: Int,
		videoGlobalLodingIntervalMillisec: Int,
		videoInitGiveupMilliSec: Int,
		imobileInterstitialAndroidPlacement: Object,
		imobileInterstitialIOSPlacement: Object,
		nendInterstitialAndroid: Object,
		nendInterstitialIOS: Object,
		interstitiaIntervalSecs: Int,
		interstitiaIntervalGlobalSecs: Int,
		ironVideoPlacementAndroidId: Object,
		ironVideoPlacementIOSId: Object,
		ironOfferPlacementAndroidId: Object,
		ironOfferPlacementIOSId: Object,
		ironInterPlacementAndroidId: Object,
		ironInterPlacementIOSId: Object,
		twitter_Key: String,
		twitter_Secret: String,
		facebook_Key: String,
		useSnsTwitter: Boolean,
		useSnsFacebook: Boolean,
		tiwtterSchemeAndroidURL: String,
		tiwtterSchemeIOSURL: String,
		snsLinkBonusNum: Byte,
		usefulShopShortcut: Boolean,
		presentDeliverPtsPercent: Int,
		snsShareBonusType: Int,
		cupGachaOpenMinPerTier: Int,
		cupGachaOpenMetalPerTier: Int,
		cupGachaShortMinByAd: Byte,
		cupGachaShortNumByAd: Byte,
		cupGachaMailKeepDay: Short,
		useHomeDecoEachType: Boolean,
		cookingShortCut: Boolean,
		memoryCookingRecipe: Boolean,
		frameIds: Object,
		titleName: String,
		titleSpineName: String,
		titleGudetamaSpineName: String,
		duplicateSceneCheckClasses: Object,
		titleNameCountry: HashMap,
		titleSpineNameCountry: HashMap,
		titleGudetamaSpineNameCountry: HashMap
	):
		self.focusGainedLimitTimeMinites = focusGainedLimitTimeMinites
		self.reloadFollowerTime = reloadFollowerTime
		self.ruleFlags = ruleFlags
		self.roundingFollowPastDay = roundingFollowPastDay
		self.locale = locale
		self.localeCode = localeCode
		self.titleMusic = titleMusic
		self.heavenTimeSecs = heavenTimeSecs
		self.touchRewards = touchRewards
		self.carnaviIds = carnaviIds
		self.enabledMoneyShop = enabledMoneyShop
		self.menuItems = menuItems
		self.shopItems = shopItems
		self.collectionTypes = collectionTypes
		self.hurryUpReduceMinutesPerMetal = hurryUpReduceMinutesPerMetal
		self.hurryUpMetalBase = hurryUpMetalBase
		self.cookingTooMatchTimeHours = cookingTooMatchTimeHours
		self.lowerLimitPercentForRouletteSpeed = lowerLimitPercentForRouletteSpeed
		self.hurryUpItemBaseMap = hurryUpItemBaseMap
		self.hurryUpReduceMinutesPerItem = hurryUpReduceMinutesPerItem
		self.gachaRateScreeningLevel = gachaRateScreeningLevel
		self.missionCommentAchievePercent = missionCommentAchievePercent
		self.maxFriendsExtension = maxFriendsExtension
		self.friendsExtensionValue = friendsExtensionValue
		self.friendsExtensionPrices = friendsExtensionPrices
		self.updateFollowerTime = updateFollowerTime
		self.maximumFriendPresentForGPWhileEvent = maximumFriendPresentForGPWhileEvent
		self.friendlyValueByAssist = friendlyValueByAssist
		self.gudetamaTeamIds = gudetamaTeamIds
		self.minimumMessageTime = minimumMessageTime
		self.messagePercents = messagePercents
		self.messageResetHourOffset = messageResetHourOffset
		self.friendPresentCost = friendPresentCost
		self.friendPresentGp = friendPresentGp
		self.friendPresentGpCountPerDay = friendPresentGpCountPerDay
		self.friendPresentGpGlobalCountPerDay = friendPresentGpGlobalCountPerDay
		self.freeFriendPresentCountPerDay = freeFriendPresentCountPerDay
		self.placeArGudetamaNumTable = placeArGudetamaNumTable
		self.placeArStampNumTable = placeArStampNumTable
		self.placeHomeStampNumTable = placeHomeStampNumTable
		self.numScreeningPresentLogs = numScreeningPresentLogs
		self.maxFriendPresentMoneyPerRank = maxFriendPresentMoneyPerRank
		self.maxAssistPerDay = maxAssistPerDay
		self.defStampSpainPath = defStampSpainPath
		self.imobileAndroidPlacement = imobileAndroidPlacement
		self.imobileIOSPlacement = imobileIOSPlacement
		self.fiveAdsAndroidId = fiveAdsAndroidId
		self.fiveAdsIOSId = fiveAdsIOSId
		self.fiveAdsAndroidSlotId = fiveAdsAndroidSlotId
		self.fiveAdsIOSSlotId = fiveAdsIOSSlotId
		self.nendAdsAndroidIds = nendAdsAndroidIds
		self.nendAdsIOSIds = nendAdsIOSIds
		self.eventBannerUpdateTime = eventBannerUpdateTime
		self.bannerCircleSec = bannerCircleSec
		self.bannerCircle = bannerCircle
		self.disableBannerOSVersionMap = disableBannerOSVersionMap
		self.maioAdsAndroidId = maioAdsAndroidId
		self.maioAdsIOSId = maioAdsIOSId
		self.maioAdsZoneAndroidId = maioAdsZoneAndroidId
		self.maioAdsZoneIOSId = maioAdsZoneIOSId
		self.videoTraceErrorSec = videoTraceErrorSec
		self.tapjoyAdsAndroidId = tapjoyAdsAndroidId
		self.tapjoyAdsIOSId = tapjoyAdsIOSId
		self.vangleAdsAndroidId = vangleAdsAndroidId
		self.vangleAdsIOSId = vangleAdsIOSId
		self.vangleAdsAndroidPlacementIds = vangleAdsAndroidPlacementIds
		self.vangleAdsIOSPlacementIds = vangleAdsIOSPlacementIds
		self.ironsourceAdsAndroidId = ironsourceAdsAndroidId
		self.ironsourceAdsIOSId = ironsourceAdsIOSId
		self.ironSourceGlobalAdsAndroidId = ironSourceGlobalAdsAndroidId
		self.ironSourceGlobalAdsIOSId = ironSourceGlobalAdsIOSId
		self.admobBannerAndroidId = admobBannerAndroidId
		self.admobBannerIOSId = admobBannerIOSId
		self.admobVideoAndroidId = admobVideoAndroidId
		self.admobVideoIOSId = admobVideoIOSId
		self.nendAndroidIds = nendAndroidIds
		self.nendIOSIds = nendIOSIds
		self.chartboosVideoAndroidIds = chartboosVideoAndroidIds
		self.chartboosVideoIOSIds = chartboosVideoIOSIds
		self.promotionVideoNames = promotionVideoNames
		self.promotionVideoIdAndRatio = promotionVideoIdAndRatio
		self.priorityMaxVideoCount = priorityMaxVideoCount
		self.preLoadingVideoSecs = preLoadingVideoSecs
		self.videoLodingIntervalMillisec = videoLodingIntervalMillisec
		self.videoGlobalLodingIntervalMillisec = videoGlobalLodingIntervalMillisec
		self.videoInitGiveupMilliSec = videoInitGiveupMilliSec
		self.imobileInterstitialAndroidPlacement = imobileInterstitialAndroidPlacement
		self.imobileInterstitialIOSPlacement = imobileInterstitialIOSPlacement
		self.nendInterstitialAndroid = nendInterstitialAndroid
		self.nendInterstitialIOS = nendInterstitialIOS
		self.interstitiaIntervalSecs = interstitiaIntervalSecs
		self.interstitiaIntervalGlobalSecs = interstitiaIntervalGlobalSecs
		self.ironVideoPlacementAndroidId = ironVideoPlacementAndroidId
		self.ironVideoPlacementIOSId = ironVideoPlacementIOSId
		self.ironOfferPlacementAndroidId = ironOfferPlacementAndroidId
		self.ironOfferPlacementIOSId = ironOfferPlacementIOSId
		self.ironInterPlacementAndroidId = ironInterPlacementAndroidId
		self.ironInterPlacementIOSId = ironInterPlacementIOSId
		self.twitter_Key = twitter_Key
		self.twitter_Secret = twitter_Secret
		self.facebook_Key = facebook_Key
		self.useSnsTwitter = useSnsTwitter
		self.useSnsFacebook = useSnsFacebook
		self.tiwtterSchemeAndroidURL = tiwtterSchemeAndroidURL
		self.tiwtterSchemeIOSURL = tiwtterSchemeIOSURL
		self.snsLinkBonusNum = snsLinkBonusNum
		self.usefulShopShortcut = usefulShopShortcut
		self.presentDeliverPtsPercent = presentDeliverPtsPercent
		self.snsShareBonusType = snsShareBonusType
		self.cupGachaOpenMinPerTier = cupGachaOpenMinPerTier
		self.cupGachaOpenMetalPerTier = cupGachaOpenMetalPerTier
		self.cupGachaShortMinByAd = cupGachaShortMinByAd
		self.cupGachaShortNumByAd = cupGachaShortNumByAd
		self.cupGachaMailKeepDay = cupGachaMailKeepDay
		self.useHomeDecoEachType = useHomeDecoEachType
		self.cookingShortCut = cookingShortCut
		self.memoryCookingRecipe = memoryCookingRecipe
		self.frameIds = frameIds
		self.titleName = titleName
		self.titleSpineName = titleSpineName
		self.titleGudetamaSpineName = titleGudetamaSpineName
		self.duplicateSceneCheckClasses = duplicateSceneCheckClasses
		self.titleNameCountry = titleNameCountry
		self.titleSpineNameCountry = titleSpineNameCountry
		self.titleGudetamaSpineNameCountry = titleGudetamaSpineNameCountry


class ScreeningDef(CompoundObject):
	_OBJECT_ID = 17

	FLAG_TEXTURE_TRACE_ENABLED = 0
	FLAG_FOR_APPLE_REVIEW = 1
	FLAG_DECORATION_ENABLED = 2
	FLAG_CANCEL_LOADING_DISABLED = 3
	FLAG_CHECK_OS_PUSH = 4
	FLAG_CHECK_INIT_BANNER = 5
	FLAG_FIRST_PART_DL = 6
	FLAG_NOTICE_PREMIUM = 7
	FLAG_PRESENT_WITHOUT_TERM = 8
	FLAG_CONVERT_GACHA_ITEM = 9
	FLAG_COLLECT_GACHA_TICKET = 10
	FLAG_DISABLE_SELECT_LOCALE = 11
	FLAG_CUP_GACHA_ENABLE = 12
	FLAG_CUP_GACHA_RATE_ENABLE = 13
	FLAG_HOMEDECO_ENABLE = 14
	FLAG_HOMEHELPER_ENABLE = 15

	def __init__(self,
		flags: Object
	):
		self.flags = flags


class ScreeningGachaItemParam(CompoundObject):
	_OBJECT_ID = 70

	def __init__(self,
		item: Object,
		newFlag: Boolean,
		pickupFlag: Boolean,
		rate: Int
	):
		self.item = item
		self.newFlag = newFlag
		self.pickupFlag = pickupFlag
		self.rate = rate


class SequenceTable(CompoundObject):
	_OBJECT_ID = 31

	def __init__(self,
		offset: Float,
		rate: Float,
		indexOffset: Int,
		values: Object
	):
		self.offset = offset
		self.rate = rate
		self.indexOffset = indexOffset
		self.values = values


class SetItemAlternativeParam(CompoundObject):
	_OBJECT_ID = 130

	def __init__(self,
		rsrc: Int,
		items: Object
	):
		self.rsrc = rsrc
		self.items = items


class SetItemBuyData(CompoundObject):
	_OBJECT_ID = 125

	def __init__(self,
		count: Short
	):
		self.count = count


class SetItemDef(CompoundObject):
	_OBJECT_ID = 124

	VIEW_NONE = 0
	VIEW_SHOP_USEFUL = 1

	def __init__(self,
		id: Int,
		viewType: Byte,
		items: Object,
		startTimeSec: Int,
		endTimeSec: Int,
		chargeItem: Object,
		buyableCount: Short,
		rsrc: Int,
		alternativeParam: Object
	):
		self.id = id
		self.viewType = viewType
		self.items = items
		self.startTimeSec = startTimeSec
		self.endTimeSec = endTimeSec
		self.chargeItem = chargeItem
		self.buyableCount = buyableCount
		self.rsrc = rsrc
		self.alternativeParam = alternativeParam


class ShareBonusDef(CompoundObject):
	_OBJECT_ID = 129

	def __init__(self,
		id: Int,
		item: Object,
		message: String,
		alternativeMessage: String
	):
		self.id = id
		self.item = item
		self.message = message
		self.alternativeMessage = alternativeMessage


class StaminaData(CompoundObject):
	STAMINA_MAX = 9999

	def __init__(self,
		currentValue: Short,
		maxChargeableValue: Short,
		nextChargeTimeRest: Int
	):
		self.currentValue = currentValue
		self.maxChargeableValue = maxChargeableValue
		self.nextChargeTimeRest = nextChargeTimeRest


class StampData(CompoundObject):
	_OBJECT_ID = 101

	STAMP_MAX = 99999

	def __init__(self,
		id: Int,
		num: Int,
		available: Boolean
	):
		self.id = id
		self.num = num
		self.available = available


class StampDef(CompoundObject):
	_OBJECT_ID = 78

	RARE_NONE = 0
	RARE_AUTO = 1
	RARE_MANUAL = 2

	def __init__(self,
		id: Int,
		rsrc: Int,
		privately: Boolean,
		name: String,
		desc: String,
		conditionDesc: String,
		price: Object,
		isNew: Boolean,
		rare: Int,
		isSpine: Boolean,
		homeStampSettingId: Int
	):
		self.id = id
		self.rsrc = rsrc
		self.privately = privately
		self.name = name
		self.desc = desc
		self.conditionDesc = conditionDesc
		self.price = price
		self.isNew = isNew
		self.rare = rare
		self.isSpine = isSpine
		self.homeStampSettingId = homeStampSettingId


class StampInfo(CompoundObject):
	_OBJECT_ID = 102

	def __init__(self,
		updateStamps: Object,
		removeStampIds: Object
	):
		self.updateStamps = updateStamps
		self.removeStampIds = removeStampIds


class SubHomeStampSettingDef(CompoundObject):
	_OBJECT_ID = 137

	def __init__(self,
		animationName: String,
		loop: Boolean,
		music: String,
		sound: String,
		voiceId: Int
	):
		self.animationName = animationName
		self.loop = loop
		self.music = music
		self.sound = sound
		self.voiceId = voiceId


class SystemMailData(CompoundObject):
	_OBJECT_ID = 35

	TYPE_PRESENT = 0
	TYPE_INFO = 1
	TYPE_PRESENT_TO_FRIEND = 2
	TYPE_DIALOG_MESSAGE = 10
	TYPE_DIALOG_WITH_PRESENT = 11
	TYPE_DIALOG_WITH_INFO = 12
	TYPE_DIALOG_SYSTEMINFO = 13
	TYPE_CHAT_OP_MESSAGE = 14
	TYPE_CHAT_OP_GUILD_MESSAGE = 15
	TYPE_DIALOG_BILLING_INFO = 16
	KIND_INFO = 0
	KIND_UPDATE = 1
	KIND_MAINTENANCE = 2
	KIND_BUG = 3
	MSG_PREFIX_USER_PRESENT = "#UP"
	MAIL_KEEP_NOLIMIT = -1
	MAIL_KEEP_DEFAULT = 0

	def __init__(self,
		type: Byte,
		kind: Byte,
		senderEncodedUid: Int,
		item: Object,
		title: String,
		url: String,
		urlAndroid: String,
		alreadyRead: Boolean,
		noticeIconId: Int,
		deleteSec: Int,
		manualDeletion: Boolean,
		uniqueKey: Int,
		message: String,
		receivedSecs: Int
	):
		self.type = type
		self.kind = kind
		self.senderEncodedUid = senderEncodedUid
		self.item = item
		self.title = title
		self.url = url
		self.urlAndroid = urlAndroid
		self.alreadyRead = alreadyRead
		self.noticeIconId = noticeIconId
		self.deleteSec = deleteSec
		self.manualDeletion = manualDeletion
		self.uniqueKey = uniqueKey
		self.message = message
		self.receivedSecs = receivedSecs


class TouchDef(CompoundObject):
	_OBJECT_ID = 113

	def __init__(self,
		voiceEvents: Object,
		itemEvents: Object,
		randomVoiceIds: Object
	):
		self.voiceEvents = voiceEvents
		self.itemEvents = itemEvents
		self.randomVoiceIds = randomVoiceIds


class TouchEventDef(CompoundObject):
	_OBJECT_ID = 85

	TAGMASK_NONE = 0
	TAGMASK_VOICE = 256
	TAGMASK_ITEM0 = 512
	TAGMASK_ITEM1 = 1024
	TAGMASK_HEAVEN = 2048
	EVENT_GUDETAMA = 0
	EVENT_VOICE = 257
	EVENT_REMOTE = 770
	EVENT_PHONE = 771
	EVENT_SAUCE = 772
	EVENT_SOY_SAUCE = 773
	EVENT_SOY_SAUCE_FISH = 1286
	EVENT_SOY_SAUCE_FISH_GOLD = 1287
	EVENT_HEAVEN = 2312
	VOICE_RANDOM = 0
	VOICE_GUDETAMA_0 = -1
	VOICE_GUDETAMA_1 = -2

	def __init__(self,
		voice: Int
	):
		self.voice = voice


class TouchEventParam(CompoundObject):
	_OBJECT_ID = 89

	def __init__(self,
		touchNum: Int,
		event: Int,
		voice: Int,
		paramByte: Byte
	):
		self.touchNum = touchNum
		self.event = event
		self.voice = voice
		self.paramByte = paramByte


class TouchInfo(CompoundObject):
	_OBJECT_ID = 88

	def __init__(self,
		params: Object,
		bonusRange: Object
	):
		self.params = params
		self.bonusRange = bonusRange


class UsefulData(CompoundObject):
	_OBJECT_ID = 72

	USEFUL_MAX = 99999

	def __init__(self,
		id: Int,
		num: Int,
		available: Boolean,
		nextAvailablePurchaseSec: Int
	):
		self.id = id
		self.num = num
		self.available = available
		self.nextAvailablePurchaseSec = nextAvailablePurchaseSec


class UsefulDef(CompoundObject):
	_OBJECT_ID = 71

	USABLE_HOME = 1
	USABLE_COOKING = 2
	USABLE_HURRY = 4

	def __init__(self,
		id: Int,
		rsrc: Int,
		privately: Boolean,
		name: String,
		desc: String,
		usable: Int,
		event: Boolean,
		abilities: Object,
		assistAbilities: Object,
		friendlyValue: Int,
		conditionDesc: String,
		sortIndex: Int,
		price: Object,
		isNew: Boolean,
		eventId: Int,
		kitchenwareTypes: Object,
		possessionLimit: Int,
		purchaseResetHourOffset: Byte
	):
		self.id = id
		self.rsrc = rsrc
		self.privately = privately
		self.name = name
		self.desc = desc
		self.usable = usable
		self.event = event
		self.abilities = abilities
		self.assistAbilities = assistAbilities
		self.friendlyValue = friendlyValue
		self.conditionDesc = conditionDesc
		self.sortIndex = sortIndex
		self.price = price
		self.isNew = isNew
		self.eventId = eventId
		self.kitchenwareTypes = kitchenwareTypes
		self.possessionLimit = possessionLimit
		self.purchaseResetHourOffset = purchaseResetHourOffset


class UsefulInfo(CompoundObject):
	_OBJECT_ID = 104

	def __init__(self,
		updateUsefuls: Object,
		removeUsefulIds: Object
	):
		self.updateUsefuls = updateUsefuls
		self.removeUsefulIds = removeUsefulIds


class UserAbilityData(CompoundObject):
	_OBJECT_ID = 91

	def __init__(self,
		ability: Object,
		restTimeSecs: Int
	):
		self.ability = ability
		self.restTimeSecs = restTimeSecs


class UserAssistData(CompoundObject):
	_OBJECT_ID = 84

	def __init__(self,
		num: Int
	):
		self.num = num


class UserData(CompoundObject):
	_OBJECT_ID = 33

	METAL_MAX = 999999999
	METAL_EXCHANGE_RATE = 100
	MONEY_MAX = 999999999
	MAX_KEEP_PRESENT_SECS = 2592000
	DEFAULT_MAX_FRIENDS = 10

	def __init__(self,
		uid: Int,
		encodedUid: Int,
		playerName: String,
		gender: Int,
		doneFirstLogin: Boolean,
		pushFlags: Int,
		nextDailyPresentTime: Double,
		timeZoneOffset: Int,
		noticeFlagData: Object,
		locale: String,
		rank: Int,
		chargeMetal: Int,
		freeMetal: Int,
		subMetal: Int,
		chargeMoney: Int,
		freeMoney: Int,
		avatar: Int,
		avatarMap: IntHashMap,
		area: Int,
		comment: Short,
		placedGudetamaId: Int,
		kitchenwareMap: IntHashMap,
		recipeNoteMap: IntHashMap,
		gudetamaMap: IntHashMap,
		gachaMap: IntHashMap,
		friendPresentMoneyParamMap: IntHashMap,
		stampMap: IntHashMap,
		usefulMap: IntHashMap,
		utensilMap: IntHashMap,
		decorationMap: IntHashMap,
		decorationId: Int,
		wantedGudetamas: Object,
		maxDelusion: Int,
		delusionStartTimeSecs: Int,
		touchInfo: Object,
		dropItemEvent: Object,
		heavenEvent: Object,
		userAbilities: Object,
		features: Object,
		numAcquiredVideoAdReward: Int,
		videoAdRewardUpdateTimeSecs: Int,
		linkageMap: IntHashMap,
		numPurchaseMap: IntHashMap,
		numFriendsExtension: Int,
		snsInterlockType: Byte,
		snsTwitterUid: String,
		snsFacebookUid: String,
		purchasePresentMap: IntHashMap,
		placeGudetamaExpansionCount: Short,
		placeStampExpansionCount: Short,
		commentList: ArrayList,
		finishMonthlyPremiumBonusTimeSec: Int,
		noticeMonthlyPremiumBonusTimeSec: Int,
		sendTouchCount: Int,
		numAcquiredIdentifiedPresentMap: IntHashMap,
		setItemBuyMap: IntHashMap,
		numFriendPresentForGPWhileEventMap: IntHashMap,
		cupGachaData: Object,
		cupGachaConditionClearIds: ArrayList,
		homeDecoDataMap: IntHashMap,
		placeHomeStampExpansionCount: Short
	):
		self.uid = uid
		self.encodedUid = encodedUid
		self.playerName = playerName
		self.gender = gender
		self.doneFirstLogin = doneFirstLogin
		self.pushFlags = pushFlags
		self.nextDailyPresentTime = nextDailyPresentTime
		self.timeZoneOffset = timeZoneOffset
		self.noticeFlagData = noticeFlagData
		self.locale = locale
		self.rank = rank
		self.chargeMetal = chargeMetal
		self.freeMetal = freeMetal
		self.subMetal = subMetal
		self.chargeMoney = chargeMoney
		self.freeMoney = freeMoney
		self.avatar = avatar
		self.avatarMap = avatarMap
		self.area = area
		self.comment = comment
		self.placedGudetamaId = placedGudetamaId
		self.kitchenwareMap = kitchenwareMap
		self.recipeNoteMap = recipeNoteMap
		self.gudetamaMap = gudetamaMap
		self.gachaMap = gachaMap
		self.friendPresentMoneyParamMap = friendPresentMoneyParamMap
		self.stampMap = stampMap
		self.usefulMap = usefulMap
		self.utensilMap = utensilMap
		self.decorationMap = decorationMap
		self.decorationId = decorationId
		self.wantedGudetamas = wantedGudetamas
		self.maxDelusion = maxDelusion
		self.delusionStartTimeSecs = delusionStartTimeSecs
		self.touchInfo = touchInfo
		self.dropItemEvent = dropItemEvent
		self.heavenEvent = heavenEvent
		self.userAbilities = userAbilities
		self.features = features
		self.numAcquiredVideoAdReward = numAcquiredVideoAdReward
		self.videoAdRewardUpdateTimeSecs = videoAdRewardUpdateTimeSecs
		self.linkageMap = linkageMap
		self.numPurchaseMap = numPurchaseMap
		self.numFriendsExtension = numFriendsExtension
		self.snsInterlockType = snsInterlockType
		self.snsTwitterUid = snsTwitterUid
		self.snsFacebookUid = snsFacebookUid
		self.purchasePresentMap = purchasePresentMap
		self.placeGudetamaExpansionCount = placeGudetamaExpansionCount
		self.placeStampExpansionCount = placeStampExpansionCount
		self.commentList = commentList
		self.finishMonthlyPremiumBonusTimeSec = finishMonthlyPremiumBonusTimeSec
		self.noticeMonthlyPremiumBonusTimeSec = noticeMonthlyPremiumBonusTimeSec
		self.sendTouchCount = sendTouchCount
		self.numAcquiredIdentifiedPresentMap = numAcquiredIdentifiedPresentMap
		self.setItemBuyMap = setItemBuyMap
		self.numFriendPresentForGPWhileEventMap = numFriendPresentForGPWhileEventMap
		self.cupGachaData = cupGachaData
		self.cupGachaConditionClearIds = cupGachaConditionClearIds
		self.homeDecoDataMap = homeDecoDataMap
		self.placeHomeStampExpansionCount = placeHomeStampExpansionCount


class UserGachaData(CompoundObject):
	_OBJECT_ID = 67

	def __init__(self,
		id: Int,
		playCount: Int,
		prices: Object,
		onceMorePlayCount: Byte,
		freePlayCount: Byte
	):
		self.id = id
		self.playCount = playCount
		self.prices = prices
		self.onceMorePlayCount = onceMorePlayCount
		self.freePlayCount = freePlayCount


class UserGachaPriceData(CompoundObject):
	_OBJECT_ID = 68

	def __init__(self,
		dailyPlayCount: Int
	):
		self.dailyPlayCount = dailyPlayCount


class UserPresentMoneyData(CompoundObject):
	_OBJECT_ID = 83

	def __init__(self,
		pid: Double,
		encodedUid: Int,
		playerName: String,
		playerRank: Int,
		money: Int,
		presentTimeSecs: Int,
		avatar: Int,
		snsProfileImage: Object,
		snsType: Byte
	):
		self.pid = pid
		self.encodedUid = encodedUid
		self.playerName = playerName
		self.playerRank = playerRank
		self.money = money
		self.presentTimeSecs = presentTimeSecs
		self.avatar = avatar
		self.snsProfileImage = snsProfileImage
		self.snsType = snsType


class UserProfileData(CompoundObject):
	_OBJECT_ID = 48

	FOLLOWSTATE_NONE = 0
	FOLLOWSTATE_FOLLOW = 1
	FOLLOWSTATE_FOLLOWER = 2
	FOLLOWSTATE_FOLLOW_MUTUAL = 3

	def __init__(self,
		encodedUid: Int,
		playerName: String,
		playerRank: Int,
		avatar: Int,
		gender: Int,
		area: Int,
		comment: Int,
		followState: Byte,
		followRequestSecs: Int,
		snsProfileImage: Object,
		lastActiveSec: Int,
		snsId: String,
		snsType: Byte
	):
		self.encodedUid = encodedUid
		self.playerName = playerName
		self.playerRank = playerRank
		self.avatar = avatar
		self.gender = gender
		self.area = area
		self.comment = comment
		self.followState = followState
		self.followRequestSecs = followRequestSecs
		self.snsProfileImage = snsProfileImage
		self.lastActiveSec = lastActiveSec
		self.snsId = snsId
		self.snsType = snsType


class UserRankingData(CompoundObject):
	_OBJECT_ID = 46

	def __init__(self,
		rankingPoint: Int
	):
		self.rankingPoint = rankingPoint


class UserRoomInfo(CompoundObject):
	_OBJECT_ID = 81

	def __init__(self,
		placedGudetamaId: Int,
		questionId: Int,
		kitchenwareMap: IntHashMap,
		friendlyData: Object,
		lastFriendlyLevel: Int,
		friendPresentMoneyParam: Object,
		assistData: Object,
		decorationId: Int,
		homeDecoDataList: ArrayList
	):
		self.placedGudetamaId = placedGudetamaId
		self.questionId = questionId
		self.kitchenwareMap = kitchenwareMap
		self.friendlyData = friendlyData
		self.lastFriendlyLevel = lastFriendlyLevel
		self.friendPresentMoneyParam = friendPresentMoneyParam
		self.assistData = assistData
		self.decorationId = decorationId
		self.homeDecoDataList = homeDecoDataList


class UserWantedData(CompoundObject):
	_OBJECT_ID = 49

	def __init__(self,
		id: Int,
		updateTime: Int
	):
		self.id = id
		self.updateTime = updateTime


class UtensilData(CompoundObject):
	_OBJECT_ID = 77

	def __init__(self,
		id: Int,
		acquired: Boolean,
		available: Boolean
	):
		self.id = id
		self.acquired = acquired
		self.available = available


class UtensilDef(CompoundObject):
	_OBJECT_ID = 76

	UTENSIL_PICTURE_BOOK = 1
	UTENSIL_TIMING_PLATE = 3
	UTENSIL_MICROWAVE = 4

	def __init__(self,
		id: Int,
		rsrc: Int,
		name: String,
		desc: String,
		conditionDesc: String,
		price: Object,
		isNew: Boolean
	):
		self.id = id
		self.rsrc = rsrc
		self.name = name
		self.desc = desc
		self.conditionDesc = conditionDesc
		self.price = price
		self.isNew = isNew


class UtensilInfo(CompoundObject):
	_OBJECT_ID = 105

	def __init__(self,
		updateUtensils: Object,
		removeUtensilIds: Object
	):
		self.updateUtensils = updateUtensils
		self.removeUtensilIds = removeUtensilIds


class VideoAdRewardDef(CompoundObject):
	_OBJECT_ID = 106

	def __init__(self,
		items: Object
	):
		self.items = items


class VoiceDef(CompoundObject):
	_OBJECT_ID = 63

	TYPE_PRIVATELY = 0
	TYPE_NUMBERING = 1
	TYPE_EVENT = 2
	POS_RIGHT = 0
	POS_LEFT = 1

	def __init__(self,
		id: Int,
		rsrc: Int,
		gudetamaId: Int,
		type: Byte,
		number: Int,
		name: String,
		position: Int,
		offset: Object,
		params: Object
	):
		self.id = id
		self.rsrc = rsrc
		self.gudetamaId = gudetamaId
		self.type = type
		self.number = number
		self.name = name
		self.position = position
		self.offset = offset
		self.params = params


class VoiceParam(CompoundObject):
	_OBJECT_ID = 122

	def __init__(self,
		resources: Object,
		names: Object,
		delays: Object,
		positions: Object,
		offsets: Object
	):
		self.resources = resources
		self.names = names
		self.delays = delays
		self.positions = positions
		self.offsets = offsets


class _AbilityParam(CompoundObject):
	UNIQUE_BITFLAG = -2147483648
	MOST_POWERFUL_BITFLAG = 1073741824
	LOW_POWER_STRENGTH_BITFLAG = 536870912
	TYPE_CORRECT_HP_HEAL = 0
	TYPE_CORRECT_CRITICAL_ATTACK = 1
	TYPE_CORRECT_SP_BONUS = 2
	TYPE_REDUCE_OPTION = 3
	TYPE_DIED_ENDURE_HP1 = 4
	TYPE_DAMAED_AVOIDANCE = 5
	TYPE_STATUS_SKILL_CT_DOWN = 6
	TYPE_STATUS_SKILL_POWER_UP = -2147483641
	TYPE_STATUS_SKILL_CHARGED = -2147483640
	TYPE_CORRECT_REVIVE_COUNTUP = 9
	TYPE_STATUS_MONEY_BONUS = 10
	TYPE_STATUS_MORIBUND_ATK_UP = 11
	TYPE_CORRECT_MORIBUND_CRITICAL = 12
	TYPE_CORRECT_CHAIN_SP_BONUS = 1610612749
	TYPE_COLLABO_GENRE_DESIGNATION = 14
	TYPE_RANKING_POINT_UP = 15
	TYPE_BASE_SKILL_LEVEL_UP = -2147483632
	JOB_TYPE = [1,0,3,3,2,2,3,0,3,1,3,0,0,1,3,3,0]
	RATIOS = [1,0.5,0.4,0.3,0.2,0.1,0.05]

	def __init__(self,
		type: Int,
		name: String,
		desc: String,
		genre: Int,
		difficulty: Int,
		grade: Byte,
		power: Int,
		startTimeSecs: Int,
		endTimeSecs: Int
	):
		self.type = type
		self.name = name
		self.desc = desc
		self.genre = genre
		self.difficulty = difficulty
		self.grade = grade
		self.power = power
		self.startTimeSecs = startTimeSecs
		self.endTimeSecs = endTimeSecs


class _UserProfileData(CompoundObject):
	FOLLOWSTATE_NONE = 0
	FOLLOWSTATE_FOLLOW = 1
	FOLLOWSTATE_FOLLOWER = 2
	FOLLOWSTATE_FOLLOW_MUTUAL = 3
	CANCEL_FOLLOW = 4
	REJECT_FOLLOWER = 5

	def __init__(self,
		encodedUid: Int,
		playerName: String,
		job: Int,
		comment: String,
		lastPlaySecs: Int,
		followRequestSecs: Int,
		leaderBookId: Int,
		deckBookIds: Object,
		leaderBookLevel: Short,
		highestRatingGenreIndex: Int,
		followState: Byte,
		playerRanks: Object,
		numPenddings: Short,
		deckLevel: Short,
		deckHp: Short,
		deckAtk: Short,
		deckDef: Short,
		deckMnd: Short,
		guildID: Int,
		guildPosition: Int,
		guildDropoutSecs: Int,
		guildPoint: Int,
		guildName: String,
		guildIconInfo: Int,
		gender: Int,
		quizRating: Int,
		friendBoardDisclosure: Byte,
		accumulatedQPoint: Int,
		monthlyQPoint: Int
	):
		self.encodedUid = encodedUid
		self.playerName = playerName
		self.job = job
		self.comment = comment
		self.lastPlaySecs = lastPlaySecs
		self.followRequestSecs = followRequestSecs
		self.leaderBookId = leaderBookId
		self.deckBookIds = deckBookIds
		self.leaderBookLevel = leaderBookLevel
		self.highestRatingGenreIndex = highestRatingGenreIndex
		self.followState = followState
		self.playerRanks = playerRanks
		self.numPenddings = numPenddings
		self.deckLevel = deckLevel
		self.deckHp = deckHp
		self.deckAtk = deckAtk
		self.deckDef = deckDef
		self.deckMnd = deckMnd
		self.guildID = guildID
		self.guildPosition = guildPosition
		self.guildDropoutSecs = guildDropoutSecs
		self.guildPoint = guildPoint
		self.guildName = guildName
		self.guildIconInfo = guildIconInfo
		self.gender = gender
		self.quizRating = quizRating
		self.friendBoardDisclosure = friendBoardDisclosure
		self.accumulatedQPoint = accumulatedQPoint
		self.monthlyQPoint = monthlyQPoint


scan_subclasses()
