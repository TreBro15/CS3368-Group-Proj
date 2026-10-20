# Simulated annealing solver (Lewis 2007, "Metaheuristics can solve sudoku puzzles")
import math
import random
import statistics

# To use:
#  solver = SudukoSolversWork(grid)
#  solver.solve_sa()
#   solver.print_sa_statistics()

#Changed by Trevor as my grid has 0's that mess up calculations

def sa_cost(self, grid):
    rows = sum(
        9 - len(set(row)) + (0 in row)
        for row in grid
    )

    cols = sum(
        9 - len({grid[r][c] for r in range(9)})
        + (0 in {grid[r][c] for r in range(9)})
        for c in range(9)
    )

    return rows + cols

def sa_random_fill(self, fixed):
    #Fill each 3x3 block's nonfixed (meaning not clues) cells with that block's missing digits,
    # random order, basically just fill all randomly
    grid= [row[:] for row in self.grid]
    for br in range(0,9, 3):
        for bc in range(0, 9, 3):
            cells= [(r, c) for r in range(br,br + 3) for c in range(bc, bc + 3)] #per block
            missing= list(self.full_domain - {grid[r][c] for r, c in cells if fixed[r][c]}) #not fixed
            random.shuffle(missing)
            for r, c in cells:
                if not fixed[r][c]:
                    grid[r][c] = missing.pop()
    return grid


def solve_sa(self, alpha=0.99, stale_limit=20, max_reheats=20):
    """Simulated annealing, swaps 2 non-fixed cells in the same block.
    Reheats w/ a new random grid after stale_limit chains with no improvement.
    """
    fixed= [[v != self.empty_cell for v in row] for row in self.grid]
    # non-fixed cells grouped by block, only blocks with 2+ of them can swap bc u swap both
    blocks= {}
    for r in range(9):
        for c in range(9):
            if not fixed[r][c]:
                blocks.setdefault((r // 3, c // 3), []).append((r, c))
    movable= [cell for cells in blocks.values() if len(cells) > 1 for cell in cells]
    chain_len= sum(len(cells) for cells in blocks.values()) ** 2  # (non-fixed)^2

    def swap(g, a, b):
        g[a[0]][a[1]],g[b[0]][b[1]]=g[b[0]][b[1]], g[a[0]][a[1]]
    def random_move():
        # pick random, then nbeighbor (in block)
        a= random.choice(movable)
        b= random.choice([x for x in blocks[(a[0] // 3, a[1] // 3)] if x != a])
        return a, b

    self.sa_iterations= 0
    self.reheats= 0
    grid= self.sa_random_fill(fixed)
    cost= self.sa_cost(grid)

    if movable:
        #from article, starting temp is stddev of cost over a few random swaps
        probe= [row[:] for row in grid]
        sample= []
        for _ in range(100):
            swap(probe, *random_move())
            sample.append(self.sa_cost(probe))
        t0= statistics.pstdev(sample) or 1.0
        t, stale, prev_best= t0, 0, cost

        while cost > 0:
            best= cost  #lowest cost seen in this chain
            for _ in range(chain_len):
                a, b = random_move()
                swap(grid, a, b)
                new_cost= self.sa_cost(grid)
                delta= new_cost - cost
                self.sa_iterations+= 1
                if delta <= 0 or random.random() < math.exp(-delta / t):
                    cost= new_cost
                    best = min(best, cost)
                    if cost == 0:
                        break
                else:
                    swap(grid, a, b)  #rejected: undo the swap

            t *= alpha
            # no better than last chain = stale
            stale= 0 if best < prev_best else stale + 1
            prev_best= best

            if cost > 0 and stale >= stale_limit:  # stuck: reheat
                if self.reheats >= max_reheats:
                    break
                self.reheats += 1
                grid= self.sa_random_fill(fixed)
                cost= prev_best= self.sa_cost(grid)
                t, stale = t0, 0

    self.solved= cost == 0
    if self.solved:
        self.grid= grid
    return self.solved

def print_sa_statistics(self):
    print("\n--- Simulated Annealing Statistics ---")
    print(f"Solved: {self.solved}")
    print(f"Swaps tried: {self.sa_iterations}")
    print(f"Reheats: {self.reheats}")
