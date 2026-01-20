"""
Simple Merkle Tree using addition (no hashing).
Matches Cairo's arithmetic-based Merkle tree for STARK verification.
"""

class SimpleMerkleTree:
    """
    Non-cryptographic Merkle tree using addition instead of hashing.
    This ensures perfect compatibility with Cairo's arithmetic operations.
    """
    
    def __init__(self, leaves):
        """Initialize with leaf values (as integers)"""
        self.leaves = [int(l) for l in leaves]
        self.levels = [self.leaves]
        self._build()
    
    def _combine(self, left, right):
        """Combine two nodes: simply add them (no hashing)"""
        return left + right
    
    def _build(self):
        """Build the tree bottom-up using addition"""
        while len(self.levels[-1]) > 1:
            level = self.levels[-1]
            next_level = []
            
            for i in range(0, len(level), 2):
                left = level[i]
                # If odd number of nodes, duplicate the last one
                right = level[i + 1] if i + 1 < len(level) else left
                next_level.append(self._combine(left, right))
            
            self.levels.append(next_level)
    
    def root(self):
        """Return the Merkle root"""
        return self.levels[-1][0]
    
    def get_proof(self, index):
        """
        Get Merkle proof for a leaf at given index.
        Returns: (path, indices)
        """
        path = []
        indices = []
        current_index = index
        
        for level in self.levels[:-1]:
            if current_index % 2 == 0:
                # Current is left child
                sibling_index = current_index + 1 if current_index + 1 < len(level) else current_index
                indices.append(0)
            else:
                # Current is right child
                sibling_index = current_index - 1
                indices.append(1)
            
            path.append(level[sibling_index])
            current_index //= 2
        
        return path, indices
    
    def verify_proof(self, leaf, path, indices, expected_root):
        """Verify a Merkle proof"""
        current = leaf
        
        for sibling, index in zip(path, indices):
            if index == 0:
                current = self._combine(current, sibling)
            else:
                current = self._combine(sibling, current)
        
        return current == expected_root


# Test the implementation
if __name__ == "__main__":
    print("=" * 80)
    print("SIMPLE MERKLE TREE TEST (Addition-based, no hashing)")
    print("=" * 80)
    
    # Test with 5 leaves (your use case)
    leaves = [100, 200, 300, 400, 500]
    tree = SimpleMerkleTree(leaves)
    
    print(f"\nLeaves: {leaves}")
    print(f"Number of levels: {len(tree.levels)}")
    
    for i, level in enumerate(tree.levels):
        print(f"Level {i}: {level}")
    
    print(f"\nRoot: {tree.root()}")
    
    # Test proof for first leaf
    leaf_idx = 0
    path, indices = tree.get_proof(leaf_idx)
    
    print(f"\nProof for leaf[{leaf_idx}] = {leaves[leaf_idx]}:")
    print(f"  Path: {path}")
    print(f"  Indices: {indices}")
    
    is_valid = tree.verify_proof(leaves[leaf_idx], path, indices, tree.root())
    print(f"  Verification: {'✓ VALID' if is_valid else '✗ INVALID'}")
    
    # Manual verification
    print(f"\nManual verification:")
    current = leaves[0]
    print(f"  Start: {current}")
    for i, (sib, idx) in enumerate(zip(path, indices)):
        if idx == 0:
            current = current + sib
            print(f"  Step {i+1}: {current - sib} + {sib} = {current}")
        else:
            current = sib + current
            print(f"  Step {i+1}: {sib} + {current - sib} = {current}")
    print(f"  Final: {current}")
    print(f"  Root: {tree.root()}")
    print(f"  Match: {current == tree.root()}")