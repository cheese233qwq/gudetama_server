"""Owned local profile editing; no external account or social integration."""
from .library import c
from .protocol import encode
from . import gameplay,tutorial

AVATAR,NAME,COMMENT=201326791,201326792,201326793
TYPES={AVATAR,NAME,COMMENT}


def sync_unlock(p,db,d):
    level=d.initDict.others.get('friend.unlock.lv')
    features={x.value if isinstance(x,c.Int) else x for x in p.features.value}
    if (not isinstance(level,c.Int) or level.value<=0 or p.rank<level.value
            or p.noticeFlagData.tutorialProgress<7 or 12 in features):return False
    p.features=c.IntArray(sorted(features|{12}))
    db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))
    return True


def process(accounts,packet,session,d):
    if not session.initialized or not gameplay.null(packet.payloadObj1):raise ValueError('invalid profile request')
    def operation(p,db):
        extra=gameplay.settle_touch(p,db,packet.payloadExtra,d)
        sync_unlock(p,db,d)
        features={x.value if isinstance(x,c.Int) else x for x in p.features.value}
        if 12 not in features:raise ValueError('profile editing requires configured unlock level')
        if packet.type==NAME:
            if not gameplay.null(packet.payloadInt) or not isinstance(packet.payloadObj0,c.String):
                raise ValueError('profile name requires String only')
            name=packet.payloadObj0.value
            code=tutorial.name_status(name)
            if code==0:p.playerName=name
            result=c.ObjArray([c.IntArray([code]),c.String(name)])
        else:
            if not gameplay.null(packet.payloadObj0):raise ValueError('external profile image not supported')
            args=gameplay.integers(packet.payloadInt,2 if packet.type==AVATAR else 1)
            ident=args[0]
            if packet.type==COMMENT:
                owned={x.value if isinstance(x,c.Int) else x for x in p.commentList}
                if ident not in owned or ident not in d.commentMap:raise ValueError('comment not owned')
                p.comment=ident
            elif packet.type==AVATAR:
                item=p.avatarMap.get(ident)
                if args[1]!=-1 or ident not in d.avatarMap or not item or not item.acquired:
                    raise ValueError('avatar not owned or external avatar unsupported')
                p.avatar,p.snsInterlockType=ident,-1
            else:raise ValueError('unsupported profile edit')
            result=c.ObjArray([])  # Both client callbacks ignore array contents.
        db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))
        extra.append(c.ObjArray([c.String('feature:'),p.features]))
        extras=c.ObjArray(extra)
        encode(result);encode(extras)
        return result,extras
    return accounts.transact(session.uiid,operation)
