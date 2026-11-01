"""Wire framing derived from HttpConnector/Packet/AESEncryptor.as."""
import base64
import io
import secrets
import struct
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from .library import c

MAX_WIRE_BYTES = 1024 * 1024


def encode(value):
    return c.Object(value).serialised()


def decode(data, max_bytes=MAX_WIRE_BYTES):
    if len(data) > max_bytes:
        raise ValueError("protocol object too large")
    buf = io.BytesIO(data)
    obj = c.Object.parse_from(buf).value
    if buf.tell() != len(data):
        raise ValueError("trailing protocol bytes")
    return obj


def encrypt(data, key, iv=None):
    if len(key) != 16:
        raise ValueError("AES-128 requires a 16-byte key")
    iv = secrets.token_bytes(16) if iv is None else iv
    if len(iv) != 16:
        raise ValueError("IV must be 16 bytes")
    padder = padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return enc.update(padded) + enc.finalize() + iv


def decrypt(data, key):
    if len(key) != 16 or len(data) < 32 or len(data) % 16:
        raise ValueError("invalid AES frame")
    dec = Cipher(algorithms.AES(key), modes.CBC(data[-16:])).decryptor()
    padded = dec.update(data[:-16]) + dec.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def request_packet(encoded, key):
    raw = base64.b64decode(encoded, validate=True)
    try:
        packet = decode(decrypt(raw, key))
    except Exception as error:
        raise ValueError("invalid encrypted Packet structure") from error
    if not isinstance(packet, c.Packet):
        raise ValueError("expected Packet type ID 14")
    if not 0 <= packet.sequence <= 255:
        raise ValueError("sequence outside client's 8-bit counter")
    return packet


def plaintext_response(value):
    # 0 is a local choice from the client's nonnegative, unencrypted branch.
    # It is not claimed to be an observed original server status.
    return b"\x00" + encode(value)


def main_response(value, sequence, key, extra=None):
    body = bytes([sequence]) + encode(value)
    if extra is not None:
        body += encode(extra)
    return b"\x40" + encrypt(body, key)


def reject(message):
    # HttpConnector.as:808-816: signed status -8 followed by readUTF().
    text = message.encode("utf-8")[:60000]
    return b"\xf8" + struct.pack(">H", len(text)) + text
