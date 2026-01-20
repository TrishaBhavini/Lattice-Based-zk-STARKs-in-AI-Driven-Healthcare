import numpy as np
import hashlib

Q = 12289

def mlwe_commit(delta):
    n = len(delta)
    A = np.random.randint(0, Q, size=(n, n))
    s = np.random.randint(0, Q, size=n)
    e = np.random.randint(-1, 2, size=n)

    B = (A @ s + e + delta) % Q
    B_hash = hashlib.sha256(B.tobytes()).hexdigest()

    return {
        "A": A.tolist(),
        "s": s.tolist(),
        "e": e.tolist(),
        "delta": delta.tolist(),
        "B": B.tolist(),
        "hash": B_hash
    }
