/**
 * Synth Engine Tests - Dual Synth with Chord Progressions
 */

const {
    WAVEFORMS,
    SCALES,
    SUBDIVISIONS,
    PROGRESSIONS,
    ARP_PATTERNS,
    CHORD_TYPES,
    NOTE_NAMES,
    midiToFrequency,
    noteNameToMidi,
    midiToNoteName,
    getScaleNotes,
    getChordNotes,
    getChordRoot,
    Arpeggiator,
    DualSynthEngine
} = require('./synth-engine');

// ===== Music Theory Utils =====

describe('Music Theory Utilities', () => {
    describe('midiToFrequency', () => {
        test('converts A4 (MIDI 69) to 440Hz', () => {
            expect(midiToFrequency(69)).toBeCloseTo(440, 1);
        });

        test('converts C4 (MIDI 60) to ~261.63Hz', () => {
            expect(midiToFrequency(60)).toBeCloseTo(261.63, 1);
        });
    });

    describe('noteNameToMidi', () => {
        test('converts C4 to MIDI 60', () => {
            expect(noteNameToMidi('C', 4)).toBe(60);
        });

        test('converts A4 to MIDI 69', () => {
            expect(noteNameToMidi('A', 4)).toBe(69);
        });

        test('returns null for invalid note', () => {
            expect(noteNameToMidi('X', 4)).toBeNull();
        });
    });

    describe('midiToNoteName', () => {
        test('converts MIDI 60 to C4', () => {
            expect(midiToNoteName(60)).toBe('C4');
        });

        test('converts MIDI 69 to A4', () => {
            expect(midiToNoteName(69)).toBe('A4');
        });
    });

    describe('getChordRoot', () => {
        test('returns root for degree 0', () => {
            expect(getChordRoot(60, 'major', 0)).toBe(60);
        });

        test('returns IV chord root (F) for C major', () => {
            // Degree 3 in 0-indexed = IV chord
            expect(getChordRoot(60, 'major', 3)).toBe(65); // F4
        });

        test('returns V chord root (G) for C major', () => {
            expect(getChordRoot(60, 'major', 4)).toBe(67); // G4
        });
    });
});

// ===== Constants =====

describe('Constants', () => {
    test('SCALES contains all expected scales', () => {
        expect(SCALES.major).toBeDefined();
        expect(SCALES.minor).toBeDefined();
        expect(SCALES.pentatonic).toBeDefined();
        expect(SCALES.blues).toBeDefined();
        expect(SCALES.dorian).toBeDefined();
        expect(SCALES.mixolydian).toBeDefined();
    });

    test('PROGRESSIONS contains common progressions', () => {
        expect(PROGRESSIONS['I-IV-V-I']).toEqual([0, 3, 4, 0]);
        expect(PROGRESSIONS['I-V-vi-IV']).toEqual([0, 4, 5, 3]);
        expect(PROGRESSIONS['ii-V-I']).toEqual([1, 4, 0]);
    });

    test('SUBDIVISIONS has correct values', () => {
        expect(SUBDIVISIONS['1/4']).toBe(1);
        expect(SUBDIVISIONS['1/8']).toBe(2);
        expect(SUBDIVISIONS['1/16']).toBe(4);
        expect(SUBDIVISIONS['1/8T']).toBe(3);  // Triplets
        expect(SUBDIVISIONS['1/16T']).toBe(6);
    });

    test('ARP_PATTERNS contains all patterns', () => {
        expect(ARP_PATTERNS.up).toBeDefined();
        expect(ARP_PATTERNS.down).toBeDefined();
        expect(ARP_PATTERNS.upDown).toBeDefined();
        expect(ARP_PATTERNS.random).toBeDefined();
        expect(ARP_PATTERNS.outside).toBeDefined();
        expect(ARP_PATTERNS['1-3-5-3']).toBeDefined();
    });

    test('CHORD_TYPES includes power chord', () => {
        expect(CHORD_TYPES.power).toEqual([0, 4]);
    });
});

// ===== Arpeggiator =====

describe('Arpeggiator', () => {
    let arp;

    beforeEach(() => {
        arp = new Arpeggiator();
    });

    test('initializes with default values', () => {
        expect(arp.rootNote).toBe(60);
        expect(arp.scale).toBe('major');
        expect(arp.progression).toBe('I');
    });

    test('generates ascending sequence for up pattern', () => {
        arp.setParams({ pattern: 'up', octaves: 1 });
        const seq = arp.getSequence();
        for (let i = 1; i < seq.length; i++) {
            expect(seq[i]).toBeGreaterThan(seq[i - 1]);
        }
    });

    test('generates descending sequence for down pattern', () => {
        arp.setParams({ pattern: 'down', octaves: 1 });
        const seq = arp.getSequence();
        for (let i = 1; i < seq.length; i++) {
            expect(seq[i]).toBeLessThan(seq[i - 1]);
        }
    });

    test('progression changes update chord root', () => {
        arp.setParams({ progression: 'I-IV-V-I' });
        expect(arp.getCurrentChordDegree()).toBe(0); // I

        arp.advanceChord();
        expect(arp.getCurrentChordDegree()).toBe(3); // IV

        arp.advanceChord();
        expect(arp.getCurrentChordDegree()).toBe(4); // V
    });

    test('advanceChord cycles through progression', () => {
        arp.setParams({ progression: 'I-IV-V-I' });

        // Cycle through entire progression (4 chords: I, IV, V, I)
        arp.advanceChord(); // -> IV (index 1)
        arp.advanceChord(); // -> V (index 2)
        arp.advanceChord(); // -> I (index 3)
        arp.advanceChord(); // -> I (wraps to index 0)

        expect(arp.getCurrentChordDegree()).toBe(0); // Back to I
    });

    test('getBassNote returns chord root', () => {
        arp.setParams({ rootNote: 60, progression: 'I' });
        expect(arp.getBassNote()).toBe(60);
    });

    test('getCurrentChordNotes returns triad notes', () => {
        arp.setParams({ rootNote: 60, scale: 'major', chordType: 'triad' });
        const notes = arp.getCurrentChordNotes();
        expect(notes).toContain(60); // C
        expect(notes).toContain(64); // E
        expect(notes).toContain(67); // G
    });

    test('reset returns to first chord', () => {
        arp.setParams({ progression: 'I-IV-V-I' });
        arp.advanceChord();
        arp.advanceChord();

        arp.reset();
        expect(arp.getCurrentChordDegree()).toBe(0);
    });
});

// ===== ARP Pattern Functions =====

describe('ARP Pattern Functions', () => {
    const testNotes = [60, 64, 67, 72]; // C E G C

    test('outside pattern alternates from edges', () => {
        const result = ARP_PATTERNS.outside.fn(testNotes);
        expect(result[0]).toBe(60); // First (lowest)
        expect(result[1]).toBe(72); // Last (highest)
    });

    test('1-3-5-3 pattern creates correct sequence', () => {
        const result = ARP_PATTERNS['1-3-5-3'].fn(testNotes);
        expect(result).toEqual([60, 64, 67, 64]); // C E G E
    });

    test('random pattern has isRandom flag', () => {
        expect(ARP_PATTERNS.random.isRandom).toBe(true);
    });
});

// ===== DualSynthEngine =====

describe('DualSynthEngine', () => {
    let engine;

    beforeEach(() => {
        engine = new DualSynthEngine();
    });

    test('initializes with correct default values', () => {
        expect(engine.tempo).toBe(120);
        expect(engine.subdivision).toBe('1/8');
        expect(engine.gate).toBe(0.8);
        expect(engine.notesPerChord).toBe(8);
    });

    test('setTempo clamps to valid range', () => {
        engine.setTempo(500);
        expect(engine.tempo).toBe(300);

        engine.setTempo(10);
        expect(engine.tempo).toBe(40);
    });

    test('setSubdivision only accepts valid values', () => {
        engine.setSubdivision('1/16');
        expect(engine.subdivision).toBe('1/16');

        engine.setSubdivision('invalid');
        expect(engine.subdivision).toBe('1/16'); // Unchanged
    });

    test('setGate clamps to valid range', () => {
        engine.setGate(1.5);
        expect(engine.gate).toBe(1);

        engine.setGate(0.05);
        expect(engine.gate).toBe(0.1);
    });

    test('setNotesPerChord clamps to valid range', () => {
        engine.setNotesPerChord(50);
        expect(engine.notesPerChord).toBe(32);

        engine.setNotesPerChord(0);
        expect(engine.notesPerChord).toBe(1);
    });

    test('setSynthAParams updates synth A', () => {
        engine.setSynthAParams({ mode: 'chord' });
        expect(engine.synthAParams.mode).toBe('chord');
    });

    test('setSynthBParams updates synth B', () => {
        engine.setSynthBParams({ filter: { cutoff: 5000 } });
        expect(engine.synthBParams.filter.cutoff).toBe(5000);
    });

    test('setMasterVolume clamps to 0-1', () => {
        engine.setMasterVolume(1.5);
        expect(engine.masterVolume).toBe(1);

        engine.setMasterVolume(-0.5);
        expect(engine.masterVolume).toBe(0);
    });

    test('setScale updates arpeggiator', () => {
        engine.setScale('A', 3, 'minor');
        expect(engine.arpeggiator.rootNote).toBe(57); // A3
        expect(engine.arpeggiator.scale).toBe('minor');
    });

    test('setArpParams updates arpeggiator', () => {
        engine.setArpParams({ pattern: 'down', progression: 'I-IV-V-I' });
        expect(engine.arpeggiator.pattern).toBe('down');
        expect(engine.arpeggiator.progression).toBe('I-IV-V-I');
    });

    test('isPlaying returns false initially', () => {
        expect(engine.isPlaying()).toBe(false);
    });

    test('getArpSequence returns formatted note info', () => {
        const seq = engine.getArpSequence();
        expect(seq.length).toBeGreaterThan(0);
        expect(seq[0]).toHaveProperty('midi');
        expect(seq[0]).toHaveProperty('name');
        expect(seq[0]).toHaveProperty('frequency');
    });

    test('getCurrentChordInfo returns chord details', () => {
        const info = engine.getCurrentChordInfo();
        expect(info).toHaveProperty('degree');
        expect(info).toHaveProperty('root');
        expect(info).toHaveProperty('rootName');
        expect(info).toHaveProperty('notes');
    });

    test('getProgressionInfo returns roman numerals', () => {
        engine.setArpParams({ progression: 'I-IV-V-I' });
        const info = engine.getProgressionInfo();
        expect(info).toContain('I');
        expect(info).toContain('IV');
        expect(info).toContain('V');
    });

    test('static getAvailableProgressions returns all progressions', () => {
        const progs = DualSynthEngine.getAvailableProgressions();
        expect(progs).toContain('I-IV-V-I');
        expect(progs).toContain('ii-V-I');
        expect(progs).toContain('12-bar');
    });

    test('static getAvailablePatterns returns pattern objects', () => {
        const patterns = DualSynthEngine.getAvailablePatterns();
        expect(patterns.find(p => p.id === 'up')).toBeDefined();
        expect(patterns.find(p => p.id === 'random')).toBeDefined();
    });

    test('static getAvailableSubdivisions returns all subdivisions', () => {
        const subdivs = DualSynthEngine.getAvailableSubdivisions();
        expect(subdivs).toContain('1/4');
        expect(subdivs).toContain('1/8');
        expect(subdivs).toContain('1/8T');
    });
});
