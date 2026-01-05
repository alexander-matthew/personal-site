/**
 * Synth Engine - Web Audio API synthesizer with arpeggiator
 * Features: Dual synths, chord progressions, note subdivisions, pattern presets
 */

// ===== Constants =====
const WAVEFORMS = ['sine', 'triangle', 'sawtooth', 'square'];

const SCALES = {
    major:      [0, 2, 4, 5, 7, 9, 11],
    minor:      [0, 2, 3, 5, 7, 8, 10],
    pentatonic: [0, 2, 4, 7, 9],
    blues:      [0, 3, 5, 6, 7, 10],
    dorian:     [0, 2, 3, 5, 7, 9, 10],
    mixolydian: [0, 2, 4, 5, 7, 9, 10]
};

// Chord degrees relative to scale (0-indexed scale degree)
const CHORD_TYPES = {
    triad:   [0, 2, 4],
    seventh: [0, 2, 4, 6],
    sus2:    [0, 1, 4],
    sus4:    [0, 3, 4],
    power:   [0, 4]       // Root + 5th only
};

// Common chord progressions (Roman numeral degrees, 0-indexed)
const PROGRESSIONS = {
    'I':         [0],
    'I-IV-V-I':  [0, 3, 4, 0],
    'I-V-vi-IV': [0, 4, 5, 3],
    'ii-V-I':    [1, 4, 0],
    'I-vi-IV-V': [0, 5, 3, 4],
    'i-iv-v':    [0, 3, 4],          // Minor
    'i-VI-III-VII': [0, 5, 2, 6],    // Minor epic
    'I-IV':      [0, 3],
    'I-V':       [0, 4],
    '12-bar':    [0, 0, 0, 0, 3, 3, 0, 0, 4, 3, 0, 4]  // 12-bar blues
};

// Note subdivisions (notes per beat)
const SUBDIVISIONS = {
    '1/4':    1,      // Quarter notes
    '1/8':    2,      // Eighth notes
    '1/16':   4,      // Sixteenth notes
    '1/8T':   3,      // Eighth note triplets
    '1/16T':  6       // Sixteenth note triplets
};

// Arpeggio patterns - define how to traverse the notes
const ARP_PATTERNS = {
    up:        { name: 'Up', fn: (notes) => [...notes] },
    down:      { name: 'Down', fn: (notes) => [...notes].reverse() },
    upDown:    { name: 'Up/Down', fn: (notes) => {
        const up = [...notes];
        const down = [...notes].reverse().slice(1, -1);
        return [...up, ...down];
    }},
    downUp:    { name: 'Down/Up', fn: (notes) => {
        const down = [...notes].reverse();
        const up = [...notes].slice(1, -1);
        return [...down, ...up];
    }},
    random:    { name: 'Random', fn: (notes) => notes, isRandom: true },
    outside:   { name: 'Outside In', fn: (notes) => {
        const result = [];
        const copy = [...notes];
        while (copy.length > 0) {
            result.push(copy.shift());
            if (copy.length > 0) result.push(copy.pop());
        }
        return result;
    }},
    inside:    { name: 'Inside Out', fn: (notes) => {
        const result = [];
        const copy = [...notes];
        const mid = Math.floor(copy.length / 2);
        let left = mid - 1;
        let right = mid;
        while (left >= 0 || right < copy.length) {
            if (right < copy.length) result.push(copy[right++]);
            if (left >= 0) result.push(copy[left--]);
        }
        return result;
    }},
    '1-3-5-3': { name: '1-3-5-3', fn: (notes) => {
        // Arpeggio pattern: root, 3rd, 5th, 3rd (for triads)
        if (notes.length >= 3) {
            return [notes[0], notes[1], notes[2], notes[1]];
        }
        return notes;
    }},
    '1-5-3-5': { name: '1-5-3-5', fn: (notes) => {
        if (notes.length >= 3) {
            return [notes[0], notes[2], notes[1], notes[2]];
        }
        return notes;
    }}
};

const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

// ===== Music Theory Utilities =====

function midiToFrequency(midiNote) {
    return 440 * Math.pow(2, (midiNote - 69) / 12);
}

function noteNameToMidi(noteName, octave) {
    const noteIndex = NOTE_NAMES.indexOf(noteName);
    if (noteIndex === -1) return null;
    return (octave + 1) * 12 + noteIndex;
}

function midiToNoteName(midiNote) {
    const octave = Math.floor(midiNote / 12) - 1;
    const noteIndex = midiNote % 12;
    return NOTE_NAMES[noteIndex] + octave;
}

function getScaleNotes(rootMidi, scaleName, octaves) {
    const intervals = SCALES[scaleName] || SCALES.major;
    const notes = [];
    for (let oct = 0; oct < octaves; oct++) {
        for (const interval of intervals) {
            notes.push(rootMidi + interval + (oct * 12));
        }
    }
    return notes;
}

function getChordNotes(rootMidi, scaleName, chordType, octaves) {
    const scaleNotes = getScaleNotes(rootMidi, scaleName, octaves + 1);
    const degrees = CHORD_TYPES[chordType] || CHORD_TYPES.triad;
    const chordNotes = [];
    const scaleLen = (SCALES[scaleName] || SCALES.major).length;

    for (let oct = 0; oct < octaves; oct++) {
        for (const degree of degrees) {
            const noteIndex = degree + (oct * scaleLen);
            if (noteIndex < scaleNotes.length) {
                chordNotes.push(scaleNotes[noteIndex]);
            }
        }
    }
    return chordNotes;
}

// Get the root note for a chord degree in a progression
function getChordRoot(baseRoot, scaleName, degree) {
    const scale = SCALES[scaleName] || SCALES.major;
    const interval = scale[degree % scale.length];
    const octaveOffset = Math.floor(degree / scale.length) * 12;
    return baseRoot + interval + octaveOffset;
}

// ===== Voice Class =====

class SynthVoice {
    constructor(audioContext, destination, params) {
        this.ctx = audioContext;
        this.destination = destination;
        this.params = params;
    }

    playNote(frequency, startTime, duration) {
        const ctx = this.ctx;
        const params = this.params;

        // Oscillator 1
        const osc1 = ctx.createOscillator();
        osc1.type = params.osc1.waveform;
        osc1.frequency.value = frequency;
        osc1.detune.value = params.osc1.detune;

        // Oscillator 2
        const osc2 = ctx.createOscillator();
        osc2.type = params.osc2.waveform;
        osc2.frequency.value = frequency * Math.pow(2, params.osc2.octave);
        osc2.detune.value = params.osc2.detune;

        // Mix gains
        const osc1Gain = ctx.createGain();
        const osc2Gain = ctx.createGain();
        osc1Gain.gain.value = 1 - params.osc2.mix;
        osc2Gain.gain.value = params.osc2.mix;

        // Filter
        const filter = ctx.createBiquadFilter();
        filter.type = params.filter.type;
        filter.frequency.value = params.filter.cutoff;
        filter.Q.value = params.filter.resonance;

        // VCA with ADSR
        const vca = ctx.createGain();
        vca.gain.value = 0;

        const { attack, decay, sustain, release } = params.envelope;
        const attackEnd = startTime + attack;
        const decayEnd = attackEnd + decay;
        const releaseStart = startTime + duration - release;
        const endTime = startTime + duration;

        vca.gain.setValueAtTime(0, startTime);
        vca.gain.linearRampToValueAtTime(1, attackEnd);
        vca.gain.linearRampToValueAtTime(sustain, decayEnd);
        if (releaseStart > decayEnd) {
            vca.gain.setValueAtTime(sustain, releaseStart);
        }
        vca.gain.linearRampToValueAtTime(0, endTime);

        // Connect
        osc1.connect(osc1Gain);
        osc2.connect(osc2Gain);
        osc1Gain.connect(filter);
        osc2Gain.connect(filter);
        filter.connect(vca);
        vca.connect(this.destination);

        // Start/stop
        osc1.start(startTime);
        osc2.start(startTime);
        osc1.stop(endTime + 0.1);
        osc2.stop(endTime + 0.1);
    }

    // Play multiple notes simultaneously (chord)
    playChord(frequencies, startTime, duration) {
        const chordGain = this.ctx.createGain();
        chordGain.gain.value = 1 / Math.sqrt(frequencies.length); // Normalize volume
        chordGain.connect(this.destination);

        for (const freq of frequencies) {
            this.playNoteToDestination(freq, startTime, duration, chordGain);
        }
    }

    playNoteToDestination(frequency, startTime, duration, dest) {
        const ctx = this.ctx;
        const params = this.params;

        const osc1 = ctx.createOscillator();
        osc1.type = params.osc1.waveform;
        osc1.frequency.value = frequency;
        osc1.detune.value = params.osc1.detune;

        const osc2 = ctx.createOscillator();
        osc2.type = params.osc2.waveform;
        osc2.frequency.value = frequency * Math.pow(2, params.osc2.octave);
        osc2.detune.value = params.osc2.detune;

        const osc1Gain = ctx.createGain();
        const osc2Gain = ctx.createGain();
        osc1Gain.gain.value = 1 - params.osc2.mix;
        osc2Gain.gain.value = params.osc2.mix;

        const filter = ctx.createBiquadFilter();
        filter.type = params.filter.type;
        filter.frequency.value = params.filter.cutoff;
        filter.Q.value = params.filter.resonance;

        const vca = ctx.createGain();
        vca.gain.value = 0;

        const { attack, decay, sustain, release } = params.envelope;
        const attackEnd = startTime + attack;
        const decayEnd = attackEnd + decay;
        const releaseStart = startTime + duration - release;
        const endTime = startTime + duration;

        vca.gain.setValueAtTime(0, startTime);
        vca.gain.linearRampToValueAtTime(1, attackEnd);
        vca.gain.linearRampToValueAtTime(sustain, decayEnd);
        if (releaseStart > decayEnd) {
            vca.gain.setValueAtTime(sustain, releaseStart);
        }
        vca.gain.linearRampToValueAtTime(0, endTime);

        osc1.connect(osc1Gain);
        osc2.connect(osc2Gain);
        osc1Gain.connect(filter);
        osc2Gain.connect(filter);
        filter.connect(vca);
        vca.connect(dest);

        osc1.start(startTime);
        osc2.start(startTime);
        osc1.stop(endTime + 0.1);
        osc2.stop(endTime + 0.1);
    }
}

// ===== Arpeggiator Class =====

class Arpeggiator {
    constructor() {
        this.rootNote = 60;
        this.scale = 'major';
        this.chordType = 'triad';
        this.pattern = 'up';
        this.octaves = 2;
        this.progression = 'I';
        this.currentChordIndex = 0;
        this.currentStep = 0;
        this.sequence = [];

        this.regenerateSequence();
    }

    setParams(params) {
        if (params.rootNote !== undefined) this.rootNote = params.rootNote;
        if (params.scale !== undefined) this.scale = params.scale;
        if (params.chordType !== undefined) this.chordType = params.chordType;
        if (params.pattern !== undefined) this.pattern = params.pattern;
        if (params.octaves !== undefined) this.octaves = params.octaves;
        if (params.progression !== undefined) this.progression = params.progression;

        this.regenerateSequence();
    }

    regenerateSequence() {
        const prog = PROGRESSIONS[this.progression] || [0];
        this.progressionDegrees = prog;
        this.currentChordIndex = 0;
        this.updateSequenceForCurrentChord();
    }

    updateSequenceForCurrentChord() {
        const degree = this.progressionDegrees[this.currentChordIndex];
        const chordRoot = getChordRoot(this.rootNote, this.scale, degree);
        const chordNotes = getChordNotes(chordRoot, this.scale, this.chordType, this.octaves);

        const patternDef = ARP_PATTERNS[this.pattern] || ARP_PATTERNS.up;
        this.sequence = patternDef.fn(chordNotes);
        this.isRandom = patternDef.isRandom || false;
        this.currentStep = 0;
    }

    getNextNote() {
        if (this.sequence.length === 0) return null;

        let note;
        if (this.isRandom) {
            const idx = Math.floor(Math.random() * this.sequence.length);
            note = this.sequence[idx];
        } else {
            note = this.sequence[this.currentStep];
            this.currentStep++;
        }

        return note;
    }

    // Check if we've completed the current chord's arpeggio
    isChordComplete() {
        return this.currentStep >= this.sequence.length;
    }

    // Advance to next chord in progression
    advanceChord() {
        this.currentChordIndex = (this.currentChordIndex + 1) % this.progressionDegrees.length;
        this.updateSequenceForCurrentChord();
    }

    getCurrentChordDegree() {
        return this.progressionDegrees[this.currentChordIndex];
    }

    getCurrentChordRoot() {
        const degree = this.getCurrentChordDegree();
        return getChordRoot(this.rootNote, this.scale, degree);
    }

    // Get full chord notes for current position (for bass/chord synth)
    getCurrentChordNotes() {
        const chordRoot = this.getCurrentChordRoot();
        return getChordNotes(chordRoot, this.scale, this.chordType, 1);
    }

    getBassNote() {
        return this.getCurrentChordRoot();
    }

    reset() {
        this.currentChordIndex = 0;
        this.currentStep = 0;
        this.updateSequenceForCurrentChord();
    }

    getSequence() {
        return [...this.sequence];
    }

    getCurrentStep() {
        return this.currentStep;
    }

    getProgressionLength() {
        return this.progressionDegrees.length;
    }
}

// ===== Dual Synth Engine =====

class DualSynthEngine {
    constructor() {
        this.audioContext = null;
        this.masterGain = null;
        this.isInitialized = false;

        // Synth A (Bass/Chords)
        this.synthAGain = null;
        this.synthAParams = {
            osc1: { waveform: 'sawtooth', detune: 0 },
            osc2: { waveform: 'square', detune: 5, octave: 0, mix: 0.3 },
            filter: { cutoff: 800, resonance: 1, type: 'lowpass' },
            envelope: { attack: 0.05, decay: 0.2, sustain: 0.6, release: 0.3 },
            volume: 0.6,
            mode: 'bass'  // 'bass', 'chord', 'off'
        };

        // Synth B (Arpeggio)
        this.synthBGain = null;
        this.synthBParams = {
            osc1: { waveform: 'sawtooth', detune: 0 },
            osc2: { waveform: 'square', detune: 7, octave: 0, mix: 0.5 },
            filter: { cutoff: 3000, resonance: 3, type: 'lowpass' },
            envelope: { attack: 0.01, decay: 0.15, sustain: 0.4, release: 0.2 },
            volume: 0.7
        };

        // Master
        this.masterVolume = 0.7;

        // Arpeggiator
        this.arpeggiator = new Arpeggiator();

        // Timing
        this.tempo = 120;
        this.subdivision = '1/8';
        this.gate = 0.8;
        this.notesPerChord = 8;  // How many arp notes before changing chord
        this.isRunning = false;

        // Scheduling
        this.scheduleAheadTime = 0.1;
        this.lookAhead = 25;
        this.nextNoteTime = 0;
        this.noteCount = 0;
        this.schedulerTimer = null;

        // Callbacks
        this.onNotePlay = null;
        this.onChordChange = null;
    }

    init() {
        if (this.isInitialized) return;

        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        this.audioContext = new AudioContextClass();

        // Master gain
        this.masterGain = this.audioContext.createGain();
        this.masterGain.gain.value = this.masterVolume;
        this.masterGain.connect(this.audioContext.destination);

        // Synth A gain
        this.synthAGain = this.audioContext.createGain();
        this.synthAGain.gain.value = this.synthAParams.volume;
        this.synthAGain.connect(this.masterGain);

        // Synth B gain
        this.synthBGain = this.audioContext.createGain();
        this.synthBGain.gain.value = this.synthBParams.volume;
        this.synthBGain.connect(this.masterGain);

        this.isInitialized = true;
    }

    async start() {
        if (!this.isInitialized) this.init();
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }
    }

    // ===== Synth A (Bass/Chords) Parameters =====

    setSynthAParams(params) {
        if (params.osc1) Object.assign(this.synthAParams.osc1, params.osc1);
        if (params.osc2) Object.assign(this.synthAParams.osc2, params.osc2);
        if (params.filter) Object.assign(this.synthAParams.filter, params.filter);
        if (params.envelope) Object.assign(this.synthAParams.envelope, params.envelope);
        if (params.volume !== undefined) {
            this.synthAParams.volume = params.volume;
            if (this.synthAGain) this.synthAGain.gain.value = params.volume;
        }
        if (params.mode) this.synthAParams.mode = params.mode;
    }

    // ===== Synth B (Arpeggio) Parameters =====

    setSynthBParams(params) {
        if (params.osc1) Object.assign(this.synthBParams.osc1, params.osc1);
        if (params.osc2) Object.assign(this.synthBParams.osc2, params.osc2);
        if (params.filter) Object.assign(this.synthBParams.filter, params.filter);
        if (params.envelope) Object.assign(this.synthBParams.envelope, params.envelope);
        if (params.volume !== undefined) {
            this.synthBParams.volume = params.volume;
            if (this.synthBGain) this.synthBGain.gain.value = params.volume;
        }
    }

    // ===== Global Parameters =====

    setMasterVolume(volume) {
        this.masterVolume = Math.max(0, Math.min(1, volume));
        if (this.masterGain) this.masterGain.gain.value = this.masterVolume;
    }

    setTempo(tempo) {
        this.tempo = Math.max(40, Math.min(300, tempo));
    }

    setSubdivision(subdivision) {
        if (SUBDIVISIONS[subdivision] !== undefined) {
            this.subdivision = subdivision;
        }
    }

    setGate(gate) {
        this.gate = Math.max(0.1, Math.min(1, gate));
    }

    setNotesPerChord(notes) {
        this.notesPerChord = Math.max(1, Math.min(32, notes));
    }

    // ===== Arpeggiator Settings =====

    setArpParams(params) {
        if (params.pattern) this.arpeggiator.setParams({ pattern: params.pattern });
        if (params.octaves) this.arpeggiator.setParams({ octaves: params.octaves });
        if (params.progression) this.arpeggiator.setParams({ progression: params.progression });
        if (params.chordType) this.arpeggiator.setParams({ chordType: params.chordType });
    }

    setScale(rootNote, octave, scale) {
        const midiRoot = noteNameToMidi(rootNote, octave);
        this.arpeggiator.setParams({ rootNote: midiRoot, scale });
    }

    // ===== Playback Control =====

    startPlayback() {
        if (!this.isInitialized) this.init();

        this.isRunning = true;
        this.nextNoteTime = this.audioContext.currentTime;
        this.noteCount = 0;
        this.arpeggiator.reset();

        this.scheduler();
    }

    stopPlayback() {
        this.isRunning = false;
        if (this.schedulerTimer) {
            clearTimeout(this.schedulerTimer);
            this.schedulerTimer = null;
        }
    }

    scheduler() {
        if (!this.isRunning) return;

        while (this.nextNoteTime < this.audioContext.currentTime + this.scheduleAheadTime) {
            this.scheduleNotes(this.nextNoteTime);
            this.advanceTime();
        }

        this.schedulerTimer = setTimeout(() => this.scheduler(), this.lookAhead);
    }

    scheduleNotes(time) {
        const notesPerBeat = SUBDIVISIONS[this.subdivision];
        const noteDuration = (60 / this.tempo / notesPerBeat) * this.gate;
        const chordDuration = (60 / this.tempo) * this.notesPerChord / notesPerBeat;

        // Check if we need to change chord
        if (this.noteCount > 0 && this.noteCount % this.notesPerChord === 0) {
            this.arpeggiator.advanceChord();
            if (this.onChordChange) {
                const delay = Math.max(0, (time - this.audioContext.currentTime) * 1000);
                setTimeout(() => {
                    this.onChordChange(this.arpeggiator.getCurrentChordDegree());
                }, delay);
            }
        }

        // Play Synth A (bass or chord) on chord changes
        if (this.noteCount % this.notesPerChord === 0 && this.synthAParams.mode !== 'off') {
            const voiceA = new SynthVoice(this.audioContext, this.synthAGain, this.synthAParams);

            if (this.synthAParams.mode === 'bass') {
                const bassNote = this.arpeggiator.getBassNote();
                const bassFreq = midiToFrequency(bassNote);
                voiceA.playNote(bassFreq, time, chordDuration * 0.95);
            } else if (this.synthAParams.mode === 'chord') {
                const chordNotes = this.arpeggiator.getCurrentChordNotes();
                const chordFreqs = chordNotes.map(n => midiToFrequency(n));
                voiceA.playChord(chordFreqs, time, chordDuration * 0.95);
            }
        }

        // Play Synth B (arpeggio)
        const midiNote = this.arpeggiator.getNextNote();
        if (midiNote !== null) {
            const frequency = midiToFrequency(midiNote);
            const voiceB = new SynthVoice(this.audioContext, this.synthBGain, this.synthBParams);
            voiceB.playNote(frequency, time, noteDuration);

            if (this.onNotePlay) {
                const delay = Math.max(0, (time - this.audioContext.currentTime) * 1000);
                setTimeout(() => {
                    this.onNotePlay(midiNote, midiToNoteName(midiNote), this.noteCount % this.notesPerChord);
                }, delay);
            }
        }

        // Reset arpeggiator step if needed
        if (this.arpeggiator.isChordComplete()) {
            this.arpeggiator.currentStep = 0;
        }

        this.noteCount++;
    }

    advanceTime() {
        const notesPerBeat = SUBDIVISIONS[this.subdivision];
        const noteInterval = 60 / this.tempo / notesPerBeat;
        this.nextNoteTime += noteInterval;
    }

    // ===== Getters =====

    isPlaying() {
        return this.isRunning;
    }

    getArpSequence() {
        return this.arpeggiator.getSequence().map(midi => ({
            midi,
            name: midiToNoteName(midi),
            frequency: midiToFrequency(midi)
        }));
    }

    getCurrentChordInfo() {
        return {
            degree: this.arpeggiator.getCurrentChordDegree(),
            root: this.arpeggiator.getCurrentChordRoot(),
            rootName: midiToNoteName(this.arpeggiator.getCurrentChordRoot()),
            notes: this.arpeggiator.getCurrentChordNotes().map(n => midiToNoteName(n))
        };
    }

    getProgressionInfo() {
        const prog = this.arpeggiator.progression;
        const degrees = PROGRESSIONS[prog] || [0];
        const romanNumerals = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii'];
        return degrees.map(d => romanNumerals[d % 7] || (d + 1));
    }

    static getAvailableProgressions() {
        return Object.keys(PROGRESSIONS);
    }

    static getAvailablePatterns() {
        return Object.keys(ARP_PATTERNS).map(k => ({ id: k, name: ARP_PATTERNS[k].name }));
    }

    static getAvailableSubdivisions() {
        return Object.keys(SUBDIVISIONS);
    }
}

// Backward compatibility alias
const SynthEngine = DualSynthEngine;

// ===== Exports for testing =====
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
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
        SynthVoice,
        DualSynthEngine,
        SynthEngine
    };
}
