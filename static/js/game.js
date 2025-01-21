const notes = ['Sa', 'Re', 'Re2', 'Ga', 'Ga2', 'Ma', 'Ma2', 'Pa', 'Dha', 'Dha2', 'Ni', 'Ni2'];
const noteToFileMap = {
    'Sa': 'note_1',
    'Re': 'note_2',
    'Re2': 'note_3',
    'Ga': 'note_4',
    'Ga2': 'note_5',
    'Ma': 'note_6',
    'Ma2': 'note_7',
    'Pa': 'note_8',
    'Dha': 'note_9',
    'Dha2': 'note_10',
    'Ni': 'note_11',
    'Ni2': 'note_12'
};

const LEVELS = {
    1: { pattern_length: 3, points: 10 },
    2: { pattern_length: 3, points: 20 },
    3: { pattern_length: 5, points: 30 }
};

const FIXED_INTERVAL =0;//.12 seconds in milliseconds
const ADDITIONAL_SUSTAIN =500;//0.5 seconds additional sustain

let currentPattern = [];
let userPattern = [];
let composedPattern = [];
let savedPatterns = [];
let totalScore = 0;
let currentLevel = 1;
let gameMode = 'recognition';
let audioContext = null;

// Sustain tracking variables
let isNotePlaying = false;
let noteStartTime = 0;
let lastNoteEndTime = 0;
let activeNotes = new Map(); // Track currently playing notes

function initAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
}

const audioBuffers = {};
async function loadAudio(note) {
    if (!audioBuffers[note]) {
        const fileName = noteToFileMap[note];
        try {
            const response = await fetch(`/static/sitar_notes/${fileName}.wav`);
            const arrayBuffer = await response.arrayBuffer();
            audioBuffers[note] = await audioContext.decodeAudioData(arrayBuffer);
        } catch (error) {
            console.error('Error loading audio:', error);
        }
    }
    return audioBuffers[note];
}

async function playNote(note, duration = null) {
    try {
        initAudioContext();
        const buffer = await loadAudio(note);
        const source = audioContext.createBufferSource();
        const gainNode = audioContext.createGain();

        source.buffer = buffer;
        source.connect(gainNode);
        gainNode.connect(audioContext.destination);

        // Only apply duration-based gain envelope if duration is specified
        if (duration) {
            const adjustedDuration = duration + ADDITIONAL_SUSTAIN;
            gainNode.gain.setValueAtTime(1, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + (adjustedDuration / 1000));
        }

        source.start(0);

        return new Promise(resolve => {
            source.onended = resolve;
        });
    } catch (error) {
        console.error('Error playing note:', error);
    }
}

function initializeSitarString() {
    const sitarString = document.getElementById('sitarString');
    sitarString.innerHTML = '';

    notes.forEach(note => {
        const noteButton = document.createElement('div');
        noteButton.className = 'flex flex-col items-center';

        const button = document.createElement('button');
        button.className = 'w-20 h-40 bg-amber-200 hover:bg-amber-300 rounded-lg text-center font-bold transition-colors border-2 border-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 disabled:opacity-50 disabled:cursor-not-allowed';
        button.innerHTML = `<div class="h-full flex flex-col justify-between p-2">
            <span>${note}</span>
            <div class="w-full h-1 bg-amber-600"></div>
        </div>`;

        if (gameMode === 'composition') {
            button.addEventListener('mousedown', () => {
                initAudioContext();
                const currentTime = Date.now();
                activeNotes.set(note, {
                    startTime: currentTime,
                    interval: FIXED_INTERVAL
                });
                playNote(note, ADDITIONAL_SUSTAIN); // Add default sustain for immediate playback
                highlightNote(button);
            });

            button.addEventListener('mouseup', () => {
                if (activeNotes.has(note)) {
                    const noteData = activeNotes.get(note);
                    const endTime = Date.now();
                    const sustain = endTime - noteData.startTime;

                    if (composedPattern.length < 8) {
                        composedPattern.push({
                            note: note,
                            sustain: sustain + ADDITIONAL_SUSTAIN, // Add default sustain when recording
                            interval: FIXED_INTERVAL
                        });
                        lastNoteEndTime = endTime;
                        updateCompositionDisplay();
                    }

                    activeNotes.delete(note);
                }
            });
        } else {
            button.addEventListener('click', () => {
                initAudioContext();
                playNote(note, ADDITIONAL_SUSTAIN); // Add default sustain for immediate playback
                highlightNote(button);

                if (gameMode === 'recognition') {
                    handleNoteSelection(note);
                }
            });
        }

        noteButton.appendChild(button);
        sitarString.appendChild(noteButton);
    });
}

function highlightNote(button) {
    if (button.disabled) return;

    button.classList.add('bg-amber-400', 'scale-105');
    setTimeout(() => {
        button.classList.remove('bg-amber-400', 'scale-105');
    }, 200);
}

async function generatePattern() {
    userPattern = [];
    const level = parseInt(document.getElementById('levelSelect').value);
    currentLevel = level;

    currentPattern = Array.from(
        { length: LEVELS[level].pattern_length },
        () => notes[Math.floor(Math.random() * notes.length)]
    );

    const buttons = document.querySelectorAll('#sitarString button');

    if (level > 1) {
        buttons.forEach(button => button.disabled = true);
    }

    document.getElementById('submitAnswer').disabled = true;
    await playCurrentPattern();

    buttons.forEach(button => button.disabled = false);
}

async function playCurrentPattern() {
    const playButton = document.getElementById('playPattern');
    const level = currentLevel;
    playButton.disabled = true;
    document.getElementById('feedback').textContent = 'Listen to the pattern...';

    try {
        for (const note of currentPattern) {
            const noteButton = Array.from(document.querySelectorAll('button'))
                .find(button => button.textContent.includes(note));

            if (level === 1 && noteButton) {
                highlightNote(noteButton);
            }

            await playNote(note, ADDITIONAL_SUSTAIN);
            await new Promise(resolve => setTimeout(resolve, FIXED_INTERVAL));
        }
    } catch (error) {
        console.error('Error playing pattern:', error);
    }

    playButton.disabled = false;
    document.getElementById('feedback').textContent = 'Now repeat the pattern!';
}

function handleNoteSelection(note) {
    if (gameMode === 'recognition' && userPattern.length < currentPattern.length) {
        userPattern.push(note);

        if (userPattern.length === currentPattern.length) {
            document.getElementById('submitAnswer').disabled = false;
        }

        const feedback = document.getElementById('feedback');
        feedback.textContent = `Notes recorded: ${userPattern.length} / ${currentPattern.length}`;
    }
}

async function checkAnswer() {
    if (userPattern.length !== currentPattern.length) {
        return;
    }

    const isCorrect = userPattern.every((note, index) => note === currentPattern[index]);
    const feedback = document.getElementById('feedback');

    if (isCorrect) {
        const points = LEVELS[currentLevel].points;
        totalScore += points;
        feedback.textContent = `Correct! +${points} points`;
        feedback.className = 'text-green-600 text-lg font-bold animate-bounce';

        const scoreElement = document.getElementById('score');
        scoreElement.classList.add('scale-125', 'text-green-600', 'transition-all', 'duration-500');
        scoreElement.textContent = totalScore;
        setTimeout(() => {
            scoreElement.classList.remove('scale-125', 'text-green-600');
        }, 1000);

        await playSuccessAnimation();
    } else {
        feedback.textContent = 'Incorrect. The correct pattern was: ' + currentPattern.join(', ');
        feedback.className = 'text-red-600 text-lg font-bold';

        setTimeout(async () => {
            await playCurrentPattern();
        }, 1500);
    }

    document.getElementById('score').textContent = totalScore;
    document.getElementById('submitAnswer').disabled = true;
    userPattern = [];
}

async function playSuccessAnimation() {
    const buttons = document.querySelectorAll('#sitarString button');
    for (const button of buttons) {
        button.classList.add('bg-green-300');
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    setTimeout(() => {
        buttons.forEach(button => button.classList.remove('bg-green-300'));
    }, 500);
}

function updateGameMode(mode) {
    gameMode = mode;

    // Hide all game sections
    document.getElementById('gameControls').style.display = mode === 'recognition' ? 'block' : 'none';
    document.getElementById('compositionControls').style.display = mode === 'composition' ? 'block' : 'none';
    document.getElementById('practiceMessage').style.display = mode === 'practice' ? 'block' : 'none';
    document.getElementById('sourNoteGame').style.display = mode === 'sour_note' ? 'block' : 'none';

    // Reset state for each mode
    userPattern = [];
    currentPattern = [];
    composedPattern = [];
    activeNotes.clear();
    lastNoteEndTime = 0;

    document.getElementById('feedback').textContent = '';
    document.getElementById('submitAnswer').disabled = true;

    initializeSitarString(); // Refresh the sitar string UI
}

// Add event listeners for the new mode button
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.mode-button').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.mode-button').forEach(b =>
                b.classList.remove('bg-amber-600'));
            button.classList.add('bg-amber-600');
            updateGameMode(button.dataset.mode);
        });
    });

    // Initialize with default mode
    updateGameMode('recognition');
});

const twinkleMelody = [
    { note: 'Sa', duration: ADDITIONAL_SUSTAIN },
    { note: 'Sa', duration: ADDITIONAL_SUSTAIN },
    { note: 'Pa', duration: ADDITIONAL_SUSTAIN },
    { note: 'Pa', duration: ADDITIONAL_SUSTAIN },
    { note: 'Dha2', duration: ADDITIONAL_SUSTAIN },
    { note: 'Dha2', duration: ADDITIONAL_SUSTAIN },
    { note: 'Pa', duration: ADDITIONAL_SUSTAIN }
];

let sourNoteMelody = [];
let correctSourIndex = null;

// Modified startSourNoteGame function
async function startSourNoteGame() {
    // Create a copy of the original melody
    sourNoteMelody = [...twinkleMelody];

    // Select a random index for the sour note
    correctSourIndex = Math.floor(Math.random() * sourNoteMelody.length);

    // Modify the note at the selected index to be "sour"
    // We'll use a different note that's not in the original melody
    const sourNotes = notes.filter(note =>
        !twinkleMelody.some(melodyNote => melodyNote.note === note)
    );
    const sourNote = sourNotes[Math.floor(Math.random() * sourNotes.length)];
    sourNoteMelody[correctSourIndex] = {
        note: sourNote,
        duration: ADDITIONAL_SUSTAIN,
        isSour: true
    };

    document.getElementById('sourNoteFeedback').textContent = 'Listen to the melody...';
    document.getElementById('submitSourNote').disabled = true;

    // Disable all buttons during playback
    const buttons = document.querySelectorAll('#sitarString button');
    buttons.forEach(button => button.disabled = true);

    await playSourNoteMelody();

    // Re-enable buttons after playback
    buttons.forEach(button => button.disabled = false);
    populateSourNoteButtons();
}

// Modified playSourNoteMelody function
async function playSourNoteMelody() {
    for (const { note, duration } of sourNoteMelody) {
        // Find and highlight the corresponding button
        const noteButton = Array.from(document.querySelectorAll('#sitarString button'))
            .find(button => button.textContent.includes(note));

        if (noteButton) {
            highlightNote(noteButton);
        }

        await playNote(note, duration);
        await new Promise(resolve => setTimeout(resolve, FIXED_INTERVAL));
    }
    document.getElementById('sourNoteFeedback').textContent = 'Select the sour note!';
}

// Modified populateSourNoteButtons function
function populateSourNoteButtons() {
    const container = document.getElementById('sourNoteButtons');
    container.innerHTML = '';

    sourNoteMelody.forEach((noteObj, index) => {
        const button = document.createElement('button');
        button.className = 'bg-amber-200 hover:bg-amber-300 text-center font-bold px-4 py-2 rounded-lg transition-colors';
        button.textContent = `Note ${index + 1}`;

        button.onclick = () => {
            // Play the note when clicked
            playNote(noteObj.note, ADDITIONAL_SUSTAIN);
            handleSourNoteSelection(index, button);
        };

        container.appendChild(button);
    });
}

// Modified handleSourNoteSelection function
function handleSourNoteSelection(index, button) {
    // Remove highlight from all buttons
    document.querySelectorAll('#sourNoteButtons button').forEach(btn => {
        btn.classList.remove('bg-green-300', 'ring-2', 'ring-green-500');
    });

    // Highlight selected button
    button.classList.add('bg-green-300', 'ring-2', 'ring-green-500');

    // Enable submit button and store selection
    const submitButton = document.getElementById('submitSourNote');
    submitButton.disabled = false;
    submitButton.dataset.selectedIndex = index;
}

// Modified submitSourNote function
async function submitSourNote() {
    const guessedIndex = parseInt(document.getElementById('submitSourNote').dataset.selectedIndex);
    const feedback = document.getElementById('sourNoteFeedback');

    if (guessedIndex === correctSourIndex) {
        feedback.textContent = 'Correct! You found the sour note!';
        feedback.className = 'text-green-600 font-bold text-lg animate-bounce';

        // Add points to score
        totalScore += 20; // You can adjust the points
        document.getElementById('score').textContent = totalScore;

        // Highlight the correct note in green
        const buttons = document.querySelectorAll('#sourNoteButtons button');
        buttons[correctSourIndex].classList.add('bg-green-500', 'text-white');
    } else {
        feedback.textContent = 'Incorrect! Try again.';
        feedback.className = 'text-red-600 font-bold text-lg';

        // Highlight the wrong guess in red
        const buttons = document.querySelectorAll('#sourNoteButtons button');
        buttons[guessedIndex].classList.add('bg-red-500', 'text-white');
    }

    // Disable submit button after answer
    document.getElementById('submitSourNote').disabled = true;
}

function updateCompositionDisplay() {
    const display = document.getElementById('composedSequence');
    if (display) {
        display.innerHTML = composedPattern.map(({note, sustain, interval}) => `
            <div class="inline-flex flex-col items-center bg-amber-100 px-2 py-1 rounded m-1">
                <span class="font-bold">${note}</span>
                <span class="text-xs text-gray-600">
                    Sustain: ${((sustain)/1000).toFixed(2)}s
                    Interval: ${(interval/1000).toFixed(2)}s
                </span>
            </div>
        `).join('');
    }
}

async function playComposition() {
    const playButton = document.getElementById('playComposition');
    if (playButton) {
        playButton.disabled = true;

        for (const {note, sustain} of composedPattern) {
            await playNote(note, sustain);
            await new Promise(resolve => setTimeout(resolve, FIXED_INTERVAL));
        }

        playButton.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeSitarString();

    document.querySelectorAll('.mode-button').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.mode-button').forEach(b =>
                b.classList.remove('bg-amber-600'));
            button.classList.add('bg-amber-600');
            updateGameMode(button.dataset.mode);
        });
    });

    document.getElementById('playPattern').addEventListener('click', generatePattern);
    document.getElementById('submitAnswer').addEventListener('click', checkAnswer);
    document.getElementById('levelSelect').addEventListener('change', () => {
        userPattern = [];
        currentPattern = [];
        document.getElementById('submitAnswer').disabled = true;
        document.getElementById('feedback').textContent = '';
    });

    const playCompositionBtn = document.getElementById('playComposition');
    const clearCompositionBtn = document.getElementById('clearComposition');

    if (playCompositionBtn) {
        playCompositionBtn.addEventListener('click', playComposition);
    }

    if (clearCompositionBtn) {
        clearCompositionBtn.addEventListener('click', () => {
            composedPattern = [];
            activeNotes.clear();
            lastNoteEndTime = 0;
            updateCompositionDisplay();
        });
    }
});