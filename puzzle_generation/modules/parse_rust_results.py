from .utils import standardize_tile_tuple


def parse_puzzles_from_txt(txt_file, standardize_tiles=True):
    with open(txt_file, "r") as f:
        lines = f.readlines()

    def parse_line(line):
        """Parse a line into coordinate tuples, handling potential format issues."""
        line = line.strip()
        if not line:  # Skip empty lines
            return None
        try:
            # Split by commas and clean up each coordinate pair
            coords = line.split(", ")
            # Convert each "(x,y)" string into a tuple of ints
            tiles = [tuple(map(int, coord.strip("()").split(","))) for coord in coords]
            return tiles
        except (ValueError, IndexError) as e:
            print(f"Warning: Could not parse line '{line}': {e}")
            return None

    puzzles = []
    seen_standardized_puzzles = set()
    for line in lines:
        tiles = parse_line(line)
        if tiles is not None:
            if standardize_tiles:
                standardized_tiles = standardize_tile_tuple(tiles)
                if standardized_tiles not in seen_standardized_puzzles:
                    puzzles.append(tiles)
                    seen_standardized_puzzles.add(standardized_tiles)
            else:
                puzzles.append(tiles)
    return puzzles
