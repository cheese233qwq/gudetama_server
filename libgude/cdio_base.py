from io import BytesIO
import struct

def p16(buf, n, signed=False):
	buf.write(n.to_bytes(2, "big", signed=signed))

def p32(buf, n, signed=False):
	buf.write(n.to_bytes(4, "big", signed=signed))

def pfloat(buf, f):
	buf.write(struct.pack(">f", f))

def pdouble(buf, d):
	buf.write(struct.pack(">d", d))

def u16(buf, signed=False):
	data = buf.read(2)
	if len(data) != 2:
		raise Exception("Expected 2 bytes to unpack from")
	return int.from_bytes(data, "big", signed=signed)

def u32(buf, signed=False):
	data = buf.read(4)
	if len(data) != 4:
		raise Exception("Expected 4 bytes to unpack from")
	return int.from_bytes(data, "big", signed=signed)

def ufloat(buf):
	return struct.unpack(">f", buf.read(4))[0]

def udouble(buf):
	return struct.unpack(">d", buf.read(8))[0]


class Object():
	def __init__(self, value):
		if issubclass(value.__class__, Object):
			self.value = value
		elif type(value) is str:
			self.value = String(value)
		elif type(value) is bytes or type(value) is bytearray:
			self.value = ByteArray(value)
		elif value is None:
			self.value = Null()
		else:
			raise Exception(f"I don't know how to objectify this yet: {value!r}")

	@classmethod
	def parse(cls, data):
		buf = BytesIO(data)
		return cls.parse_from(buf)

	@classmethod
	def parse_from(cls, buf):
		obj_type = u16(buf)
		if obj_type not in id_to_class:
			raise Exception(f"Unknown object type: {obj_type}")
		cls_inner = id_to_class[obj_type]
		return cls(cls_inner.parse_from(buf))

	def serialised(self):
		buf = BytesIO()
		self.serialise_into(buf)
		return buf.getvalue()

	def serialise_into(self, buf):
		p16(buf, self.value._OBJECT_ID)
		self.value.serialise_into(buf)

	def __repr__(self):
		return f"{self.__class__.__name__}({self.value!r})"

	def to_source(self):
		return _generate_source(self)

	# passthru
	def __int__(self):
		return int(self.value)

	def __float__(self):
		return float(self.value)

	def __iter__(self):
		return iter(self.value)


class Boolean(Object):
	def __init__(self, value):
		self.value = bool(value)

	@classmethod
	def parse_from(cls, buf):
		return cls(buf.read(1)[0])

	def serialise_into(self, buf):
		buf.write(bytes([int(self.value)]))

class Byte(Object):
	def __init__(self, value):
		self.value = int(value)

	@classmethod
	def parse_from(cls, buf):
		return cls(buf.read(1)[0])

	def serialise_into(self, buf):
		buf.write(bytes([self.value]))

class Float(Object):
	def __init__(self, value):
		self.value = float(value)

	@classmethod
	def parse_from(cls, buf):
		return cls(ufloat(buf))

	def serialise_into(self, buf):
		pfloat(buf, self.value)

class Double(Object):
	def __init__(self, value):
		self.value = float(value)

	@classmethod
	def parse_from(cls, buf):
		return cls(udouble(buf))

	def serialise_into(self, buf):
		pdouble(buf, self.value)

class Null(Object):
	_OBJECT_ID = 0

	def __init__(self):
		self.value = None

	@classmethod
	def parse_from(cls, buf):
		buf.read(0)  # nop
		return cls()

	def serialise_into(self, buf):
		buf.write(b"")  # nop

	def __repr__(self):
		return "Null()"


# TODO: use this to see if obj might be iterable
class ArrayObject(Object):
	def __init__(self):
		raise Exception("ArrayObject cannot be instantiated directly (maybe you want ObjArray?)")


class MapObject(Object):
	def __init__(self):
		raise Exception("MapObject cannot be instantiated directly")


class ObjArray(ArrayObject):
	_OBJECT_ID = 1

	def __init__(self, value):
		self.value = list(value) # TODO: check are objects

	@classmethod
	def parse_from(cls, buf):
		array_len = u16(buf)
		values = []
		for _ in range(array_len):
			values.append(Object.parse_from(buf).value)
		return cls(values)

	def serialise_into(self, buf):
		p16(buf, len(self.value))
		for v in self.value:
			Object(v).serialise_into(buf)


class IntArray(ArrayObject):
	_OBJECT_ID = 2

	def __init__(self, value):
		self.value = [int(v) for v in value] # TODO: range checks?

	@classmethod
	def parse_from(cls, buf):
		array_len = u16(buf)
		values = []
		for _ in range(array_len):
			values.append(u32(buf, signed=True))
		return cls(values)

	def serialise_into(self, buf):
		p16(buf, len(self.value))
		for v in self.value:
			p32(buf, int(v), signed=True)


class ShortArray(ArrayObject):
	_OBJECT_ID = 3

	def __init__(self, value):
		self.value = [int(v) for v in value] # TODO: range checks?

	@classmethod
	def parse_from(cls, buf):
		array_len = u16(buf)
		values = []
		for _ in range(array_len):
			values.append(u16(buf, signed=True))
		return cls(values)

	def serialise_into(self, buf):
		p16(buf, len(self.value))
		for v in self.value:
			p16(buf, int(v), signed=True)


class ByteArray(Object):
	_OBJECT_ID = 4

	def __init__(self, value):
		self.value = bytes(value)

	@classmethod
	def parse_from(cls, buf):
		array_len = u32(buf)
		value = buf.read(array_len)
		if len(value) != array_len:
			raise Exception("Not enough data")
		return cls(value)

	def serialise_into(self, buf):
		p32(buf, len(self.value))
		buf.write(self.value)


class FloatArray(ArrayObject):
	_OBJECT_ID = 5

	def __init__(self, value):
		self.value = [float(v) for v in value]

	@classmethod
	def parse_from(cls, buf):
		array_len = u16(buf)
		values = []
		for _ in range(array_len):
			values.append(ufloat(buf))
		return cls(values)

	def serialise_into(self, buf):
		p16(buf, len(self.value))
		for v in self.value:
			pfloat(buf, float(v))


class String(Object):
	_OBJECT_ID = 6

	def __init__(self, value):
		self.value = str(value)

	@classmethod
	def parse_from(cls, buf):
		str_len = u16(buf)
		value = buf.read(str_len)
		if len(value) != str_len:
			raise Exception("Not enough data")
		return cls(value.decode())

	def serialise_into(self, buf):
		encoded = self.value.encode()
		p16(buf, len(encoded))
		buf.write(encoded)


class IntHashMap(MapObject):
	_OBJECT_ID = 7

	def __init__(self, value):
		self.value = dict(value)

	@classmethod
	def parse_from(cls, buf):
		value = {}
		for _ in range(u16(buf)):
			intkey = Int.parse_from(buf).value
			value[intkey] = Object.parse_from(buf).value
		return cls(value)

	def serialise_into(self, buf):
		p16(buf, len(self.value))
		for k, v in self.value.items():
			p32(buf, k)
			Object(v).serialise_into(buf)


class HashMap(MapObject):
	_OBJECT_ID = 8

	def __init__(self, value):
		self.value = dict(value)

	@classmethod
	def parse_from(cls, buf):
		value = {}
		for _ in range(u16(buf)):
			strkey = String.parse_from(buf).value
			value[strkey] = Object.parse_from(buf).value
		return cls(value)

	def serialise_into(self, buf):
		p16(buf, len(self.value))
		for k, v in self.value.items():
			String(k).serialise_into(buf)
			Object(v).serialise_into(buf)


# functionally equivalent to ObjArray
class ArrayList(ObjArray):
	_OBJECT_ID = 9


class Int(Object):
	_OBJECT_ID = 10

	def __init__(self, value):
		self.value = int(value)  # TODO: range check?

	@classmethod
	def parse_from(cls, buf):
		return cls(u32(buf, signed=True))

	def serialise_into(self, buf):
		p32(buf, self.value, signed=True)


class Short(Object):
	_OBJECT_ID = 11

	def __init__(self, value):
		self.value = int(value)  # TODO: range check?

	@classmethod
	def parse_from(cls, buf):
		return cls(u16(buf, signed=True))

	def serialise_into(self, buf):
		p16(buf, self.value, signed=True)


# https://stackoverflow.com/a/17246726
def get_all_subclasses(cls):
	all_subclasses = []

	for subclass in cls.__subclasses__():
		all_subclasses.append(subclass)
		all_subclasses.extend(get_all_subclasses(subclass))

	return all_subclasses


"""
Wow this is some really neat code.

Creating a subclass with a type-annotated constructor allows it to
be serialised and parsed automagically.

Isn't that cool?!?!
"""
class CompoundObject(Object):
	def __init__(self):
		raise Exception("CompoundObject cannot be instantiated directly")

	@classmethod
	def parse_from(cls, buf):
		kwargs = {}
		for field, objtype in cls.__init__.__annotations__.items():
			kwargs[field] = objtype.parse_from(buf).value
		return cls(**kwargs)
	
	def serialise_into(self, buf):
		for field, objtype in self.__init__.__annotations__.items():
			objtype(getattr(self, field)).serialise_into(buf)

	def __repr__(self):
		parts = []
		for field in self.__init__.__annotations__.keys():
			parts.append(field + "=" + repr(getattr(self, field)))
		return f"{self.__class__.__name__}({', '.join(parts)})"

"""
This is *not* neat code, but it's still useful.
It transforms any object into valid python source which, if executed,
results in the exact same object.

TODO: maybe move to inside Object()?
"""
def _generate_source(object, level=0, parent=None):
	indent = "\t" * (level+1)
	sep = ",\n" + indent
	if type(object) is String:
		return repr(object.value)
	if type(object) is ByteArray:
		return repr(object.value)
	if type(object) is Null:
		return "None"
	if issubclass(object.__class__, CompoundObject):
		parts = []
		for field in object.__init__.__annotations__.keys():
			val = getattr(object, field)
			valstr = _stringify_const(object, field, val) or _generate_source(val, level + 1)
			parts.append(field + "=" + valstr)
		return f"{object.__class__.__name__}(\n{indent}{sep.join(parts)})"
	if issubclass(object.__class__, Object):
		if issubclass(object.__class__, ArrayObject):
			level -= 1
		if issubclass(object.__class__, MapObject):
			level -= 1
		if type(object) is Object:
			level -= 1
		val = _generate_source(object.value, level + 1, parent=parent)
		return f"{object.__class__.__name__}({val})"
	if type(object) is list:
		if not object:
			return "[]"
		return "[\n" + indent + sep.join([
			_generate_source(x, level+1)
			for x in object
		]) + "]"
	if type(object) is dict:
		if not object:
			return "{}"
		parts = []
		for k, v in object.items():
			val = _generate_source(v, level+1)
			parts.append(_generate_source(k) + ": " + val)
		return "{\n" + indent + sep.join(parts) + "}"
	
	return repr(object)

# dirty hack to help stringify the packet type field
packet_ids = {
	0x00000001: "GENERAL_CUP_GACHA_PLACE",
	0x0000000a: "GENERAL_INIT_AT_LOGIN",
	0x0000000b: "GENERAL_RELOGIN",
	0x00000013: "GENERAL_PUSH_PACKET",
	0x00000017: "GENERAL_PURCHASE",
	0x00000019: "GENERAL_PUSH_TOKEN",
	0x0000001a: "GENERAL_SEND_MESSAGE",
	0x0000001b: "GENERAL_GET_MESSAGES",
	0x0000001c: "GENERAL_REQUEST_TAKEOVER_CODE",
	0x0000001d: "GENERAL_PURCHASE_CHECK",
	0x00000026: "GENERAL_PUSH_PERMIT",
	0x00000033: "GENERAL_RANKING_INFO",
	0x0000003b: "GENERAL_PING",
	0x0000003c: "GENERAL_ENTER_HOME",
	0x0000003e: "GENERAL_ENTER_SHOP",
	0x0000003f: "GENERAL_ENTER_FRIEND",
	0x00000042: "GENERAL_GET_AVAILABLE_SYSTEM_MAILS",
	0x00000045: "PACKET_GET_NUM_FOLLOWERS",
	0x00000048: "GENERAL_GET_PRESENT",
	0x00000049: "GENERAL_GET_PRESENT_BULK",
	0x0000004d: "GENERAL_ENTER_OPENING",
	0x00000072: "PACKET_GET_ANDROID_PUBLIC_KEY",
	0x00000077: "GENERAL_APPSFLYER_UID",
	0x0000007c: "GENERAL_CHECK_TAKEOVER_CODE",
	0x0000007f: "GENERAL_REQUEST_FOLLOW",
	0x0000008d: "GENERAL_ENTER_COOKING",
	0x0000008e: "GENERAL_ENTER_COLLECTION",
	0x0000008f: "GENERAL_ENTER_GACHA",
	0x00000090: "GENERAL_ENTER_MISSION",
	0x00000091: "GENERAL_ENTER_PROFILE",
	0x00000092: "GENERAL_ENTER_DECORATION",
	0x00000093: "GENERAL_ENTER_LINKAGE",
	0x00000094: "GENERAL_ENTER_OPTION",
	0x00000095: "GENERAL_ENTER_AR",
	0x00000096: "GENERAL_ENTER_RANKING",
	0x0000009f: "GENERAL_CHECK_CLEARED_MISSION",
	0x000000a0: "GENERAL_READ_INFORMATION",
	0x000000a2: "GENERAL_FRIEND_REQUEST_FOLLOW",
	0x000000a3: "GENERAL_FRIEND_REMOVE_FOLLOW",
	0x000000a6: "GENERAL_UPDATE_WANTED",
	0x000000a7: "GENERAL_FRIEND_DETAIL",
	0x000000a8: "GENERAL_PRESENT_TO_FRIEND",
	0x000000bd: "GENERAL_USE_USEFUL",
	0x000000be: "GENERAL_EXTRA",
	0x000000ca: "PACKET_START_TUTORIAL_GUIDE",
	0x000000cb: "PACKET_CHECK_AND_START_TUTORIAL_GUIDE",
	0x000000cc: "PACKET_CHECK_TUTORIAL_GUIDE",
	0x000000d0: "GENERAL_LINK_SNS",
	0x000000d1: "GENERAL_SEARCH_SNS_PROFILE",
	0x000000d2: "PACKET_DONE_NOTICE_GUIDE",
	0x000000d9: "PACKET_SHARED",
	0x000000da: "PACKET_GET_SHARE_BONUS_PARAM",
	0x000000db: "GENERAL_GET_WANTED_FRIENDS",
	0x000000dc: "GENERAL_PROFILE_NAME",
	0x000000dd: "GENERAL_PRESENT_TO_FRIEND_AT_FREE",
	0x000000e1: "GENERAL_UNLINK_SNS",
	0x000000e4: "GENERAL_PRESENT_MONEY_TO_FRIEND",
	0x000000e5: "GENERAL_GET_OFFERWALL_REWARD",
	0x000000ec: "PACKET_TRIED_SHARE",
	0x000000ed: "GENERAL_STARTED_VIDEO",
	0x000000ee: "GENERAL_GET_VIDEO_RATE",
	0x000000ef: "GENERAL_TOUCH_BANNER",
	0x000000f0: "GENERAL_IDENTIFIED_PRESENT",
	0x000000f1: "GENERAL_PRESENT_TO_FRIEND_AT_GP",
	0x000000f2: "GENERAL_CHECK_GUDE_PRESENT",
	0x000000f3: "GENERAL_TOUCH_IINTERSTITIAL",
	0x000000f7: "GENERAL_GET_DIALOG_SHARE_BONUS",
	0x000000f8: "GENERAL_SHARED_DIALOG",
	0x000000f9: "GENERAL_CHECK_KITCHENWARE",
	0x01000001: "HOME_CUP_GACHA_COOK",
	0x01000002: "HOME_CUP_GACHA_SHORT",
	0x01000003: "HOME_CUP_GACHA_DRAW",
	0x01000004: "HOME_CUP_GACHA_GUIDE",
	0x010000ba: "HOME_DELUSION",
	0x010000bb: "HOME_GET_INFO",
	0x010000c0: "HOME_LINKAGE_NOTIFY",
	0x010000c1: "HOME_USE_CODE",
	0x010000c2: "HOME_UNLOCK_VOICE",
	0x010000cd: "PACKET_GET_GUDETAMA_VOICE_EVENT_TUTORIAL",
	0x010000ce: "PACKET_GET_HEAVEN_EVENT_TUTORIAL",
	0x010000cf: "PACKET_FINISHED_TUTORIAL_GUIDE",
	0x010000d4: "HOME_VIDEO_AD_REWARD",
	0x010000e6: "HOME_ASSIST_FROM_FRIEND",
	0x010000e7: "HOME_HIDE_GUDE",
	0x010000e8: "HOME_GET_HIDE_GUDE_SHARE_BONUS",
	0x010000ea: "HOME_HIDE_GUDE_SHARE",
	0x010000f4: "HOME_DECORATION_CHANGE",
	0x010000f5: "GENERATE_HIDE_GUDE_4GUIDE",
	0x010000f6: "HOME_DECORATION_STAMP",
	0x010000f7: "HOME_DECORATION_EXTENSION_PLACE",
	0x010000f8: "HOME_UNLOCK_VOICE_USE_HELPER",
	0x010000f9: "HOME_MANUALDELETION_PRESENT",
	0x02000001: "RANKING_DELIVER",
	0x02000002: "RANKING_DELIVER_ALL",
	0x03000010: "PURCHASE_ITEM",
	0x030000d3: "PACKET_SEND_MONEY_4PICTUREBOOK",
	0x040000a1: "FRIEND_GET_LIST",
	0x040000a4: "FRIEND_SEARCH",
	0x040000a9: "FRIEND_ENTER_ROOM",
	0x040000aa: "FRIEND_ASSIST",
	0x040000ab: "FRIEND_ANSWER_QUESTION",
	0x040000ac: "FRIEND_EXTENSION",
	0x040000ad: "FRIEND_REMOVE_FOLLOWER_AUTO",
	0x0600000b: "PACKET_CHECKED_TERMS_OF_SERVICE",
	0x0600000d: "PACKET_SET_FIRSTLOGIN_INFO",
	0x070003c2: "DEBUG_COOKING_UNLOCK",
	0x070003c3: "DEBUG_RESET_SETITEM_BUYDATA",
	0x070003c4: "DEBUG_RESET_GUDE_PRESENT_REST",
	0x070003c5: "DEBUG_CHANGE_AREA",
	0x070003c6: "DEBUG_RESET_NEXT_HIDE_GUDE",
	0x070003c7: "DEBUG_RESET_DAILY_MISSION",
	0x070003c8: "DEBUG_SEND_PRESENT",
	0x070003c9: "DEBUG_RESET_MONTHLY_PREMIUMBONUS",
	0x070003ca: "DEBUG_RESET_SHARE_BONUS",
	0x070003cb: "DEBUG_RESET_CARNAVI",
	0x070003cc: "DEBUG_RESET_LOGIN_PRESENT_TIME",
	0x070003cd: "DEBUG_COOK_GUDETAMA",
	0x070003ce: "DEBUG_FREE_USEFULITEM",
	0x070003cf: "DEBUG_CHANGE_METAL",
	0x070003d0: "DEBUG_FREE_GUDETAMA",
	0x070003d1: "DEBUG_CHANGE_NOTICE_BIT_FLAG",
	0x070003d2: "DEBUG_UNLOCK_MISSION",
	0x070003d3: "DEBUG_UNLOCK_ALL",
	0x070003d4: "DEBUG_UNLOCK_VOICE",
	0x070003d5: "DEBUG_LOGOUT",
	0x070003d6: "DEBUG_NOTICE_RETRY",
	0x070003d7: "DEBUG_HIDE_GUDE",
	0x070003d8: "DEBUG_INPUT_MONEY",
	0x070003d9: "DEBUG_PURCHASE",
	0x070003da: "DEBUG_USER_NAME",
	0x070003dd: "DEBUG_RELOAD_CONF",
	0x070003e7: "DEBUG_GENERATE_USERDATA",
	0x080000b5: "COOKING_START",
	0x080000b6: "COOKING_CANCEL",
	0x080000b7: "COOKING_HURRY_UP",
	0x080000b8: "COOKING_COMPLETE",
	0x080000c3: "COOKING_ROULETTE",
	0x080000c4: "COOKING_USEFUL",
	0x080000c5: "COOKING_UNLOCK",
	0x080000c6: "COOKING_PURCHASE_RECIPE",
	0x080000d6: "COOKING_FINISH",
	0x080000d7: "COOKING_RETRY",
	0x080000df: "COOKING_RETRY_FREE",
	0x080000e0: "COOKING_REPAIR",
	0x080000e2: "COOKING_PLACE",
	0x080000eb: "COOKING_ROULETTE_START",
	0x080000f3: "COOKING_HURRY_UP_BY_USEFUL",
	0x080000f8: "COOKING_HURRY_UP_BY_USUALLY",
	0x080000f9: "COOKING_GET_CUP_GACHA_LIST_RECIPE",
	0x090000b9: "COLLECTION_PLACE",
	0x0a00009b: "GACHA_GET_AVAILABLE_DATA_LIST",
	0x0a00009c: "GACHA_PLAY",
	0x0a00009d: "GACHA_PLAY_FREE",
	0x0a00009e: "GACHA_PLAY_ONCE_MORE",
	0x0a0000d5: "GACHA_PLAY_ENTRY",
	0x0a0000f9: "GACHA_PLAY_STAMP",
	0x0c0000a5: "PROFILE_INIT",
	0x0c0000c7: "PROFILE_SET_AVATAR",
	0x0c0000c8: "PROFILE_NAME",
	0x0c0000c9: "PROFILE_SET_COMMENT",
	0x0d0000bf: "DECORATION_CHANGE",
	0x100000d8: "PACKET_AR_EXTENSION_PLACE",
	0x100000e3: "AR_CAPTURE",
}

def _stringify_const(object, fieldname, value):
	if not (type(value) in [str, int]):
		return None

	if type(object).__name__ == "Packet" and fieldname == "type":
		if value in packet_ids:
			return "QnqServletConstants." + packet_ids[value]
		return str(value)
	
	prefix = str(fieldname).upper() + "_"
	for k, v in object.__class__.__dict__.items():
		if v == value and k.startswith(prefix):
			return object.__class__.__name__ + "." + k

	return None

id_to_class = None
def scan_subclasses():
	global id_to_class
	id_to_class = {
		obj._OBJECT_ID: obj
		for obj in get_all_subclasses(Object)
		if hasattr(obj, "_OBJECT_ID")
	}
