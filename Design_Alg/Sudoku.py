import logging
import os
import pandas as pd 
import matplotlib.pyplot as plt

class SudukoSolversWork:

    def __init__(self, grid):
        if len(grid) != 9 or any(len(row) != 9 for row in grid):
            raise ValueError("Grid must be a 9x9 list of lists.")

        self.empty_cell = 0
        self.full_domain = set(range(1, 10))
        self.grid = [row[:] for row in grid]

        # Initialize candidate domains.
        self.domains = self.initialize_domains()

        # Performance statistics.
        self.solved = False
        self.backtrack_steps = 0
        self.forward_steps = 0
        self.ac3_revisions = 0
        self.ac3_contradictions = 0
        self.mrv_invocations = 0
        self.recursive_calls = 0
    
    def print_statistics(self):
        print("\n--- Sudoku Solver Statistics ---")
        print(f"Solved: {self.solved}")
        print(f"Backtracking steps: {self.backtrack_steps}")
        print(f"Forward steps: {self.forward_steps}")
        print(f"AC-3 revisions: {self.ac3_revisions}")
        print(f"AC-3 contradictions: {self.ac3_contradictions}")
        print(f"MRV invocations: {self.mrv_invocations}")
        print(f"Recursive calls: {self.recursive_calls}")
