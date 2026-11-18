import copy
import random

SIZE = 9
EMPTY = 0
_DIFFICULTY_CLUES = {
    "Easy": 40,
    "Medium": 35,
    "Hard": 30,
}

def deep_copy(board):
    return copy.deepcopy(board)

def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]

def is_safe(board, row, col, num):
    # Check row and column
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True

def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True

def remove_cells(board, clues):
    attempts = SIZE * SIZE - clues
    while attempts > 0:
        row = random.randrange(SIZE)
        col = random.randrange(SIZE)
        if board[row][col] != EMPTY:
            board[row][col] = EMPTY
            attempts -= 1

def _count_solutions(board, limit=2):
    best_cell = None
    best_candidates = None

    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] != EMPTY:
                continue
            candidates = [
                num
                for num in range(1, SIZE + 1)
                if is_safe(board, row, col, num)
            ]
            if not candidates:
                return 0
            if best_candidates is None or len(candidates) < len(best_candidates):
                best_cell = (row, col)
                best_candidates = candidates
                if len(candidates) == 1:
                    break
        if best_candidates is not None and len(best_candidates) == 1:
            break

    if best_cell is None:
        return 1

    row, col = best_cell
    solution_count = 0
    for candidate in best_candidates:
        board[row][col] = candidate
        solution_count += _count_solutions(board, limit - solution_count)
        board[row][col] = EMPTY
        if solution_count >= limit:
            break
    return solution_count


def has_unique_solution(board):
    if len(board) != SIZE or any(len(row) != SIZE for row in board):
        return False

    if any(
        value != EMPTY
        and (not isinstance(value, int) or value < 1 or value > SIZE)
        for row in board
        for value in row
    ):
        return False

    units = list(board)
    units.extend(
        [board[row][col] for row in range(SIZE)]
        for col in range(SIZE)
    )
    units.extend(
        [
            board[row + row_offset][col + col_offset]
            for row_offset in range(3)
            for col_offset in range(3)
        ]
        for row in range(0, SIZE, 3)
        for col in range(0, SIZE, 3)
    )
    for unit in units:
        values = [value for value in unit if value != EMPTY]
        if len(values) != len(set(values)):
            return False

    return _count_solutions(board) == 1


def _create_unique_puzzle(solution, clues):
    puzzle = deep_copy(solution)
    positions = [
        (row, col)
        for row in range(SIZE)
        for col in range(SIZE)
    ]
    random.shuffle(positions)
    remaining_clues = SIZE * SIZE

    for row, col in positions:
        if remaining_clues == clues:
            break
        value = puzzle[row][col]
        puzzle[row][col] = EMPTY
        if has_unique_solution(puzzle):
            remaining_clues -= 1
        else:
            puzzle[row][col] = value

    if remaining_clues == clues:
        return puzzle
    return None


def generate_puzzle(clues=35, difficulty=None):
    if difficulty is not None:
        try:
            clues = _DIFFICULTY_CLUES[difficulty]
        except KeyError:
            raise ValueError(
                "difficulty must be 'Easy', 'Medium', or 'Hard'"
            ) from None

    if not isinstance(clues, int) or not 17 <= clues <= SIZE * SIZE:
        raise ValueError("clues must be an integer between 17 and 81")

    for _ in range(100):
        solution = create_empty_board()
        if not fill_board(solution):
            raise RuntimeError("Unable to generate a complete Sudoku solution")
        puzzle = _create_unique_puzzle(solution, clues)
        if puzzle is not None:
            return puzzle, solution
    raise RuntimeError("Unable to generate a unique puzzle with the requested clues")
