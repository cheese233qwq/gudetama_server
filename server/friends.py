"""Local directed follows, using the original profile/list/room wire types.

No external accounts, gifts, assistance rewards or friendship XP are simulated.
"""
import time
from .library import c
from .player import blank
from .protocol import decode, encode
from . import gameplay, profile

ENTER, LIST, SEARCH = 63, 67109025, 67109028
FOLLOW, REMOVE, DETAIL, ROOM, BLOCK, WANTED = 162, 163, 167, 67109033, 67109037, 219
TYPES = {ENTER, LIST, SEARCH, FOLLOW, REMOVE, DETAIL, ROOM, BLOCK, WANTED}
from . import friend_actions
TYPES |= friend_actions.TYPES
OFFSET = 1262271600


def ensure(db):
    db.execute('''CREATE TABLE IF NOT EXISTS local_follows(
        source INTEGER NOT NULL REFERENCES accounts(uid),
        target INTEGER NOT NULL REFERENCES accounts(uid),
        created_unix INTEGER NOT NULL, PRIMARY KEY(source,target), CHECK(source<>target))''')
    db.execute('CREATE INDEX IF NOT EXISTS local_follows_target ON local_follows(target,source)')
    db.execute('''CREATE TABLE IF NOT EXISTS local_friend_activity(
        uid INTEGER PRIMARY KEY REFERENCES accounts(uid),last_unix INTEGER NOT NULL)''')


def eligible(p, d):
    return p.rank >= d.initDict.others['friend.unlock.lv'].value and p.noticeFlagData.tutorialProgress >= 7


def relations(db, uid, other):
    outgoing = db.execute('SELECT created_unix FROM local_follows WHERE source=? AND target=?',(uid,other)).fetchone()
    incoming = db.execute('SELECT created_unix FROM local_follows WHERE source=? AND target=?',(other,uid)).fetchone()
    return (1 if outgoing else 0)+(2 if incoming else 0), (outgoing or incoming or (OFFSET,))[0]-OFFSET


def user_profile(db, viewer, p):
    state, requested = relations(db, viewer.uid, p.uid)
    active = db.execute('SELECT last_unix FROM local_friend_activity WHERE uid=?',(p.uid,)).fetchone()
    return blank(c.UserProfileData,encodedUid=p.encodedUid,playerName=p.playerName,
        playerRank=p.rank,avatar=p.avatar,gender=p.gender,area=p.area,comment=p.comment,
        followState=state,followRequestSecs=requested,snsProfileImage=c.Null(),
        lastActiveSec=active[0]-OFFSET if active else 0,snsId='',snsType=0)


def friendly(p):
    # Explicit local baseline. No friendship progression is awarded by this module.
    return c.FriendlyData(encodedUid=p.encodedUid,friendly=0,friendlyLevel=0)


def process(accounts, packet, session, d, engine, *, request_fingerprint=None):
    if packet.type in friend_actions.TYPES:
        return friend_actions.process(accounts,packet,session,d,engine,request_fingerprint=request_fingerprint)
    if not session.initialized or not gameplay.null(packet.payloadObj1): raise ValueError('invalid friend request')
    def operation(p, db):
        ensure(db)
        if not eligible(p,d): raise ValueError('friends require level 10 and completed tutorial')
        extras = gameplay.settle_touch(p,db,packet.payloadExtra,d)
        profile.sync_unlock(p,db,d)
        db.execute('INSERT OR REPLACE INTO local_friend_activity VALUES(?,?)',(p.uid,int(time.time())))
        players = [decode(row[0]) for row in db.execute('SELECT player FROM accounts WHERE player IS NOT NULL ORDER BY uid')]
        targets = {q.encodedUid:q for q in players if q.uid!=p.uid and eligible(q,d)}
        typ = packet.type
        if typ == SEARCH:
            if not gameplay.null(packet.payloadInt) or not isinstance(packet.payloadObj0,c.String): raise ValueError('friend search requires String')
            key = packet.payloadObj0.value.strip()
            if not key.isascii() or not key.isdecimal() or len(key)>10: raise ValueError('invalid friend key')
            target = targets.get(int(key))
            result = user_profile(db,p,target) if target else c.Null()
        else:
            if not gameplay.null(packet.payloadObj0): raise ValueError('unexpected friend object payload')
            if typ == ENTER:
                if not gameplay.null(packet.payloadInt): raise ValueError('friend entry takes no integers')
                db.execute('UPDATE player_state SET scene=?,revision=revision+1 WHERE uid=?',(ENTER,p.uid))
                result = c.ObjArray([])
            elif typ == LIST:
                flags = gameplay.integers(packet.payloadInt,2)
                if any(x not in (0,1) for x in flags): raise ValueError('invalid friend refresh flags')
                recommended, followers, follows = [], [], []
                for target in targets.values():
                    item = user_profile(db,p,target)
                    if item.followState == 0: recommended.append(item)
                    if item.followState & 2: followers.append(item)
                    if item.followState & 1: follows.append(item)
                # FriendScene indexes each row as [FriendlyData, [lastLevel]].
                # Level rewards are already mailed by friend_actions.increase;
                # refreshing this list must not replay their notification.
                mutual=[]
                for target in targets.values():
                    if relations(db,p.uid,target.uid)[0]==3:
                        data=friend_actions.friendly(db,p,target,d)
                        mutual.append(c.ObjArray([data,c.IntArray([data.friendlyLevel])]))
                # Full snapshots even when flags=0: another device may have changed the relation.
                result = c.ObjArray([c.ObjArray(recommended[:20]),c.ObjArray(followers),c.ObjArray(follows),
                    c.ObjArray(mutual),c.IntHashMap({}),c.IntHashMap(p.friendPresentMoneyParamMap)])
            else:
                args = gameplay.integers(packet.payloadInt,1) if typ != BLOCK else (
                    packet.payloadInt.value if isinstance(packet.payloadInt,c.IntArray) else [])
                if not args or len(args)>100 or len(set(args))!=len(args): raise ValueError('invalid friend target list')
                if typ == WANTED:
                    if args[0] not in d.gudetamaMap: raise ValueError('unknown wanted gudetama')
                    result = c.ObjArray([user_profile(db,p,q) for q in targets.values()
                        if relations(db,p.uid,q.uid)[0]==3 and any(w.id==args[0] for w in q.wantedGudetamas.value)])
                else:
                    if any(i not in targets for i in args): raise ValueError('unknown, locked or self friend target')
                    target = targets[args[0]]
                    state,_ = relations(db,p.uid,target.uid)
                    if typ == FOLLOW:
                        code = -2 if state & 1 else 0
                        if not state & 1:
                            def counts(q):
                                outgoing = db.execute('SELECT COUNT(*) FROM local_follows WHERE source=?',(q.uid,)).fetchone()[0]
                                incoming = db.execute('SELECT COUNT(*) FROM local_follows WHERE target=?',(q.uid,)).fetchone()[0]
                                mutual = db.execute('SELECT COUNT(*) FROM local_follows a JOIN local_follows b ON a.source=b.target AND a.target=b.source WHERE a.source=?',(q.uid,)).fetchone()[0]
                                return outgoing-mutual,incoming-mutual,mutual
                            own, other = counts(p),counts(target)
                            # Client FriendPart.getMaxFriends: 10 + extension * rule value.
                            if state==2 and own[2]>=10+p.numFriendsExtension*d.rule.friendsExtensionValue: code=-5
                            elif state==2 and other[2]>=10+target.numFriendsExtension*d.rule.friendsExtensionValue: code=-4
                            elif own[0]>=100: code=-3  # Local pending-follow limit, not an official recovered rule.
                            elif other[1]>=100: code=-1
                            else:
                                db.execute('INSERT INTO local_follows VALUES(?,?,?)',(p.uid,target.uid,int(time.time())))
                                code = 1 if state==2 else 0
                        result = c.IntArray([code])
                    elif typ in (REMOVE,BLOCK):
                        for ident in args:
                            uid=targets[ident].uid
                            db.execute('DELETE FROM local_follows WHERE (source=? AND target=?) OR (source=? AND target=?)',(p.uid,uid,uid,p.uid))
                        result = c.ObjArray([])
                    elif typ == DETAIL:
                        result = c.FriendInfo(friendlyData=friend_actions.friendly(db,p,target,d),wantedGudetamas=target.wantedGudetamas,
                            friendPresentLogDiff=c.ObjArray([]),lastFriendlyLevel=0)
                    elif typ == ROOM:
                        if not state: raise ValueError('follow this player before visiting')
                        friend_actions.ensure(db)
                        result = friend_actions.room(db,p,target,d,engine)
                    else: raise ValueError('unsupported friend operation')
        extra = c.ObjArray(extras)
        encode(result); encode(extra)
        return result,extra
    return accounts.transact(session.uiid,operation)
