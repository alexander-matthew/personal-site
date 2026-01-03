/**
 * Sudoku Engine Unit Tests
 */

const {
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
    generateSolution,
    hasUniqueSolution,
    generatePuzzle,
    isComplete
} = require('./sudoku-engine');

describe('Grid Utilities', () => {
    test('createEmptyGrid creates 9x9 grid of zeros', () => {
        const grid = createEmptyGrid();
        expect(grid.length).toBe(9);
        expect(grid[0].length).toBe(9);
        expect(grid.flat().every(v => v === 0)).toBe(true);
    });

    test('copyGrid creates deep copy', () => {
        const original = createEmptyGrid();
        original[0][0] = 5;
        const copy = copyGrid(original);

        expect(copy[0][0]).toBe(5);
        copy[0][0] = 9;
        expect(original[0][0]).toBe(5);
    });

    test('shuffle returns same length array', () => {
        const arr = [1, 2, 3, 4, 5];
        const shuffled = shuffle(arr);
        expect(shuffled.length).toBe(5);
    });

    test('shuffle does not modify original array', () => {
        const arr = [1, 2, 3, 4, 5];
        const original = [...arr];
        shuffle(arr);
        expect(arr).toEqual(original);
    });

    test('getAllPositions returns 81 positions', () => {
        const positions = getAllPositions();
        expect(positions.length).toBe(81);
        expect(positions[0]).toEqual([0, 0]);
        expect(positions[80]).toEqual([8, 8]);
    });
});

describe('Validation Functions', () => {
    let grid;

    beforeEach(() => {
        grid = createEmptyGrid();
        grid[0] = [5, 3, 0, 0, 7, 0, 0, 0, 0];
        grid[1] = [6, 0, 0, 1, 9, 5, 0, 0, 0];
        grid[2] = [0, 9, 8, 0, 0, 0, 0, 6, 0];
    });

    test('isInRow detects value in row', () => {
        expect(isInRow(grid, 0, 5)).toBe(true);
        expect(isInRow(grid, 0, 1)).toBe(false);
    });

    test('isInColumn detects value in column', () => {
        expect(isInColumn(grid, 0, 5)).toBe(true);
        expect(isInColumn(grid, 0, 1)).toBe(false);
    });

    test('isInBox detects value in 3x3 box', () => {
        expect(isInBox(grid, 0, 0, 9)).toBe(true);
        expect(isInBox(grid, 0, 0, 1)).toBe(false);
    });

    test('isValidPlacement combines all checks', () => {
        expect(isValidPlacement(grid, 0, 2, 1)).toBe(true);
        expect(isValidPlacement(grid, 0, 2, 5)).toBe(false);
        expect(isValidPlacement(grid, 0, 2, 8)).toBe(false);
    });

    test('isValidSet returns true for valid set', () => {
        expect(isValidSet([1, 2, 3, 4, 5, 6, 7, 8, 9])).toBe(true);
    });

    test('isValidSet returns false for duplicates', () => {
        expect(isValidSet([1, 1, 3, 4, 5, 6, 7, 8, 9])).toBe(false);
    });

    test('isValidSet ignores zeros', () => {
        expect(isValidSet([1, 0, 3, 0, 5, 6, 7, 8, 9])).toBe(true);
    });
});

describe('Solver', () => {
    test('findEmptyCell returns first empty position', () => {
        const grid = createEmptyGrid();
        grid[0][0] = 5;

        const empty = findEmptyCell(grid);
        expect(empty).toEqual([0, 1]);
    });

    test('findEmptyCell returns null for complete grid', () => {
        const grid = [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9]
        ];

        expect(findEmptyCell(grid)).toBe(null);
    });

    test('solve completes a solvable puzzle', () => {
        const grid = createEmptyGrid();
        grid[0] = [5, 3, 0, 0, 7, 0, 0, 0, 0];

        expect(solve(grid)).toBe(true);
        expect(findEmptyCell(grid)).toBe(null);
        expect(isValidGrid(grid)).toBe(true);
    });
});

describe('Puzzle Generation', () => {
    test('generateSolution creates valid complete grid', () => {
        const solution = generateSolution();

        expect(findEmptyCell(solution)).toBe(null);
        expect(isValidGrid(solution)).toBe(true);
    });

    test('generatePuzzle returns puzzle and solution', () => {
        const { puzzle, solution } = generatePuzzle('easy');

        expect(puzzle).toBeDefined();
        expect(solution).toBeDefined();
        expect(isValidGrid(solution)).toBe(true);
    });

    test('easy puzzle has 45-50 clues', () => {
        const { puzzle } = generatePuzzle('easy');
        const clueCount = puzzle.flat().filter(v => v !== 0).length;

        expect(clueCount).toBeGreaterThanOrEqual(45);
        expect(clueCount).toBeLessThanOrEqual(50);
    });

    test('medium puzzle has 35-40 clues', () => {
        const { puzzle } = generatePuzzle('medium');
        const clueCount = puzzle.flat().filter(v => v !== 0).length;

        expect(clueCount).toBeGreaterThanOrEqual(35);
        expect(clueCount).toBeLessThanOrEqual(40);
    });

    test('hard puzzle has 25-30 clues', () => {
        const { puzzle } = generatePuzzle('hard');
        const clueCount = puzzle.flat().filter(v => v !== 0).length;

        expect(clueCount).toBeGreaterThanOrEqual(25);
        expect(clueCount).toBeLessThanOrEqual(30);
    });

    test('generated puzzle has unique solution', () => {
        const { puzzle } = generatePuzzle('medium');
        expect(hasUniqueSolution(puzzle)).toBe(true);
    });
});

describe('Completion Detection', () => {
    test('isComplete returns false for incomplete grid', () => {
        const grid = createEmptyGrid();
        expect(isComplete(grid)).toBe(false);
    });

    test('isComplete returns true for valid complete grid', () => {
        const grid = [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9]
        ];

        expect(isComplete(grid)).toBe(true);
    });

    test('isComplete returns false for invalid complete grid', () => {
        const grid = [
            [5, 5, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9]
        ];

        expect(isComplete(grid)).toBe(false);
    });
});
