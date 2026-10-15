"""Read-only WAHA history scan and explicit maintenance replay; never sends messages."""
import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from pydantic import ValidationError
from app.admin import store
from app.integrations import waha
from app.config.settings import get_settings
from scripts.migrate_state import admin_db, control_row, encoded, private_json

PRIVATE_CHAT=re.compile(r'\d+@(c\.us|lid)')


def validated(rows):
    unique={}
    for row in rows:
        try:
            message=waha.Message.model_validate(row)
            timestamp=row['timestamp']
            if type(row['fromMe'])!=bool or type(timestamp) not in (int,float) or not math.isfinite(timestamp):
                raise ValueError()
            datetime.fromtimestamp(timestamp,timezone.utc)
            item={'id':message.id,'from':message.sender,'body':message.body,'fromMe':message.fromMe,'timestamp':timestamp}
            ack=row.get('ack')
            if ack is not None:
                if type(ack)!=int or not -1<=ack<=4: raise ValueError()
                item['ack']=ack
            old=unique.get(message.id)
            if old:
                if any(old.get(k)!=item.get(k) for k in ('id','from','body','fromMe','timestamp')):
                    raise ValueError('Conflicting WAHA history identity.')
                if ack is not None: old['ack']=max(old.get('ack',-1),ack)
            else:
                unique[message.id]=item
        except (ValidationError,KeyError,TypeError,OverflowError,OSError):
            raise ValueError('Malformed WAHA history payload.') from None
    return sorted(unique.values(),key=lambda row:(row['timestamp'],row['id']))


def pages(path, request, suffix=''):
    repeated=0
    previous=None
    for offset in range(0,1_000_000,100):
        result=request('GET',f'{path}?limit=100&offset={offset}{suffix}')
        if not isinstance(result,list) or any(not isinstance(row,dict) for row in result):
            raise ValueError('WAHA history must return a list of objects.')
        if not result: return
        fingerprint=hashlib.sha256(encoded(result).encode()).hexdigest()
        repeated=repeated+1 if fingerprint==previous else 0
        if repeated>=2: raise ValueError('WAHA history pagination did not advance.')
        previous=fingerprint
        yield from result
    raise ValueError('WAHA history pagination safety limit reached; completion refused.')


def scan_interval(start, end, request):
    if not (math.isfinite(start) and math.isfinite(end) and 0<=start<=end):
        raise ValueError('Invalid closed history interval.')
    session=quote(get_settings().waha_session,safe='')
    root=f'/api/{session}/chats'
    chats=list(pages(root,request))
    chat_ids=set()
    for chat in chats:
        if not isinstance(chat.get('id'),str):
            raise ValueError('Malformed WAHA chat identity.')
        if PRIVATE_CHAT.fullmatch(chat['id']): chat_ids.add(chat['id'])
    messages=[]
    for chat_id in sorted(chat_ids):
        suffix=f'&downloadMedia=false&filter.timestamp.gte={math.floor(start)-1}&filter.timestamp.lte={math.ceil(end)+1}'
        messages.extend(pages(f'{root}/{quote(chat_id,safe="")}/messages',request,suffix))
    return [row for row in validated(messages) if start-1<=row['timestamp']<=end+1]


def eligible(row):
    return not row['fromMe'] and PRIVATE_CHAT.fullmatch(row['from']) and row['body'] and row['body'].strip()


def reconcile_messages(messages, session, write=False):
    messages=validated(messages)
    incoming=[row for row in messages if eligible(row)]
    existing={row['message_id']:row for row in store.inbox_rows(session)}
    missing=0
    for row in incoming:
        old=existing.get(row['id'])
        if old and (old['sender']!=row['from'] or old['body']!=row['body']):
            raise ValueError('Stored WAHA identity has conflicting content.')
        missing+=old is None
    known_replies={identifier for row in existing.values() for identifier in json.loads(row['reply_ids'] or '[]')}
    acks={row['id']:row['ack'] for row in messages if row['fromMe'] and row['id'] in known_replies and 'ack' in row}
    summary={'eligible':len(incoming),'existing':len(incoming)-missing,'missing':missing,'inserted':0,'acknowledgements':len(acks)}
    if write:
        items=[{'message_id':row['id'],'sender':row['from'],'body':row['body'],
                'received_at':datetime.fromtimestamp(row['timestamp'],timezone.utc).isoformat()} for row in incoming]
        summary['inserted']=store.reconcile_intake(session,items,acks)
    return summary


def complete_reconciliation(messages, session, start, end, admin_dsn):
    messages=validated(messages)
    if not 0<=start<=end: raise ValueError('Invalid reconciliation interval.')
    if any(row['timestamp']<start-1 or row['timestamp']>end+1 for row in messages):
        raise ValueError('History lies outside the fixed scan interval.')
    with admin_db(admin_dsn) as db:
        mode,started,_=control_row(db)
        if mode!='intake' or not started: raise ValueError('Completion requires intake maintenance.')
        for row in messages:
            if eligible(row):
                stored=db.execute('SELECT sender,body FROM chatbot.whatsapp_inbox WHERE session=%s AND message_id=%s',(session,row['id'])).fetchone()
                if stored!=(row['from'],row['body']): raise ValueError('History reconciliation is incomplete.')
        ledger=db.execute('SELECT snapshot_sha256,manifest FROM chatbot.state_imports').fetchall()
        if len(ledger)!=1: raise ValueError('Verified import ledger is required.')
        digest,raw=ledger[0];metadata=json.loads(raw)
        receipt={'snapshot_sha256':digest,'session':session,'start':start,'end':end,
                 'scan_sha256':hashlib.sha256(encoded(messages).encode()).hexdigest(),'complete':True}
        metadata['reconciliation']=receipt
        db.execute('UPDATE chatbot.state_imports SET manifest=%s WHERE snapshot_sha256=%s',(encoded(metadata),digest))
    return receipt


def epoch(value):
    parsed=datetime.fromisoformat(value)
    if parsed.tzinfo is None: raise ValueError('Watermarks require an explicit timezone.')
    return parsed.timestamp()


def gateway_identity():
    return hashlib.sha256(get_settings().waha_base_url.rstrip('/').encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('scan');p.add_argument('--start',required=True);p.add_argument('--end',required=True);p.add_argument('--output',type=Path,required=True)
    p=commands.add_parser('replay');p.add_argument('--report',type=Path,required=True);p.add_argument('--write',action='store_true')
    args=parser.parse_args()
    try:
        session=get_settings().waha_session
        if args.command=='scan':
            start,end=epoch(args.start),epoch(args.end)
            rows=scan_interval(start,end,waha.api)
            report={'format':1,'session':session,'gateway_sha256':gateway_identity(),'start':start,'end':end,'messages':rows}
            report['sha256']=hashlib.sha256(encoded(report).encode()).hexdigest()
            private_json(args.output,report)
            result={'scanned':len(rows),'sha256':report['sha256']}
        else:
            report=json.loads(args.report.read_text())
            digest=report.pop('sha256')
            if hashlib.sha256(encoded(report).encode()).hexdigest()!=digest or report['session']!=session or report['gateway_sha256']!=gateway_identity() or report['format']!=1:
                raise ValueError('Scan identity or integrity does not match.')
            result=reconcile_messages(report['messages'],session,args.write)
            if args.write:
                complete_reconciliation(report['messages'],session,report['start'],report['end'],get_settings().database_migration_url)
        print(encoded(result))
    except (ValueError,KeyError,TypeError,OSError,requests.RequestException,store.StateUnavailable):
        parser.exit(1,'History reconciliation refused or failed; maintain intake mode and inspect private evidence. No message content is printed.\n')


if __name__=='__main__':
    main()
