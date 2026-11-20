// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const THEME_STORAGE_KEY = 'sudoku-theme';
const LEADERBOARD_STORAGE_KEY = 'sudoku-leaderboard';
let puzzle = [];
let currentDifficulty = 'Medium';
let gameStartedAt = null;
let elapsedTimeMs = 0;
let timerInterval = null;
let gameWon = false;
let pendingScore = null;

function updateThemeToggle() {
    const isDark = document.documentElement.dataset.theme === 'dark';
    const toggle = document.getElementById('theme-toggle');
    toggle.setAttribute('aria-pressed', String(isDark));
    toggle.textContent = isDark ? 'Switch to light mode' : 'Switch to dark mode';
}

function setTheme(theme, persist = false) {
    document.documentElement.dataset.theme = theme;
    if (persist) {
        localStorage.setItem(THEME_STORAGE_KEY, theme);
    }
    updateThemeToggle();
}

const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
document.documentElement.dataset.theme = savedTheme === 'dark' ? 'dark' : 'light';

function setMessage(text, status = '') {
    const message = document.getElementById('message');
    message.textContent = text;
    message.className = status ? `message ${status}` : 'message';
}

function formatTime(milliseconds) {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    const pad = (value) => String(value).padStart(2, '0');

    if (hours > 0) {
        return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    }
    return `${pad(minutes)}:${pad(seconds)}`;
}

function updateTimerDisplay() {
    const elapsed = gameStartedAt === null ?
        elapsedTimeMs :
        performance.now() - gameStartedAt;
    document.getElementById('timer-display').textContent = formatTime(elapsed);
}

function startTimer() {
    if (timerInterval !== null) {
        window.clearInterval(timerInterval);
    }
    elapsedTimeMs = 0;
    gameStartedAt = performance.now();
    updateTimerDisplay();
    timerInterval = window.setInterval(updateTimerDisplay, 250);
}

function stopTimer() {
    if (gameStartedAt === null) {
        return elapsedTimeMs;
    }
    elapsedTimeMs = performance.now() - gameStartedAt;
    gameStartedAt = null;
    if (timerInterval !== null) {
        window.clearInterval(timerInterval);
        timerInterval = null;
    }
    updateTimerDisplay();
    return elapsedTimeMs;
}

function loadLeaderboard() {
    const savedRecords = localStorage.getItem(LEADERBOARD_STORAGE_KEY);
    if (savedRecords === null) {
        return [];
    }

    let records;
    try {
        records = JSON.parse(savedRecords);
    } catch (error) {
        if (!(error instanceof SyntaxError)) {
            throw error;
        }
        console.error('The saved Sudoku leaderboard is not valid JSON.', error);
        return [];
    }

    if (!Array.isArray(records)) {
        console.error('The saved Sudoku leaderboard must be a list.');
        return [];
    }
    return records.filter((record) => (
        record !== null &&
        typeof record === 'object' &&
        typeof record.name === 'string' &&
        Number.isFinite(record.timeMs) &&
        typeof record.difficulty === 'string'
    ));
}

function renderLeaderboard(records = loadLeaderboard()) {
    const tableBody = document.getElementById('leaderboard-body');
    const emptyMessage = document.getElementById('leaderboard-empty');
    const sortedRecords = [...records]
        .sort((first, second) => first.timeMs - second.timeMs)
        .slice(0, 10);

    tableBody.replaceChildren();
    sortedRecords.forEach((record, index) => {
        const row = document.createElement('tr');
        const values = [
            String(index + 1),
            record.name,
            formatTime(record.timeMs),
            record.difficulty,
        ];
        values.forEach((value) => {
            const cell = document.createElement('td');
            cell.textContent = value;
            row.appendChild(cell);
        });
        tableBody.appendChild(row);
    });
    emptyMessage.hidden = sortedRecords.length > 0;
}

function saveLeaderboardEntry(name, timeMs, difficulty) {
    const records = loadLeaderboard();
    records.push({ name, timeMs, difficulty });
    records.sort((first, second) => first.timeMs - second.timeMs);
    const topTen = records.slice(0, 10);
    localStorage.setItem(LEADERBOARD_STORAGE_KEY, JSON.stringify(topTen));
    renderLeaderboard(topTen);
}

function showNamePrompt(timeMs) {
    pendingScore = { timeMs, difficulty: currentDifficulty };
    document.getElementById('win-summary').textContent =
        `You completed ${currentDifficulty} in ${formatTime(timeMs)}.`;
    const nameInput = document.getElementById('player-name');
    nameInput.value = '';
    nameInput.setCustomValidity('');
    document.getElementById('player-dialog').showModal();
    nameInput.focus();
}

function getCurrentBoard() {
    const inputs = document
        .getElementById('sudoku-board')
        .getElementsByTagName('input');
    const board = [];
    for (let row = 0; row < SIZE; row++) {
        board[row] = [];
        for (let col = 0; col < SIZE; col++) {
            const value = inputs[row * SIZE + col].value;
            board[row][col] = value ? parseInt(value, 10) : 0;
        }
    }
    return board;
}

function createBoardElement() {
    const boardDiv = document.getElementById('sudoku-board');
    boardDiv.innerHTML = '';
    for (let i = 0; i < SIZE; i++) {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'sudoku-row';
        for (let j = 0; j < SIZE; j++) {
            const input = document.createElement('input');
            input.type = 'text';
            input.maxLength = 1;
            input.className = 'sudoku-cell';
            input.dataset.row = i;
            input.dataset.col = j;
            if ((Math.floor(i / 3) + Math.floor(j / 3)) % 2 === 1) {
                input.classList.add('subgrid-shaded');
            }
            input.addEventListener('input', (e) => {
                const val = e.target.value.replace(/[^1-9]/g, '');
                e.target.value = val;

                // Clear all previous live conflict highlights
                document
                    .querySelectorAll('.sudoku-cell.invalid-entry')
                    .forEach((cell) => cell.classList.remove('invalid-entry'));

                // Re-check every filled cell on the current board
                const currentBoard = getCurrentBoard();
                for (let r = 0; r < SIZE; r++) {
                    for (let c = 0; c < SIZE; c++) {
                        const cellVal = currentBoard[r][c];
                        if (cellVal > 0) {
                            checkConflict(r, c, cellVal);
                        }
                    }
                }
            });
            rowDiv.appendChild(input);
        }
        boardDiv.appendChild(rowDiv);
    }
}

function findConflicts(board, row, col, value) {
    const conflicts = [];
    if (!value || value < 1 || value > SIZE) {
        return conflicts;
    }

    // Check same row
    for (let c = 0; c < SIZE; c++) {
        if (c !== col && board[row][c] === value) {
            conflicts.push([row, c]);
        }
    }

    // Check same column
    for (let r = 0; r < SIZE; r++) {
        if (r !== row && board[r][col] === value) {
            conflicts.push([r, col]);
        }
    }

    // Check same 3x3 box
    const startRow = Math.floor(row / 3) * 3;
    const startCol = Math.floor(col / 3) * 3;
    for (let r = startRow; r < startRow + 3; r++) {
        for (let c = startCol; c < startCol + 3; c++) {
            if ((r !== row || c !== col) && board[r][c] === value) {
                conflicts.push([r, c]);
            }
        }
    }

    // Highlight the newly entered/conflicting cell itself too
    if (conflicts.length > 0) {
        conflicts.push([row, col]);
    }

    return conflicts;
}

function checkConflict(row, col, value) {
    const board = getCurrentBoard();
    const conflicts = findConflicts(board, row, col, value);
    conflicts.forEach(([r, c]) => {
        const cell = getCellElement(r, c);
        if (cell) {
            cell.classList.add('invalid-entry');
        }
    });
    return conflicts.length === 0;
}

function getCellElement(row, col) {
    const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
    return inputs[row * SIZE + col];
}

function renderPuzzle(puz) {
    puzzle = puz;
    createBoardElement();
    const boardDiv = document.getElementById('sudoku-board');
    const inputs = boardDiv.getElementsByTagName('input');
    for (let i = 0; i < SIZE; i++) {
        for (let j = 0; j < SIZE; j++) {
            const idx = i * SIZE + j;
            const val = puzzle[i][j];
            const inp = inputs[idx];
            if (val !== 0) {
                inp.value = val;
                inp.disabled = true;
                inp.classList.add('prefilled');
            } else {
                inp.value = '';
                inp.disabled = false;
            }
        }
    }
}

async function newGame() {
    const difficulty = document.getElementById('difficulty-select').value;
    const res = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
    const data = await res.json();
    if (!res.ok || data.error) {
        setMessage(data.error || 'Unable to start a new game.', 'error');
        return;
    }
    renderPuzzle(data.puzzle);
    currentDifficulty = data.difficulty;
    gameWon = false;
    document.getElementById('hint-button').disabled = false;
    startTimer();
    setMessage('');
}

async function getHint() {
    if (gameWon) {
        return;
    }

    const hintButton = document.getElementById('hint-button');
    hintButton.disabled = true;
    try {
        const res = await fetch('/hint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ board: getCurrentBoard() })
        });
        const data = await res.json();
        if (!res.ok || data.error) {
            setMessage(data.error || 'Unable to retrieve a hint.', 'error');
            return;
        }

        const inputs = document.getElementById('sudoku-board')
            .getElementsByTagName('input');
        const index = data.row * SIZE + data.col;
        const cell = inputs[index];
        if (!Number.isInteger(data.row) ||
            !Number.isInteger(data.col) ||
            data.row < 0 ||
            data.row >= SIZE ||
            data.col < 0 ||
            data.col >= SIZE ||
            !Number.isInteger(data.value) ||
            data.value < 1 ||
            data.value > SIZE ||
            !cell ||
            cell.disabled ||
            cell.value
        ) {
            setMessage('The hint service returned an invalid cell.', 'error');
            return;
        }

        cell.value = String(data.value);
        cell.disabled = true;
        cell.classList.add('prefilled', 'hinted');
        setMessage('A correct cell has been revealed and locked.', 'success');
    } finally {
        hintButton.disabled = gameWon;
    }
}

async function checkSolution() {
    if (gameWon) {
        return;
    }
    const inputs = document.getElementById('sudoku-board')
        .getElementsByTagName('input');
    const board = getCurrentBoard();
    const res = await fetch('/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ board })
    });
    const data = await res.json();
    if (data.error) {
        setMessage(data.error, 'error');
        return;
    }
    const incorrect = new Set(data.incorrect.map(x => x[0] * SIZE + x[1]));
    for (let idx = 0; idx < inputs.length; idx++) {
        const inp = inputs[idx];
        if (inp.disabled) continue;
        inp.classList.toggle('incorrect', incorrect.has(idx));
    }
    if (data.complete) {
        gameWon = true;
        const completionTime = stopTimer();
        const formattedTime = formatTime(completionTime);
        for (const input of inputs) {
            input.disabled = true;
        }
        document.getElementById('hint-button').disabled = true;
        setMessage(`Victory! You solved it in ${formattedTime}.`, 'success');
        showNamePrompt(completionTime);
    } else if (incorrect.size === 0) {
        setMessage('No incorrect entries, but the puzzle is incomplete.');
    } else {
        setMessage('Some cells are incorrect.', 'error');
    }
}

// Wire buttons
window.addEventListener('load', () => {
    document.getElementById('new-game').addEventListener('click', newGame);
    document.getElementById('hint-button').addEventListener('click', getHint);
    document.getElementById('check-solution').addEventListener('click', checkSolution);
    renderLeaderboard();
    document.getElementById('player-form').addEventListener('submit', (event) => {
        event.preventDefault();
        const nameInput = document.getElementById('player-name');
        const playerName = nameInput.value.trim();
        if (!playerName) {
            nameInput.setCustomValidity('Enter a name to save your time.');
            nameInput.reportValidity();
            return;
        }
        if (pendingScore === null) {
            throw new Error('No completed game is waiting to be saved.');
        }
        saveLeaderboardEntry(
            playerName,
            pendingScore.timeMs,
            pendingScore.difficulty
        );
        pendingScore = null;
        document.getElementById('player-dialog').close();
    });
    document.getElementById('player-name').addEventListener('input', (event) => {
        event.currentTarget.setCustomValidity('');
    });
    document.getElementById('player-dialog').addEventListener('cancel', (event) => {
        event.preventDefault();
    });
    document.getElementById('theme-toggle').addEventListener('click', () => {
        const nextTheme = document.documentElement.dataset.theme === 'dark' ?
            'light' :
            'dark';
        setTheme(nextTheme, true);
    });
    updateThemeToggle();
    // initialize
    newGame();

});