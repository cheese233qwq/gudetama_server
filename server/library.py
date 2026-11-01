"""Import the archived library without installing or modifying it."""
import sys
from .paths import ROOT

LIBRARY = ROOT if (ROOT/'libgude/cdio.py').is_file() else ROOT / "libgude-main/libgude-main/src"
sys.dont_write_bytecode = True
sys.path.insert(0, str(LIBRARY))
from libgude import cdio as c  # noqa: E402


class SignedByte(c.Byte):
    """AIR readByte is signed; upstream Byte currently parses it unsigned."""
    @classmethod
    def parse_from(cls, buf):
        data = buf.read(1)
        if len(data) != 1:
            raise ValueError("truncated signed byte")
        return cls(int.from_bytes(data, "big", signed=True))

    def serialise_into(self, buf):
        buf.write(int(self.value).to_bytes(1, "big", signed=True))


# Only this confirmed signed sentinel field needs adaptation for the fixture.
# CupGachaData.as:35; UserDataWrapper.as:1805. No backup source is patched.
c.CupGachaData.__init__.__annotations__["cookIndex"] = SignedByte
# UserData.as:278/392 uses readByte/writeByte; -1 means a game avatar.
c.UserData.__init__.__annotations__["snsInterlockType"] = SignedByte
