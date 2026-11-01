"""Local manual-stop policy. Official slip/anti-cheat algorithms UNKNOWN.

UtensilDef.TIMING_PLATE=3; archived description enables timing control.
RouletteDialog consumes negative autoStopPercent as manual mode.
"""


def ensure(db):
    db.execute('''CREATE TABLE IF NOT EXISTS cooking_roulette_control(
        run_id TEXT PRIMARY KEY REFERENCES cooking_runs(run_id),
        manual INTEGER NOT NULL CHECK(manual IN (0,1)))''')


def owns_plate(player):
    plate=player.utensilMap.get(3)
    return bool(plate and plate.acquired and player.noticeFlagData.tutorialProgress>=7)


def configure(db,player,run):
    row=db.execute('SELECT manual FROM cooking_roulette_control WHERE run_id=?',(run['run_id'],)).fetchone()
    # Ownership may change before spinning, never switch a spinning run's mode.
    if row is None or run['status']=='roulette':
        value=int(owns_plate(player)) if run['status']=='roulette' else 0
        db.execute('INSERT OR REPLACE INTO cooking_roulette_control VALUES(?,?)',(run['run_id'],value))
        return bool(value)
    return bool(row[0])


def manual(db,run):
    row=db.execute('SELECT manual FROM cooking_roulette_control WHERE run_id=?',(run,)).fetchone()
    return bool(row and row[0])


def validate(db,player,run,percent):
    if run['status'] not in ('spinning','resolved') or not 0<=percent<100:
        raise ValueError('invalid authoritative percent/state')
    if run['status']=='resolved' or not manual(db,run['run_id']):
        if percent!=run['percent']:raise ValueError('invalid authoritative percent/state')
    elif not owns_plate(player):
        raise ValueError('manual roulette requires owned timing plate')
