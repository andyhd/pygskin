import binascii
import struct
from base64 import b64decode
from base64 import b64encode


def rhash(n: int) -> str:
    """Reversibly hash a number to a 6 character string."""
    return b64encode(struct.pack("<q", n * 387420469 % 1000000000)).decode("ascii")[:6]


def unrhash(h: str) -> int:
    """Unhash a 6 character string to a number."""
    try:
        return struct.unpack("<q", b64decode(h + "AAAAA="))[0] * 703225629 % 1000000000
    except (struct.error, binascii.Error) as e:
        raise ValueError("Invalid hash") from e

