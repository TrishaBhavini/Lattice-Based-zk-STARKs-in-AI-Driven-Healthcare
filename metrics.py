import random
import time
import math
import matplotlib.pyplot as plt
from merkle import SimpleMerkleTree

# =============================================================================
# 1. Tamper Detection vs Tamper Magnitude
# =============================================================================

def tamper_detection_vs_magnitude(leaves, magnitudes, trials=100):
    """
    Vary how much a single leaf is altered
    """
    results = []

    base_tree = SimpleMerkleTree(leaves)
    base_root = base_tree.root()

    for mag in magnitudes:
        detected = 0

        for _ in range(trials):
            tampered = leaves.copy()
            idx = random.randint(0, len(tampered) - 1)
            tampered[idx] += mag

            tampered_root = SimpleMerkleTree(tampered).root()
            if tampered_root != base_root:
                detected += 1

        results.append(detected / trials)

    return results


# =============================================================================
# 2. Tamper Detection vs Fraction of Leaves Modified
# =============================================================================

def tamper_detection_vs_fraction(leaves, fractions, trials=50):
    """
    Modify k leaves simultaneously and test detection
    """
    results = []
    base_root = SimpleMerkleTree(leaves).root()
    n = len(leaves)

    for frac in fractions:
        k = max(1, int(frac * n))
        detected = 0

        for _ in range(trials):
            tampered = leaves.copy()
            indices = random.sample(range(n), k)

            for idx in indices:
                tampered[idx] += 1

            tampered_root = SimpleMerkleTree(tampered).root()
            if tampered_root != base_root:
                detected += 1

        results.append(detected / trials)

    return results


# =============================================================================
# 3. Verification Latency vs Tree Size
# =============================================================================

def verification_latency_vs_size(base_leaves, sizes, trials=20):
    latencies = []

    for size in sizes:
        leaves = base_leaves[:size]
        tree = SimpleMerkleTree(leaves)
        root = tree.root()

        total_time = 0.0

        for _ in range(trials):
            idx = random.randint(0, size - 1)
            leaf = leaves[idx]
            path, indices = tree.get_proof(idx)

            start = time.perf_counter()
            tree.verify_proof(leaf, path, indices, root)
            end = time.perf_counter()

            total_time += (end - start)

        latencies.append((total_time / trials) * 1000)  # ms

    return latencies


# =============================================================================
# 4. Baseline Metrics
# =============================================================================

def evaluate_tamper_detection(leaves, trials=100):
    tree = SimpleMerkleTree(leaves)
    original_root = tree.root()
    detected = 0

    for _ in range(trials):
        tampered = leaves.copy()
        idx = random.randint(0, len(tampered) - 1)
        tampered[idx] += 1

        if SimpleMerkleTree(tampered).root() != original_root:
            detected += 1

    return detected / trials


def evaluate_false_acceptance(leaves, trials=100):
    tree = SimpleMerkleTree(leaves)
    root = tree.root()
    false_accepts = 0

    for _ in range(trials):
        idx = random.randint(0, len(leaves) - 1)
        leaf = leaves[idx] + 1
        path, indices = tree.get_proof(idx)

        if tree.verify_proof(leaf, path, indices, root):
            false_accepts += 1

    return false_accepts / trials


# =============================================================================
# 5. Plotting Helpers 
# =============================================================================

def plot_detection_vs_magnitude(magnitudes, rates):
    plt.figure()
    plt.plot(magnitudes, rates, marker="o")
    plt.xlabel("Tamper Magnitude (Δ value)")
    plt.ylabel("Detection Rate")
    plt.title("Tamper Detection vs Modification Magnitude")
    plt.grid(True)
    plt.show()


def plot_detection_vs_fraction(fractions, rates):
    plt.figure()
    plt.plot([f * 100 for f in fractions], rates, marker="o")
    plt.xlabel("Fraction of Leaves Tampered (%)")
    plt.ylabel("Detection Rate")
    plt.title("Tamper Detection vs Fraction of Leaves Modified")
    plt.grid(True)
    plt.show()


def plot_latency_vs_size(sizes, latencies):
    plt.figure()
    plt.plot(sizes, latencies, marker="o")
    plt.xlabel("Number of Merkle Leaves")
    plt.ylabel("Verification Latency (ms)")
    plt.title("Merkle Proof Verification Latency vs Tree Size")
    plt.grid(True)
    plt.show()


# =============================================================================
# 6. One-Call Runner
# =============================================================================

def run_all_metrics(all_leaves):
    print("\n=== EXTENDED AUDIT METRICS ===")

    magnitudes = [1, 2, 5, 10, 50, 100]
    fractions = [0.01, 0.05, 0.1, 0.25, 0.5]
    sizes = [20, 40, 80, 160, 200]

    mag_rates = tamper_detection_vs_magnitude(all_leaves, magnitudes)
    frac_rates = tamper_detection_vs_fraction(all_leaves, fractions)
    latencies = verification_latency_vs_size(all_leaves, sizes)

    print("Tamper vs Magnitude:", mag_rates)
    print("Tamper vs Fraction:", frac_rates)
    print("Latency vs Size (ms):", latencies)

    plot_detection_vs_magnitude(magnitudes, mag_rates)
    plot_detection_vs_fraction(fractions, frac_rates)
    plot_latency_vs_size(sizes, latencies)
