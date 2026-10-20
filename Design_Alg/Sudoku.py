from collections import deque


class SudukoSolversWork:

    def __init__(
        self,
        grid,
        variable_heuristic="mrv",
        value_heuristic="lcv",
        use_arc_consistency=True,
    ):
        if len(grid) != 9 or any(len(row) != 9 for row in grid):
            raise ValueError("Grid must be a 9x9 list of lists.")

        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
            for row in grid
            for value in row
        ):
            raise ValueError("Grid values must be integers between 0 and 9.")

        if variable_heuristic != "mrv":
            raise ValueError("Must choose viable var heuristic")

        if value_heuristic not in ("lcv", "lcb"):
            raise ValueError("Must choose viable val heuristic")

        if not isinstance(use_arc_consistency, bool):
            raise ValueError("use_arc_consistency must be a boolean.")

        self.variable_heuristic = variable_heuristic
        self.value_heuristic = value_heuristic
        self.use_arc_consistency = use_arc_consistency
        self.empty_cell = 0
        self.full_domain = set(range(1, 10))
        self.grid = [row[:] for row in grid]

        # Initialize candidate domains.
        self.domains = self.initialize_domains()

        # Performance statistics.
        self.solved = False
        self.backtrack_steps = 0
        self.forward_steps = 0
        self.recursive_calls = 0


# code from raythepizzo link: https://github.com/PayThePizzo/SudokuSolver.git

    def initialize_domains(self):
        """Initialize the domains for each cell in the 9x9 Sudoku grid.
        The domain of a cell represents the set of possible values (1 to 9)
        that the cell can take, based on the current grid. Initially, all cells
        have the full domain {1, 2, ..., 9}, except for cells that already
        have an assigned value.

        Returns:
            (list): A 9x9 list where each element is a set representing
                the possible values for the corresponding cell.

        Raises:
            ValueError: If a cell's domain is unexpectedly None.
        """
        # 2D Matrix of empty sets for digits 1-9
        domain_matrix = []

        for row in range(9):
            # Row of the Matrix
            domain_row = []

            for col in range(9):
                # Domain of single variable
                domain_cell = None

                if self.grid[row][col] == self.empty_cell:
                    # Assign full domain to non-assigned cell
                    domain_cell = self.full_domain.copy()
                else:
                    # Limit domain of assigned cell
                    domain_cell = {self.grid[row][col]}

                if domain_cell is None:
                    raise ValueError(
                        'Domain cannot be None.'
                    )

                domain_row.append(domain_cell)

            domain_matrix.append(domain_row)

        return domain_matrix

    def update_domains(self, row: int, col: int, num: int) -> bool:

        """Update the domains of other cells when a number is placed.

        This method updates the possible values (domains) of cells in the same
        row, column, and 3x3 subgrid as the cell where a number has been placed.

        Args:
            row (int): The row index of the cell where the number is placed.
            col (int): The column index of the cell where the number is placed.
            num (int): The number placed in the cell.

        Returns:
            bool: Whether every cell still has a non-empty domain.
        """
        # For each variable in same row or col
        for idx in range(9):
            if idx != col:
                # Restrict domains of same-row var
                self.domains[row][idx].discard(num)

            if idx != row:
                # Restrict domains of same-col var
                self.domains[idx][col].discard(num)

        # Find starting indices
        start_row = (row // 3) * 3
        start_col = (col // 3) * 3

        # Update 3x3 subgrid
        for idx_r in range(start_row, start_row + 3):
            for idx_c in range(start_col, start_col + 3):
                if idx_r != row or idx_c != col:
                    # Restrict domain of same-grid var
                    self.domains[idx_r][idx_c].discard(num)

        return all(
            self.domains[r][c]
            for r in range(9)
            for c in range(9)
        )

    def preprocess_domains(self):
        """Preprocess the domains by performing initial constraint propagation.

        This Forward Checking method reduces the initial set of possible values
        for each cell by considering the values already assigned to neighboring
        cells in the same row, column, and subgrid. It applies the rules of
        Sudoku to narrow down possibilities.
        """
        # For each variable
        for row in range(9):
            for col in range(9):
                # If variable's domain is restricted to 1 choice
                if len(self.domains[row][col]) == 1:
                    # Restrict the domains of variables in same row, col and grid
                    self.update_domains(row, col, list(self.domains[row][col])[0])

    def get_neighbors(self, row: int, col: int):
        """Get all neighboring cells (same row, column, or 3x3 subgrid).

        This method returns the neighboring cells that share the same row,
        column, or 3x3 subgrid with the given cell. These neighbors are the
        ones affected by the value of the given cell.

        Args:
            row (int): Row index of the cell.
            col (int): Column index of the cell.

        Returns:
            (set): A set of tuples representing the coordinates (row, col) of the
                neighboring cells.
        """
        neighbors = set()

        # Find row and column neighbors
        for idx in range(9):
            if idx != col:
                neighbors.add((row, idx))

            if idx != row:
                neighbors.add((idx, col))

        # Find starting indices
        start_row = (row // 3) * 3
        start_col = (col // 3) * 3

        # Find 3x3 subgrid neighbors
        for idx_r in range(start_row, start_row + 3):
            for idx_c in range(start_col, start_col + 3):
                if (idx_r, idx_c) != (row, col):
                    neighbors.add((idx_r, idx_c))

        return neighbors

    def revise(self, xi: tuple[int, int], xj: tuple[int, int]):
        """Revise the domain of cell xi to ensure arc consistency with cell xj.

        Arc consistency is ensured by checking if any value in xi's domain is
        inconsistent with xj's domain. If xj has only one possible value, that
        value is removed from xi's domain (if present).

        Args:
            xi (tuple): A tuple (row, col) representing the coordinates of the
                first cell.
            xj (tuple): A tuple (row, col) representing the coordinates of the
                second cell (neighbor).

        Returns:
            (bool): True if xi's domain was revised (values were removed), False
                otherwise.
        """
        revised = False

        # Find coordinated of Xi and Xj
        xi_row, xi_col = xi
        xj_row, xj_col = xj

        # Find domains of Xi and Xj
        domain_xi = self.domains[xi_row][xi_col]
        domain_xj = self.domains[xj_row][xj_col]

        # If no values of Xj allows to satisfy the constraint
        if len(domain_xj) == 1:
            # Retrieve the single constrained value of Xj
            single_value = next(iter(domain_xj))
            # If present in the domain of Xi
            if single_value in domain_xi:
                # Remove it
                domain_xi.discard(single_value)
                revised = True

        return revised

    def maintain_arc_consistency(self):
        """Ensure that the entire puzzle remains arc consistent.

        This method enforces arc consistency throughout the puzzle by using a
        queue of arcs (pairs of cells) and revising domains until no
        contradictions remain.

        Returns:
            (bool): True if the domains are arc consistent, False if a
                contradiction is found (i.e., a cell has an empty domain).
        """
        # Neighbor arcs queue
        queue = deque()

        # Initialize the queue with all arcs (each cell and its neighbors)
        for row in range(9):
            for col in range(9):
                # Find neighbors
                neighbors = self.get_neighbors(row, col)
                # For each neighbor add the arc
                for (nr, nc) in neighbors:
                    queue.append(((row, col), (nr, nc)))

        # Standard AC-3 Procedure
        while queue:
            (xi, xj) = queue.popleft()

            if self.revise(xi, xj):
                # Contradiction found
                if len(self.domains[xi[0]][xi[1]]) == 0:
                    return False

                for neighbor in self.get_neighbors(*xi):
                    # If xi's domain was revised
                    if neighbor != xj:
                        # add its neighbors back to the queue
                        queue.append((neighbor, xi))

        return True


#Most Restricted Variable Heuristic written by Trevor

    def MRVh(self):
        min_possibilites = 10
        chosen = (None,None)
        for row in range(9):
            for col in range(9):
                if self.grid[row][col] == self.empty_cell:
                    possible_vals = len(self.domains[row][col])
                    if 0 < possible_vals < min_possibilites:
                        min_possibilites = possible_vals
                        chosen = (row,col)
        return chosen

#Least Constrained Val Heuristic

    def LCVh(self, row: int, col: int):
        def count_restrictions(value):
            count = 0
            for neighbor in self.get_neighbors(row, col):
                if value in self.domains[neighbor[0]][neighbor[1]]:
                    count += 1
            return count
        return sorted(self.domains[row][col], key=count_restrictions)

#Least Constrained Box Heuristic TREVOR'S HEURISTIC

    def LCBh(self, row, col):
        """Order values by how many candidates remain in the 3x3 box."""

        candidates = list(self.domains[row][col])
        box_scores = {}

        start_row = (row // 3) * 3
        start_col = (col // 3) * 3

        for value in candidates:
            self.grid[row][col] = value

            remaining_candidates = 0

            for r in range(start_row, start_row + 3):
                for c in range(start_col, start_col + 3):

                    if (r, c) == (row, col):
                        continue

                    if self.grid[r][c] == self.empty_cell:
                        used = set(self.grid[r])
                        used.update(self.grid[i][c] for i in range(9))

                        box_row = (r // 3) * 3
                        box_col = (c // 3) * 3

                        used.update(
                            self.grid[i][j]
                            for i in range(box_row, box_row + 3)
                            for j in range(box_col, box_col + 3)
                        )

                        remaining_candidates += len(
                            self.full_domain - used
                        )

            box_scores[value] = remaining_candidates

            # Restore
            self.grid[row][col] = self.empty_cell

        # Try the value that preserves the most options first.
        return sorted(
            candidates,
            key=lambda value: box_scores[value],
            reverse=True
        )

    def select_variable(self):

        if self.variable_heuristic == "mrv":
            return self.MRVh()

        return None, None


    def order_values(self, row, col):

        if self.value_heuristic == "lcv":
            return self.LCVh(row, col)

        if self.value_heuristic == "lcb":
            return self.LCBh(row, col)

        # Baseline: try candidate values in ascending order.
        return sorted(self.domains[row][col])


    def solve(self):
        """Preprocess domains once, then begin backtracking."""

        self.preprocess_domains()

        if self.use_arc_consistency and not self.maintain_arc_consistency():
            return False

        if any(
            not self.domains[row][col]
            for row in range(9)
            for col in range(9)
        ):
            return False

        return self.backtrack()



    def backtrack(self):

        self.recursive_calls += 1

        if any(
            not self.domains[row][col]
            for row in range(9)
            for col in range(9)
        ):
            return False

        row, col = self.select_variable()

        if row is None and col is None:
            self.solved = True
            return True

        possible_vals = self.order_values(row, col)

        for val in possible_vals:
            original_grid = [r[:] for r in self.grid]
            original_domains = [
                [domain.copy() for domain in domain_row]
                for domain_row in self.domains
            ]

            self.grid[row][col] = val
            self.domains[row][col] = {val}
            self.forward_steps += 1

            if self.use_arc_consistency:
                consistent = self.maintain_arc_consistency()
            else:
                consistent = self.update_domains(row, col, val)

            if consistent:
                consistent = all(
                    self.domains[r][c]
                    for r in range(9)
                    for c in range(9)
                )

            if consistent and self.backtrack():
                return True

            self.grid = original_grid
            self.domains = original_domains
            self.backtrack_steps += 1

        return False

    def print_statistics(self):
        print("\n--- Sudoku Solver Statistics ---")
        print(f"Solved: {self.solved}")
        print(f"Backtracking steps: {self.backtrack_steps}")
        print(f"Forward steps: {self.forward_steps}")
        print(f"Recursive calls: {self.recursive_calls}")
