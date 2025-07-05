// Import the CSV data as raw text at build time
import puzzlesCSV from './puzzles.csv?raw';

function parsePuzzleData(csvText) {
  const puzzles = {};
  const lines = csvText.trim().split('\n');

  lines.forEach((line) => {
    if (line.length > 0) {
      const parts = line.split(',');
      if (parts.length >= 2) {
        const compactedPuzzle = parts[0];
        const difficulty = parts[1];
        const gridSize = parseInt(compactedPuzzle[0]);

        // Initialize nested structure for this grid size and difficulty if it doesn't exist
        if (!puzzles[gridSize]) {
          puzzles[gridSize] = {};
        }
        if (!puzzles[gridSize][difficulty]) {
          puzzles[gridSize][difficulty] = [];
        }

        puzzles[gridSize][difficulty].push(compactedPuzzle);
      }
    }
  });

  return puzzles;
}

// Parse the data at module load time
export const puzzleData = parsePuzzleData(puzzlesCSV); 