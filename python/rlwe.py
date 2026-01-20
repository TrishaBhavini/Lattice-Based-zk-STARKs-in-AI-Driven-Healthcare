import hashlib

def rlwe_hash(B, delta):
    h = hashlib.sha256(
        str(B).encode() + str(delta).encode()
    ).digest()
    return int.from_bytes(h, "big") % 12289
