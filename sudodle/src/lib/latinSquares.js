// Simple seeded random number generator (using LCG algorithm)
class SeededRandom {
    constructor(seed = null) {
        this.seed = seed !== null ? seed : Math.floor(Math.random() * 2147483647);
        this.current = this.seed;
    }
    
    next() {
        this.current = (this.current * 16807) % 2147483647;
        return this.current / 2147483647;
    }
    
    nextInt(max) {
        return Math.floor(this.next() * max);
    }
    
    shuffle(array) {
        const arr = [...array];
        for (let i = arr.length - 1; i > 0; i--) {
            const j = this.nextInt(i + 1);
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    }
    
    sample(array, count) {
        const shuffled = this.shuffle(array);
        return shuffled.slice(0, count);
    }
}

/**
 * Generate a single N×N Latin square in a reproducible (pseudo-random) way.
 *
 * This function uses backtracking with randomized value selection to generate
 * a valid Latin square. The randomization ensures different squares are generated
 * with different seeds, while the same seed produces the same square.
 *
 * @param {number} N - Order of the Latin square (number of rows/columns).
 * @param {number|null} seed - Seed for the random number generator. If provided,
 *     results will be deterministic for the same (N, seed) pair.
 * @returns {number[][]|null} An N×N Latin square (each row and each column is a
 *     permutation of 1..N). If no square is found (extremely unlikely
 *     for reasonable N), returns null.
 */
function backtrackedRandomLatinSquare(N, seed = null) {
    const rng = new SeededRandom(seed);
    
    // Prepare the empty square and bitmasks for row/column usage
    const square = Array(N).fill().map(() => Array(N).fill(-1));
    const rowUsed = Array(N).fill(0);  // rowUsed[i] has bit v set iff v+1 is already in row i
    const colUsed = Array(N).fill(0);  // colUsed[j] has bit v set iff v+1 is already in column j
    const fullMask = (1 << N) - 1;  // bits 0..N-1 all set
    
    function backtrack(cell = 0) {
        // cell runs from 0..N*N-1 in row-major order
        if (cell === N * N) {
            return true;  // filled every cell successfully
        }
        
        const i = Math.floor(cell / N);
        const j = cell % N;
        
        // Compute which values are still available at (i,j)
        const used = rowUsed[i] | colUsed[j];
        let availMask = fullMask & ~used;
        
        // If no available symbol, backtrack
        if (availMask === 0) {
            return false;
        }
        
        // Build a list of all available values and shuffle it
        const candidates = [];
        let m = availMask;
        while (m) {
            const bit = m & -m;
            m -= bit;
            const v = Math.log2(bit) + 1;  // Add 1 to get numbers 1..N
            candidates.push(Math.round(v));
        }
        const shuffledCandidates = rng.shuffle(candidates);
        
        // Try each candidate in randomized order
        for (const v of shuffledCandidates) {
            const bit = 1 << (v - 1);  // Subtract 1 for bitmask operations
            square[i][j] = v;
            rowUsed[i] |= bit;
            colUsed[j] |= bit;
            
            if (backtrack(cell + 1)) {
                return true;  // once one full square is found, stop
            }
            
            // undo placement
            rowUsed[i] ^= bit;
            colUsed[j] ^= bit;
            square[i][j] = -1;
        }
        
        return false;
    }
    
    const success = backtrack(0);
    return success ? square : null;
}

/**
 * Generate the basic cyclic Latin square of order N.
 *
 * A cyclic Latin square is constructed using the formula: L[i][j] = (i + j) mod N + 1
 * This is guaranteed to be a valid Latin square for any positive integer N.
 *
 * @param {number} N - Order of the Latin square (number of rows/columns).
 * @returns {number[][]} An N×N cyclic Latin square with values 1..N.
 */
function cyclicLatinSquare(N) {
    return Array(N).fill().map((_, i) => 
        Array(N).fill().map((_, j) => (i + j) % N + 1)
    );
}

/**
 * Attempt one random intercalate swap on a Latin square in place.
 *
 * This function implements one step of the Jacobson-Matthews algorithm for
 * generating uniformly random Latin squares. It looks for a 2×2 submatrix
 * of the form [[a,b],[b,a]] and swaps it to [[b,a],[a,b]].
 *
 * @param {number[][]} L - The Latin square to modify in place.
 * @param {SeededRandom} rng - Random number generator to use for selection.
 * @returns {boolean} True if a swap was performed, False if no valid swap was found.
 */
function _randomIntercalateStep(L, rng) {
    const N = L.length;
    const [r1, r2] = rng.sample([...Array(N).keys()], 2);
    const [c1, c2] = rng.sample([...Array(N).keys()], 2);
    
    const a = L[r1][c1];
    const b = L[r1][c2];
    if (a === b) {
        return false;
    }
    if (L[r2][c1] === b && L[r2][c2] === a) {
        // We have an intercalate [[a,b],[b,a]], so flip:
        L[r1][c1] = b;
        L[r1][c2] = a;
        L[r2][c1] = a;
        L[r2][c2] = b;
        return true;
    }
    
    return false;
}

/**
 * Generate a (nearly) uniformly random Latin square of order N.
 *
 * Uses the Jacobson–Matthews "intercalate‐flip" Markov chain to generate
 * Latin squares that are approximately uniformly distributed over all
 * possible Latin squares of the given order.
 *
 * @param {number} N - Order of the Latin square (number of rows/columns).
 * @param {number|null} seed - Seed for the random number generator. If provided,
 *     results will be deterministic for the same (N, seed) pair.
 * @param {number|null} burnInSteps - Number of random intercalate flips to perform
 *     before returning the square. If null, defaults to 50 * N².
 * @returns {number[][]} An N×N Latin square with values 1..N that is approximately
 *     uniformly distributed over all possible Latin squares.
 */
function uniformRandomLatinSquare(N, seed = null, burnInSteps = null) {
    const rng = new SeededRandom(seed);
    const L = backtrackedRandomLatinSquare(N, seed);
    
    if (burnInSteps === null) {
        burnInSteps = 50 * (N ** 2);
    }
    
    for (let i = 0; i < burnInSteps; i++) {
        // Try an intercalate‐flip; if it's not valid, we simply continue.
        _randomIntercalateStep(L, rng);
    }
    
    // At this point, L is (approximately) a uniform sample.
    return L;
}

/**
 * Check if a square is a valid Latin square and find all invalid positions.
 * 
 * A position is invalid if its number appears more than once in its row or column.
 *
 * @param {number[][]} square - The square to check (NxN array of numbers 1..N)
 * @returns {[number, number][]} Array of [row,col] positions that are invalid
 */
function findLatinSquareViolations(square) {
    const N = square.length;
    const invalidPositions = new Set();
    
    // Check rows for violations
    for (let row = 0; row < N; row++) {
        const seen = new Set();
        const duplicates = new Set();
        
        // First pass: identify which values appear multiple times in this row
        for (let col = 0; col < N; col++) {
            const val = square[row][col];
            if (seen.has(val)) {
                duplicates.add(val);
            } else {
                seen.add(val);
            }
        }
        
        // Second pass: mark all positions with duplicate values as invalid
        for (let col = 0; col < N; col++) {
            const val = square[row][col];
            if (duplicates.has(val)) {
                invalidPositions.add(`${row},${col}`);
            }
        }
    }
    
    // Check columns for violations
    for (let col = 0; col < N; col++) {
        const seen = new Set();
        const duplicates = new Set();
        
        // First pass: identify which values appear multiple times in this column
        for (let row = 0; row < N; row++) {
            const val = square[row][col];
            if (seen.has(val)) {
                duplicates.add(val);
            } else {
                seen.add(val);
            }
        }
        
        // Second pass: mark all positions with duplicate values as invalid
        for (let row = 0; row < N; row++) {
            const val = square[row][col];
            if (duplicates.has(val)) {
                invalidPositions.add(`${row},${col}`);
            }
        }
    }
    
    // Convert Set back to array of tuples
    return Array.from(invalidPositions).map(pos => {
        const [row, col] = pos.split(',').map(Number);
        return [row, col];
    });
}

/**
 * Check if a square is a valid Latin square.
 * 
 * A Latin square is valid if each number 1..N appears exactly once in each row
 * and exactly once in each column.
 *
 * @param {number[][]} square - The square to check (NxN array of numbers 1..N)
 * @returns {boolean} True if the square is a valid Latin square, false otherwise
 */
function checkLatinSquare(square) {
    const violations = findLatinSquareViolations(square);
    return violations.length === 0;
}

// Export functions for use in other modules
export {
    cyclicLatinSquare,
    uniformRandomLatinSquare,
    backtrackedRandomLatinSquare,
    findLatinSquareViolations,
    checkLatinSquare,
    SeededRandom
};