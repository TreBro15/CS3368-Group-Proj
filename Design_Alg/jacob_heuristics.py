#Conflict based heuristic
#Uses MRV first and checks neighboring cells for a tie
#Built neighbors at start to cut back runtime

def build_peers():
    peers={}

    for row in range(9):
        for col in range(9):
            neighbors=[]

            for r in range(9):
                for c in range(9):

                    if row==r and col==c:
                        continue

                    same_row=r==row
                    same_col=c==col
                    same_box=(row//3==r//3 and col//3==c//3)

                    if same_row or same_col or same_box:
                        neighbors.append((r,c))

            peers[(row,col)]=tuple(neighbors)
    return peers
PEERS = build_peers()

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