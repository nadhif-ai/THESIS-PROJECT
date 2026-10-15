"""Explicit SQLite → PostgreSQL transfer. Reports contain hashes and counts only."""
import argparse
import hashlib
import json
import math
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from app.config.settings import get_settings

COLUMNS = {
    'settings': ('key','value'),
    'users': ('name','salt','password_hash'),
    'sessions': ('token_hash','expires','csrf'),
    'versions': ('id','namespace','status','created_at','manifest','records','error'),
    'jobs': ('id','kind','status','payload','result','error','created_at','updated_at','progress'),
    'conversations': ('id','session_id','channel','question','answer','usage','latency','trace_id','created_at'),
    'whatsapp_inbox': ('session','message_id','sender','body','status','answer','media_url','reply_ids','error','created_at','updated_at'),
    'whatsapp_receipts': ('message_id','ack','updated_at'),
}
KEYS = {t: (cols[0],) for t,cols in COLUMNS.items()}
KEYS['whatsapp_inbox'] = ('session','message_id')
REAL = {('sessions','expires'),('conversations','latency')}
INTEGER = {('conversations','id'),('whatsapp_receipts','ack')}
JSON_FIELDS = {('settings','value'),('versions','manifest'),('versions','records'),('jobs','payload'),
               ('jobs','result'),('jobs','progress'),('conversations','usage'),('whatsapp_inbox','reply_ids')}


def encoded(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False)


def checksum(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def private_json(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    path.parent.chmod(0o700)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as stream:
        stream.write(encoded(value)+'\n')


@contextmanager
def source_db(path):
    path=Path(path).resolve(strict=True)
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
        yield db


def snapshot(source, output):
    source,output=Path(source).resolve(strict=True),Path(output).resolve()
    if source==output:
        raise ValueError('Snapshot must use a new destination.')
    output.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    output.parent.chmod(0o700)
    os.close(os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600))
    with source_db(source) as original, sqlite3.connect(output) as copy:
        original.backup(copy)
        if copy.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise ValueError('SQLite snapshot integrity failed.')
    result={'format':1,'snapshot_sha256':checksum(output)}
    private_json(output.with_suffix(output.suffix+'.manifest.json'),result)
    return result


def source_columns(db):
    names={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    if names!=set(COLUMNS):
        raise ValueError('Unexpected or missing source tables.')
    observed={}
    for table, columns in COLUMNS.items():
        info=db.execute(f'PRAGMA table_info("{table}")').fetchall()
        observed[table]=[r[1] for r in info]
        legacy=table=='jobs' and set(observed[table])==set(columns)-{'progress'}
        if set(observed[table])!=set(columns) and not legacy:
            raise ValueError(f'Unexpected source columns: {table}.')
        primary=tuple(r[1] for r in sorted(info,key=lambda r:r[5]) if r[5])
        if primary!=KEYS[table]:
            raise ValueError(f'Unexpected primary keys: {table}.')
    return observed


def rows(db, table, dialect, observed=None):
    columns=COLUMNS[table]
    if dialect=='sqlite':
        selections=[f'"{c}"' if c in observed[table] else "'{}' AS progress" for c in columns]
        query='SELECT '+','.join(selections)+f' FROM "{table}" ORDER BY '+','.join(KEYS[table])
        return db.execute(query).fetchall()
    query=sql.SQL('SELECT {} FROM chatbot.{} ORDER BY {}').format(
        sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(table),
        sql.SQL(',').join(map(sql.Identifier,KEYS[table])))
    return db.execute(query).fetchall()


def cell(table,column,value):
    if value is None:
        return ['null']
    if (table,column) in REAL:
        if isinstance(value,(bool,str,bytes)) or not math.isfinite(value):
            raise ValueError(f'Invalid numeric source: {table}.{column}.')
        return ['float',float(value).hex()]
    if (table,column) in INTEGER:
        if type(value)!=int:
            raise ValueError(f'Invalid integer source: {table}.{column}.')
        return ['integer',value]
    if not isinstance(value,str):
        raise ValueError(f'Invalid text source: {table}.{column}.')
    if (table,column) in JSON_FIELDS:
        try:
            json.loads(value,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
        except (ValueError,TypeError):
            raise ValueError(f'Invalid JSON source: {table}.{column}.') from None
    return ['text',value]


def content_manifest(connection, dialect):
    observed=source_columns(connection) if dialect=='sqlite' else None
    tables={}
    selection=None
    published=[]
    namespaces=set()
    for table,columns in COLUMNS.items():
        digest=hashlib.sha256()
        seen=set()
        data=rows(connection,table,dialect,observed)
        for row in data:
            item=dict(zip(columns,row))
            key=tuple(item[k] for k in KEYS[table])
            if any(v is None or v=='' for v in key) or key in seen:
                raise ValueError(f'Invalid source primary key: {table}.')
            seen.add(key)
            if table=='whatsapp_receipts' and (type(item['ack'])!=int or not -1<=item['ack']<=4):
                raise ValueError('Invalid acknowledgement source.')
            if table=='jobs' and item['progress'] is None:
                raise ValueError('Missing job progress in current schema.')
            typed=[cell(table,c,v) for c,v in zip(columns,row)]
            digest.update((encoded(typed)+'\n').encode())
            if table=='settings' and item['key']=='published_version':
                selection=json.loads(item['value'])
            if table=='versions':
                namespace=item['namespace']
                if not namespace or namespace in namespaces:
                    raise ValueError('Invalid knowledge namespace selection.')
                namespaces.add(namespace)
                if item['status']=='published':
                    published.append(item['id'])
        tables[table]={'columns':list(columns),'keys':list(KEYS[table]),'count':len(data),'sha256':digest.hexdigest()}
    if not isinstance(selection,str) or published!=[selection]:
        raise ValueError('Published selection does not match source content.')
    return {'format':1,'tables':tables}


def inspect_source(snapshot_path):
    with source_db(snapshot_path) as db:
        return content_manifest(db,'sqlite')


def validate_identity(dsn, expected_project):
    opts=conninfo_to_dict(dsn)
    host=opts.get('host','')
    if expected_project=='local-rehearsal':
        if host not in ('127.0.0.1','localhost','::1') or not opts.get('dbname','').startswith('chatbot_test_'):
            raise ValueError('Local rehearsal identity mismatch.')
    elif (host!=f'db.{expected_project}.supabase.co' and
          not (host.endswith('.pooler.supabase.com') and opts.get('user')==f'postgres.{expected_project}')):
        raise ValueError('Supabase project identity mismatch.')


@contextmanager
def admin_db(dsn):
    opts=conninfo_to_dict(dsn)
    local=opts.get('host') in ('127.0.0.1','localhost','::1')
    with psycopg.connect(dsn,sslmode='disable' if local else 'require',connect_timeout=10,prepare_threshold=None) as db:
        db.execute("SET LOCAL statement_timeout='60s'")
        db.execute("SET LOCAL lock_timeout='5s'")
        yield db


def control_row(db):
    if db.execute('SELECT version FROM chatbot.schema_migrations ORDER BY version').fetchall()!=[(1,)]:
        raise ValueError('Unexpected administration schema version.')
    row=db.execute('SELECT mode,cutover_started_at,first_live_write_at FROM chatbot.runtime_control WHERE id=1 FOR UPDATE').fetchone()
    if not row:
        raise ValueError('Missing runtime control.')
    return row


def import_snapshot(snapshot_path, admin_dsn, expected_project):
    validate_identity(admin_dsn,expected_project)
    manifest=inspect_source(snapshot_path)
    digest=checksum(snapshot_path)
    with admin_db(admin_dsn) as db:
        control=control_row(db)
        existing=db.execute('SELECT snapshot_sha256,manifest FROM chatbot.state_imports').fetchall()
        if existing:
            if len(existing)!=1 or existing[0][0]!=digest or json.loads(existing[0][1])['source']!=manifest:
                raise ValueError('A different state import already exists.')
            return {'status':'already-imported','snapshot_sha256':digest}
        if control[0]!='closed':
            raise ValueError('Import requires closed maintenance mode.')
        if any(db.execute(sql.SQL('SELECT EXISTS(SELECT 1 FROM chatbot.{})').format(sql.Identifier(t))).fetchone()[0] for t in COLUMNS):
            raise ValueError('Destination business tables must be empty.')
        with source_db(snapshot_path) as original:
            observed=source_columns(original)
            for table,columns in COLUMNS.items():
                query=sql.SQL('INSERT INTO chatbot.{} ({}) VALUES ({})').format(sql.Identifier(table),
                    sql.SQL(',').join(map(sql.Identifier,columns)),sql.SQL(',').join(sql.Placeholder() for _ in columns))
                with db.cursor() as cursor:
                    cursor.executemany(query,rows(original,table,'sqlite',observed))
        if content_manifest(db,'postgres')!=manifest:
            raise ValueError('Imported content verification failed.')
        db.execute("SELECT setval(pg_get_serial_sequence('chatbot.conversations','id'),COALESCE(MAX(id),1),MAX(id) IS NOT NULL) FROM chatbot.conversations")
        db.execute('INSERT INTO chatbot.state_imports VALUES (%s,%s,%s)',
                   (digest,encoded({'source':manifest,'verified':True}),datetime.now(timezone.utc).isoformat()))
    return {'status':'imported','snapshot_sha256':digest,'counts':{t:m['count'] for t,m in manifest['tables'].items()}}


def verify_snapshot(snapshot_path, admin_dsn):
    expected=inspect_source(snapshot_path)
    with admin_db(admin_dsn) as db:
        control_row(db)
        if expected!=content_manifest(db,'postgres'):
            raise ValueError('Source and destination content differ.')
        ledger=db.execute('SELECT manifest FROM chatbot.state_imports WHERE snapshot_sha256=%s',(checksum(snapshot_path),)).fetchone()
        if not ledger or json.loads(ledger[0])['source']!=expected:
            raise ValueError('Source import ledger does not match content.')
    return {'verified':True,'snapshot_sha256':checksum(snapshot_path),'counts':{t:m['count'] for t,m in expected['tables'].items()}}


def set_runtime_mode(mode, admin_dsn):
    if mode not in ('closed','intake','live'):
        raise ValueError('Invalid runtime mode.')
    with admin_db(admin_dsn) as db:
        current,started,first=control_row(db)
        if current==mode:
            return
        ledger=db.execute('SELECT snapshot_sha256,manifest FROM chatbot.state_imports').fetchall()
        if mode!='closed':
            if len(ledger)!=1 or not json.loads(ledger[0][1]).get('verified'):
                raise ValueError('Verified state import is required.')
            metadata=json.loads(ledger[0][1])
            if not first and content_manifest(db,'postgres')!=metadata['source']:
                raise ValueError('Verified import content has changed.')
            if mode=='live':
                receipt=metadata.get('reconciliation',{})
                if current!='intake' or not started or receipt.get('snapshot_sha256')!=ledger[0][0] or not receipt.get('complete'):
                    raise ValueError('Completed reconciliation is required before live mode.')
                if receipt.get('start',float('inf'))>datetime.fromisoformat(started).timestamp() or receipt.get('end',0)<datetime.fromisoformat(started).timestamp():
                    raise ValueError('Reconciliation watermarks do not cover cutover.')
        if mode!='live' and ledger:
            metadata=json.loads(ledger[0][1]);metadata.pop('reconciliation',None)
            db.execute('UPDATE chatbot.state_imports SET manifest=%s WHERE snapshot_sha256=%s',(encoded(metadata),ledger[0][0]))
        db.execute('UPDATE chatbot.runtime_control SET mode=%s,cutover_started_at=COALESCE(cutover_started_at,%s) WHERE id=1',
                   (mode,datetime.now(timezone.utc).isoformat() if mode=='intake' else None))


def rollback_check(admin_dsn):
    with admin_db(admin_dsn) as db:
        _,_,first=control_row(db)
    return {'allowed':first is None,'reason':'No post-cutover business write recorded.' if first is None else 'New PostgreSQL state exists; retain maintenance and repair forward.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('snapshot');p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p=commands.add_parser('import');p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--expected-project',required=True)
    p=commands.add_parser('verify');p.add_argument('--snapshot',type=Path,required=True)
    p=commands.add_parser('control');p.add_argument('mode',choices=['closed','intake','live'])
    commands.add_parser('rollback-check')
    args=parser.parse_args()
    try:
        if args.command=='snapshot':
            result=snapshot(args.source,args.output)
        else:
            dsn=get_settings().database_migration_url
            if not dsn:
                raise ValueError('DATABASE_MIGRATION_URL is required.')
            if args.command=='import': result=import_snapshot(args.snapshot,dsn,args.expected_project)
            elif args.command=='verify': result=verify_snapshot(args.snapshot,dsn)
            elif args.command=='rollback-check': result=rollback_check(dsn)
            else:
                set_runtime_mode(args.mode,dsn);result={'mode':args.mode}
        print(encoded(result))
    except (ValueError,psycopg.Error,sqlite3.Error,OSError):
        parser.exit(1,'Migration command refused or failed; no credentials or source contents are printed. Check the target, mode and private evidence.\n')


if __name__=='__main__':
    main()
