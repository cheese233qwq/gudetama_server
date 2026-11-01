"""Replaceable NON-OFFICIAL rules. All dynamic formulas are local designs."""
import hashlib
import json
import secrets
from pathlib import Path

DEFAULTS = dict(version=1, recipe_ids=[1], gudetama_ids=[6,7,8,58,199,204], seconds_per_minute=60,
                refund="full_before_claim", currency="free_gp_only", extra_rewards=False)


class Rules:
    def __init__(self, settings=None, random_below=None):
        s = self.settings = dict(DEFAULTS if settings is None else settings)
        if set(s) != set(DEFAULTS) or s["version"] != 1 or s["refund"] != "full_before_claim" or s["currency"] != "free_gp_only" or s["extra_rewards"] is not False:
            raise ValueError("unsupported local rules")
        if type(s["seconds_per_minute"]) is not int or not 1 <= s["seconds_per_minute"] <= 3600:
            raise ValueError("invalid local duration scale")
        for key in ("recipe_ids", "gudetama_ids"):
            if not isinstance(s[key], list) or not s[key] or any(type(i) is not int or i <= 0 for i in s[key]):
                raise ValueError("invalid rule ID allowlist")
        self.json = json.dumps(s,sort_keys=True,separators=(",", ":"))
        self.digest = hashlib.sha256(self.json.encode()).hexdigest()
        self.random_below = random_below or secrets.randbelow

    @classmethod
    def load(cls,path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8-sig")))

    @classmethod
    def current(cls,definition):
        """Use current recipe definitions, without an operator-maintained allowlist.

        Keep the settings shape for existing run snapshots and save compatibility.
        Actual ownership and progression are still checked when starting cooking.
        """
        from .recipe_progression import ordinary_ids
        recipes=list(ordinary_ids(definition))
        characters=sorted({gid for rid in recipes for gid in
                           definition.recipeNoteMap[rid].defaults.value+definition.recipeNoteMap[rid].appends.value})
        return cls(dict(DEFAULTS,recipe_ids=recipes,gudetama_ids=characters))

    def extends(self, old):
        """Only adding eligible recipes/characters preserves old run snapshots.

        Timer, costs, refunds, probability interpretation and recipe policy must
        remain identical. Old snapshots are never rewritten.
        """
        return (all(self.settings[k] == old.settings[k] for k in self.settings if k not in ('gudetama_ids','recipe_ids'))
                and all(set(old.settings[k]) <= set(self.settings[k]) for k in ('recipe_ids','gudetama_ids')))

    def candidates(self,d,rd,gd):
        parts = [(x.type,x.percent) for x in gd.roulettes.value]
        if not parts or sum(w for t,w in parts) != 100 or any(t not in (0,1,2) or w <= 0 for t,w in parts):
            raise ValueError("unsupported static roulette segments")
        for t,w in parts:
            ids = [gd.id] if t == 0 else (rd.happeningIds.value if t == 1 else rd.failureIds.value)
            if not ids or any(i not in d.gudetamaMap or d.gudetamaMap[i].reward < 0 for i in ids):
                raise ValueError("missing configured outcome")
        return parts

    def qualify(self,p,d,rid,gid,target,*,allow_event=False):
        if (not allow_event and (rid not in self.settings["recipe_ids"] or gid not in self.settings["gudetama_ids"])) or target != 0:
            raise ValueError("outside local recipe/character/target policy")
        rd,gd = d.recipeNoteMap.get(rid),d.gudetamaMap.get(gid)
        if not rd or not gd or (rd.eventId and not allow_event) or gid not in rd.defaults.value + rd.appends.value:
            raise ValueError("invalid static candidate")
        kd = d.kitchenwareMap[rd.kitchenwareId]
        k = p.kitchenwareMap.get(kd.type)
        param = k.paramMap.get(kd.id) if k else None
        note,role = p.recipeNoteMap.get(rid),p.gudetamaMap.get(gid)
        if kd.type not in ((0,1,2,3,4) if allow_event else (0,1,2,3)) or not param or not param.available or not note or not (note.visible and note.available and note.purchased) or not role or not (role.available and role.unlocked):
            raise ValueError("kitchen/recipe/role not owned and eligible")
        if any(a.ability.type not in (256,257,261) for a in p.userAbilities.value):
            raise ValueError("ability modifiers not supported")
        duration = rd.minutes * self.settings["seconds_per_minute"]
        if type(duration) is not int or not 1 <= duration <= 2147483647 or gd.cost < 0:
            raise ValueError("invalid configured duration/cost")
        self.candidates(d,rd,gd)
        return k,gd.cost,duration

    def draw(self,d,rid,gid,*,parts=None):
        rd,gd = d.recipeNoteMap[rid],d.gudetamaMap[gid]
        roll,limit = self.random_below(100),0
        parts=self.candidates(d,rd,gd) if parts is None else parts
        for typ,weight in parts:
            limit += weight
            if roll < limit:
                ids = [gid] if typ == 0 else (rd.happeningIds.value if typ == 1 else rd.failureIds.value)
                outcome = ids[self.random_below(len(ids))]
                return roll,typ,outcome,d.gudetamaMap[outcome].reward
        raise ValueError("invalid local random source")
