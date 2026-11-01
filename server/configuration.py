import mimetypes
import struct
import zlib
from pathlib import Path, PurePosixPath
from .library import ROOT, c
from .protocol import decode, encode
from .paths import APK, STATIC

LOCALES = {"ja": "", "en": "en.", "cn": "cn.", "ko": "ko.", "tw": "tw."}
LOCAL_SHOP_VERSION = 16057  # Local derivative; never an official release number.
# ID1: user-supplied 100 GP; ID5: Wiki Refrigerator cost. ID6 remains a
# non-official fallback: archived GameDef has -1 and its Wiki cost is unverified.
LOCAL_UTENSIL_PRICES = {1: 100, 5: 100000, 6: 100000}


def configure_local_shop(definition):
    """Local catalogue view; explicit sourced/fallback replacement prices.

    ShopScene_Gudetama.as:188-207, 399-415; ItemShopDialog_Gudetama.as:
    162-194, 353-444. Cash bundles otherwise block ordinary lists on Billing.
    Keep all item definitions: other scenes still need their IDs/resources.
    """
    definition.rule.shopItems = c.IntArray([i for i in definition.rule.shopItems.value if i in (2, 3, 4, 5, 6, 8)])
    # This increment only opens the five base ready-cup products; retain all
    # cup definitions for animations, characters, and tutorial gift ID1001.
    for ident,cup in definition.cupGachaMap.items():
        if ident not in (1,2,3,4,5):cup.price=c.Null()
    definition.setItemMap = {i: item for i, item in definition.setItemMap.items()
                             if isinstance(item.chargeItem, c.Null) or item.chargeItem is None}
    definition.version = LOCAL_SHOP_VERSION
    for ident, cost in LOCAL_UTENSIL_PRICES.items():
        definition.utensilMap[ident].price = c.ItemParam(kind=0,id=0,num=cost)
    configure_local_voice_guide(definition)
    # Local archive replay: the final original setting only lists the last
    # event on the hotplate. Permit the existing older recipe event IDs too.
    definition.kitchenwareMap[7].eventIds = c.IntArray(sorted({r.eventId for r in definition.recipeNoteMap.values() if r.kitchenwareId==7 and r.eventId>0}))
    configure_local_event_entry(definition)
    configure_local_ranking_colors(definition)
    # Preserve the archived PromotionVideo candidate IDs and weights. All eight
    # configured films exist locally; forcing movie1 here prevents variation.


def configure_local_ranking_colors(definition):
    # RankingRecordAndRewardDialog.as:559-603 directly tints tabs/backgrounds
    # with RankingDef colors. Earliest definitions have an entirely zero
    # palette. Borrow a complete archived palette from the same group layout;
    # legitimate black text and partial/custom palettes remain untouched.
    required=('topRecordMatColor','rankingRewardMatColor','pointRewardMatColor',
              'topRecordBgMatColor','rankingRewardBgMatColor','pointRewardBgMatColor')
    ranks=sorted(definition.rankingMap.values(),key=lambda r:r.id)
    for rank in ranks:
        fields=[k for k in vars(rank) if k.endswith('Color')]
        if not fields or any(getattr(rank,k)!=0 for k in fields):continue
        source=next((r for r in ranks if r.groupType==rank.groupType and all(getattr(r,k)>0 for k in required)),None)
        if source is None:raise ValueError('missing archived ranking palette')
        for key in fields:setattr(rank,key,getattr(source,key))


def configure_local_event_entry(definition):
    # Restore the independent announcement strip (HomeScene.as:5548).
    label=definition.dict.uitext.get('event.notice.1002',c.String('LOCAL TEST EVENT'))
    for ranking_id in definition.rankingMap:
        definition.dict.uitext.setdefault(f'event.notice.{1000+ranking_id}',label)
    # Guide1023 points at the event button (arrow7), but HomeScene.as:1398
    # only unlocks friendButton for notice23. Use the existing action0 to
    # unlock controls before waiting for the event click. Preserve every word.
    sentences=definition.guideTalkTable[1023].paragraph.sentences.value
    hide=next(i for i,s in enumerate(sentences) if s.event==5 and s.paramStr=='hide')
    sentences.insert(hide,c.GuideTalkSentenceParam(word=False,event=17,paramInt=0,paramStr='',
        waitTime=0.0,forceTime=0.0,nextWordsConnect=False,forceWordsFinish=False))


def configure_local_voice_guide(definition):
    """Local timing repair; retain every word, action and interruption.

    HomeScene.as:2338-2346 resumes immediately when a positive voice plays.
    GuideTalkPanel.as:488-500 discards that signal before event 18. The
    archived guide arms a one-tap event and arrow before four explanatory
    messages. Arm them only after the window hides, at the waiting boundary.
    """
    sentences = definition.guideTalkTable[5].paragraph.sentences.value
    action = next(s for s in sentences if s.event == 17 and s.paramInt == 7)
    arrow = next(s for s in sentences if s.event == 19 and s.paramInt == 6)
    sentences.remove(action)
    sentences.remove(arrow)
    boundary = next(i for i, s in enumerate(sentences) if s.event == 18)
    sentences[boundary:boundary] = [action, arrow]


def replace_resource_url(data, resource_url):
    """Change only a raw UTF field; retain every other byte of the GameDef."""
    compressed = data[:2] == b"\x78\xda"
    raw = zlib.decompress(data) if compressed else data
    definition = decode(raw, max_bytes=16 * 1024 * 1024)
    if not isinstance(definition, c.GameDef):
        raise ValueError("expected GameDef")
    old = definition.resourceUrl.encode("utf-8")
    new = resource_url.encode("utf-8")
    if len(new) > 65535:
        raise ValueError("CDN URL too long")
    needle = struct.pack(">H", len(old)) + old
    if raw.count(needle) != 1:
        raise ValueError("resourceUrl UTF field is not unique")
    changed = raw.replace(needle, struct.pack(">H", len(new)) + new, 1)
    verified = decode(changed, max_bytes=16 * 1024 * 1024)
    if verified.resourceUrl != resource_url:
        raise ValueError("resourceUrl verification failed")
    return zlib.compress(changed, 9) if compressed else changed


class Configuration:
    def __init__(self, resource_url, *, local_shop=False):
        self.resource_url = resource_url
        self.version = LOCAL_SHOP_VERSION if local_shop else 6045
        self.definitions = {}
        self.settings = {}
        self.overrides = {}
        if local_shop:
            from . import event_assets
            self.overrides[event_assets.PATH]=event_assets.asset((STATIC/event_assets.PATH).read_bytes())
        for locale, suffix in LOCALES.items():
            path = STATIC / f"setting/setting.dat.{suffix}6045.34"
            data = path.read_bytes()
            definition = decode(zlib.decompress(data), max_bytes=16 * 1024 * 1024)
            if definition.version != 6045:
                raise ValueError("unexpected setting version")
            if local_shop:
                # Refuse a lossy whole-GameDef rewrite. Archive stays read-only.
                if encode(definition) != zlib.decompress(data):
                    raise ValueError("local catalogue requires lossless GameDef roundtrip")
                configure_local_shop(definition)
                event_assets.metadata(definition,self.overrides[event_assets.PATH])
                definition.resourceUrl = resource_url
                name = f"setting/setting.dat.{suffix}{self.version}.34"
                self.settings[name] = zlib.compress(encode(definition), 9)
            else:
                self.settings[path.relative_to(STATIC).as_posix()] = replace_resource_url(data, resource_url)
            self.definitions[locale] = definition
        # Archive checkout may have converted text LF to CRLF. Restore only
        # bytes proven by the original GameDef size AND ObjectUtil hash.
        self._original_file_info = {f.path: (f.size, f.hash)
                                    for f in self.definitions['ja'].fileInfos.value}
        self._restored_text_assets = {}

    def asset(self, name):
        parts = PurePosixPath(name)
        if not name or "\\" in name or parts.is_absolute() or ".." in parts.parts:
            raise ValueError("invalid static path")
        if name in self.settings:
            return self.settings[name], "application/octet-stream"
        if name in self.overrides:
            return self.overrides[name], mimetypes.guess_type(name)[0] or 'application/octet-stream'
        if name in self._restored_text_assets:
            return self._restored_text_assets[name], mimetypes.guess_type(name)[0] or 'application/octet-stream'
        path = (STATIC / name).resolve()
        if not path.is_relative_to(STATIC.resolve()):
            raise ValueError("static path escaped archive")
        data = None
        if path.is_file():
            data = path.read_bytes()
        else:
            if name == 'rsrc/json/_CupListRecipeItem.json':
                from .compat_layouts import cup_recipe_item
                data = cup_recipe_item(lambda resource: self.asset(resource)[0])
            else:
                raise FileNotFoundError(name)
        if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
            raise FileNotFoundError("unmaterialized LFS asset: " + name)
        expected = self._original_file_info.get(name)
        if (expected and len(data) != expected[0] and len(data) <= 51200
                and parts.suffix in ('.atlas', '.json', '.xml') and b'\r\n' in data):
            from .event_assets import short_hash
            restored = data.replace(b'\r\n', b'\n')
            if len(restored) == expected[0] and short_hash(restored) == expected[1]:
                data = restored
                self._restored_text_assets[name] = data
        return data, mimetypes.guess_type(name)[0] or "application/octet-stream"
