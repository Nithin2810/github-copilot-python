from flask import Flask, render_template, jsonify, request
import sudoku_logic

app = Flask(__name__)

# Keep a simple in-memory store for current puzzle and solution
CURRENT = {
    'puzzle': None,
    'solution': None,
    'initial_clues': None,
    'difficulty': None,
}


def _request_board():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    board = data.get("board", data.get("puzzle"))
    if (
        not isinstance(board, list)
        or len(board) != sudoku_logic.SIZE
        or any(not isinstance(row, list) or len(row) != sudoku_logic.SIZE for row in board)
    ):
        return None, "Board must be a 9x9 grid"

    if any(
        type(value) is not int or value < sudoku_logic.EMPTY or value > sudoku_logic.SIZE
        for row in board
        for value in row
    ):
        return None, "Board cells must be integers from 0 to 9"

    return board, None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/new')
def new_game():
    difficulty = request.args.get("difficulty")
    try:
        if difficulty is not None:
            puzzle, solution = sudoku_logic.generate_puzzle(
                difficulty=difficulty
            )
        else:
            clues = int(request.args.get("clues", 35))
            puzzle, solution = sudoku_logic.generate_puzzle(clues)
            difficulty = {
                40: "Easy",
                35: "Medium",
                30: "Hard",
            }.get(clues, "Custom")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    initial_clues = [
        {"row": row, "col": col, "value": value}
        for row, values in enumerate(puzzle)
        for col, value in enumerate(values)
        if value != sudoku_logic.EMPTY
    ]
    CURRENT['puzzle'] = puzzle
    CURRENT['solution'] = solution
    CURRENT['initial_clues'] = initial_clues
    CURRENT['difficulty'] = difficulty
    return jsonify({
        "board": puzzle,
        "puzzle": puzzle,
        "initial_clues": initial_clues,
        "difficulty": difficulty,
    })


@app.route('/hint', methods=['POST'])
def get_hint():
    solution = CURRENT.get("solution")
    if solution is None:
        return jsonify({"error": "No game in progress"}), 400

    board, error = _request_board()
    if error is not None:
        return jsonify({"error": error}), 400

    puzzle = CURRENT["puzzle"]
    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            if (
                puzzle[row][col] == sudoku_logic.EMPTY
                and board[row][col] == sudoku_logic.EMPTY
            ):
                return jsonify({
                    "row": row,
                    "col": col,
                    "value": solution[row][col],
                })

    return jsonify({"error": "No unassigned cells available for a hint"}), 409


@app.route('/check', methods=['POST'])
def check_solution():
    solution = CURRENT.get('solution')
    if solution is None:
        return jsonify({"error": "No game in progress"}), 400

    board, error = _request_board()
    if error is not None:
        return jsonify({"error": error}), 400

    incorrect = []
    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            value = board[row][col]
            if value != sudoku_logic.EMPTY and value != solution[row][col]:
                incorrect.append([row, col])
    complete = not incorrect and all(
        value != sudoku_logic.EMPTY
        for row in board
        for value in row
    )
    return jsonify({"incorrect": incorrect, "complete": complete})


if __name__ == '__main__':
    app.run(debug=True)