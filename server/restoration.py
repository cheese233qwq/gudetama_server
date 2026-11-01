"""Explicit LOCAL policies for missing official dynamic algorithms."""
import json
import time
from .library import ROOT,c
from .protocol import encode
from . import gameplay,missions

SILVER_PER_GOLD = 100  # Wiki GPS / Golden Eggs: automatic conversion, not a local rate.


def exchange_silver(p, added=0):
    """Credit silver and convert full hundreds to free gold, retaining change."""
    total = p.subMetal + added
    if added < 0 or not 0 <= total <= 2147483647:
        raise ValueError('silver egg balance overflow')
    gold,remainder = divmod(total,SILVER_PER_GOLD)
    if p.freeMetal+p.chargeMetal+gold > gameplay.MONEY_MAX:
        raise ValueError('silver egg conversion exceeds gold balance limit')
    p.subMetal = remainder
    p.freeMetal += gold
    return gold*SILVER_PER_GOLD,gold


def restore_silver_conversion(p,db):
    """Normalize legacy silver once in the caller's login transaction."""
    if p.subMetal < SILVER_PER_GOLD:return
    before = encode(p)
    exchange_silver(p)
    db.execute('INSERT OR IGNORE INTO player_migrations VALUES(?,?,?,?)',
               (p.uid,'silver-eggs-100-to-1-v1',before,int(time.time())))
    db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(p.uid,))


def policy():
    data=json.loads((ROOT/'server/restoration_policy.json').read_text(encoding='utf-8'))
    # Older running processes re-read this JSON on every request and require
    # this key. Keep it in the shipped file, but ignore it in current code.
    # Also accept files saved without it by the brief field-removal version.
    legacy_cooldown=data.pop('video_cooldown_seconds',60)
    if type(legacy_cooldown) is not int or not 0<=legacy_cooldown<=86400:
        raise ValueError('invalid legacy video cooldown setting')
    limits={'microwave_level':(1,32767),'drop_percent':(0,100),
            'hidden_cooldown_seconds':(1,86400),'hidden_gp_per_level':(0,100000),
            'gift_friendship':(0,100),'friend_touch_friendship':(0,100),
            'pity_draws':(0,1000),'pity_minimum_egg':(1,2),'duplicate_unique_gp':(0,1000000),
            'video_minimum_seconds':(1,3600)}
    if set(data)!=set(limits) or any(type(data[k]) is not int or not lo<=data[k]<=hi for k,(lo,hi) in limits.items()):
        raise ValueError('invalid local restoration policy')
    return data


def mail(db,uid,key,item,title,sender=0):
    missions.ensure_box(db)
    db.execute('CREATE TABLE IF NOT EXISTS local_extension_mails(uid INTEGER NOT NULL,event_key TEXT NOT NULL,mail_key INTEGER NOT NULL,PRIMARY KEY(uid,event_key))')
    old=db.execute('SELECT mail_key FROM local_extension_mails WHERE uid=? AND event_key=?',(uid,key)).fetchone()
    if old:return old[0]
    source=min(0,db.execute('SELECT coalesce(min(mission_id),0) FROM normal_mission_presents').fetchone()[0])-1
    now=int(time.time())
    cur=db.execute('INSERT INTO normal_mission_presents(uid,mission_id,mail,created_unix) VALUES(?,?,?,?)',(uid,source,b'',now))
    if cur.lastrowid>2147483647 or source < -2147483647:raise ValueError('BOX key overflow')
    m=c.SystemMailData(type=0,kind=0,senderEncodedUid=sender,item=item,title=title,url='',urlAndroid='',
                      alreadyRead=False,noticeIconId=0,deleteSec=-1,manualDeletion=False,uniqueKey=cur.lastrowid,
                      message=title,receivedSecs=now-1262271600)
    db.execute('UPDATE normal_mission_presents SET mail=? WHERE mail_key=?',(encode(m),cur.lastrowid))
    db.execute('INSERT INTO local_extension_mails VALUES(?,?,?)',(uid,key,cur.lastrowid))
    return cur.lastrowid


def award(p,d,item):
    if item.num<=0:raise ValueError('invalid local reward')
    if item.kind in (0,1):
        field='freeMoney' if item.kind==0 else 'freeMetal'
        other=p.chargeMoney if item.kind==0 else p.chargeMetal
        if getattr(p,field)+other+item.num>gameplay.MONEY_MAX:raise ValueError('reward overflow')
        setattr(p,field,getattr(p,field)+item.num)
        return item
    if item.kind==3:
        spent,gold = exchange_silver(p,item.num)
        # UserDataWrapper.addSubMetal adds num first, then uses originalItem
        # and credits convertedItem/convertedParam. Return deltas, not balances.
        original = c.ItemParam(kind=3,id=0,num=spent) if spent else c.Null()
        converted = c.ItemParam(kind=1,id=0,num=gold) if gold else c.Null()
        return c.ConvertParam(originalItem=original,convertedItem=converted,
                              convertedParam=converted,kind=3,id=0,num=item.num)
    from .local_gacha import Engine
    return Engine().award(p,d,item)
