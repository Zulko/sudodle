use std::collections::{HashMap, HashSet};
use std::fs::OpenOptions;
use std::io::{BufWriter, Write};
use rayon::prelude::*;
use std::sync::Arc;
use clap::Parser;
use rand::prelude::*;

#[derive(Parser)]
#[command(
    name = "find_puzzles",
    about = "Find single solution puzzles for Latin squares",
    version = "1.0"
)]
struct Args {
    /// Size of the Latin square (5-9)
    #[arg(long, value_parser = clap::value_parser!(u8).range(3..=9))]
    size: u8,
    
    /// Number of tiles to place as correct values
    #[arg(long)]
    placed: usize,
    
    /// Optional output file path
    #[arg(long)]
    out_file: Option<String>,
    
    /// Number of processor threads to use for parallel processing
    #[arg(long, default_value = "10")]
    processors: usize,
    
    /// Number of random tile combinations to try (alternative to exhaustive search)
    #[arg(long)]
    random_tries: Option<usize>,
}

/// Find all completions of a partial Latin square using advanced optimized backtracking.
///
/// This function takes a partially filled Latin square with known correct values
/// and known incorrect values, then uses multiple optimization techniques including:
/// - 🔥 Constraint Propagation Cascading - automatically fills forced moves
/// - 🎯 Naked Singles Detection - cells with only one possible value
/// - 🔍 Hidden Singles Detection - values with only one possible position
/// - ⚡ Efficient Bitmask Operations - O(1) constraint checking
/// - 🧠 Most Constrained Variable (MCV) heuristic - tackle hardest cells first
/// - 🚀 Initial Preprocessing - solve obvious cells before backtracking
/// - 🛡️ Advanced Validity Checking - early impossible state detection
///
/// # Parameters
/// - `size`: Size of the Latin square (N×N). Default is 5.
/// - `known_values`: HashMap mapping (row, col) tuples to known correct values.
///   Example: {(0, 1): 3, (2, 0): 1} means cell (0,1) must be 3 and cell (2,0) must be 1.
/// - `known_wrong_values`: HashMap mapping (row, col) tuples to vectors of values
///   that are known to be wrong for that cell.
///   Example: {(0, 0): vec![1, 2]} means cell (0,0) cannot be 1 or 2.
/// - `max_solutions`: Maximum number of solutions to find. If None, finds all solutions.
///   If set, stops when this many solutions are found.
///
/// # Returns
/// A vector of completed N×N Latin squares with values 1 to N.
/// Returns empty vector if no valid completion exists.
///
/// # Algorithm
/// 1. Initialize square with known values and bitmasks
/// 2. 🚀 Initial preprocessing: apply constraint propagation to solve obvious cells
/// 3. Use MCV heuristic to select the most constrained empty cell
/// 4. Try each candidate value with full constraint propagation
/// 5. Recursively solve remaining cells with advanced pruning
/// 6. When complete solution found, save it and continue searching
/// 7. Stop when max_solutions is reached or all possibilities exhausted
pub fn complete_latin_square_backtrack_all_solutions(
    size: usize,
    known_values: &HashMap<(usize, usize), usize>,
    known_wrong_values: &HashMap<(usize, usize), Vec<usize>>,
    max_solutions: Option<usize>,
) -> Vec<Vec<Vec<usize>>> {
    // Initialize the square with 0 for unknown cells (using 0 instead of -1)
    let mut square = vec![vec![0; size]; size];
    let mut solutions = Vec::new();

    // Fill in known values
    for (&(i, j), &value) in known_values {
        if i < size && j < size && value >= 1 && value <= size {
            square[i][j] = value;
        }
    }

    // Create bitmasks for tracking used values in rows and columns
    let mut row_used = vec![0u32; size]; // row_used[i] has bit v-1 set iff value v is in row i
    let mut col_used = vec![0u32; size]; // col_used[j] has bit v-1 set iff value v is in column j
    let full_mask = (1u32 << size) - 1; // bits 0..size-1 all set

    // Initialize bitmasks based on known values
    for i in 0..size {
        for j in 0..size {
            if square[i][j] != 0 {
                let value = square[i][j];
                let bit = 1u32 << (value - 1); // Convert to 0-based for bitmask
                row_used[i] |= bit;
                col_used[j] |= bit;
            }
        }
    }

    // 🔥 CONSTRAINT PROPAGATION CASCADE - automatically fills forced moves
    // Returns true if progress was made, false if contradiction found
    let apply_constraint_propagation = |square: &mut Vec<Vec<usize>>, 
                                           row_used: &mut Vec<u32>, 
                                           col_used: &mut Vec<u32>| -> Result<bool, ()> {
        let mut progress = true;
        let mut total_progress = false;
        
        while progress {
            progress = false;
            
            // 🎯 NAKED SINGLES DETECTION - cells with only one possible value
            for i in 0..size {
                for j in 0..size {
                    if square[i][j] == 0 {
                        let used = row_used[i] | col_used[j];
                        let avail_mask = full_mask & !used;
                        
                        // Apply known wrong values constraint
                        let mut final_mask = avail_mask;
                        if let Some(wrong_values) = known_wrong_values.get(&(i, j)) {
                            for &wrong_val in wrong_values {
                                let wrong_bit = 1u32 << (wrong_val - 1);
                                final_mask &= !wrong_bit;
                            }
                        }
                        
                        if final_mask == 0 {
                            return Err(()); // Contradiction found
                        }
                        
                        // Check if exactly one bit is set (naked single)
                        if final_mask & (final_mask - 1) == 0 {
                            let value = final_mask.trailing_zeros() as usize + 1;
                            let bit = 1u32 << (value - 1);
                            
                            square[i][j] = value;
                            row_used[i] |= bit;
                            col_used[j] |= bit;
                            progress = true;
                            total_progress = true;
                        }
                    }
                }
            }
            
            // 🔍 HIDDEN SINGLES DETECTION - values with only one possible position
            // Check rows for hidden singles
            for i in 0..size {
                for val in 1..=size {
                    let bit = 1u32 << (val - 1);
                    if (row_used[i] & bit) == 0 { // Value not yet in this row
                        let mut possible_positions = Vec::new();
                        
                        for j in 0..size {
                            if square[i][j] == 0 {
                                let cell_used = row_used[i] | col_used[j];
                                let mut can_place = (cell_used & bit) == 0;
                                
                                // Check known wrong values
                                if can_place {
                                    if let Some(wrong_values) = known_wrong_values.get(&(i, j)) {
                                        can_place = !wrong_values.contains(&val);
                                    }
                                }
                                
                                if can_place {
                                    possible_positions.push(j);
                                }
                            }
                        }
                        
                        if possible_positions.is_empty() {
                            return Err(()); // Contradiction: value can't be placed anywhere
                        } else if possible_positions.len() == 1 {
                            // Hidden single found
                            let j = possible_positions[0];
                            square[i][j] = val;
                            row_used[i] |= bit;
                            col_used[j] |= bit;
                            progress = true;
                            total_progress = true;
                        }
                    }
                }
            }
            
            // Check columns for hidden singles
            for j in 0..size {
                for val in 1..=size {
                    let bit = 1u32 << (val - 1);
                    if (col_used[j] & bit) == 0 { // Value not yet in this column
                        let mut possible_positions = Vec::new();
                        
                        for i in 0..size {
                            if square[i][j] == 0 {
                                let cell_used = row_used[i] | col_used[j];
                                let mut can_place = (cell_used & bit) == 0;
                                
                                // Check known wrong values
                                if can_place {
                                    if let Some(wrong_values) = known_wrong_values.get(&(i, j)) {
                                        can_place = !wrong_values.contains(&val);
                                    }
                                }
                                
                                if can_place {
                                    possible_positions.push(i);
                                }
                            }
                        }
                        
                        if possible_positions.is_empty() {
                            return Err(()); // Contradiction: value can't be placed anywhere
                        } else if possible_positions.len() == 1 {
                            // Hidden single found
                            let i = possible_positions[0];
                            square[i][j] = val;
                            row_used[i] |= bit;
                            col_used[j] |= bit;
                            progress = true;
                            total_progress = true;
                        }
                    }
                }
            }
        }
        
        Ok(total_progress)
    };

    // Helper function to get available values for cell (i, j)
    let get_available_values = |square: &Vec<Vec<usize>>, 
                               row_used: &Vec<u32>, 
                               col_used: &Vec<u32>, 
                               i: usize, 
                               j: usize,
                               temp_candidates: &mut Vec<usize>| -> usize {
        temp_candidates.clear();
        
        if square[i][j] != 0 {
            return 0; // Cell already filled
        }

        // Values already used in this row or column
        let used = row_used[i] | col_used[j];
        let avail_mask = full_mask & !used;

        if avail_mask == 0 {
            return 0; // No candidates available
        }

        // Build list of available values using bit manipulation
        let mut m = avail_mask;
        while m != 0 {
            let bit = m & m.wrapping_neg(); // Get lowest set bit
            m ^= bit; // Clear the bit
            let v = bit.trailing_zeros() as usize + 1; // Convert back to 1-based
            temp_candidates.push(v);
        }

        // Remove values that are known to be wrong for this cell
        if let Some(wrong_values) = known_wrong_values.get(&(i, j)) {
            temp_candidates.retain(|&v| !wrong_values.contains(&v));
        }

        temp_candidates.len()
    };

    // Helper function to find most constrained cell
    let find_most_constrained_cell = |square: &Vec<Vec<usize>>, 
                                     row_used: &Vec<u32>, 
                                     col_used: &Vec<u32>| -> (Option<(usize, usize)>, usize) {
        let mut best_cell = None;
        let mut min_choices = size + 1;
        let mut temp_candidates = Vec::with_capacity(size); // Reuse allocation

        for i in 0..size {
            for j in 0..size {
                if square[i][j] == 0 { // Empty cell
                    let choices = get_available_values(square, row_used, col_used, i, j, &mut temp_candidates);
                    if choices == 0 {
                        return (Some((i, j)), 0); // Dead end - return immediately
                    }
                    if choices < min_choices {
                        min_choices = choices;
                        best_cell = Some((i, j));
                        if choices == 1 {
                            return (best_cell, 1); // Can't get better than 1 choice
                        }
                    }
                }
            }
        }

        (best_cell, min_choices)
    };



    // Enhanced early termination with constraint propagation
    let has_valid_assignment = |square: &Vec<Vec<usize>>, 
                               row_used: &Vec<u32>, 
                               col_used: &Vec<u32>| -> bool {
        let mut temp_candidates = Vec::with_capacity(size);
        
        // Check if any empty cell has no possible values
        for i in 0..size {
            for j in 0..size {
                if square[i][j] == 0 {
                    let choices = get_available_values(square, row_used, col_used, i, j, &mut temp_candidates);
                    if choices == 0 {
                        return false;
                    }
                }
            }
        }
        
        // Additional constraint: check if any value is impossible in any row/column
        for val in 1..=size {
            let bit = 1u32 << (val - 1);
            
            // Check each row - ensure value can be placed somewhere
            for i in 0..size {
                if (row_used[i] & bit) == 0 {
                    let mut can_place = false;
                    for j in 0..size {
                        if square[i][j] == 0 && (col_used[j] & bit) == 0 {
                            // Check if this cell specifically excludes this value
                            if let Some(wrong_values) = known_wrong_values.get(&(i, j)) {
                                if !wrong_values.contains(&val) {
                                    can_place = true;
                                    break;
                                }
                            } else {
                                can_place = true;
                                break;
                            }
                        }
                    }
                    if !can_place {
                        return false;
                    }
                }
            }
            
            // Check each column - ensure value can be placed somewhere
            for j in 0..size {
                if (col_used[j] & bit) == 0 {
                    let mut can_place = false;
                    for i in 0..size {
                        if square[i][j] == 0 && (row_used[i] & bit) == 0 {
                            // Check if this cell specifically excludes this value
                            if let Some(wrong_values) = known_wrong_values.get(&(i, j)) {
                                if !wrong_values.contains(&val) {
                                    can_place = true;
                                    break;
                                }
                            } else {
                                can_place = true;
                                break;
                            }
                        }
                    }
                    if !can_place {
                        return false;
                    }
                }
            }
        }
        
        true
    };

    // 🚀 ENHANCED BACKTRACKING with optimized constraint propagation
    fn backtrack(
        square: &mut Vec<Vec<usize>>,
        row_used: &mut Vec<u32>,
        col_used: &mut Vec<u32>,
        solutions: &mut Vec<Vec<Vec<usize>>>,
        size: usize,
        full_mask: u32,
        max_solutions: Option<usize>,
        known_wrong_values: &HashMap<(usize, usize), Vec<usize>>,
        get_available_values: &dyn Fn(&Vec<Vec<usize>>, &Vec<u32>, &Vec<u32>, usize, usize, &mut Vec<usize>) -> usize,
        find_most_constrained_cell: &dyn Fn(&Vec<Vec<usize>>, &Vec<u32>, &Vec<u32>) -> (Option<(usize, usize)>, usize),
        has_valid_assignment: &dyn Fn(&Vec<Vec<usize>>, &Vec<u32>, &Vec<u32>) -> bool,
        apply_constraint_propagation: &dyn Fn(&mut Vec<Vec<usize>>, &mut Vec<u32>, &mut Vec<u32>) -> Result<bool, ()>,
    ) {
        // Check if we've found enough solutions
        if let Some(max) = max_solutions {
            if solutions.len() >= max {
                return;
            }
        }

        // Find the most constrained empty cell
        let (cell, num_choices) = find_most_constrained_cell(square, row_used, col_used);

        if let Some((i, j)) = cell {
            if num_choices == 0 {
                return; // Dead end
            }

            let mut candidates = Vec::new();
            let _choices = get_available_values(square, row_used, col_used, i, j, &mut candidates);

            // Try each candidate value with proper state management
            for &value in &candidates {
                // Early termination check
                if let Some(max) = max_solutions {
                    if solutions.len() >= max {
                        return;
                    }
                }

                let bit = 1u32 << (value - 1);

                // Save complete state before making changes
                let original_square: Vec<Vec<usize>> = square.iter().map(|row| row.clone()).collect();
                let original_row_used = row_used.clone();
                let original_col_used = col_used.clone();

                // Place the value
                square[i][j] = value;
                row_used[i] |= bit;
                col_used[j] |= bit;

                // Apply constraint propagation after placing value
                let mut should_continue = true;
                let empty_cells = square.iter().flatten().filter(|&&x| x == 0).count();
                if empty_cells < size * size / 2 {  // Only when puzzle is more than half filled
                    match apply_constraint_propagation(square, row_used, col_used) {
                        Err(()) => should_continue = false, // Contradiction found
                        Ok(_) => {} // Continue with current state
                    }
                }

                // 🛡️ Enhanced validity check before deeper recursion
                if should_continue && has_valid_assignment(square, row_used, col_used) {
                    backtrack(
                        square,
                        row_used,
                        col_used,
                        solutions,
                        size,
                        full_mask,
                        max_solutions,
                        known_wrong_values,
                        get_available_values,
                        find_most_constrained_cell,
                        has_valid_assignment,
                        apply_constraint_propagation,
                    );
                }

                // Restore complete state
                *square = original_square;
                *row_used = original_row_used;
                *col_used = original_col_used;
            }
        } else {
            // All cells filled successfully - save this solution
            let solution: Vec<Vec<usize>> = square.iter().map(|row| row.clone()).collect();
            solutions.push(solution);
        }
    }

    // Validate that known values don't violate Latin square constraints
    for i in 0..size {
        let mut row_values = Vec::new();
        for j in 0..size {
            if square[i][j] != 0 {
                row_values.push(square[i][j]);
            }
        }
        let mut sorted_values = row_values.clone();
        sorted_values.sort();
        sorted_values.dedup();
        if row_values.len() != sorted_values.len() {
            return Vec::new(); // Duplicate values in row
        }
    }

    for j in 0..size {
        let mut col_values = Vec::new();
        for i in 0..size {
            if square[i][j] != 0 {
                col_values.push(square[i][j]);
            }
        }
        let mut sorted_values = col_values.clone();
        sorted_values.sort();
        sorted_values.dedup();
        if col_values.len() != sorted_values.len() {
            return Vec::new(); // Duplicate values in column
        }
    }

    // 🚀 INITIAL PREPROCESSING - solve obvious cells only if puzzle is sufficiently constrained
    let initial_filled = square.iter().flatten().filter(|&&x| x != 0).count();
    if initial_filled > size {  // Only preprocess if we have enough initial constraints
        match apply_constraint_propagation(&mut square, &mut row_used, &mut col_used) {
            Err(()) => return Vec::new(), // Contradiction in initial state
            Ok(_) => {} // Continue with preprocessed state
        }
    }

    // Final validity check after preprocessing
    if !has_valid_assignment(&square, &row_used, &col_used) {
        return Vec::new();
    }

    // Try to find all completions with enhanced backtracking
    backtrack(
        &mut square,
        &mut row_used,
        &mut col_used,
        &mut solutions,
        size,
        full_mask,
        max_solutions,
        known_wrong_values,
        &get_available_values,
        &find_most_constrained_cell,
        &has_valid_assignment,
        &apply_constraint_propagation,
    );

    solutions
}

/// Generate the basic cyclic Latin square of order N.
///
/// A cyclic Latin square is constructed using the formula: L[i][j] = (i + j) mod N + 1
/// This is guaranteed to be a valid Latin square for any positive integer N.
///
/// # Parameters
/// - `n`: Order of the Latin square (number of rows/columns).
///
/// # Returns
/// An N×N cyclic Latin square with values 1..N.
///
/// # Example
/// ```
/// let square = cyclic_latin_square(3);
/// // Returns [[1, 2, 3], [2, 3, 1], [3, 1, 2]]
/// ```
///
/// Note: This is often used as a starting point for generating more random
/// Latin squares through transformations.
pub fn cyclic_latin_square(n: usize) -> Vec<Vec<usize>> {
    (0..n)
        .map(|i| (0..n).map(|j| (i + j) % n + 1).collect())
        .collect()
}

/// Standardize a tuple of tile coordinates to avoid counting equivalent puzzles multiple times.
/// This function sorts the coordinates to create a canonical representation.
fn standardize_tile_tuple(tiles: &[(usize, usize)]) -> Vec<(usize, usize)> {
    let mut standardized = tiles.to_vec();
    standardized.sort();
    standardized
}

/// Process a batch of tile combinations to find single-solution puzzles.
fn process_batch(
    batch: &[Vec<(usize, usize)>],
    grid: &Arc<Vec<Vec<usize>>>,
    n: usize,
    tile_coordinates: &[(usize, usize)],
    all_solutions: &mut Vec<(Vec<(usize, usize)>, Vec<Vec<usize>>)>,
    seen_standardized_puzzles: &mut HashSet<Vec<(usize, usize)>>,
    writer: &mut Option<BufWriter<std::fs::File>>,
    processed_count: &mut usize,
) {
    
    // Process this batch in parallel - first check for single solutions
    let batch_solutions: Vec<_> = batch
        .par_iter()
        .filter_map(|selected_tiles| {
            // Set up known values and wrong values
            let mut known_values = HashMap::new();
            let mut known_wrong_values = HashMap::new();
            
            for &(i, j) in tile_coordinates {
                if selected_tiles.contains(&(i, j)) {
                    known_values.insert((i, j), grid[i][j]);
                } else {
                    known_wrong_values.insert((i, j), vec![grid[i][j]]);
                }
            }
            
            // Find solutions with max of 2 to check if exactly 1 exists
            let solutions = complete_latin_square_backtrack_all_solutions(
                n,
                &known_values,
                &known_wrong_values,
                Some(2),
            );
            
            // Only return if this is a single-solution puzzle
            if solutions.len() == 1 {
                Some((selected_tiles.clone(), solutions[0].clone()))
            } else {
                None
            }
        })
        .collect();
    
    // Process batch results in main thread: standardize, deduplicate, and collect
    for (selected_tiles, solution) in batch_solutions {
        // Standardize the tile tuple only after we know it's a valid puzzle
        let standardized_tiles = standardize_tile_tuple(&selected_tiles);
        
        // Check if we've seen this standardized form before
        if seen_standardized_puzzles.contains(&standardized_tiles) {
            continue; // Skip this puzzle as we've seen this standardized form before
        }
        
        // Mark this standardized form as seen
        seen_standardized_puzzles.insert(standardized_tiles);
        
        // Add to results
        all_solutions.push((selected_tiles.clone(), solution.clone()));
        
        // Write to output file if specified
        if let Some(ref mut w) = writer {
            let tiles_str = selected_tiles.iter()
                .map(|(r, c)| format!("({},{})", r, c))
                .collect::<Vec<_>>()
                .join(", ");
            writeln!(w, "{}", tiles_str).expect("Failed to write to output file");
            w.flush().expect("Failed to flush output file");
        }
    }
    
    *processed_count += batch.len();
}

/// Find puzzles that have exactly one solution.
///
/// This function generates a cyclic Latin square and then tests combinations
/// of n_well_placed tiles to find configurations that result in puzzles with
/// exactly one valid solution.
///
/// # Parameters
/// - `n`: Size of the Latin square (N×N)
/// - `n_well_placed`: Number of tiles to place as "correct" values
/// - `output_file`: Optional path to write puzzles as they are discovered
/// - `random_tries`: If Some(count), randomly sample this many combinations instead of exhaustive search
///
/// # Returns
/// A vector of tuples containing (selected_tiles, unique_solution) for each
/// puzzle that has exactly one solution.
pub fn find_single_solution_puzzles(
    n: usize,
    n_well_placed: usize,
    output_file: Option<&str>,
    random_tries: Option<usize>,
) -> Vec<(Vec<(usize, usize)>, Vec<Vec<usize>>)> {
    let grid = Arc::new(cyclic_latin_square(n));
    
    // Generate all tile coordinates
    let tile_coordinates: Vec<(usize, usize)> = (0..n)
        .flat_map(|i| (0..n).map(move |j| (i, j)))
        .collect();
    
    // Collection for final results and set to track seen standardized puzzles
    let mut all_solutions = Vec::new();
    let mut seen_standardized_puzzles = HashSet::new();
    
    // Set up output file writer if specified
    let mut writer = if let Some(path) = output_file {
        let file = OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(path)
            .expect("Failed to create output file");
        Some(BufWriter::new(file))
    } else {
        None
    };
    
    let mut processed_count = 0;
    let mut batch_count = 0;
    let chunk_size = if random_tries.is_some() { 10000 } else { 100000 }; // Smaller batches for random mode
    let progress_interval = 5; // Report progress every 5 batches
    
    // Choose iteration strategy based on random_tries parameter
    if let Some(num_random) = random_tries {
        println!("Processing {} random combinations in batches of {} to conserve memory...", num_random, chunk_size);
        
        let mut rng = thread_rng();
        let mut tried_combinations = HashSet::new();
        let mut remaining_tries = num_random;
        
        while remaining_tries > 0 {
            // Collect a batch of random combinations
            let mut batch = Vec::with_capacity(chunk_size.min(remaining_tries));
            for _ in 0..chunk_size.min(remaining_tries) {
                // Generate random combination
                let mut selected_tiles: Vec<(usize, usize)> = tile_coordinates
                    .choose_multiple(&mut rng, n_well_placed)
                    .cloned()
                    .collect();
                selected_tiles.sort(); // Normalize for deduplication
                
                if tried_combinations.insert(selected_tiles.clone()) {
                    batch.push(selected_tiles);
                }
            }
            
            if batch.is_empty() {
                break; // No more unique combinations possible
            }
            
            remaining_tries = remaining_tries.saturating_sub(batch.len());
            process_batch(&batch, &grid, n, &tile_coordinates, &mut all_solutions, &mut seen_standardized_puzzles, &mut writer, &mut processed_count);
            
            batch_count += 1;
            
            // Progress reporting every X batches
            if batch_count % progress_interval == 0 {
                println!("Processed {} batches ({} combinations), found {} solutions so far", batch_count, processed_count, all_solutions.len());
            }
        }
    } else {
        println!("Processing all combinations in batches of {} to conserve memory...", chunk_size);
        
        // Process combinations in batches without collecting all into memory
        let mut combinations = CombinationIterator::new(tile_coordinates.clone(), n_well_placed);
        
        // Process combinations in batches
        loop {
            // Collect a batch of combinations
            let mut batch = Vec::with_capacity(chunk_size);
            for _ in 0..chunk_size {
                if let Some(combo) = combinations.next() {
                    batch.push(combo);
                } else {
                    break;
                }
            }
            
            if batch.is_empty() {
                break; // No more combinations
            }
            
            process_batch(&batch, &grid, n, &tile_coordinates, &mut all_solutions, &mut seen_standardized_puzzles, &mut writer, &mut processed_count);
            
            batch_count += 1;
            
            // Progress reporting every X batches
            if batch_count % progress_interval == 0 {
                println!("Processed {} batches ({} combinations), found {} solutions so far", batch_count, processed_count, all_solutions.len());
            }
        }
    }
    
    println!("Finished processing {} total combinations", processed_count);
    
    all_solutions
}

/// Generate combinations iteratively to avoid storing all in memory
struct CombinationIterator<T: Clone> {
    items: Vec<T>,
    indices: Vec<usize>,
    k: usize,
    first: bool,
    exhausted: bool,
}

impl<T: Clone> CombinationIterator<T> {
    fn new(items: Vec<T>, k: usize) -> Self {
        if k == 0 || k > items.len() {
            return Self {
                items,
                indices: Vec::new(),
                k,
                first: true,
                exhausted: true,
            };
        }
        
        Self {
            items,
            indices: (0..k).collect(),
            k,
            first: true,
            exhausted: false,
        }
    }
}

impl<T: Clone> Iterator for CombinationIterator<T> {
    type Item = Vec<T>;
    
    fn next(&mut self) -> Option<Self::Item> {
        if self.exhausted {
            return None;
        }
        
        if self.first {
            self.first = false;
            return Some(self.indices.iter().map(|&i| self.items[i].clone()).collect());
        }
        
        let n = self.items.len();
        let k = self.k;
        
        // Find the rightmost index that can be incremented
        let mut i = k;
        while i > 0 {
            i -= 1;
            if self.indices[i] < n - k + i {
                self.indices[i] += 1;
                // Reset all indices to the right
                for j in (i + 1)..k {
                    self.indices[j] = self.indices[j - 1] + 1;
                }
                return Some(self.indices.iter().map(|&idx| self.items[idx].clone()).collect());
            }
        }
        
        self.exhausted = true;
        None
    }
}

fn validate_args(args: &Args) -> Result<(), String> {
    let size = args.size as usize;
    if args.placed > size * size {
        return Err(format!(
            "Number of placed tiles ({}) cannot exceed total tiles ({})", 
            args.placed, 
            size * size
        ));
    }
    Ok(())
}

fn main() {
    let args = Args::parse();
    
    if let Err(e) = validate_args(&args) {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }
    
    // Configure rayon thread pool
    rayon::ThreadPoolBuilder::new()
        .num_threads(args.processors)
        .build_global()
        .expect("Failed to initialize thread pool");
    
    let size = args.size as usize;
    let placed = args.placed;
    let out_file = args.out_file;
    
    if let Some(ref file_path) = out_file {
        if let Some(tries) = args.random_tries {
            println!("Finding single solution puzzles for N={}, n_well_placed={}, processors={}, random_tries={}, output file: {}...", size, placed, args.processors, tries, file_path);
        } else {
            println!("Finding single solution puzzles for N={}, n_well_placed={}, processors={}, output file: {}...", size, placed, args.processors, file_path);
        }
    } else {
        if let Some(tries) = args.random_tries {
            println!("Finding single solution puzzles for N={}, n_well_placed={}, processors={}, random_tries={}...", size, placed, args.processors, tries);
        } else {
            println!("Finding single solution puzzles for N={}, n_well_placed={}, processors={}...", size, placed, args.processors);
        }
    }
    
    let solutions = find_single_solution_puzzles(size, placed, out_file.as_deref(), args.random_tries);
    
    println!("\nFound {} puzzles with exactly one solution:", solutions.len());
    
    for (i, (tiles, solution)) in solutions.iter().enumerate().take(5) {
        println!("\nPuzzle {} - Placed tiles: {:?}", i + 1, tiles);
        println!("Unique solution:");
        for row in solution {
            println!("  {:?}", row);
        }
    }
    
    if solutions.len() > 5 {
        println!("... and {} more puzzles", solutions.len() - 5);
    }
}

