"""A deliberate local test profile, not a recovered official starter account."""
from .library import c


def blank(cls, **overrides):
    fields = {}
    for name, kind in cls.__init__.__annotations__.items():
        if kind in (c.IntHashMap, c.HashMap):
            fields[name] = {}
        elif kind is c.ArrayList:
            fields[name] = []
        elif kind is c.String:
            fields[name] = ""
        elif kind is c.Object:
            fields[name] = None
        else:
            fields[name] = 0
    if overrides.keys() - fields.keys():
        raise ValueError("unknown fixture fields")
    fields.update(overrides)
    return cls(**fields)


def test_player(uid, locale, definition):
    # IDs are checked against the actual archive, never made-up config entries.
    if 1 not in definition.gudetamaMap or 1 not in definition.avatarMap or 1 not in definition.decorationMap:
        raise ValueError("fixture ID 1 absent from configuration")
    touch = c.TouchInfo(params=c.ObjArray([]), bonusRange=c.IntArray([]))
    return blank(
        c.UserData, uid=uid, encodedUid=uid, playerName="Local Test",
        doneFirstLogin=True, locale=locale, rank=1, avatar=1,
        # The test account has completed the tutorial, so the original TitleScene
        # chooses the existing HomeScene path. This is not new-account behavior.
        noticeFlagData=c.NoticeFlagData(noticeFlags=c.ByteArray(bytes([2]) * 31), tutorialProgress=7, bitFlags=0),
        avatarMap={1: c.AvatarData(id=1, acquired=True, available=True)},
        placedGudetamaId=1,
        gudetamaMap={1: blank(c.GudetamaData, id=1, count=1, num=1, available=True, unlocked=True)},
        decorationId=1,
        decorationMap={1: c.DecorationData(id=1, acquired=True, available=True)},
        wantedGudetamas=c.ObjArray([c.UserWantedData(id=0, updateTime=0) for _ in range(3)]), touchInfo=touch,
        userAbilities=c.ObjArray([]), features=c.ObjArray([]),
        cupGachaData=c.CupGachaData(cookIndex=-1, cupGachaIds=c.IntArray([0, 0, 0, 0]), restSec=0, showAdNum=0),
    )


def login_response(player, client_time, server_time):
    # TitleScene.as:401-430 fixes all five top-level elements and their meanings.
    return c.ObjArray([
        player, c.ObjArray([]), c.IntArray([server_time - client_time, 0]),
        c.IntArray([0, 0]), c.ObjArray([]),
    ])


def home_response(player):
    # HomeScene.as:582-596; MessageUI accepts no question, DelusionButton empty.
    return c.ObjArray([
        player.touchInfo, c.Null(), c.IntArray([]),
        c.IntArray([0, 0, player.decorationId]), c.IntArray([]),
    ])
