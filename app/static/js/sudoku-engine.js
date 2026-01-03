/**
 * Sudoku Game Engine
 * Pure game logic separated from UI for testability
 */

// ===== Grid Utilities =====

function createEmptyGrid() {
    return Array(9).fill(null).map(() => Array(9).fill(0));
}

function copyGrid(grid) {
    return grid.map(row => [...row]);
}

function shuffle(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

function getAllPositions() {
    const positions = [];
    for (let row = 0; row < 9; row++) {
        for (let col = 0; col < 9; col++) {
            positions.push([row, col]);
        }
    }
    return positions;
}

// ===== Validation Functions =====

function isInRow(grid, row, value) {
    return grid[row].includes(value);
}

function isInColumn(grid, col, value) {
    for (let row = 0; row < 9; row++) {
        if (grid[row][col] === value) return true;
    }
    return false;
}

function isInBox(grid, row, col, value) {
    const boxRow = Math.floor(row / 3) * 3;
    const boxCol = Math.floor(col / 3) * 3;

    for (let r = boxRow; r < boxRow + 3; r++) {
        for (let c = boxCol; c < boxCol + 3; c++) {
            if (grid[r][c] === value) return true;
        }
    }
    return false;
}

function isValidPlacement(grid, row, col, value) {
    return !isInRow(grid, row, value) &&
           !isInColumn(grid, col, value) &&
           !isInBox(grid, row, col, value);
}

function isValidSet(arr) {
    const filtered = arr.filter(n => n !== 0);
    return filtered.length === new Set(filtered).size;
}

function isValidGrid(grid) {
    // Check rows
    for (let row = 0; row < 9; row++) {
        if (!isValidSet(grid[row])) return false;
    }

    // Check columns
    for (let col = 0; col < 9; col++) {
        const column = grid.map(row => row[col]);
        if (!isValidSet(column)) return false;
    }

    // Check 3x3 boxes
    for (let boxRow = 0; boxRow < 3; boxRow++) {
        for (let boxCol = 0; boxCol < 3; boxCol++) {
            const box = [];
            for (let r = 0; r < 3; r++) {
                for (let c = 0; c < 3; c++) {
                    box.push(grid[boxRow * 3 + r][boxCol * 3 + c]);
                }
            }
            if (!isValidSet(box)) return false;
        }
    }

    return true;
}

// ===== Solver =====

function findEmptyCell(grid) {
    for (let row = 0; row < 9; row++) {
        for (let col = 0; col < 9; col++) {
            if (grid[row][col] === 0) return [row, col];
        }
    }
    return null;
}

function solve(grid) {
    const empty = findEmptyCell(grid);
    if (!empty) return true;

    const [row, col] = empty;

    for (let num = 1; num <= 9; num++) {
        if (isValidPlacement(grid, row, col, num)) {
            grid[row][col] = num;
            if (solve(grid)) return true;
            grid[row][col] = 0;
        }
    }

    return false;
}

// ===== Puzzle Generation =====

function fillGrid(grid) {
    const empty = findEmptyCell(grid);
    if (!empty) return true;

    const [row, col] = empty;
    const numbers = shuffle([1, 2, 3, 4, 5, 6, 7, 8, 9]);

    for (const num of numbers) {
        if (isValidPlacement(grid, row, col, num)) {
            grid[row][col] = num;
            if (fillGrid(grid)) return true;
            grid[row][col] = 0;
        }
    }

    return false;
}

function generateSolution() {
    const grid = createEmptyGrid();
    fillGrid(grid);
    return grid;
}

function countSolutions(grid, limit = 2) {
    let count = 0;
    const copy = copyGrid(grid);

    function search(g) {
        if (count >= limit) return;

        const empty = findEmptyCell(g);
        if (!empty) {
            count++;
            return;
        }

        const [row, col] = empty;

        for (let num = 1; num <= 9; num++) {
            if (isValidPlacement(g, row, col, num)) {
                g[row][col] = num;
                search(g);
                g[row][col] = 0;
            }
        }
    }

    search(copy);
    return count;
}

function hasUniqueSolution(grid) {
    return countSolutions(grid, 2) === 1;
}

function generatePuzzle(difficulty = 'medium') {
    const solution = generateSolution();
    const puzzle = copyGrid(solution);

    const clueTargets = {
        easy: { min: 45, max: 50 },
        medium: { min: 35, max: 40 },
        hard: { min: 25, max: 30 }
    };

    const { min, max } = clueTargets[difficulty] || clueTargets.medium;
    const targetClues = min + Math.floor(Math.random() * (max - min + 1));
    const cellsToRemove = 81 - targetClues;

    const positions = shuffle(getAllPositions());
    let removed = 0;

    for (const [row, col] of positions) {
        if (removed >= cellsToRemove) break;
        if (puzzle[row][col] === 0) continue;

        const backup = puzzle[row][col];
        puzzle[row][col] = 0;

        if (hasUniqueSolution(puzzle)) {
            removed++;
        } else {
            puzzle[row][col] = backup;
        }
    }

    return { puzzle, solution };
}

// ===== Completion Detection =====

function isComplete(grid) {
    for (let row = 0; row < 9; row++) {
        for (let col = 0; col < 9; col++) {
            if (grid[row][col] === 0) return false;
        }
    }
    return isValidGrid(grid);
}

// ===== Export for Node.js (testing) and browser =====

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createEmptyGrid,
        copyGrid,
        shuffle,
        getAllPositions,
        isInRow,
        isInColumn,
        isInBox,
        isValidPlacement,
        isValidSet,
        isValidGrid,
        findEmptyCell,
        solve,
        fillGrid,
        generateSolution,
        countSolutions,
        hasUniqueSolution,
        generatePuzzle,
        isComplete
    };
}
