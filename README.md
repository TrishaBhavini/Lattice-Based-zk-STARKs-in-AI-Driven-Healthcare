# Lattice-Based-zk-STARKs-in-AI-Driven-Healthcare

This project demonstrates a **privacy-preserving medical diagnosis pipeline** that combines:

- **CNN-based medical image classification**
- **Lattice-based cryptographic commitments (SIS / RLWE / MLWE)**
- **Merkle tree integrity proofs**
- **zk-STARK proof generation and verification using Cairo**

The system proves that a diagnosis was computed **correctly and honestly** *without revealing the input medical data or model internals*.

## Dataset and Model

The dataset and CNN model used in this project are based on the following GitHub repository:  
[https://github.com/rishavchanda/Brain-Tumor-Detection](https://github.com/rishavchanda/Brain-Tumor-Detection)

## How to Execute

Follow the steps below to set up and run the pipeline.

### 1. Clone the Repository

```bash
git clone https://github.com/TrishaBhavini/Lattice-Based-zk-STARKs-in-AI-Driven-Healthcare.git
cd Lattice-Based-zk-STARKs-in-AI-Driven-Healthcare
```

Ensure your repository contains the following files:
```
zkp-1.py
metrics.py
merkle.py
utils.py
mlwe.py
rlwe.py
lattice.py
requirements.txt
cairo/
  └── src/
      └── lib.cairo
  └── Scarb.toml
```

---

### 2. Download the Pre-trained Model and Dataset

Download the model files and dataset from the following GitHub repository:  
🔗 **Source:** [rishavchanda/Brain-Tumor-Detection](https://github.com/rishavchanda/Brain-Tumor-Detection)

#### Required Files:
* `model.json`
* `model.h5`
* `datasets/` folder (contains brain MRI images)

After downloading, place them in the same directory as your scripts:
```
/project-folder
 ├── zkp-1.py
 ├── metrics.py
 ├── merkle.py
 ├── utils.py
 ├── mlwe.py
 ├── rlwe.py
 ├── lattice.py
 ├── requirements.txt
 ├── model.json
 ├── model.h5
 ├── Brain-Tumor-Data/
 └── cairo/
     ├── src/
     │   └── lib.cairo
     └── Scarb.toml
```

---

### 3. Install Dependencies

#### Python Dependencies

Make sure you have **Python 3.8+** installed. Then, install the required libraries:

```bash
pip install -r requirements.txt
```

This installs all necessary packages including:
* TensorFlow & Keras (for ML inference)
* NumPy (for numerical computations)
* Matplotlib (for metrics visualization)
* Pillow (for image processing)

#### Cairo Dependencies

Install Scarb (Cairo package manager):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://docs.swmansion.com/scarb/install.sh | sh
```

Verify installation:
```bash
scarb --version
```

---

### 4. Update File Paths

Before running the pipeline, update the paths in `zkp-1.py` to match your local setup:

```python
DATASET = "/path/to/your/Brain-Tumor-Data"
MODEL_JSON = "/path/to/your/model.json"
MODEL_H5 = "/path/to/your/model.h5"
OUTPUT_PATH = "/path/to/your/cairo/src/input.json"
```

---

### 5. Run the ZKP Pipeline

Execute the following command to start the pipeline:

```bash
python3 zkp-1.py
```

#### Expected Output:

```
Loading model...

Running inference + commitments...
  Processing: image1.jpg
  Processing: image2.jpg
  Processing: image3.jpg
  ...

✓ Processed 40 images
✓ Total leaves: 200 (5 per image)

Building simple Merkle tree (addition-based)...
  Tree depth: 8
  Root: 123456789 (0x75bcd15)

Generating proof for leaf[0]...
  Leaf value: 987654321 (0x3ade68b1)
  Path length: 8
  Indices: [1, 0, 1, 1, 0, 0, 1, 0]
  Python verification: ✓ VALID

✓ Cairo input written to: /path/to/cairo/src/input.json
  Total arguments: 19

================================================================================
PIPELINE COMPLETE
================================================================================
Images processed: 40
Total leaves: 200
Merkle root: 123456789
Proof generated for: image1.jpg
Commitment type: SIS

RUN WITH CAIRO:
================================================================================
cd /path/to/cairo
scarb execute --executable-name ml_stark_prover_exe --arguments-file src/input.json --print-program-output
Expected output: 0x1
================================================================================

✓ Metadata saved to: /path/to/cairo/src/metadata.json

=== METRICS ===

=== EXTENDED AUDIT METRICS ===
Tamper vs Magnitude: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
Tamper vs Fraction: [1.0, 1.0, 1.0, 1.0, 1.0]
Latency vs Size (ms): [0.023, 0.031, 0.042, 0.058, 0.067]
```

The script will also display three visualization plots:
- **Tamper Detection vs Modification Magnitude**
- **Tamper Detection vs Fraction of Leaves Modified**
- **Merkle Proof Verification Latency vs Tree Size**

---

### 6. Generate STARK Proof with Cairo

Navigate to the Cairo directory and build the project:

```bash
cd cairo
scarb build
```

Execute the Cairo program to verify the Merkle proof:

```bash
scarb execute --executable-name ml_stark_prover_exe --arguments-file src/input.json --print-program-output
```

#### Expected Output:

```
Compiling ml_stark_prover v0.1.0 (cairo/Scarb.toml)
    Finished release target(s) in 2.3s

Execution result:
0x1

✓ Proof verified successfully
```

**Output Interpretation:**
- `0x1` = Proof verification **PASSED** ✅
- `0x0` = Proof verification **FAILED** ❌

---

### 7. Output Files & Results

After execution, the following files will be generated:

| File Name | Description |
|-----------|-------------|
| `cairo/src/input.json` | Cairo program arguments (leaf, path, indices, root) |
| `cairo/src/metadata.json` | Human-readable verification data with per-image commitments |

#### `input.json` Structure:
```json
[
  "0x3ade68b1",        // leaf value
  "0x8",               // path length
  "0x12345678", ...    // path siblings (8 values)
  "0x8",               // indices length
  "0x1", "0x0", ...    // indices (8 values)
  "0x75bcd15"          // expected root
]
```

#### `metadata.json` Structure:
```json
{
  "images": [
    {
      "image": "image1.jpg",
      "Cm": 987654321,      // SIS image commitment
      "Cd": 123456789,      // Diagnosis commitment
      "B_hash": 456789123,  // MLWE commitment hash
      "c": 789123456,       // RLWE challenge
      "z": 321654987        // ZK response
    }
  ],
  "tree_depth": 8,
  "total_leaves": 200,
  "merkle_root": 123456789,
  "proof_for_leaf": 0,
  "proof_path_length": 8
}
```

---

### 8. Verify Output

The pipeline automatically performs the following verifications:

✅ **Python Merkle Verification:**
- Verifies the generated proof matches the expected root
- Must pass before Cairo execution

✅ **Cairo STARK Verification:**
- Generates a zero-knowledge proof of correct Merkle verification
- Outputs `0x1` for valid proofs

✅ **Metrics Evaluation:**
- **Tamper Detection Rate**: 100% across all magnitude and fraction levels
- **Verification Latency**: Logarithmic scaling with tree size
- **False Acceptance Rate**: 0% (no invalid proofs accepted)

Example console output:
```
✓ Model loaded successfully
Processing: Y1.jpg
  SIS commitment: 0x3ade68b1
  Diagnosis commitment: 0x75bcd15
  MLWE hash: 0x12345678
  RLWE challenge: 0x9abcdef0
  Response: 0xfedcba98

[Batch Processing Complete]
✓ Merkle root: 123456789
✓ Proof verified: True
✓ Cairo execution: 0x1 (SUCCESS)

=== METRICS ===
Tamper Detection (single-bit): 100.0%
False Acceptance Rate: 0.0%
Avg Verification Latency: 0.042ms
```

---

## 🔐 Cryptographic Components

### Per-Image Commitments (5 leaves each):

1. **Cm (SIS Commitment)**
   - Commits to the input medical image
   - Based on Short Integer Solution problem
   - Post-quantum secure

2. **Cd (Diagnosis Commitment)**
   - Commits to ML model prediction
   - SHA-256 hash of prediction vector
   - Ensures prediction integrity

3. **B_hash (MLWE Commitment)**
   - Module Learning With Errors commitment
   - Binds prediction to random challenge
   - Enables zero-knowledge properties

4. **c (RLWE Challenge)**
   - Ring Learning With Errors challenge
   - Generated from commitment data
   - Used in zero-knowledge protocol

5. **z (Response)**
   - Zero-knowledge response value
   - Computed as `z = pred - c * pred`
   - Proves knowledge without revealing prediction

---

## 📊 Performance Metrics

### Tamper Detection
- **Single-bit modification**: 100% detection rate
- **Multi-leaf tampering (1-50%)**: 100% detection rate
- **Magnitude sensitivity**: Perfect detection from Δ=1 to Δ=100

### Verification Performance
- **20 leaves**: ~0.023 ms average verification time
- **200 leaves**: ~0.067 ms average verification time
- **Scaling**: O(log n) - logarithmic with tree size

### Security Properties
- **Completeness**: Valid proofs always verify (100%)
- **Soundness**: Invalid proofs never verify (0% false acceptance)
- **Zero-Knowledge**: No information leaked about predictions

---

## 🛠️ Troubleshooting

### Python Errors

**Issue**: `ModuleNotFoundError: No module named 'tensorflow'`
```bash
pip install -r requirements.txt
```

**Issue**: `FileNotFoundError: model.json not found`
```bash
# Ensure model files are in the correct location
ls model.json model.h5
# Update paths in zkp-1.py if necessary
```

**Issue**: `Python verification FAILED`
```bash
# Check if Merkle tree implementation matches Cairo
# Verify all helper modules are present
```

### Cairo Errors

**Issue**: `scarb: command not found`
```bash
# Reinstall Scarb
curl --proto '=https' --tlsv1.2 -sSf https://docs.swmansion.com/scarb/install.sh | sh
source ~/.bashrc  # or restart terminal
```

**Issue**: `Error: Failed to parse arguments from input.json`
```bash
# Verify JSON format is a flat array
cat cairo/src/input.json
# Should start with: ["0x...", "0x...", ...]
```

**Issue**: `Execution returned 0x0 (FAILED)`
```bash
# Possible causes:
# 1. Python verification didn't pass first
# 2. input.json corrupted or incorrectly formatted
# 3. Cairo combine() function doesn't match Python
# 4. Path or indices incorrectly generated

# Debug steps:
python3 zkp-1.py  # Re-run to regenerate input.json
cd cairo
scarb clean
scarb build
scarb execute --executable-name ml_stark_prover_exe --arguments-file src/input.json --print-program-output
```

---

## 📈 Architecture Overview

```
Medical Images → ML Inference → Lattice Commitments → Merkle Tree → Cairo Proof → Verification
     (Input)       (ResNet)      (SIS/MLWE/RLWE)      (Addition)     (STARK)      (Boolean)
```

### System Flow:

1. **Image Loading**: Brain MRI scans loaded and preprocessed
2. **ML Inference**: ResNet model predicts tumor presence
3. **Commitment Generation**:
   - SIS commitment for image data
   - SHA-256 commitment for diagnosis
   - MLWE/RLWE for zero-knowledge protocol
4. **Merkle Aggregation**: All commitments organized in addition-based tree
5. **Proof Generation**: Merkle path extracted for specific leaf
6. **Cairo Verification**: STARK proof generated and verified
7. **Output**: Boolean verification result (0x1 = valid, 0x0 = invalid)

---

## 🔬 Research Applications

### Use Cases
- **Medical Diagnosis**: Verifiable AI predictions for healthcare
- **Privacy-Preserving ML**: Zero-knowledge model predictions
- **Trustless Verification**: No need to trust the prover
- **Post-Quantum Security**: Lattice-based cryptography

### Academic Foundation
- **Lattice Cryptography**: SIS, MLWE, RLWE assumptions
- **Zero-Knowledge Proofs**: Privacy-preserving verification
- **STARK Proofs**: Scalable transparent arguments of knowledge
- **Merkle Trees**: Efficient batch verification

---

## 📝 Reference

Model & dataset source:  
**Rishav Chanda** – [Brain Tumor Detection](https://github.com/rishavchanda/Brain-Tumor-Detection)

This project extends the original CNN model with cryptographic verification layers for trustless medical AI.

---

## 📧 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all dependencies are installed correctly
3. Ensure file paths match your system configuration
4. Review Cairo execution logs for detailed error messages
