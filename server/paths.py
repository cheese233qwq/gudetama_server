"""Runtime paths; release assets live in resources, legacy checkouts still work."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Do not mix two resource trees: an explicitly supplied resources directory wins.
RESOURCES = ROOT / ('resources' if (ROOT / 'resources').is_dir() else 'cdn-archive')
STATIC = RESOURCES / 'static'
APK = RESOURCES / 'apps/gudetama_tap_1.47.5.apk'


def validate_save_path(value):
    """Accept release saves and existing development saves without moving either."""
    path = Path(value).resolve()
    legacy = (ROOT / 'server/state').resolve()
    if (path == legacy / 'accounts.sqlite3'
            or not any(path.is_relative_to(base.resolve()) and path != base.resolve()
                       for base in (ROOT / 'save', legacy))):
        raise ValueError('save must be under save/ or the existing development save directory')
    return path
