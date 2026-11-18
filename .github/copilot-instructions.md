# GitHub Copilot Instructions - Sudoku Project

## Project Structure & Architecture

- **Backend**: Flask application located in `starter/app.py` and `starter/sudoku_logic.py`.
- **Frontend**: Vanilla JavaScript (`starter/static/main.js`), CSS (`starter/static/styles.css`), and HTML (`starter/templates/index.html`).
- **Testing**: Automated test suite written with `pytest` in `starter/test_sudoku_logic.py`.

## Core Requirements & Rules

- **Puzzle Generation**: Puzzles must support Easy, Medium, and Hard difficulty levels mapping to specific clue counts, and guarantee a single unique solution using a backtracking solver.
- **Frontend Interactivity**: Includes a stopwatch timer, live conflict highlighting, hint system (locking correct cells), dark/light mode toggle, and Top 10 fastest times leaderboard persisted in browser `localStorage`.
- **Error Handling**: Invalid user moves or rule violations instantly trigger visual conflict highlighting (red background) on the grid.
- **Testing**: All core logic must be covered by unit tests, ensuring correctness and robustness.
