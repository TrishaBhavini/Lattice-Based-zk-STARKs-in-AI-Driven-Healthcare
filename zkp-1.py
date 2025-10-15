#!/usr/bin/env python3
"""
zkp_pipeline_commitments.py

algorithm: generates commitments for each image and diagnosis using the
Prover construction (Rm = A*s + e mod q + Merkle over diagnosis commitments), then
generates ZK-like proofs only for positive cases. Also supports batch proofs
(using commitments) and plots Sequential vs Batch timings.

"""

import os
import csv
import time
import hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2
import random
from typing import List, Any
from PIL import Image
from tensorflow.keras.models import model_from_json
from tensorflow.keras.applications.vgg16 import preprocess_input
from tensorflow.keras.preprocessing import image as kimage
import argparse

# ------------------ Utilities ------------------
def bytes_hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def hash_of_obj(obj: Any) -> str:
    """Deterministic hash for arrays/strings/lists"""
    if isinstance(obj, np.ndarray):
        return bytes_hash(obj.tobytes())
    if isinstance(obj, (bytes, bytearray)):
        return bytes_hash(bytes(obj))
    if isinstance(obj, (list, tuple)):
        h = hashlib.sha256()
        for el in obj:
            h.update(hash_of_obj(el).encode())
        return h.hexdigest()
    return bytes_hash(str(obj).encode())

def ring_lwe_hash(image_commitment_hex: str, diagnosis_commitment_hex: str) -> int:
    combined = (image_commitment_hex + diagnosis_commitment_hex).encode()
    return int(bytes_hash(combined), 16) % (10**5)

# ------------------ Merkle Tree ------------------
class MerkleTree:
    def __init__(self, leaves: List[Any]):
        if not leaves:
            raise ValueError("Leaves cannot be empty")
        self.leaf_hashes = [hash_of_obj(l) for l in leaves]
        self.levels = [self.leaf_hashes]
        self.build_tree()

    def build_tree(self):
        current = self.leaf_hashes
        while len(current) > 1:
            next_level = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else left
                combined = (left + right).encode()
                next_level.append(bytes_hash(combined))
            self.levels.append(next_level)
            current = next_level

    def root(self) -> str:
        return self.levels[-1][0] if self.levels else None

# ------------------ Prover  ------------------
class Prover:
    def __init__(self, image_vector: np.ndarray, diagnosis_commitments: List[str], A: np.ndarray, q: int):
        if A.shape[1] != image_vector.shape[0]:
            # allow if image_vector is concatenated multiple images: A must match columns
            if A.shape[1] != image_vector.shape[0]:
                raise ValueError("A matrix column count must equal secret vector length")
        self.q = q
        self.A = A.copy() % q

        # secret vector s (quantize floats -> 0..255)
        if np.issubdtype(image_vector.dtype, np.floating):
            s_int = np.round(image_vector * 255.0).astype(np.int64)
        else:
            s_int = image_vector.astype(np.int64)
        self.s = (s_int % q).reshape((-1,))

        # small noise vector e
        noise_bound = max(1, q // 1024)
        self.e = np.random.randint(-noise_bound, noise_bound + 1, size=A.shape[0])
        # SIS-like commitment Rm = A*s + e (mod q)
        self.Rm = (self.A.dot(self.s) + self.e) % q
        # image commitment is hash of Rm
        self.image_commitment = hash_of_obj(self.Rm)

        # diagnosis commitments (list of hex str)
        self.diagnosis_commitments = diagnosis_commitments
        self.merkle = MerkleTree(self.diagnosis_commitments)
        self.delta_X = self.merkle.root()

        # toy accumulator constants
        self.g = 3
        self.h = 5
        self.s_val = 7
        self.m_val = 11

        pre_hash_int = int(bytes_hash((self.image_commitment + self.delta_X).encode()), 16)
        self.D = (pre_hash_int * pow(self.g, self.s_val, q) * pow(self.h, self.m_val, q)) % q

    def generate_proof(self):
        c = ring_lwe_hash(self.image_commitment, self.delta_X)
        sj_values = {}
        delta_j_values = {}
        responses = {}
        for j in range(len(self.diagnosis_commitments)):
            sj = random.randrange(1, self.q)
            delta_j = random.randrange(1, self.q)
            sj_values[j] = int(sj)
            delta_j_values[j] = int(delta_j)
            z_j = (sj - (delta_j * c)) % self.q
            responses[f"z{j}"] = int(z_j)

        proof = {
            "image_commitment": self.image_commitment,
            "delta_X": self.delta_X,
            "D": int(self.D),
            "q": int(self.q),
            "challenge": int(c),
            "responses": responses,
            "sj_values": sj_values,
            "delta_j_values": delta_j_values,
            "num_diagnosis": len(self.diagnosis_commitments)
        }
        return proof

# ------------------ Verifier  ------------------
class Verifier:
    def __init__(self, proof: dict, g=3, h=5, s_val=7, m_val=11):
        self.proof = proof
        self.g = g
        self.h = h
        self.s_val = s_val
        self.m_val = m_val

    def verify(self) -> bool:
        q = int(self.proof["q"])
        recom_pre_hash_int = int(bytes_hash((self.proof["image_commitment"] + self.proof["delta_X"]).encode()), 16)
        recom_D = (recom_pre_hash_int * pow(self.g, self.s_val, q) * pow(self.h, self.m_val, q)) % q
        if recom_D != int(self.proof["D"]):
            # Accumulator mismatch
            return False
        c = ring_lwe_hash(self.proof["image_commitment"], self.proof["delta_X"])
        if c != int(self.proof["challenge"]):
            return False
        for k, z_val in self.proof["responses"].items():
            j = int(k[1:])
            sj = int(self.proof["sj_values"][j])
            delta_j = int(self.proof["delta_j_values"][j])
            expected = (sj - (delta_j * c)) % q
            if expected != int(z_val) % q:
                return False
        return True

# ------------------ Image helpers ------------------
VALID_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")
def is_image_file(name: str) -> bool:
    return name.lower().endswith(VALID_EXTS)

def image_to_vector(image_path: str, normalize=False, target_size=(16,16)) -> np.ndarray:
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Error loading image {image_path}")
    img = cv2.resize(img, target_size)
    if normalize:
        arr = img.astype(np.float32) / 255.0
    else:
        arr = img.astype(np.int64)
    return arr.flatten()

def preprocess_for_model(image_path: str, target_size=(224,224)):
    # using PIL for consistent behavior
    img = Image.open(image_path).convert("RGB").resize(target_size)
    arr = np.array(img).astype(np.float32)
    arr = np.expand_dims(arr, axis=0)
    arr = preprocess_input(arr)
    return arr

def is_positive(preds: np.ndarray) -> bool:
    preds = np.array(preds)
    if preds.ndim == 2 and preds.shape[1] == 1:
        score = float(preds.flatten()[0])
        return score >= 0.5
    elif preds.ndim == 2:
        idx = int(np.argmax(preds[0]))
        return idx == 1
    else:
        vals = preds.flatten()
        return np.any(vals > 0.5)

# ------------------ Main experiment (sequential + batch) ------------------
def run_pipeline(dataset_dir: str, model_json_path: str, model_h5_path: str,
                 sizes: List[int]=[8,16,32], runs_per_size:int=3, max_batch:int=6):
    # load model
    with open(model_json_path, "r") as f:
        model_json = f.read()
    model = model_from_json(model_json)
    model.load_weights(model_h5_path)
    print("✅ Model loaded successfully")

    # gather image files (sorted for reproducibility)
    all_files = sorted([f for f in os.listdir(dataset_dir) if is_image_file(f)])
    if not all_files:
        raise RuntimeError("No image files found in dataset folder")

    overall_seq_results = []
    batch_points = []

    for sz in sizes:
        print(f"\n--- Testing size {sz}x{sz} ---")
        n = sz * sz
        q = 12289
        # A must be (m x n). Use m = n for simplicity
        A = np.random.randint(0, q, size=(n, n), dtype=np.int64)

        seq_rows = []
        total_proof_time = 0.0
        total_verify_time = 0.0
        total_positives = 0
        total_images = 0

        # Sequential: process first N images repeatedly (runs_per_size times)
        for run in range(runs_per_size):
            for fname in all_files:
                img_path = os.path.join(dataset_dir, fname)
                total_images += 1

                # model inference (full-size)
                try:
                    model_input = preprocess_for_model(img_path)
                except Exception as e:
                    print(f"Skipping {fname}: cannot open ({e})")
                    continue
                preds = model.predict(model_input)

                # Build diagnosis commitments (model-derived)
                commit_pred = hash_of_obj(preds.flatten())
                commit_model = hash_of_obj(model_json)   # architecture fingerprint
                commit_logits = hash_of_obj(preds.flatten())
                diagnosis_commitments = [commit_pred, commit_model, commit_logits]

                # Build small secret vector for commitments (quantized image)
                s_vec = image_to_vector(img_path, normalize=True, target_size=(sz,sz))

                if is_positive(preds):
                    total_positives += 1
                    # instantiate Prover (computes image_commitment and merkle root)
                    prover = Prover(s_vec, diagnosis_commitments, A, q)

                    # time proof generation
                    t0 = time.time()
                    proof = prover.generate_proof()
                    t_gen = time.time() - t0
                    total_proof_time += t_gen

                    # time verification
                    verifier = Verifier(proof)
                    t0 = time.time()
                    ok = verifier.verify()
                    t_ver = time.time() - t0
                    total_verify_time += t_ver

                    seq_rows.append({
                        "image": fname,
                        "size": sz,
                        "run": run,
                        "proof_gen_s": t_gen,
                        "verify_s": t_ver,
                        "ok": ok
                    })
                    print(f"[{sz}] {fname} run{run}: positive -> gen={t_gen:.4f}s ver={t_ver:.4f}s ok={ok}")
                else:
                    # negative: skip proof
                    seq_rows.append({
                        "image": fname,
                        "size": sz,
                        "run": run,
                        "proof_gen_s": 0.0,
                        "verify_s": 0.0,
                        "ok": None
                    })
                    print(f"[{sz}] {fname} run{run}: negative -> skipped")

        avg_proof = (total_proof_time / total_positives) if total_positives>0 else 0.0
        avg_verify = (total_verify_time / total_positives) if total_positives>0 else 0.0
        print(f"\nSize {sz}: processed_images={total_images}, positives={total_positives}")
        print(f"Total proof time (positives only): {total_proof_time:.4f}s, avg per positive: {avg_proof:.4f}s")
        print(f"Total verify time (positives only): {total_verify_time:.4f}s, avg per positive: {avg_verify:.4f}s")

        # Save sequential results
        df_seq = pd.DataFrame(seq_rows)
        seq_csv = f"seq_results_{sz}x{sz}.csv"
        df_seq.to_csv(seq_csv, index=False)
        overall_seq_results.append((sz, total_proof_time, total_verify_time, total_positives, total_images))

        # ---------------- Batch experiments using commitments ----------------
        # collect first K positives to try batching (if not enough positives, skip)
        # We collect positives in a pass to build tumor_cases list
        tumor_cases = []
        for fname in all_files:
            img_path = os.path.join(dataset_dir, fname)
            model_input = preprocess_for_model(img_path)
            preds = model.predict(model_input)
            if is_positive(preds):
                # create small s_vec and diagnosis commitments for this image
                s_vec = image_to_vector(img_path, normalize=True, target_size=(sz,sz))
                commit_pred = hash_of_obj(preds.flatten())
                commit_model = hash_of_obj(model_json)
                commit_logits = hash_of_obj(preds.flatten())
                diagnosis_commitments = [commit_pred, commit_model, commit_logits]
                tumor_cases.append((fname, s_vec, diagnosis_commitments))

        # Try batch sizes 2..max_batch (or up to available positives)
        for batch_size in range(2, min(max_batch, len(tumor_cases))+1):
            # combine first batch_size cases into one combined secret vector & commitments
            selected = tumor_cases[:batch_size]
            # combined secret vector: concatenate s vectors
            s_concat = np.concatenate([s for (_, s, _) in selected])
            # combined diagnosis commitments: flatten list of commitments
            comb_diag_commits = []
            for (_, _, dc) in selected:
                comb_diag_commits.extend(dc)
            # create A for combined length: columns must equal len(s_concat)
            n_comb = s_concat.shape[0]
            A_comb = np.random.randint(0, q, size=(n_comb, n_comb), dtype=np.int64)

            prover_batch = Prover(s_concat, comb_diag_commits, A_comb, q)
            t0 = time.time()
            proof_batch = prover_batch.generate_proof()
            t_gen_batch = time.time() - t0

            verifier_batch = Verifier(proof_batch)
            t0 = time.time()
            ok_batch = verifier_batch.verify()
            t_ver_batch = time.time() - t0

            print(f"[Batch size {batch_size} @ {sz}x{sz}] gen={t_gen_batch:.4f}s ver={t_ver_batch:.4f}s ok={ok_batch}")
            batch_points.append({
                "size": sz,
                "batch_size": batch_size,
                "batch_gen_s": t_gen_batch,
                "batch_ver_s": t_ver_batch,
                "ok": ok_batch
            })

            # ---------------- Save to CSV ----------------
            batch_csv_path = "batch_results_per_size.csv"
            with open(batch_csv_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["size", "batch_size", "batch_gen_s", "batch_ver_s", "ok"])
                writer.writerow({
                    "size": sz,
                    "batch_size": batch_size,
                    "batch_gen_s": t_gen_batch,
                    "batch_ver_s": t_ver_batch,
                    "ok": ok_batch
                })



    # end sizes loop

    # ---------------- Plotting ----------------
    # Sequential plot: total proof time vs size (use overall_seq_results)
    sizes_plot = [r[0] for r in overall_seq_results]
    total_proof_plot = [r[1] for r in overall_seq_results]
    total_verify_plot = [r[2] for r in overall_seq_results]

    plt.figure(figsize=(10,6))
    plt.plot(sizes_plot, total_proof_plot, marker='o', label='Total Proof Time (positives only)')
    plt.plot(sizes_plot, total_verify_plot, marker='o', label='Total Verify Time (positives only)')
    plt.xlabel("Image vector size (N x N)")
    plt.ylabel("Time (seconds)")
    plt.title("Sequential total proof/verify time vs input-size")
    plt.legend()
    plt.grid(True)
    plt.savefig("sequential_totals.png")
    print("Saved sequential_totals.png")

    # Batch plot
    if batch_points:
        df_batch = pd.DataFrame(batch_points)
        # plot batch_gen_s vs batch_size for each image size
        plt.figure(figsize=(10,6))
        for sz in sorted(df_batch['size'].unique()):
            sub = df_batch[df_batch['size']==sz].sort_values('batch_size')
            plt.plot(sub['batch_size'], sub['batch_gen_s'], marker='o', label=f"gen (size {sz})")
            plt.plot(sub['batch_size'], sub['batch_ver_s'], marker='x', linestyle='--', label=f"ver (size {sz})")
        plt.xlabel("Batch size")
        plt.ylabel("Time (seconds)")
        plt.title("Batch proof gen & verify times")
        plt.legend()
        plt.grid(True)
        plt.savefig("batch_times.png")
        print("Saved batch_times.png")

    # return dataframes maybe
    return

# ---------------- CLI ------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ZKP pipeline using your commitments algorithm (positives-only proofs)")
    parser.add_argument("--dataset", required=True, help="Path to dataset directory (images only)")
    parser.add_argument("--model_json", required=True, help="Path to model.json")
    parser.add_argument("--model_h5", required=True, help="Path to model.h5 (weights)")
    parser.add_argument("--sizes", nargs="+", type=int, default=[8,16,32], help="Square sizes to test (e.g. 8 16 32)")
    parser.add_argument("--runs", type=int, default=2, help="Runs per size (for sequential loop)")
    parser.add_argument("--max_batch", type=int, default=6, help="Maximum batch size to try")
    args = parser.parse_args()

    run_pipeline(args.dataset, args.model_json, args.model_h5, sizes=args.sizes, runs_per_size=args.runs, max_batch=args.max_batch)
