#Conflict based heuristic
#Uses MRV first and checks neighboring cells for a tie

def conflict_heuristic(self):
    fewest=10
    most_conflicts=-1
    chosen=(None,None)

    for row in range(9):
        for col in range(9):
            if self.grid[row][col]!= self.empty_cell:
                continue

            possible = self.domains[row][col]
            if len(possible)== 0:
                continue

            conflicts=0

            #check how many numbers neighbors share
            for r, c in self.get_neighbors(row,col):
                if self.grid[r][c]== self.empty_cell:
                    conflicts += len(possible & self.domains[r][c])

            #choose fewest options first then highest conflicts
            if len(possible)<fewest or (
                len(possible)==fewest and conflicts>most_conflicts
            ):
                fewest=len(possible)
                most_conflicts=conflicts
                chosen=(row,col)

    return chosen