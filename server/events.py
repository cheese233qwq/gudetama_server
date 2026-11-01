"""Local event calendar. Archive references are facts; schedules/notices are local.

Playable delivery events are implemented separately in event_gameplay.
"""
import time
from .library import ROOT,c
from .protocol import encode
from .paths import STATIC


def catalogue(definition):
    result = {}
    for name, mapping in vars(definition).items():
        if not isinstance(mapping, dict):
            continue
        for ident, item in mapping.items():
            ids = [getattr(item, 'eventId', 0)]
            multiple = getattr(item, 'eventIds', None)
            if isinstance(multiple, c.IntArray):
                ids.extend(multiple.value)
            for eid in set(ids):
                if type(eid) is int and eid > 0:
                    row = result.setdefault(eid, dict(id=eid, name=f'Event {eid}', references={}))
                    row['references'].setdefault(name, []).append(ident)
    return result


def ensure(db):
    db.execute('''CREATE TABLE IF NOT EXISTS local_event_calendar(
        event_id INTEGER PRIMARY KEY, opened_unix INTEGER NOT NULL,
        deadline_unix INTEGER NOT NULL)''')


def active(db, now=None):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='local_event_calendar'").fetchone():
        return []
    now = int(time.time()) if now is None else now
    return db.execute('SELECT event_id,deadline_unix FROM local_event_calendar WHERE deadline_unix>? ORDER BY event_id', (now,)).fetchall()


def home_button(ranking_id):
    # EventButton consumes a standalone home button, not eventN@btn01 (a
    # placeholder in ranking atlases). Missing variants use archived button1.
    name=f'event-btn_{ranking_id}'
    if name=='event-btn_1' or not (STATIC/f'rsrc/event/{name}.png').is_file():
        return 'event-btn_1'  # Generic art already includes the event label.
    # EventButton.setup strips '&' and displays the client's imgText overlay.
    return '&'+name


def change(db, definition, body, now=None):
    if not isinstance(body, dict) or set(body) != {'id', 'days', 'enabled'}:
        raise ValueError('event id, days and enabled required')
    eid, days, enabled = body['id'], body['days'], body['enabled']
    if type(eid) is not int or eid not in catalogue(definition):
        raise ValueError('unknown archived event ID')
    if type(days) is not int or not 1 <= days <= 365 or type(enabled) is not bool:
        raise ValueError('event duration must be 1..365 days; enabled must be boolean')
    now = int(time.time()) if now is None else now
    ensure(db)
    if enabled:
        others=[i for i,_ in active(db,now) if i!=eid]
        if others:
            raise ValueError('Only one event can be open. Close active event(s) '+', '.join(map(str,others))+' first.')
        db.execute('INSERT INTO local_event_calendar VALUES(?,?,?) ON CONFLICT(event_id) DO UPDATE SET opened_unix=excluded.opened_unix,deadline_unix=excluded.deadline_unix',
                   (eid, now, now + days * 86400))
    else:
        db.execute('DELETE FROM local_event_calendar WHERE event_id=?', (eid,))
    from .event_gameplay import calendar_changed
    calendar_changed(db,definition,eid,enabled,now+days*86400,now)


def extra(db, definition, now=None, *, include_closed=False):
    now = int(time.time()) if now is None else now
    from . import event_gameplay
    rows, known = [], catalogue(definition)
    entries=dict(active(db,now))
    # HomeScene.as:5541-5555 advertises every EventData in the map without
    # checking endTallyRestTimeSecs. Keep the results grace period only for
    # ranking responses, otherwise home continues to say the event is live.
    if include_closed and db.execute("SELECT 1 FROM sqlite_master WHERE name='local_event_cycles'").fetchone():
        for eid,deadline in db.execute('SELECT event_id,max(deadline_unix) FROM local_event_cycles WHERE deadline_unix>? GROUP BY event_id',(now-86400,)):
            entries.setdefault(eid,deadline)
    for eid, deadline in sorted(entries.items()):
        if eid not in known:
            raise ValueError('active event is absent from archive')
        # EventData.read/write and EventPart.update are confirmed. Calendar and
        # explanatory notices are LOCAL policy.
        spec=event_gameplay.profile(definition,eid)
        rank=spec[0] if spec else None
        rows.append(c.EventData(id=eid, endRestTimeSecs=max(1,deadline-now+(86400 if rank else 0)),
            background='', buttonImage=home_button(rank.id) if rank else '', title=f'LOCAL TEST {rank.title if rank else "Event "+str(eid)}',
            message='Local delivery event. Cook, deliver and claim rewards in BOX.' if rank else 'Calendar only; event gameplay not restored.',
            url='type#11!scene#ranking!' if rank else '', decorationId=0, endTallyRestTimeSecs=deadline-now, rankingId=rank.id if rank else 0,
            noticeIconRsrc=eid if rank and (STATIC/f'rsrc/event/event-notice_{eid}.png').is_file() else 0,
            gudetamaIds=c.IntArray([]), chBGM=c.Null(),
            # RankingScene.as:702 treats attendable=false as insufficient
            # player level, even during results viewing. Closing is expressed
            # by endTallyRestTimeSecs/showOnly and enforced by live-cycle checks.
            rentalDecorations=c.IntArray([]), noticeTextKey=f'event.notice.{eid}' if rank else '', attendable=bool(rank)))
    frame = c.ObjArray([c.String('event:'), c.ObjArray(rows)])
    encode(frame)
    return frame
