# CS3368-Group-Proj

CS3368 Group Project working on solving Sudoku puzzles with backtracking

Initial Peer Reviewed Articles:
https://www.sciencedirect.com/science/article/pii/S0004370221001016?pes=vor&utm_source=scopus&getft_integrator=scopus - Trevor

https://link.springer.com/article/10.1007/s10732-007-9012-8 - Ahmad

https://www.dbai.tuwien.ac.at/research/project/arte/sudoku/HybridHeuristicApproachForSudoku.pdf - Jacob

Presentation: https://texastechuniversity-my.sharepoint.com/:p:/g/personal/bro32090_ttu_edu/IQBeIznnRzyAT4A1yYQTDA-rAeBoDqZN10ozVw9KxdgPvvQ?e=dBhPHY

Possible Code: https://github.com/PayThePizzo/SudokuSolver

# To Run Code
- cd to work path
- clone this repository
- cd to `Design_Alg`
- run `python SudokuTester.py`
- choose configuration of your choice and see results

The tester can solve generated puzzles or load a puzzle dataset from CSV. By
default, dataset mode reads `Design_Alg/sudoku_puzzles.csv`; enter another path
to use a different file. Dataset CSVs must have a `puzzle` column containing
81 digits (`0` for blanks; `.` is also accepted). An optional `name` or `id`
column labels results, and an optional `solution` column lets the tester report
whether its answer matches the dataset's known answer. A valid Sudoku solution
that preserves the clues is reported as valid even if it differs from the
provided answer, since a puzzle may admit multiple solutions.

# Dataset (Kaggle)
### Dataset is too large to run through GitHub so please download from https://www.kaggle.com/datasets/radcliffe/3-million-sudoku-puzzles-with-ratings
For large files such as Kaggle's Sudoku dataset, choose either a specific
1-based CSV data row (the header is not counted) or a random sample size. Random
sampling uses reservoir sampling, so only the requested number of puzzles is
kept in memory; an optional seed makes the sample repeatable. You can also set
minimum and maximum difficulty/rating filters when the CSV has a `difficulty`,
`rating`, or `difficulty rating` column. The full CSV is scanned when sampling
or filtering to produce an unbiased sample.

Trevor's Model:
The LCB value-ordering heuristic scores each candidate by the weighted number
of candidates it preserves in peer cells. Its default row, column, and box
weights are `(1.0, 1.0, 1.5)` and can be overridden with the solver's
`lcb_weights` argument.

## How Results are Displayed
Graphical Results should automatically display after run
Tabular Results are stored in sudoku_benchmark.csv for viewing

### Who did what (models):
Trevor: MRV, LCB, tester, benchmark, and the Kaggle loader

Ahmad: SA approach.

Jacob: the conflict heuristic.

Shared code: taken from the PayThePizzo repo.
