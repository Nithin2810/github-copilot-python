import copy

import pytest

import app as sudoku_app
import sudoku_logic


@pytest.fixture
def client():
    sudoku_app.app.config["TESTING"] = True
    sudoku_app.CURRENT.update({
        "puzzle": None,
        "solution": None,
        "initial_clues": None,
        "difficulty": None,
    })
    with sudoku_app.app.test_client() as test_client:
        yield test_client


def test_new_game_returns_board_initial_clues_and_difficulty(client):
    response = client.get("/new?difficulty=Hard")

    assert response.status_code == 200
    payload = response.get_json()
    board = payload["board"]
    assert payload["puzzle"] == board
    assert payload["difficulty"] == "Hard"
    assert len(payload["initial_clues"]) == 30
    assert all(
        board[clue["row"]][clue["col"]] == clue["value"]
        for clue in payload["initial_clues"]
    )


def test_new_game_defaults_to_medium_and_keeps_legacy_puzzle_field(client):
    response = client.get("/new")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["difficulty"] == "Medium"
    assert payload["puzzle"] == payload["board"]
    assert len(payload["initial_clues"]) == 35


def test_new_game_keeps_legacy_clues_parameter(client):
    response = client.get("/new?clues=81")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["difficulty"] == "Custom"
    assert len(payload["initial_clues"]) == 81


@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("?difficulty=Expert", "difficulty must be"),
        ("?clues=invalid", "invalid literal"),
    ],
)
def test_new_game_returns_bad_request_for_invalid_parameters(
    client, query, message
):
    response = client.get(f"/new{query}")

    assert response.status_code == 400
    assert message in response.get_json()["error"]


def test_hint_requires_an_active_game(client):
    response = client.post("/hint", json={"board": sudoku_logic.create_empty_board()})

    assert response.status_code == 400
    assert response.get_json()["error"] == "No game in progress"


def test_hint_returns_solution_value_for_an_unassigned_cell(client):
    client.get("/new?difficulty=Easy")
    puzzle = sudoku_app.CURRENT["puzzle"]
    solution = sudoku_app.CURRENT["solution"]

    response = client.post("/hint", json={"puzzle": copy.deepcopy(puzzle)})

    assert response.status_code == 200
    hint = response.get_json()
    row, col = hint["row"], hint["col"]
    assert puzzle[row][col] == sudoku_logic.EMPTY
    assert hint["value"] == solution[row][col]


def test_hint_returns_conflict_when_no_cells_are_unassigned(client):
    client.get("/new?difficulty=Easy")
    solution = sudoku_app.CURRENT["solution"]

    response = client.post("/hint", json={"board": solution})

    assert response.status_code == 409
    assert response.get_json()["error"] == "No unassigned cells available for a hint"


def test_check_validates_filled_entries_and_reports_completion(client):
    client.get("/new?difficulty=Easy")
    solution = sudoku_app.CURRENT["solution"]
    puzzle = copy.deepcopy(sudoku_app.CURRENT["puzzle"])
    response = client.post("/check", json={"board": puzzle})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [], "complete": False}

    board = copy.deepcopy(puzzle)
    row, col = next(
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if board[row][col] == sudoku_logic.EMPTY
    )
    board[row][col] = solution[row][col] % sudoku_logic.SIZE + 1

    response = client.post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [[row, col]],
        "complete": False,
    }

    response = client.post("/check", json={"board": solution})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [], "complete": True}


def test_check_requires_an_active_game(client):
    response = client.post("/check", json={"board": sudoku_logic.create_empty_board()})

    assert response.status_code == 400
    assert response.get_json()["error"] == "No game in progress"


@pytest.mark.parametrize(
    "board",
    [
        [],
        [[0] * sudoku_logic.SIZE for _ in range(sudoku_logic.SIZE - 1)],
        [[0] * sudoku_logic.SIZE for _ in range(sudoku_logic.SIZE - 1)]
        + [[10] * sudoku_logic.SIZE],
    ],
)
def test_check_rejects_malformed_board(client, board):
    client.get("/new")

    response = client.post("/check", json={"board": board})

    assert response.status_code == 400
    assert "error" in response.get_json()
