#Inspired by RayThePizzo Test benchmarks

import csv
import time
import random

from Sudoku import SudukoSolversWork


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


def is_valid_solution(grid):
    """Check whether the completed grid follows Sudoku rules."""

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
    return True

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

def benchmark_solver(solver):
    """Run the solver and report execution time and statistics."""

    result, elapsed_time = run_solver(solver, "csp")

    valid = result and is_valid_solution(solver.grid)

    print("\n--- Sudoku Solver Benchmark ---")
    print(f"Solved: {result}")
    print(f"Valid solution: {valid}")
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
        "execution_time": elapsed_time,
        "recursive_calls": solver.recursive_calls,
        "forward_steps": solver.forward_steps,
        "backtrack_steps": solver.backtrack_steps
    }


def plot_benchmark_results(results, algorithm):
    """Plot individual runtimes and the average runtime for each cell count."""
    import matplotlib.pyplot as plt

    empty_counts = [result["empty_cells"] for result in results]
    runtimes_ms = [result["execution_time_ms"] for result in results]
    grouped_runtimes = {}
    for empty_cells, runtime in zip(empty_counts, runtimes_ms):
        grouped_runtimes.setdefault(empty_cells, []).append(runtime)

    average_empty_counts = sorted(grouped_runtimes)
    average_runtimes = [
        sum(grouped_runtimes[empty_cells]) / len(grouped_runtimes[empty_cells])
        for empty_cells in average_empty_counts
    ]

    plt.figure()
    plt.scatter(empty_counts, runtimes_ms, alpha=0.7, label="Individual tests")
    plt.plot(
        average_empty_counts,
        average_runtimes,
        marker="o",
        label="Average runtime",
    )
    plt.xlabel("Number of empty cells")
    plt.ylabel("Execution time (milliseconds)")
    plt.title(f"Sudoku Solver Runtime ({algorithm.upper()})")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    output_path = "sudoku_benchmark.png"
    plt.savefig(output_path)
    plt.show()
    plt.close()
    print(f"\nBenchmark plot saved to {output_path}")


def export_results_to_csv(results):
    """Write benchmark results to a CSV file."""
    output_path = "sudoku_benchmark.csv"
    fieldnames = [
        "test_number",
        "algorithm",
        "empty_cells",
        "execution_time_ms",
        "solved",
        "valid",
        "recursive_calls",
        "backtrack_steps",
        "forward_steps",
        "sa_iterations",
        "reheats",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nBenchmark results saved to {output_path}")


def get_user_settings():

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
                if empty_counts and all(0 <= count <= 81 for count in empty_counts):
                    break
                print("Enter one or more counts between 0 and 81.")
            except ValueError:
                print("Enter integer counts separated by commas.")

        while True:
            try:
                repetitions = int(input("Trials per empty-cell count: "))
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

    # Choose variable-selection heuristic.
    while True:
        print("\nChoose variable-selection heuristic:")
        print("1. MRV (Minimum Remaining Values)")

        variable_choice = input("Enter 1").strip()

        if variable_choice == "1":
            variable_heuristic = "mrv"
            break
        else:
            print("Invalid choice. Try again.")

    # Choose value-ordering heuristic.
    while True:
        print("\nChoose value-ordering heuristic:")
        print("1. LCV (Least Constraining Value)")
        print("2. LCB (Box-based heuristic)")

        value_choice = input("Enter 1 or 2: ").strip()

        if value_choice == "1":
            value_heuristic = "lcv"
            break
        elif value_choice == "2":
            value_heuristic = "lcb"
            break
        else:
            print("Invalid choice. Try again.")

    while True:
        print("\n Are you using arc consistency?")
        print("1. Yes")
        print("2. No")

        value_choice = input("Enter 1 or 2: ").strip()

        if value_choice == "1":
            use_arc_consistency = True
            break
        elif value_choice == "2":
            use_arc_consistency = False
            break
        else:
            print("Invalid choice. Try again.")
    while True:
        print("\nChoose solving algorithm:")
        print("1. CSP Backtracking")
        print("2. Simulated Annealing")

        algorithm_choice = input("Enter 1 or 2: ").strip()

        if algorithm_choice == "1":
            algorithm = "csp"
            break
        elif algorithm_choice == "2":
            algorithm = "sa"
            break
        else:
            print("Invalid choice. Try again.")
    return (
        empty_counts,
        repetitions,
        batch_mode,
        seed,
        variable_heuristic,
        value_heuristic,
        use_arc_consistency,
        algorithm,
    )


if __name__ == "__main__":
    (
        empty_counts,
        repetitions,
        batch_mode,
        seed,
        variable_heuristic,
        value_heuristic,
        use_arc_consistency,
        algorithm,
    ) = get_user_settings()

    results = []
    test_number = 0
    for empty_cells in empty_counts:
        for _ in range(repetitions):
            test_seed = seed + test_number if seed is not None else None
            puzzle = generate_puzzle(empty_cells=empty_cells, seed=test_seed)
            solver = SudukoSolversWork(
                puzzle,
                variable_heuristic=variable_heuristic,
                value_heuristic=value_heuristic,
                use_arc_consistency=use_arc_consistency,
            )

            if not batch_mode:
                print("\nGenerated Sudoku:")
                for row in puzzle:
                    print(row)

            if not batch_mode and algorithm == "csp":
                benchmark_result = benchmark_solver(solver)
                solved = benchmark_result["solved"]
                valid = benchmark_result["valid"]
                elapsed_time = benchmark_result["execution_time"]
            else:
                solved, elapsed_time = run_solver(solver, algorithm)
                valid = solved and is_valid_solution(solver.grid)

            results.append(
                {
                    "test_number": test_number + 1,
                    "algorithm": algorithm,
                    "empty_cells": empty_cells,
                    "execution_time_ms": elapsed_time * 1000,
                    "solved": solved,
                    "valid": valid,
                    "recursive_calls": (
                        solver.recursive_calls if algorithm == "csp" else None
                    ),
                    "backtrack_steps": (
                        solver.backtrack_steps if algorithm == "csp" else None
                    ),
                    "forward_steps": (
                        solver.forward_steps if algorithm == "csp" else None
                    ),
                    "sa_iterations": (
                        solver.sa_iterations if algorithm == "sa" else None
                    ),
                    "reheats": solver.reheats if algorithm == "sa" else None,
                }
            )

            if batch_mode:
                print(
                    f"Test {test_number + 1}: {empty_cells} empty cells, "
                    f"{elapsed_time * 1000:.3f} ms, "
                    f"solved: {solved}, valid: {valid}"
                )
            elif algorithm == "sa":
                print(f"\nSA Runtime: {elapsed_time * 1000:.3f} milliseconds")
                solver.print_sa_statistics()
                if solved:
                    print("\nSolved Sudoku:")
                    for row in solver.grid:
                        print(row)
                else:
                    print("\nSimulated annealing did not find a solution.")

            test_number += 1

    export_results_to_csv(results)
    plot_benchmark_results(results, algorithm)
