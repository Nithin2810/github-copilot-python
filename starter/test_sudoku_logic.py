from unittest.mock import Mock

import pytest

import sudoku_logic


SOLVABLE_PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


def assert_complete_valid_board(board):
    expected = set(range(1, sudoku_logic.SIZE + 1))

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(set(row) == expected for row in board)
    assert all(
        {board[row][col] for row in range(sudoku_logic.SIZE)} == expected
        for col in range(sudoku_logic.SIZE)
    )
    assert all(
        {
            board[row + row_offset][col + col_offset]
            for row_offset in range(3)
            for col_offset in range(3)
        }
        == expected
        for row in range(0, sudoku_logic.SIZE, 3)
        for col in range(0, sudoku_logic.SIZE, 3)
    )


def test_deep_copy_is_equal_but_independent():
    board = [[1, 2], [3, 4]]

    copied = sudoku_logic.deep_copy(board)

    assert copied == board
    assert copied is not board
    assert copied[0] is not board[0]
    copied[0][0] = 9
    assert board[0][0] == 1


def test_create_empty_board_has_nine_independent_rows():
    board = sudoku_logic.create_empty_board()

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(cell == sudoku_logic.EMPTY for row in board for cell in row)

    board[0][0] = 1
    assert board[1][0] == sudoku_logic.EMPTY


@pytest.mark.parametrize(
    ("row", "col"),
    [(4, 4), (0, 0), (8, 8)],
)
def test_is_safe_returns_true_when_number_is_absent(row, col):
    assert sudoku_logic.is_safe(
        sudoku_logic.create_empty_board(), row, col, 5
    )


@pytest.mark.parametrize(
    ("occupied_row", "occupied_col"),
    [
        (4, 0),  # Same row
        (0, 4),  # Same column
        (3, 3),  # Same 3x3 box
    ],
)
def test_is_safe_rejects_number_in_row_column_or_box(
    occupied_row, occupied_col
):
    board = sudoku_logic.create_empty_board()
    board[occupied_row][occupied_col] = 5

    assert not sudoku_logic.is_safe(board, 4, 4, 5)


def test_fill_board_solves_puzzle_and_preserves_clues():
    board = sudoku_logic.deep_copy(SOLVABLE_PUZZLE)
    clues = [
        (row, col, value)
        for row, values in enumerate(board)
        for col, value in enumerate(values)
        if value != sudoku_logic.EMPTY
    ]

    assert sudoku_logic.fill_board(board) is True

    assert_complete_valid_board(board)
    assert all(board[row][col] == value for row, col, value in clues)


def test_fill_board_returns_false_when_first_empty_cell_has_no_candidate():
    board = sudoku_logic.create_empty_board()
    board[0][:8] = list(range(1, 9))
    board[1][8] = 9
    original = sudoku_logic.deep_copy(board)

    assert sudoku_logic.fill_board(board) is False
    assert board == original


def test_has_unique_solution_accepts_unique_puzzle_without_mutating_it():
    board = sudoku_logic.deep_copy(SOLVABLE_PUZZLE)
    original = sudoku_logic.deep_copy(board)

    assert sudoku_logic.has_unique_solution(board) is True
    assert board == original


def test_has_unique_solution_rejects_multiple_solutions_and_conflicts():
    assert sudoku_logic.has_unique_solution(sudoku_logic.create_empty_board()) is False

    conflicting_board = sudoku_logic.create_empty_board()
    conflicting_board[0][0] = 1
    conflicting_board[0][1] = 1
    assert sudoku_logic.has_unique_solution(conflicting_board) is False


def test_remove_cells_removes_exact_number_of_cells(monkeypatch):
    board = [list(range(row * 9 + 1, row * 9 + 10)) for row in range(9)]
    positions = iter([0, 0, 0, 0, 0, 1, 0, 2])
    monkeypatch.setattr(
        sudoku_logic.random, "randrange", Mock(side_effect=positions)
    )

    sudoku_logic.remove_cells(board, clues=78)

    assert board[0][0] == sudoku_logic.EMPTY
    assert board[0][1] == sudoku_logic.EMPTY
    assert board[0][2] == sudoku_logic.EMPTY
    assert sum(cell != sudoku_logic.EMPTY for row in board for cell in row) == 78


def test_remove_cells_does_nothing_when_board_already_has_requested_clues(
    monkeypatch,
):
    board = sudoku_logic.create_empty_board()
    monkeypatch.setattr(sudoku_logic.random, "randrange", pytest.fail)

    sudoku_logic.remove_cells(board, clues=81)

    assert board == sudoku_logic.create_empty_board()


@pytest.mark.parametrize("clues", [35, 81])
def test_generate_puzzle_returns_consistent_puzzle_and_solution(clues):
    puzzle, solution = sudoku_logic.generate_puzzle(clues)

    assert_complete_valid_board(solution)
    assert sudoku_logic.has_unique_solution(puzzle)
    assert len(puzzle) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in puzzle)
    assert (
        sum(cell != sudoku_logic.EMPTY for row in puzzle for cell in row)
        == clues
    )
    assert all(
        value == sudoku_logic.EMPTY or value == solution[row][col]
        for row, values in enumerate(puzzle)
        for col, value in enumerate(values)
    )


def test_generate_puzzle_uses_35_clues_by_default():
    puzzle, solution = sudoku_logic.generate_puzzle()

    assert_complete_valid_board(solution)
    assert sudoku_logic.has_unique_solution(puzzle)
    assert (
        sum(cell != sudoku_logic.EMPTY for row in puzzle for cell in row)
        == 35
    )


@pytest.mark.parametrize(
    ("difficulty", "expected_clues"),
    [("Easy", 40), ("Medium", 35), ("Hard", 30)],
)
def test_generate_puzzle_selects_unique_puzzle_for_difficulty(
    difficulty, expected_clues
):
    puzzle, solution = sudoku_logic.generate_puzzle(difficulty=difficulty)

    assert_complete_valid_board(solution)
    assert (
        sum(cell != sudoku_logic.EMPTY for row in puzzle for cell in row)
        == expected_clues
    )
    assert sudoku_logic.has_unique_solution(puzzle)


def test_generate_puzzle_rejects_unknown_difficulty():
    with pytest.raises(ValueError, match="difficulty must be"):
        sudoku_logic.generate_puzzle(difficulty="Expert")


def test_generate_puzzle_rejects_clue_counts_that_cannot_be_unique():
    with pytest.raises(ValueError, match="clues must be"):
        sudoku_logic.generate_puzzle(clues=16)


def test_generate_puzzle_returns_independent_puzzle_and_solution():
    puzzle, solution = sudoku_logic.generate_puzzle(clues=81)
    original_value = solution[0][0]

    puzzle[0][0] = sudoku_logic.EMPTY

    assert solution[0][0] == original_value