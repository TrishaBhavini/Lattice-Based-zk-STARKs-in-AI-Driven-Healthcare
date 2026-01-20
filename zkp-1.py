import os
import json
import hashlib
import numpy as np

from tensorflow.keras.models import model_from_json

from merkle import SimpleMerkleTree
from utils import load_image_vector, preprocess_for_model
from mlwe import mlwe_commit
from rlwe import rlwe_hash
from lattice import sis_commitment
from metrics import run_all_metrics


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

DATASET_DIR = "data/images"
MODEL_JSON_PATH = "models/model.json"
MODEL_WEIGHTS_PATH = "models/model.h5"
CAIRO_INPUT_PATH = "cairo/src/input.json"


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def to_u64(x: int) -> int:
    return x % (2**64)


def hash_to_u64(data: bytes) -> int:
    digest = hashlib.sha256(data).digest()
    return int.from_bytes(digest, "big") % (2**64)


def to_cairo_felt(value: int) -> str:
    return hex(value)


# ---------------------------------------------------------------------
# Load model
# ---------------------------------------------------------------------

with open(MODEL_JSON_PATH, "r") as f:
    model = model_from_json(f.read())

model.load_weights(MODEL_WEIGHTS_PATH)


# ---------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------

all_leaves = []
images_data = []

for image_name in sorted(os.listdir(DATASET_DIR)):
    image_path = os.path.join(DATASET_DIR, image_name)

    # Inference
    model_input = preprocess_for_model(image_path)
    prediction = model.predict(model_input, verbose=0).flatten()

    # Image commitment (SIS-style)
    image_vector = load_image_vector(image_path)
    Cm = to_u64(int(sis_commitment(image_vector)["commitment"], 16))

    # Diagnosis commitment
    Cd = hash_to_u64(prediction.tobytes())

    # MLWE-style commitment
    mlwe_data = mlwe_commit(prediction.astype(int))
    B_hash = hash_to_u64(str(mlwe_data["hash"]).encode())

    # RLWE-style challenge
    c = to_u64(int(rlwe_hash(mlwe_data["B"], prediction.astype(int))))

    # Response value
    z = to_u64(int((prediction.astype(int) - c * prediction.astype(int))[0]))

    all_leaves.extend([Cm, Cd, B_hash, c, z])

    images_data.append({
        "image": image_name,
        "Cm": Cm,
        "Cd": Cd,
        "B_hash": B_hash,
        "c": c,
        "z": z
    })


# ---------------------------------------------------------------------
# Merkle tree construction
# ---------------------------------------------------------------------

tree = SimpleMerkleTree(all_leaves)
root = tree.root()


# ---------------------------------------------------------------------
# Proof generation and verification
# ---------------------------------------------------------------------

leaf_index = 0
leaf_value = all_leaves[leaf_index]
path, indices = tree.get_proof(leaf_index)

assert tree.verify_proof(leaf_value, path, indices, root)


# ---------------------------------------------------------------------
# Cairo input generation
# ---------------------------------------------------------------------

cairo_args = []

cairo_args.append(to_cairo_felt(leaf_value))

cairo_args.append(to_cairo_felt(len(path)))
cairo_args.extend(to_cairo_felt(p) for p in path)

cairo_args.append(to_cairo_felt(len(indices)))
cairo_args.extend(to_cairo_felt(i) for i in indices)

cairo_args.append(to_cairo_felt(root))

with open(CAIRO_INPUT_PATH, "w") as f:
    json.dump(cairo_args, f, indent=2)


# ---------------------------------------------------------------------
# Metadata export
# ---------------------------------------------------------------------

metadata_path = CAIRO_INPUT_PATH.replace("input.json", "metadata.json")

with open(metadata_path, "w") as f:
    json.dump({
        "num_images": len(images_data),
        "total_leaves": len(all_leaves),
        "tree_depth": len(tree.levels) - 1,
        "merkle_root": root,
        "proof_leaf_index": leaf_index,
        "proof_path_length": len(path)
    }, f, indent=2)


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------

run_all_metrics(all_leaves)
