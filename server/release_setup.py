"""Validate operator-supplied assets and create a NEW empty local database."""
import argparse
import os
import uuid
from pathlib import Path
from .library import ROOT


def initialize(config):
    from .configuration import Configuration,STATIC
    from .state import Accounts
    from .local_cooking import initialize_database,validate_database
    from .local_cooking_rules import Rules
    from .connection import read_server_config
    selected=read_server_config(Path(config),require_state=False)
    state=Path(selected['state'])
    # Client-bundled layouts and the admin icon are only used on demand.
    # Their absence must not prevent initializing the server or existing saves.
    required=[STATIC/'rsrc/atlas/event0.xml']
    required += [STATIC/f'setting/setting.dat.{suffix}6045.34' for suffix in ('','en.','cn.','ko.','tw.')]
    missing=[str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    if missing:raise ValueError('Missing required resources:\n  '+'\n  '.join(missing))
    # Validate complete configuration round trips before creating any save.
    definition=Configuration(selected['origin']+'/gde/static/',local_shop=True).definitions['ja']
    rules=Rules.current(definition)
    created=False
    if not state.exists():
        state.parent.mkdir(parents=True,exist_ok=True)
        temporary=state.with_name(state.name+'.setup-'+uuid.uuid4().hex)
        accounts=Accounts(temporary)
        try:
            initialize_database(accounts.db,rules)
            accounts.db.execute('CREATE TABLE tutorial_test_metadata(name TEXT PRIMARY KEY,value TEXT NOT NULL)')
            accounts.db.execute("INSERT INTO tutorial_test_metadata VALUES('enabled','1')")
            accounts.db.commit()
            accounts.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        finally:accounts.close()
        # Windows rename is atomic and refuses an existing destination; unlike
        # hard links it also works in restricted Windows folders/on exFAT.
        # POSIX rename can overwrite, so retain exclusive link publication there.
        try:
            if os.name=='nt':os.rename(temporary,state)
            else:os.link(temporary,state)
        finally:
            if temporary.exists():temporary.unlink()
        created=True
    selected=read_server_config(Path(config))
    validate_database(state,rules)
    print('Setup complete. '+('Created an empty database; no accounts or currency granted.' if created else 'Existing marked database retained.'))
    print('Client endpoint: '+selected['origin'])
    return created


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,default=ROOT/'server_config.json')
    args=parser.parse_args()
    try:initialize(args.config)
    except (ValueError,OSError) as error:parser.exit(1,str(error)+'\n')


if __name__=='__main__':main()
