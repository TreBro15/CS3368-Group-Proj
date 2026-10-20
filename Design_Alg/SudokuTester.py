#Inspired by RayThePizzo Test benchmarks

import time
import random

from Sudoku import SudukoSolversWork


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

    start_time = time.perf_counter()
    result = solver.solve()
    elapsed_time = time.perf_counter() - start_time

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
    
def get_user_settings():
    
    while True:
        try:
            empty_cells = int(input("Enter the number of empty cells (0-81): "))
            if 0 <= empty_cells <= 81:
                break
            print("Please enter a number between 0 and 81.")
        except ValueError:
            print("Please enter a valid integer.")

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
    return empty_cells, seed, variable_heuristic, value_heuristic, use_arc_consistency, algorithm




if __name__ == "__main__":
    empty_cells, seed, variable_heuristic, value_heuristic, use_arc_consistency, algorithm = (
        get_user_settings()
    )

    puzzle = generate_puzzle(
        empty_cells=empty_cells,
        seed=seed
    )

    print("\nGenerated Sudoku:")
    for row in puzzle:
        print(row)

    solver = SudukoSolversWork(
        puzzle,
        variable_heuristic=variable_heuristic,
        value_heuristic=value_heuristic,
        use_arc_consistency=use_arc_consistency
    )

    if algorithm == "csp":
        benchmark_solver(solver)

    elif algorithm == "sa":
        import time

        start_time = time.perf_counter()
        result = solver.solve_sa()
        elapsed_time = time.perf_counter() - start_time

        print(f"\nSA Runtime: {elapsed_time*1000:.3f} milliseconds")
        solver.print_sa_statistics()

        if result:
            print("\nSolved Sudoku:")
            for row in solver.grid:
                print(row)
        else:
            print("\nSimulated annealing did not find a solution.")

