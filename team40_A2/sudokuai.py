#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import copy
import random
import time
import typing
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai

import numpy as np # TODO: Look at exactly what functions we need from numpy (instead of importing everything)

class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def _init_(self):
        super()._init_()

    def compute_best_move(self, game_state: GameState) -> None:
        start = time.time()
        N = game_state.board.N    

        def checkEmpty(board) -> list[typing.Tuple[int,int]]:
            """
            Finds all the empty cells of the input board
            @param board: a SudokuBoard stored as array of N**2 entries
            """
            emptyCells = []
            for k in range(N**2):
                i,j = SudokuBoard.f2rc(board, k)
                if board.get(i,j) == SudokuBoard.empty:
                    emptyCells.append([i,j])
            return emptyCells

        def getColumn(state, i, j) -> np.array:
            """
            Gets the column where the position (i,j) is in
            @param state: a game state containing a SudokuBoard object
            @param i: A row value in the range [0, ..., N)
            @param j: A column value in the range [0, ..., N)
            """
            column = []
            for c in range(N):
                column.append(state.board.get(c,j))
            return np.asarray(column)

        def getRow(state, i, j) -> np.array:
            row = []
            for r in range(N):
                row.append(state.board.get(i,r))
            return np.asarray(row)

        def getBlock(state, i, j) -> np.array:
            block = []
            x = i - (i % state.board.m)
            y = j - (j % state.board.n)
            for c in range(state.board.m):
                for r in range(state.board.n):
                    block.append(state.board.get(x+c, y+r))
            return np.asarray(block)

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

        self.propose_move(getAllPossibleMoves(game_state)[0])

        def assignScore(move, state) -> int:
            """
            Assigns a score to a move using some heuristic
            @param move: a Move object containing a coordinate and a value
            """

            def completeColumn(i, j) -> bool:
                """
                Checks whether the given position (i,j) is the only empty square in the column
                @param i: A row value in the range [0, ..., N)
                @param j: A column value in the range [0, ..., N)
                """
                return np.count_nonzero(getColumn(state, i, j) == SudokuBoard.empty) == 1
            
            def completeRow(i, j) -> bool:
                """
                Checks whether the given position (i,j) is the only empty square in the row
                @param i: A row value in the range [0, ..., N)
                @param j: A column value in the range [0, ..., N)
                """
                return np.count_nonzero(getRow(state, i, j) == SudokuBoard.empty) == 1
            
            def completeBlock(i, j) -> bool:
                """
                Checks whether the given position (i,j) is the only empty square in the block
                @param i: A row value in the range [0, ..., N)
                @param j: A column value in the range [0, ..., N)
                """
                return np.count_nonzero(getBlock(state, i, j) == SudokuBoard.empty) == 1

            completedRegions = completeRow(move.i, move.j) + completeColumn(move.i, move.j) + completeBlock(move.i, move.j)
            
            scores = {0: 0, 1: 1, 2: 3, 3: 7}
            return scores[completedRegions]

        # def firstMove(moves):
        #     for move in moves:
        #         if not secondToLast(state, move):
        #             return move
        #     return moves[0]


        def usefulMoves(legalmoves):
            usefulmoves = []
            non_usefulmoves = []

            for move in legalmoves:
                if assignScore(move, game_state) > 0:
                    usefulmoves.append(move)
                else:
                    non_usefulmoves.append(move)
            
            if len(non_usefulmoves)>0:
                usefulmoves.extend(non_usefulmoves)
            # print(usefulmoves)
            return usefulmoves
        legalmoves = getAllPossibleMoves(game_state)
        self.propose_move(usefulMoves(legalmoves)[0])
        print(time.time() - start)

        def secondToLast(state, move):

            return np.count_nonzero(getColumn(state, move.i, move.j) == SudokuBoard.empty) == 2 \
                or np.count_nonzero(getRow(state, move.i, move.j) == SudokuBoard.empty) == 2 \
                or np.count_nonzero(getBlock(state, move.i, move.j) == SudokuBoard.empty) == 2
        
        def evaluate(state) -> typing.Tuple[Move, int]:
            """
            Finds the best Move for the given game state
            @param state: a game state containing a SudokuBoard object
            """
            best_value = -1
            # Initalize the best move as a random possible move
            legalmoves = getAllPossibleMoves(game_state)
            moves = usefulMoves(legalmoves)

            best_move = (legalmoves[0])
            notsecondtolast = []
            for move in moves:
                if not secondToLast(state, move):
                    notsecondtolast.append(move)
            
            moves = notsecondtolast if len(notsecondtolast) > 0 else moves

            for move in moves:
                value = assignScore(move, state)
                if value > best_value:
                    best_move = move
                    best_value = value

            return best_move, best_value
                

        def minimax(state, isMaximizingPlayer, max_depth, current_depth = 0, current_score = 0, transposition_table = {}, alpha=float("-inf"), beta=float("inf")) -> typing.Tuple[Move, int]:
            """
            Makes a tree to a given depth and returns the move a node needs to make to get a certain value
            @param state: a game state containing a SudokuBoard object
            @param isMaximizingPlayer: a boolean value which determines if the player is maximizing
            @param max_depth: a depth value which defines when to terminate the tree search
            @param current_depth: a depth value which defines the current depth
            @param current_score: a score value which defines the score of the parent node 
            """

            # print("empty cells: ", state.board.squares.count(game_state.board.empty)%2)
            alphaOrig = alpha

            if state in transposition_table:
                trans_move, trans_value, trans_depth, trans_alphabeta = transposition_table[state]
                if max_depth - trans_depth < max_depth - current_depth:
                    if trans_alphabeta == "EXACT":
                        return trans_move, trans_value + current_score
                    elif trans_alphabeta == "LOWERBOUND":
                        alpha = max(alpha, trans_value)
                    elif trans_alphabeta == "UPPERBOUND":
                        beta = min(beta, trans_value)
                    if alpha >= beta:
                        return trans_move, trans_value + current_score

            # If there are no possible moves (when no move is valid), return a infinite value
            if len(getAllPossibleMoves(state)) == 0:
                if isMaximizingPlayer:
                    return None, float("-inf")
                return None, float("inf")

            # If the tree is in the final leaf, resturn a move and value
            if len(getAllPossibleMoves(state)) == 1 or current_depth == max_depth:
                move, value = evaluate(state)
                transposition_table[state] = (move, value+current_score, current_depth, "EXACT")
                if isMaximizingPlayer:
                    return move, value
                return move, -value

            if isMaximizingPlayer:
                best_move = Move(0,0,0)
                best_value = float("-inf")
                for move in getAllPossibleMoves(state):
                    total_score = current_score + assignScore(move, state)
                    state.board.put(move.i, move.j, move.value)
                    result_move, result_value = minimax(state, not isMaximizingPlayer, max_depth, current_depth+1, total_score, transposition_table, alpha, beta)
                    state.board.put(move.i, move.j, SudokuBoard.empty)
                    if result_value > best_value:
                        best_move = move
                        best_value = result_value
                    alpha = max(alpha, best_value)
                    if beta <= alpha:
                        break
            else:
                best_move = Move(0,0,0)
                best_value = float("inf")
                for move in getAllPossibleMoves(state):
                    total_score = current_score - assignScore(move, state)
                    state.board.put(move.i, move.j, move.value)
                    result_move, result_value = minimax(state, not isMaximizingPlayer, max_depth, current_depth+1, total_score, transposition_table, alpha, beta)
                    state.board.put(move.i, move.j, SudokuBoard.empty)
                    if result_value < best_value:
                        best_move = move
                        best_value = result_value
                    beta = min(beta, best_value)
                    if beta <= alpha:
                        break

            if best_value <= alphaOrig:
                alphabeta = "UPPERBOUND"
            elif best_value >= beta:
                alphabeta = "LOWERBOUND"
            else:
                alphabeta = "EXACT"

            transposition_table[state] = (best_move, best_value+current_score, current_depth, alphabeta)
            return best_move, best_value + current_score

        #  Intialize a random possible move as return
        # (to ensure we always have a return ready on timeout)
        start = time.time()

        emptyCells = game_state.board.squares.count(game_state.board.empty)

        # self.propose_move(firstMove(legalmoves))
        if emptyCells > 55:
            legalmoves = getAllPossibleMoves(game_state)
            self.propose_move(usefulMoves(legalmoves)[0])
            # print("1:", time.time() - start)
        elif emptyCells > 30:
            for depth in range(0, game_state.board.squares.count(SudokuBoard.empty)):
                move, value = minimax(game_state, True, depth)
                self.propose_move(move)
                # print("2:", time.time() - start)
        else:
            for depth in range(0, game_state.board.squares.count(SudokuBoard.empty)):
                move, value = minimax(game_state, True, depth)
                self.propose_move(move)        
                # print("3", time.time() - start)