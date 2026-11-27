#Least Constrained Box Heuristic TREVOR'S HEURISTIC improved with weights 11/12/2026
def LCB_scores(self, row, col):
        row_weight, column_weight, box_weight = self.lcb_weights
        box_row = (row // 3) * 3
        box_col = (col // 3) * 3
        scores = {}

        for value in self.domains[row][col]:
            score = 0
            contradiction = False

            for peer_col in range(9):
                if peer_col != col and self.grid[row][peer_col] == self.empty_cell:
                    remaining = (
                        len(self.domains[row][peer_col])
                        - (value in self.domains[row][peer_col])
                    )
                    contradiction = contradiction or remaining == 0
                    score += row_weight * remaining

            for peer_row in range(9):
                if peer_row != row and self.grid[peer_row][col] == self.empty_cell:
                    remaining = (
                        len(self.domains[peer_row][col])
                        - (value in self.domains[peer_row][col])
                    )
                    contradiction = contradiction or remaining == 0
                    score += column_weight * remaining

            for peer_row in range(box_row, box_row + 3):
                for peer_col in range(box_col, box_col + 3):
                    if (
                        (peer_row, peer_col) != (row, col)
                        and self.grid[peer_row][peer_col] == self.empty_cell
                    ):
                        remaining = (
                            len(self.domains[peer_row][peer_col])
                            - (value in self.domains[peer_row][peer_col])
                        )
                        contradiction = contradiction or remaining == 0
                        score += box_weight * remaining

            scores[value] = float("-inf") if contradiction else score

        return scores

# Improved Least Constraining Box Heuristic (LCB v2)
def LCB_scores_v2(self, row, col):
    """
    Score each candidate based on its impact on neighboring domains.

    Lower impact is better because it means the candidate
    removes fewer possibilities from constrained neighbors.
    """
    scores = {}

    neighbors = self.get_neighbors(row, col)

    for value in self.domains[row][col]:
        impact = 0.0
        contradiction = False

        for nr, nc in neighbors:
            # Only consider unassigned cells.
            if self.grid[nr][nc] != self.empty_cell:
                continue

            neighbor_domain = self.domains[nr][nc]

            if value in neighbor_domain:
                # Removing the only remaining candidate
                # would create a contradiction.
                if len(neighbor_domain) == 1:
                    contradiction = True
                    break

                # Penalize removing a candidate more heavily
                # when the neighbor has a small domain.
                impact += 1.0 / len(neighbor_domain)

        scores[value] = (
            float("inf") if contradiction else impact
        )

    return scores

def LCBh_v2(self, row, col):
    """
    Order candidate values from lowest domain impact to highest.
    """
    scores = self.LCB_scores_v2(row, col)

    return sorted(
        scores,
        key=lambda value: (scores[value], value)
    )

def LCBh(self, row, col):
    scores = self.LCB_scores(row, col)
    return sorted(scores, key=lambda value: (-scores[value], value))