use core::array::{Array, ArrayTrait};

/// Combine two nodes using addition (no hashing)
/// This matches Python's: left + right
fn combine(left: felt252, right: felt252) -> felt252 {
    left + right
}

/// Verify Merkle proof using addition
/// This matches Python's verify_proof method exactly
fn verify_proof(
    leaf: felt252,
    path: Array<felt252>,
    indices: Array<u8>,
    expected_root: felt252
) -> bool {
    let mut current = leaf;
    let mut i = 0;

    while i < path.len() {
        let sibling = *path.at(i);
        let index = *indices.at(i);

        // index == 0: current is left, sibling is right
        // index == 1: current is right, sibling is left
        current = if index == 0 {
            combine(current, sibling)
        } else {
            combine(sibling, current)
        };

        i += 1;
    }

    current == expected_root
}

fn verify_sis_commitment(
    A: Array<felt252>,
    x: Array<felt252>,
    claimed_cm: felt252
) -> bool {
    let mut acc: felt252 = 0;
    let mut i = 0;

    while i < A.len() {
        acc = acc + (*A.at(i)) * (*x.at(i));
        i += 1;
    };

    acc == claimed_cm
}

/// Main executable: Verify a Merkle proof
/// Returns 1 for success, 0 for failure
#[executable]
fn main(
    leaf: felt252,
    path: Array<felt252>,
    indices: Array<u8>,
    expected_root: felt252
) -> felt252 {
    let is_valid = verify_proof(leaf, path, indices, expected_root);
    
    if is_valid {
        1  // Success
    } else {
        0  // Failure
    }
}