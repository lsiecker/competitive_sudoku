#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import array
import copy
import math
import random
import typing

from numpy import asarray, count_nonzero
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


class Node:
    def __init__(self, move, parent, turn) -> None:
        self.move, self.parent, self.children = move, parent, []
        self.wins, self.visits = 0, 0
        self.my_turn = turn

    def expand(self, state, possibleMoves) -> None:
        """
        Expands the gametree with new child nodes for all possible moves
        @param state: a game state containing a SudokuBoard object
        @param possibleMoves: a list of the possible moves for that gamestate
        """
        if possibleMoves != None:
            for move in possibleMoves:
                child = Node(move, self, not self.my_turn)  # New child node
                self.children.append(child)                 # New child is appended to the current children.

    def update(self, win) -> None:
        """
        Updates the amount of wins for the node
        @param win: boolean that determines if there was a win or not.
        """
        if win:
            self.wins += 1

    def is_leaf(self) -> bool:
        """
        Function that returns a boolean to state if the current node has explored children or not.
        """
        return len(self.children) == 0

    def has_parent(self) -> bool:
        """
        Function that returns a boolean that states if the current node has a parent.
        """
        if self.parent is not None:
            return True
        return False


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self) -> None:
        super().__init__()

    # N.B. This is a very naive implementation.
    def compute_best_move(self, game_state: GameState) -> None:
        N = game_state.board.N

        def checkEmpty(board) -> list[typing.Tuple[int, int]]:
            """
            Finds all the empty cells of the input board
            @param board: a SudokuBoard stored as array of N**2 entries
            """
            emptyCells = []
            for k in range(N**2):
                i, j = SudokuBoard.f2rc(board, k)
                if board.get(i, j) == SudokuBoard.empty:
                    emptyCells.append([i, j])
            return emptyCells

        def getColumn(state, i, j) -> array:
            """
            Gets the column where the position (i,j) is in
            @param state: a game state containing a SudokuBoard object
            @param i: A row value in the range [0, ..., N)
            @param j: A column value in the range [0, ..., N)
            """
            column = []
            for c in range(N):
                column.append(state.board.get(c, j))
            return asarray(column)

        def getRow(state, i, j) -> array:
            """
            Gets the row where the position (i,j) is in
            @param state: a game state containing a SudokuBoard object
            @param i: A row value in the range [0, ..., N)
            @param j: A column value in the range [0, ..., N)
            """
            row = []
            for r in range(N):
                row.append(state.board.get(i, r))
            return asarray(row)

        def getBlock(state, i, j) -> array:
            """
            Gets the block where the position (i,j) is in
            @param state: a game state containing a SudokuBoard object
            @param i: A row value in the range [0, ..., N)
            @param j: A column value in the range [0, ..., N)
            """
            block = []
            x = i - (i % state.board.m)
            y = j - (j % state.board.n)
            for c in range(state.board.m):
                for r in range(state.board.n):
                    block.append(state.board.get(x+c, y+r))
            return asarray(block)

        def getAllPossibleMoves(state) -> list[Move]:
            """
            Finds a list of all possible moves for a given game state
            @param state: a game state containing a SudokuBoard object
            """
            def possible(i, j, value) -> bool:
                """
                Checks whether the given value at position (i,j) is valid for all regions
                    and not a previously tried wrong move
                @param i: A row value in the range [0, ..., N)
                @param j: A column value in the range [0, ..., N)
                @param value: A value in the range [1, ..., N]
                """
                def valueInColumn(i, j, value) -> bool:
                    """
                    Checks whether the given value at position (i,j) is valid for the column
                        i.e. finds if the value already exists in the column
                    @param i: A row value in the range [0, ..., N)
                    @param j: A column value in the range [0, ..., N)
                    @param value: A value in the range [1, ..., N]
                    """
                    return value in getColumn(state, i, j)

                def valueInRow(i, j, value) -> bool:
                    """
                    Checks whether the given value at position (i,j) is valid for the row
                        i.e. finds if the value already exists in the row
                    @param i: A row value in the range [0, ..., N)
                    @param j: A column value in the range [0, ..., N)
                    @param value: A value in the range [1, ..., N]
                    """
                    return value in getRow(state, i, j)

                def valueInBlock(i, j, value) -> bool:
                    """
                    Checks whether the given value at position (i,j) is valid for the block
                        i.e. finds if the value already exists in the block which holds (i,j)
                    @param i: A row value in the range [0, ..., N)
                    @param j: A column value in the range [0, ..., N)
                    @param value: A value in the range [1, ..., N]
                    """
                    return value in getBlock(state, i, j)

                return not TabooMove(i, j, value) in state.taboo_moves \
                    and not valueInColumn(i, j, value) \
                    and not valueInRow(i, j, value) \
                    and not valueInBlock(i, j, value)

            return [Move(cell[0], cell[1], value) for cell in checkEmpty(state.board)
                    for value in range(1, N+1) if possible(cell[0], cell[1], value)]

        def assignScore(move, state) -> int:
            """
            Assigns a score to a move using some heuristic
            @param move: a Move object containing a coordinate and a value
            @param state: a game state containing a SudokuBoard object
            """
            def completeColumn(i, j) -> bool:
                """
                Checks whether the given position (i,j) is the only empty square in the column
                @param i: A row value in the range [0, ..., N)
                @param j: A column value in the range [0, ..., N)
                """
                return count_nonzero(getColumn(state, i, j) == SudokuBoard.empty) == 1
            
            def completeRow(i, j) -> bool:
                """
                Checks whether the given position (i,j) is the only empty square in the row
                @param i: A row value in the range [0, ..., N)
                @param j: A column value in the range [0, ..., N)
                """
                return count_nonzero(getRow(state, i, j) == SudokuBoard.empty) == 1
            
            def completeBlock(i, j) -> bool:
                """
                Checks whether the given position (i,j) is the only empty square in the block
                @param i: A row value in the range [0, ..., N)
                @param j: A column value in the range [0, ..., N)
                """
                return count_nonzero(getBlock(state, i, j) == SudokuBoard.empty) == 1

            # Assign a score based on how many regions are completed
            completedRegions = completeRow(move.i, move.j) + completeColumn(move.i, move.j) + completeBlock(move.i, move.j)
            
            scores = {0: 0, 1: 1, 2: 3, 3: 7}
            return scores[completedRegions]

        def usefulMoves(moves, state) -> list[Move]:
            """
            Compute a list of useful moves, i.e. moves that score at least one point
            @param moves: a list of Move objects to filter
            @param state: a game state containing a SudokuBoard object
            """
            usefulmoves = []

            for move in moves:
                if assignScore(move, state) > 0:
                    usefulmoves.append(move)
            
            if len(usefulmoves) > 0:
                return usefulmoves
            return moves

        def secondToLast(move, state) -> bool:
            """
            Computes whether doing the given move leaves only one empty square in any region
            i.e. finds if there are two empty cells in any region
            @param move: a Move object containing a coordinate and a value
            @param state: a game state containing a SudokuBoard object
            """
            return count_nonzero(getColumn(state, move.i, move.j) == SudokuBoard.empty) == 2 \
                or count_nonzero(getRow(state, move.i, move.j) == SudokuBoard.empty) == 2 \
                or count_nonzero(getBlock(state, move.i, move.j) == SudokuBoard.empty) == 2

        def select_child_UCT(node) -> Node:
            """
            Function that returns the best child based on the UCT property
            @param: node for which you want to know the best child.
            """
            best_child = node.children[0]
            best_value = -9999

            # Loop through the children
            for child in node.children:
                if child.visits == 0:
                    value = 9999
                else:
                    value = child.wins/child.visits
                    # If it is the opponents turn, turn around the value
                    if not node.my_turn:
                        value = 1 - value
                    else:
                        # UCB calculation
                        value = child.wins/child.visits + math.sqrt(2*math.log(child.parent.visits/child.visits))
                
                # Determine best child and return this child
                if best_value < value:
                    best_value = value
                    best_child = child
            return best_child

        def monte_carlo_tree_search(initial_state, iterations) -> Move:
            """
            The MCTS function that constists of 4 phases: Selection, Expansion, Simulation and Backpropagation
            @param initial_state: the game_state that is the initial for the tree
            @param iterations: the number of iterations the algorithm should go through before returning a move
            """

            # Root initialization
            root = Node(None, None, True)

            for _ in range(iterations):
                # For every iteration, get a node and the unmodified initial state
                node, state = root, copy.deepcopy(initial_state)

                ### Selection phase ###
                while not node.is_leaf():
                    node = select_child_UCT(node)
                    state.board.put(node.move.i, node.move.j, node.move.value)

                ### Expansion phase ###
                node.expand(state, usefulMoves(getAllPossibleMoves(state), state)[:10])
                if node.children:
                    best_node = select_child_UCT(node)

                if node.is_leaf() and state.board.squares.count(SudokuBoard.empty) > 0:
                    break

                ### Simulation phase ###
                if node.children:
                    state.board.put(best_node.move.i, best_node.move.j, best_node.move.value)

                # Get current scores of the players
                agent_score = state.scores[0]
                opponent_score = state.scores[1]

                # As long as there are moves, make the moves. If no moves available, game has ended.
                while len(moves := usefulMoves(getAllPossibleMoves(state), state)) > 1:
                    move = random.choice(moves)
                    value = assignScore(move, state)
                    if best_node.my_turn:
                        agent_score += value
                    else:
                        opponent_score += value
                    state.board.put(move.i, move.j, move.value)

                ### Backpropagatin phase ###
                while node:
                    node.visits += 1
                    if node.has_parent():
                        node.update(agent_score > opponent_score)
                        node = node.parent
                    else:
                        break

            # Return the move of the best child in the root
            return select_child_UCT(root).move

        for i in range(1,25):
            self.propose_move(monte_carlo_tree_search(game_state, i))
