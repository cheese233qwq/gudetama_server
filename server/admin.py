"""Loopback-only admin for explicitly marked local compatibility test saves."""
import argparse
import hmac
import json
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from wsgiref.simple_server import make_server
from .library import ROOT,c
from .state import Accounts
from .protocol import encode,decode
from .configuration import Configuration
from .gameplay import MONEY_MAX
from . import missions, gacha_settings, events, event_gameplay
from .paths import validate_save_path


def plain(value):
    if isinstance(value,(str,int,float,bool)) or value is None:return value
    if isinstance(value,bytes):return list(value)
    if isinstance(value,(list,tuple)):return [plain(x) for x in value]
    if hasattr(value,'items'):return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value,c.Null):return None
    if hasattr(value,'value'):return plain(value.value)
    return {k:plain(v) for k,v in vars(value).items()}


class Admin:
    def __init__(self,path,token,port=8081,definition=None):
        try:path=validate_save_path(path)
        except ValueError:raise ValueError('existing isolated test database required') from None
        if not path.is_file():
            raise ValueError('existing isolated test database required')
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
            try:marked=db.execute("SELECT value FROM cooking_mode_metadata WHERE name='rules'").fetchone()
            except sqlite3.Error:marked=None
            if not marked:raise ValueError('unmarked test database')
        if not token or len(token)<24:raise ValueError('admin token too short')
        self.accounts=Accounts(path)
        self.token=token
        self.hosts={f'127.0.0.1:{port}',f'localhost:{port}'}
        self.definition=definition or Configuration('http://127.0.0.1:8080/gde/static/',local_shop=True).definitions['ja']

    def close(self):self.accounts.close()

    def pools(self, body=None):
        with self.accounts.lock:
            db=self.accounts.db
            if body is not None:
                if not isinstance(body,dict) or set(body)!={'active'}:raise ValueError('active pool IDs required')
                try:
                    db.execute('BEGIN IMMEDIATE')
                    gacha_settings.select(db,self.definition,body['active'])
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
            return dict(active=list(gacha_settings.active(db)),pools=[
                dict(id=i,name=d.name,resource=d.rsrc,items=len(d.screeningItems.value))
                for i,d in sorted(self.definition.gachaMap.items())])

    def account_rows(self):
        with self.accounts.lock:
            rows=self.accounts.db.execute('SELECT uid,player FROM accounts WHERE player IS NOT NULL ORDER BY uid').fetchall()
        result=[]
        for uid,blob in rows:
            p=decode(blob)
            result.append(dict(uid=uid,name=p.playerName,rank=p.rank,gp=p.freeMoney,gold=p.freeMetal,
                               tutorial=p.noticeFlagData.tutorialProgress))
        return result

    def events(self, body=None):
        with self.accounts.lock:
            db=self.accounts.db
            if body is not None:
                try:
                    db.execute('BEGIN IMMEDIATE')
                    events.change(db,self.definition,body)
                    events.extra(db,self.definition)  # Validate wire before commit.
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
            rows=list(events.catalogue(self.definition).values())
            for row in rows:
                spec=event_gameplay.profile(self.definition,row['id'])
                row.update(playable=bool(spec),name=spec[0].title if spec else row['name'])
            return dict(active=[dict(id=i,deadline_unix=t) for i,t in events.active(db)],
                        events=rows,scope='archived delivery tours and regional festivals; other events calendar only')

    def detail(self,uid):
        with self.accounts.lock:
            row=self.accounts.db.execute('SELECT player FROM accounts WHERE uid=? AND player IS NOT NULL',(uid,)).fetchone()
            if not row:raise ValueError('account not found')
            exists=self.accounts.db.execute("SELECT 1 FROM sqlite_master WHERE name='admin_rewards'").fetchone()
            audit=self.accounts.db.execute('SELECT grant_id,kind,item_id,amount,before_value,after_value,note,created_unix FROM admin_rewards WHERE uid=? ORDER BY created_unix DESC LIMIT 50',(uid,)).fetchall() if exists else []
            has_box=self.accounts.db.execute("SELECT 1 FROM sqlite_master WHERE name='normal_mission_presents'").fetchone()
            box=[plain(decode(m[0])) for m in self.accounts.db.execute(
                'SELECT mail FROM normal_mission_presents WHERE uid=? AND claimed_unix IS NULL ORDER BY mail_key',(uid,))] if has_box else []
        return dict(player=plain(decode(row[0])),admin_rewards=audit,box=box)

    def reward(self,body):
        if not isinstance(body,dict) or set(body)!={'uid','kind','item_id','amount','grant_id','note'}:
            raise ValueError('invalid reward fields')
        uid,kind,ident,amount,grant_id,note=(body[x] for x in ('uid','kind','item_id','amount','grant_id','note'))
        if type(uid) is not int or uid<1 or kind not in ('gp','gold','useful') or type(ident) is not int:
            raise ValueError('invalid reward account/kind/item')
        if type(amount) is not int or not 1<=amount<=MONEY_MAX:
            raise ValueError('positive integer reward required')
        if not isinstance(grant_id,str) or not 1<=len(grant_id)<=128 or not isinstance(note,str) or not 1<=len(note.strip())<=300:
            raise ValueError('unique grant ID and audit reason required')
        if kind=='useful' and ident not in self.definition.usefulMap or kind!='useful' and ident!=0:
            raise ValueError('unknown reward item ID')
        with self.accounts.lock:
            row=self.accounts.db.execute('SELECT uiid FROM accounts WHERE uid=? AND player IS NOT NULL',(uid,)).fetchone()
        if not row:raise ValueError('account not found')
        def operation(p,db):
            db.execute('''CREATE TABLE IF NOT EXISTS admin_rewards(
                grant_id TEXT PRIMARY KEY,uid INTEGER NOT NULL REFERENCES accounts(uid),
                kind TEXT NOT NULL,item_id INTEGER NOT NULL,amount INTEGER NOT NULL,
                before_value INTEGER NOT NULL,after_value INTEGER NOT NULL,
                before_player BLOB NOT NULL,note TEXT NOT NULL,created_unix INTEGER NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS admin_reward_mail(
                grant_id TEXT PRIMARY KEY REFERENCES admin_rewards(grant_id),
                mail_key INTEGER NOT NULL UNIQUE REFERENCES normal_mission_presents(mail_key))''')
            old=db.execute('SELECT uid,kind,item_id,amount,note,before_value,after_value FROM admin_rewards WHERE grant_id=?',(grant_id,)).fetchone()
            if old:
                if old[:5]!=(uid,kind,ident,amount,note):raise ValueError('grant ID reused with different parameters')
                mail=db.execute('SELECT mail_key FROM admin_reward_mail WHERE grant_id=?',(grant_id,)).fetchone()
                return dict(uid=uid,before=old[5],after=old[6],replayed=True,grant_id=grant_id,
                            delivery='box' if mail else 'legacy_direct',mail_key=mail[0] if mail else None)
            backup=encode(p)
            if kind in ('gp','gold'):
                free,paid=('freeMoney','chargeMoney') if kind=='gp' else ('freeMetal','chargeMetal')
                before=getattr(p,free)
                if before+getattr(p,paid)+amount>MONEY_MAX:raise ValueError('reward exceeds currency limit')
            else:
                owned=p.usefulMap.get(ident)
                before=owned.num if owned else 0
                if before+amount>self.definition.usefulMap[ident].possessionLimit:raise ValueError('reward exceeds inventory limit')
            # Reserve a distinct negative source ID: positive IDs belong to missions.
            # Issuing a mail never credits balances/inventory; claim does so atomically.
            missions.ensure_box(db)
            source=db.execute('SELECT min(mission_id) FROM normal_mission_presents WHERE uid=?',(uid,)).fetchone()[0]
            source=min(0,source or 0)-1
            now=int(time.time())
            cur=db.execute('INSERT INTO normal_mission_presents(uid,mission_id,mail,created_unix) VALUES(?,?,?,?)',
                           (uid,source,b'',now))
            if cur.lastrowid>2147483647:raise ValueError('BOX key overflow')
            item=c.ItemParam(kind={'gp':0,'gold':1,'useful':8}[kind],id=ident,num=amount)
            mail=c.SystemMailData(type=0,kind=0,senderEncodedUid=0,item=item,
                title='Administrator reward',url='',urlAndroid='',alreadyRead=False,noticeIconId=0,
                deleteSec=-1,manualDeletion=False,uniqueKey=cur.lastrowid,message=note,receivedSecs=now-1262271600)
            db.execute('UPDATE normal_mission_presents SET mail=? WHERE mail_key=?',(encode(mail),cur.lastrowid))
            db.execute('INSERT INTO admin_rewards VALUES(?,?,?,?,?,?,?,?,?,?)',
                (grant_id,uid,kind,ident,amount,before,before,backup,note,now))
            db.execute('INSERT INTO admin_reward_mail VALUES(?,?)',(grant_id,cur.lastrowid))
            db.execute('UPDATE player_state SET revision=revision+1 WHERE uid=?',(uid,))
            result=dict(uid=uid,before=before,after=before,replayed=False,grant_id=grant_id,
                        delivery='box',mail_key=cur.lastrowid)
            json.dumps(result)  # Validate the response before committing.
            return result
        return self.accounts.transact(row[0],operation)

    def __call__(self,env,start):
        status,mime,result='200 OK','application/json; charset=utf-8',None
        try:
            if env.get('REMOTE_ADDR') not in ('127.0.0.1','::1') or env.get('HTTP_HOST') not in self.hosts:
                status,result='403 Forbidden',{'error':'loopback access only'}
            elif env.get('HTTP_ORIGIN') and env['HTTP_ORIGIN'] not in {'http://'+h for h in self.hosts}:
                status,result='403 Forbidden',{'error':'foreign origin rejected'}
            elif env['PATH_INFO']=='/' and env['REQUEST_METHOD']=='GET':
                mime='text/html; charset=utf-8';result=(Path(__file__).with_name('admin.html')).read_bytes()
            elif env['PATH_INFO'] in ('/favicon.png','/favicon.ico') and env['REQUEST_METHOD']=='GET':
                status,result='204 No Content',b''
            elif not hmac.compare_digest(env.get('HTTP_AUTHORIZATION',''),'Bearer '+self.token):
                status,result='401 Unauthorized',{'error':'admin token required'}
            elif env['PATH_INFO']=='/api/accounts' and env['REQUEST_METHOD']=='GET':result=self.account_rows()
            elif env['PATH_INFO'].startswith('/api/accounts/') and env['REQUEST_METHOD']=='GET':
                result=self.detail(int(env['PATH_INFO'].split('/')[-1]))
            elif env['PATH_INFO']=='/api/items' and env['REQUEST_METHOD']=='GET':
                result=[dict(id=i,name=d.name,limit=d.possessionLimit) for i,d in self.definition.usefulMap.items()]
            elif env['PATH_INFO']=='/api/pools' and env['REQUEST_METHOD']=='GET':result=self.pools()
            elif env['PATH_INFO']=='/api/events' and env['REQUEST_METHOD']=='GET':result=self.events()
            elif env['PATH_INFO'] in ('/api/rewards','/api/pools','/api/events') and env['REQUEST_METHOD']=='POST':
                size=int(env.get('CONTENT_LENGTH','0'))
                if not 0<size<=8192 or env.get('CONTENT_TYPE')!='application/json':raise ValueError('small JSON request required')
                raw=env['wsgi.input'].read(size)
                if len(raw)!=size:raise ValueError('truncated reward request')
                body=json.loads(raw)
                result={'/api/rewards':self.reward,'/api/pools':self.pools,'/api/events':self.events}[env['PATH_INFO']](body)
            else:status,result='404 Not Found',{'error':'unknown admin route'}
        except (ValueError,UnicodeError) as error:status,result='400 Bad Request',{'error':str(error)}
        except sqlite3.Error:status,result='503 Service Unavailable',{'error':'database busy/error; retry with same grant ID'}
        body=result if isinstance(result,bytes) else json.dumps(result,ensure_ascii=False).encode('utf-8')
        start(status,[('Content-Type',mime),('Content-Length',str(len(body))),('Cache-Control','no-store'),
                      ('X-Content-Type-Options','nosniff'),('X-Frame-Options','DENY'),('Referrer-Policy','no-referrer')])
        return [body]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--state',type=Path,default=ROOT/'server/state/tutorial-compatible/accounts.sqlite3')
    parser.add_argument('--port',type=int,default=8081)
    args=parser.parse_args()
    token=secrets.token_urlsafe(32)
    admin=Admin(args.state,token,args.port)
    try:
        with make_server('127.0.0.1',args.port,admin) as http:
            print(f'Admin: http://127.0.0.1:{args.port}/',flush=True)
            print(f'Admin token (paste into page): {token}',flush=True)
            print('Claim rewards in the game BOX. Ctrl+C stops admin.',flush=True)
            http.serve_forever()
    finally:admin.close()


if __name__=='__main__':main()
