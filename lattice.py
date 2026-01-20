import numpy as np
import hashlib

Q = 12289

def sis_commitment(x: np.ndarray):
    n = x.shape[0]
    A = np.random.randint(0, Q, size=(n, n))
    e = np.random.randint(-1, 2, size=n)
    y = (A @ x + e) % Q
    h = hashlib.sha256(y.tobytes()).hexdigest()
    return {
        "A": A.tolist(),
        "x": x.tolist(),
        "e": e.tolist(),
        "commitment": h
    }
