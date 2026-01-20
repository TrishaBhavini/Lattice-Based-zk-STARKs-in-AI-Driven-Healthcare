import os
import hashlib
import json
import numpy as np

from tensorflow.keras.models import model_from_json

from merkle import SimpleMerkleTree
from utils import load_image_vector, preprocess_for_model
from mlwe import mlwe_commit
from rlwe import rlwe_hash
from lattice import sis_commitment
from metrics import run_all_metrics

# =============================================================================
# CONFIG
# =============================================================================

DATASET = "/Users/rajivsingh/10Jan26_LatticeBasedUpdate/Brain-Tumor-Data"
MODEL_JSON = "/Users/rajivsingh/10Jan26_LatticeBasedUpdate/model.json"
MODEL_H5 = "/Users/rajivsingh/10Jan26_LatticeBasedUpdate/model.h5"
OUTPUT_PATH = "/Users/rajivsingh/10Jan26_LatticeBasedUpdate/cairo/src/input.json"


# =============================================================================
# HELPERS
# =============================================================================

def to_u64(x: int) -> int:
    """Convert arbitrary int to Cairo u64 by modulo 2^64"""
    return x % (2**64)


def hash_to_u64(data: bytes) -> int:
    """Convert SHA256 hash to u64"""
    h = hashlib.sha256(data).hexdigest()
    return int(h, 16) % (2**64)


def to_cairo_felt(value: int) -> str:
    """Convert integer to Cairo felt252 hex string format"""
    return hex(value)


# =============================================================================
# LOAD MODEL
# =============================================================================

print("Loading model...")
with open(MODEL_JSON) as f:
    model = model_from_json(f.read())

model.load_weights(MODEL_H5)


# =============================================================================
# PIPELINE
# =============================================================================

all_leaves = []     # Holds all Merkle leaves
images_data = []   # Stores per-image metadata

print("\nRunning inference + commitments...")

for img_name in sorted(os.listdir(DATASET)):
    img_path = os.path.join(DATASET, img_name)
    print(f"  Processing: {img_name}")

    # -------------------------------------------------------------------------
    # 1. Inference
    # -------------------------------------------------------------------------
    inp = preprocess_for_model(img_path)
    preds = model.predict(inp, verbose=0)
    delta = preds.flatten()

    # -------------------------------------------------------------------------
    # 2. SIS commitment (image commitment)
    # -------------------------------------------------------------------------
    image_vec = load_image_vector(img_path)
    Cm = to_u64(int(sis_commitment(image_vec)["commitment"], 16))

    # -------------------------------------------------------------------------
    # 3. Diagnosis commitment
    # -------------------------------------------------------------------------
    Cd = hash_to_u64(delta.tobytes())

    # -------------------------------------------------------------------------
    # 4. MLWE commitment
    # -------------------------------------------------------------------------
    mlwe = mlwe_commit(delta.astype(int))
    B_hash = hash_to_u64(str(mlwe["hash"]).encode())

    # -------------------------------------------------------------------------
    # 5. RLWE challenge
    # -------------------------------------------------------------------------
    c = to_u64(int(rlwe_hash(mlwe["B"], delta.astype(int))))

    # -------------------------------------------------------------------------
    # 6. Response
    # -------------------------------------------------------------------------
    z = to_u64(int((delta.astype(int) - c * delta.astype(int))[0]))

    # -------------------------------------------------------------------------
    # Collect Merkle leaves (NO hashing)
    # -------------------------------------------------------------------------
    all_leaves.extend([Cm, Cd, B_hash, c, z])

    images_data.append({
        "image": img_name,
        "Cm": Cm,
        "Cd": Cd,
        "B_hash": B_hash,
        "c": c,
        "z": z
    })


print(f"\n✓ Processed {len(images_data)} images")
print(f"✓ Total leaves: {len(all_leaves)} (5 per image)")


# =============================================================================
# BUILD SIMPLE MERKLE TREE
# =============================================================================

print("\nBuilding simple Merkle tree (addition-based)...")
tree = SimpleMerkleTree(all_leaves)
root = tree.root()

print(f"  Tree depth: {len(tree.levels) - 1}")
print(f"  Root: {root} (0x{root:x})")


# =============================================================================
# GENERATE PROOF
# =============================================================================

leaf_index = 0
leaf_value = all_leaves[leaf_index]
path, indices = tree.get_proof(leaf_index)

print(f"\nGenerating proof for leaf[{leaf_index}]...")
print(f"  Leaf value: {leaf_value} (0x{leaf_value:x})")
print(f"  Path length: {len(path)}")
print(f"  Indices: {indices}")

is_valid = tree.verify_proof(leaf_value, path, indices, root)
print(f"  Python verification: {'✓ VALID' if is_valid else '✗ INVALID'}")

if not is_valid:
    print("\n✗ ERROR: Proof verification failed in Python!")
    exit(1)


# =============================================================================
# GENERATE CAIRO INPUT
# =============================================================================

print("\nGenerating Cairo input (flat array format)...")

cairo_args = []

# leaf
cairo_args.append(to_cairo_felt(leaf_value))

# path
cairo_args.append(to_cairo_felt(len(path)))
cairo_args.extend([to_cairo_felt(p) for p in path])

# indices
cairo_args.append(to_cairo_felt(len(indices)))
cairo_args.extend([to_cairo_felt(i) for i in indices])

# expected root
cairo_args.append(to_cairo_felt(root))

with open(OUTPUT_PATH, "w") as f:
    json.dump(cairo_args, f, indent=2)

print(f"✓ Cairo input written to: {OUTPUT_PATH}")
print(f"  Total arguments: {len(cairo_args)}")


# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("PIPELINE COMPLETE")
print("=" * 80)
print(f"Images processed: {len(images_data)}")
print(f"Total leaves: {len(all_leaves)}")
print(f"Merkle root: {root}")
print(f"Proof generated for: {images_data[leaf_index // 5]['image']}")
print(f"Commitment type: {['SIS', 'Diag', 'MLWE', 'RLWE', 'Response'][leaf_index % 5]}")

print("\nRUN WITH CAIRO:")
print("=" * 80)
print("cd /Users/rajivsingh/10Jan26_LatticeBasedUpdate/cairo")
print("scarb execute --executable-name ml_stark_prover_exe "
      "--arguments-file src/input.json --print-program-output")
print("Expected output: 0x1")
print("=" * 80)


# =============================================================================
# SAVE METADATA
# =============================================================================

metadata_path = OUTPUT_PATH.replace("input.json", "metadata.json")

with open(metadata_path, "w") as f:
    json.dump({
        "images": images_data,
        "tree_depth": len(tree.levels) - 1,
        "total_leaves": len(all_leaves),
        "merkle_root": root,
        "proof_for_leaf": leaf_index,
        "proof_path_length": len(path)
    }, f, indent=2)

print(f"\n✓ Metadata saved to: {metadata_path}")

print("\n=== METRICS ===")

run_all_metrics(all_leaves)