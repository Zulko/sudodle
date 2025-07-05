#!/usr/bin/env python3
"""
Generate a PDF with Sudodle puzzles using WeasyPrint and Jinja2.
"""

import pandas as pd
from pathlib import Path
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader


def load_and_process_puzzles(csv_file):
    """Load puzzles from CSV using pandas and process them."""
    # Read CSV with pandas
    df = pd.read_csv(csv_file)

    # Add grid_size column (first character of compacted_puzzle)
    df["grid_size"] = df["compacted_puzzle"].str[0].astype(int)

    # For 5x5 grids, only use 1/5th of the puzzles
    df_5x5 = df[df["grid_size"] == 5].iloc[::7]  # Take every 7th row
    df_6x6 = df[df["grid_size"] == 6].iloc[::7]  # Take every 7th row
    df_others = df[
        (df["grid_size"] != 5) & (df["grid_size"] != 6)
    ]  # Take every 7th row
    df = (
        pd.concat([df_others, df_5x5, df_6x6])
        .sort_values(["grid_size", "level", "difficulty"])
        .reset_index(drop=True)
    )

    # Group by grid_size and level
    grouped = df.groupby(["grid_size", "level"])

    # Convert to nested dictionary structure for the template
    puzzle_data = {}
    for (grid_size, level), group in grouped:
        if grid_size not in puzzle_data:
            puzzle_data[grid_size] = {}
        group_data = group.to_dict("records")
        puzzle_data[grid_size][level] = group_data

    return puzzle_data


def generate_puzzle_book_pdf(
    csv_file, output_file, template_file="puzzle_book_template.html"
):
    """Generate the complete puzzle PDF using Jinja2 template."""
    puzzles = load_and_process_puzzles(csv_file)

    # Set up Jinja2 environment
    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_file)

    # Render the template with puzzle data
    html_content = template.render(puzzle_data=puzzles)
    html_file = output_file.with_suffix(".html")
    with html_file.open("w") as f:
        f.write(html_content)

    # Generate PDF - use the HTML file instead of string content so paths resolve correctly
    html_doc = HTML(filename=str(html_file))
    print(f"Generating PDF: {output_file}")
    html_doc.write_pdf(output_file)
    print(f"PDF generated successfully!")


def main():
    """Main function."""
    csv_file = Path("outputs/puzzles.csv")
    output_file = Path("outputs/sudodles_puzzle_book.pdf")

    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)

    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}")
        return

    generate_puzzle_book_pdf(csv_file, output_file)


if __name__ == "__main__":
    main()
