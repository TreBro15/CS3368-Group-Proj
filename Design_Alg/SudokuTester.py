#Inspired by RayThePizzo Test benchmarks

import csv
import time
import random
import math
from pathlib import Path

from Sudoku import SudukoSolversWork
from itertools import product


def get_benchmark_models():
    """Generate every supported CSP heuristic configuration."""

    models = []

    for variable, value, arc in product(
        ("mrv", "conflict"),
        ("lcv", "lcb"),
        (False, True),
    ):
        model_name = (
            f"{variable.upper()} + {value.upper()}"
            + (" + AC3" if arc else "")
        )

        models.append({
            "name": model_name,
            "variable_heuristic": variable,
            "value_heuristic": value,
            "use_arc_consistency": arc,
            "algorithm": "csp",
        })

    return models

def run_solver(solver, algorithm):
    """Run the selected solver and return its result and elapsed time."""
    start_time = time.perf_counter()
    if algorithm == "csp":
        result = solver.solve()
    elif algorithm == "sa":
        result = solver.solve_sa()
    else:
        raise ValueError(f"Unsupported solver algorithm: {algorithm}")
    return result, time.perf_counter() - start_time


def is_valid_solution(grid, puzzle=None):
    """Check Sudoku rules and, when provided, preserve the puzzle clues."""

    expected = set(range(1, 10))

    for row in grid:
        if set(row) != expected:
            return False

    for col in range(9):
        if {grid[row][col] for row in range(9)} != expected:
            return False

    for start_row in range(0, 9, 3):
        for start_col in range(0, 9, 3):
            values = {
                grid[r][c]
                for r in range(start_row, start_row + 3)
                for c in range(start_col, start_col + 3)
            }

            if values != expected:
                return False

    if puzzle is not None and any(
        puzzle[row][col] != 0 and grid[row][col] != puzzle[row][col]
        for row in range(9)
        for col in range(9)
    ):
        return False

    return True


def matches_known_solution(grid, expected_solution):
    """Return whether a solver result exactly matches the dataset answer."""
    return None if expected_solution is None else grid == expected_solution


def parse_puzzle_grid(value, description):
    """Parse an 81-character puzzle or solution using digits and dots."""
    cells = "".join(value.split())
    if len(cells) != 81 or any(cell not in "0123456789." for cell in cells):
        raise ValueError(
            f"{description} must contain exactly 81 digits or dots."
        )

    cells = cells.replace(".", "0")
    return [
        [int(cells[row * 9 + col]) for col in range(9)]
        for row in range(9)
    ]

# Allows testing selected records without retaining a large dataset in memory.


def load_puzzle_dataset(
    path,
    row_number=None,
    sample_size=1,
    difficulty_min=None,
    difficulty_max=None,
    seed=None,
):
    """Select CSV records by data-row number or a reservoir-sampled subset."""
    dataset_path = Path(path).expanduser()
    if row_number is not None and (
        not isinstance(row_number, int)
        or isinstance(row_number, bool)
        or row_number < 1
    ):
        raise ValueError("row_number must be a positive integer.")
    if row_number is None and (
        not isinstance(sample_size, int)
        or isinstance(sample_size, bool)
        or sample_size < 1
    ):
        raise ValueError("sample_size must be a positive integer.")
    for label, difficulty in (
        ("Minimum", difficulty_min),
        ("Maximum", difficulty_max),
    ):
        if difficulty is not None and (
            not isinstance(difficulty, (int, float))
            or isinstance(difficulty, bool)
            or not math.isfinite(difficulty)
            or difficulty < 0
        ):
            raise ValueError(f"{label} difficulty must be a non-negative number.")
    if (
        difficulty_min is not None
        and difficulty_max is not None
        and difficulty_min > difficulty_max
    ):
        raise ValueError("Minimum difficulty cannot exceed maximum difficulty.")

    try:
        with dataset_path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            if not reader.fieldnames:
                raise ValueError("Dataset CSV must include a header row.")

            columns = {
                name.strip().lower().replace("_", " "): name
                for name in reader.fieldnames
                if name is not None
            }
            if "puzzle" not in columns:
                raise ValueError("Dataset CSV must have a 'puzzle' column.")

            rating_column = next(
                (
                    columns[name]
                    for name in ("difficulty", "rating", "difficulty rating")
                    if name in columns
                ),
                None,
            )
            if (
                rating_column is None
                and (difficulty_min is not None or difficulty_max is not None)
            ):
                raise ValueError(
                    "Difficulty filtering requires a 'difficulty' or 'rating' column."
                )

            rng = random.Random(seed)
            selected = []
            matching_count = 0
            for data_row_number, row in enumerate(reader, start=1):
                puzzle_value = row.get(columns["puzzle"], "")
                if not puzzle_value or not puzzle_value.strip():
                    continue
                if row_number is not None and data_row_number != row_number:
                    continue

                rating = None
                if rating_column is not None and row.get(rating_column, "").strip():
                    try:
                        rating = float(row[rating_column])
                    except ValueError as error:
                        raise ValueError(
                            f"Invalid difficulty on CSV data row {data_row_number}."
                        ) from error
                    if not math.isfinite(rating):
                        raise ValueError(
                            f"Invalid difficulty on CSV data row {data_row_number}."
                        )

                if (
                    (difficulty_min is not None or difficulty_max is not None)
                    and rating is None
                ):
                    continue
                if difficulty_min is not None and rating < difficulty_min:
                    continue
                if difficulty_max is not None and rating > difficulty_max:
                    continue

                matching_count += 1
                entry = {
                    "row_number": data_row_number,
                    "raw_row": row,
                    "rating": rating,
                }
                if row_number is not None:
                    selected = [entry]
                    break

                if len(selected) < sample_size:
                    selected.append(entry)
                else:
                    replacement_index = rng.randrange(matching_count)
                    if replacement_index < sample_size:
                        selected[replacement_index] = entry
    except OSError as error:
        raise ValueError(
            f"Could not read puzzle dataset '{dataset_path}': {error}"
        ) from error

    if not selected:
        if row_number is not None:
            raise ValueError(
                f"CSV data row {row_number} was not found or did not match "
                "the selected difficulty filter."
            )
        raise ValueError(
            f"No puzzles matched the selection in dataset '{dataset_path}'."
        )

    puzzles = []
    for entry in selected:
        row = entry.pop("raw_row")
        data_row_number = entry["row_number"]
        puzzle = parse_puzzle_grid(
            row.get(columns["puzzle"], ""),
            f"Puzzle on CSV data row {data_row_number}",
        )
        solution_column = columns.get("solution")
        solution_value = row.get(solution_column, "") if solution_column else ""
        solution = None
        if solution_value and solution_value.strip():
            solution = parse_puzzle_grid(
                solution_value, f"Solution on CSV data row {data_row_number}"
            )
            if not is_valid_solution(solution, puzzle):
                raise ValueError(
                    f"Solution on CSV data row {data_row_number} is invalid "
                    "or does not match its puzzle clues."
                )

        name_column = columns.get("name") or columns.get("id")
        name = row.get(name_column, "").strip() if name_column else ""
        puzzles.append(
            {
                "name": name or f"CSV row {data_row_number}",
                "row_number": data_row_number,
                "rating": entry["rating"],
                "puzzle": puzzle,
                "solution": solution,
            }
        )

    return puzzles

#Oiriginal auto generated puzzles initially created for prototype
def generate_puzzle(empty_cells=40, seed=None):
    """Generate a random Sudoku puzzle with an exact number of empty cells.

    Args:
        empty_cells: Number of cells to replace with 0 (0-81).
        seed: Optional integer seed for reproducibility.

    Returns:
        A 9x9 list of lists representing the puzzle.
    """
    if not isinstance(empty_cells, int) or isinstance(empty_cells, bool):
        raise ValueError("empty_cells must be an integer.")

    if not 0 <= empty_cells <= 81:
        raise ValueError("empty_cells must be between 0 and 81.")

    rng = random.Random(seed)
    grid = [[0 for _ in range(9)] for _ in range(9)]

    def candidates(row, col):
        used = set(grid[row])

        used.update(grid[r][col] for r in range(9))

        start_row = (row // 3) * 3
        start_col = (col // 3) * 3

        used.update(
            grid[r][c]
            for r in range(start_row, start_row + 3)
            for c in range(start_col, start_col + 3)
        )

        return set(range(1, 10)) - used

    def fill_board():
        # Find an empty cell with the fewest legal candidates.
        best_cell = None
        best_candidates = None

        for row in range(9):
            for col in range(9):
                if grid[row][col] == 0:
                    options = candidates(row, col)

                    if not options:
                        return False

                    if best_candidates is None or len(options) < len(best_candidates):
                        best_cell = (row, col)
                        best_candidates = options

        # No empty cells remain: the board is complete.
        if best_cell is None:
            return True

        row, col = best_cell
        options = list(best_candidates)
        rng.shuffle(options)

        for value in options:
            grid[row][col] = value

            if fill_board():
                return True

            grid[row][col] = 0

        return False

    fill_board()

    # Remove exactly the requested number of cells.
    positions = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(positions)

    for row, col in positions[:empty_cells]:
        grid[row][col] = 0

    return grid

def benchmark_solver(solver, puzzle=None, expected_solution=None):
    """Run the solver and report execution time and statistics."""

    result, elapsed_time = run_solver(solver, "csp")

    valid = result and is_valid_solution(solver.grid, puzzle)
    matches_solution = matches_known_solution(solver.grid, expected_solution)

    print("\n--- Sudoku Solver Benchmark ---")
    print(f"Solved: {result}")
    print(f"Valid solution: {valid}")
    if matches_solution is not None:
        print(f"Matches known solution: {matches_solution}")
    print(f"Execution time: {elapsed_time*1000:.3f} milliseconds")

    print("\n--- Solver Statistics ---")
    print(f"Recursive calls: {solver.recursive_calls}")
    print(f"Forward steps: {solver.forward_steps}")
    print(f"Backtracking steps: {solver.backtrack_steps}")

    if valid:
        print("\n--- Solved Sudoku ---")
        for row in solver.grid:
            print(row)

    return {
        "solved": result,
        "valid": valid,
        "matches_known_solution": matches_solution,
        "execution_time": elapsed_time,
        "recursive_calls": solver.recursive_calls,
        "forward_steps": solver.forward_steps,
        "backtrack_steps": solver.backtrack_steps
    }

def plot_benchmark_results(results, algorithm="csp"):
    import matplotlib.pyplot as plt
    from collections import defaultdict

    metrics = {
        "execution_time_ms": "Average Execution Time (ms)",
        "backtrack_steps": "Average Backtracking Steps",
        "recursive_calls": "Average Recursive Calls",
    }

    grouped_results = defaultdict(list)

    for result in results:
        grouped_results[result["model"]].append(result)

    models = list(grouped_results.keys())

    for metric, title in metrics.items():
        averages = []

        for model in models:
            values = [
                result[metric]
                for result in grouped_results[model]
                if result.get(metric) is not None
            ]

            average = sum(values) / len(values) if values else 0
            averages.append(average)

        plt.figure(figsize=(12, 6))

        bars = plt.bar(models, averages)

        plt.xlabel("Solver Configuration")
        plt.ylabel(title)
        plt.title(f"{title} by Solver Configuration")

        plt.xticks(rotation=35, ha="right")
        plt.grid(axis="y", alpha=0.3)

        # Display the numerical value above each bar.
        for bar, value in zip(bars, averages):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=8
            )

        plt.tight_layout()

        output_dir = Path(__file__).parent.parent / "data"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = output_dir / f"{metric}_comparison.png"
        plt.savefig(filename, dpi=300)
        plt.savefig(filename, dpi=300)
        plt.show()
        plt.close()

        print(f"Saved {filename}")

def export_results_to_csv(results):
    """Write benchmark results to a CSV file."""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sudoku_benchmark.csv"

    fieldnames = [
    "test_number",
    "puzzle_name",
    "dataset_row",
    "rating",
    "model",
    "algorithm",
    "empty_cells",
    "execution_time_ms",
    "solved",
    "valid",
    "matches_known_solution",
    "recursive_calls",
    "backtrack_steps",
    "forward_steps",
    "sa_iterations",
    "reheats",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nBenchmark results saved to {output_path}")

def get_user_settings():

    while True:
        print("\nChoose puzzle source:")
        print("1. Generate puzzles")
        print("2. Load puzzles from a CSV dataset")
        puzzle_source_choice = input("Enter 1 or 2: ").strip()

        if puzzle_source_choice in ("1", "2"):
            break
        print("Invalid choice. Try again.")

    if puzzle_source_choice == "2":
        dataset_path = Path(__file__).parent.parent / "data" / "sudoku_test_sample.csv"

        while True:
            print("\nChoose dataset selection:")
            print("1. Test one CSV data row (header is not counted)")
            print("2. Test a random sample")

            selection_choice = input("Enter 1 or 2: ").strip()

            if selection_choice in ("1", "2"):
                break
            print("Invalid choice. Try again.")

        row_number = None
        sample_size = 1

        if selection_choice == "1":

            while True:
                try:
                    row_number = int(
                        input("CSV data row number (starting at 1): ")
                    )

                    if row_number > 0:
                        break

                    print("Enter a positive row number.")

                except ValueError:
                    print("Enter a positive integer.")

        else:

            while True:
                try:
                    sample_size = int(
                        input("Number of puzzles to sample: ")
                    )

                    if sample_size > 0:
                        break

                    print("Enter at least one puzzle.")

                except ValueError:
                    print("Enter a valid positive integer.")

        def optional_difficulty(prompt):

            while True:
                value = input(prompt).strip()

                if not value:
                    return None

                try:
                    difficulty = float(value)

                    if math.isfinite(difficulty) and difficulty >= 0:
                        return difficulty

                    print("Enter a finite, non-negative rating.")

                except ValueError:
                    print("Enter a number or leave blank.")

        difficulty_min = optional_difficulty(
            "Minimum difficulty/rating (blank for no minimum): "
        )

        difficulty_max = optional_difficulty(
            "Maximum difficulty/rating (blank for no maximum): "
        )

        while (
            difficulty_min is not None
            and difficulty_max is not None
            and difficulty_min > difficulty_max
        ):
            print("Minimum difficulty cannot exceed maximum difficulty.")

            difficulty_max = optional_difficulty(
                "Enter a maximum at least as large as the minimum: "
            )

        sample_seed = None

        if selection_choice == "2":

            while True:
                seed_input = input(
                    "Random sample seed (blank for a different sample each run): "
                ).strip()

                if not seed_input:
                    break

                try:
                    sample_seed = int(seed_input)
                    break

                except ValueError:
                    print("Seed must be an integer or blank.")

        dataset_puzzles = load_puzzle_dataset(
            dataset_path,
            row_number=row_number,
            sample_size=sample_size,
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max,
            seed=sample_seed,
        )

        print(
            f"Selected {len(dataset_puzzles)} puzzle(s) from "
            f"{dataset_path}."
        )

        empty_counts = []
        repetitions = 1
        batch_mode = True
        seed = None
        puzzle_source = "dataset"

    else:

        dataset_puzzles = []
        puzzle_source = "generated"

        while True:
            print("\nChoose test mode:")
            print("1. Single test")
            print("2. Batch tests and plot")

            test_mode = input("Enter 1 or 2: ").strip()

            if test_mode in ("1", "2"):
                break

            print("Invalid choice. Try again.")

        if test_mode == "1":

            while True:
                try:
                    empty_counts = [
                        int(input("Enter the number of empty cells (0-81): "))
                    ]

                    if 0 <= empty_counts[0] <= 81:
                        break

                    print("Please enter a number between 0 and 81.")

                except ValueError:
                    print("Please enter a valid integer.")

            repetitions = 1
            batch_mode = False

        else:

            while True:
                try:
                    empty_counts = [
                        int(value.strip())
                        for value in input(
                            "Enter empty-cell counts separated by commas (0-81): "
                        ).split(",")
                    ]

                    if empty_counts and all(
                        0 <= count <= 81 for count in empty_counts
                    ):
                        break

                    print("Enter one or more counts between 0 and 81.")

                except ValueError:
                    print("Enter integer counts separated by commas.")

            while True:
                try:
                    repetitions = int(
                        input("Trials per empty-cell count: ")
                    )

                    if repetitions > 0:
                        break

                    print("Enter at least one trial.")

                except ValueError:
                    print("Enter a valid positive integer.")

            batch_mode = True

        while True:
            seed_input = input(
                "Enter a random seed (or press Enter for None): "
            ).strip()

            if seed_input == "":
                seed = None
                break

            try:
                seed = int(seed_input)
                break

            except ValueError:
                print("Seed must be an integer or blank.")

    return (
        puzzle_source,
        dataset_puzzles,
        empty_counts,
        repetitions,
        batch_mode,
        seed,
    )

if __name__ == "__main__":

    (
        puzzle_source,
        dataset_puzzles,
        empty_counts,
        repetitions,
        batch_mode,
        seed,
    ) = get_user_settings()

    models = get_benchmark_models()

    print("\n--- Models Selected ---")
    for model in models:
        print(f"- {model['name']}")

    results = []
    test_number = 0

    if puzzle_source == "dataset":
        test_cases = [
            (
                entry["name"],
                entry["row_number"],
                entry["rating"],
                entry["puzzle"],
                entry["solution"],
            )
            for entry in dataset_puzzles
        ]

    else:
        test_cases = []

        for empty_cells in empty_counts:
            for _ in range(repetitions):

                test_seed = (
                    seed + test_number if seed is not None else None
                )

                test_cases.append((
                    f"Generated {test_number + 1}",
                    None,
                    None,
                    generate_puzzle(
                        empty_cells=empty_cells,
                        seed=test_seed
                    ),
                    None,
                ))

                test_number += 1

    # Run every model against every puzzle.
    test_number = 0

    for puzzle_name, dataset_row, rating, puzzle, expected_solution in test_cases:

        test_number += 1
        empty_cells = sum(
            value == 0 for row in puzzle for value in row
        )

        print(f"\n{'=' * 55}")
        print(f"PUZZLE {test_number}: {puzzle_name}")
        print(f"{'=' * 55}")

        for model in models:

            solver = SudukoSolversWork(
                puzzle,
                variable_heuristic=model["variable_heuristic"],
                value_heuristic=model["value_heuristic"],
                use_arc_consistency=model["use_arc_consistency"],
            )

            solved, elapsed_time = run_solver(solver, "csp")

            valid = (
                solved and is_valid_solution(solver.grid, puzzle)
            )

            matches_solution = matches_known_solution(
                solver.grid,
                expected_solution
            )

            result = {
                "test_number": test_number,
                "puzzle_name": puzzle_name,
                "dataset_row": dataset_row,
                "rating": rating,
                "model": model["name"],
                "algorithm": "csp",
                "empty_cells": empty_cells,
                "execution_time_ms": elapsed_time * 1000,
                "solved": solved,
                "valid": valid,
                "matches_known_solution": matches_solution,
                "recursive_calls": solver.recursive_calls,
                "backtrack_steps": solver.backtrack_steps,
                "forward_steps": solver.forward_steps,
                "sa_iterations": None,
                "reheats": None,
            }

            results.append(result)

            print(
                f"{model['name']:<25} "
                f"{elapsed_time * 1000:>10.3f} ms | "
                f"Backtracks: {solver.backtrack_steps:>7} | "
                f"Recursive: {solver.recursive_calls:>7} | "
                f"Solved: {solved}"
            )

    # Export and visualize results.
    export_results_to_csv(results)

    plot_benchmark_results(results, "csp")
