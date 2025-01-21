from flask import Flask, render_template, jsonify, request, session
import random
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configure static folder for audio files
app.static_folder = 'static'

# Notes for the games
NOTES = ['Sa', 'Re', 'Ga', 'Ma', 'Pa', 'Dha', 'Ni', 'Sa2', 'Re2', 'Ga2', 'Ma2', 'Pa2']
LEVELS = {
    1: {'pattern_length': 3, 'points': 10},
    2: {'pattern_length': 5, 'points': 20},
    3: {'pattern_length': 7, 'points': 30},
}

# Navarasa emotions and corresponding audio files
NAVARASA_AUDIO = {
    "Shanta": "static/audio/shanta.mp3",
    "Veera": "static/audio/veera.mp3",
    "Shringara": "static/audio/shringara.mp3",
    "Karuna": "static/audio/karuna.mp3",
    "Adbhuta": "static/audio/adbhuta.mp3",
    "Bhayanaka": "static/audio/bhayanaka.mp3"

}
#"Hasya": "static/audio/hasya.mp3", "Bibhatsa": "static/audio/bibhatsa.mp3","Raudra": "static/audio/raudra.mp3",
# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Pattern Recognition Game
@app.route('/generate_pattern', methods=['POST'])
def generate_pattern():
    """Generate a random pattern for the Pattern Recognition game."""
    level = int(request.json.get('level', 1))
    pattern_length = LEVELS[level]['pattern_length']
    pattern = random.sample(NOTES, pattern_length)
    return jsonify({
        'pattern': pattern,
        'points': LEVELS[level]['points']
    })

@app.route('/check_answer', methods=['POST'])
def check_answer():
    """Check the user's answer for the Pattern Recognition game."""
    data = request.json
    user_pattern = data.get('user_pattern', [])
    correct_pattern = data.get('correct_pattern', [])
    is_correct = user_pattern == correct_pattern
    return jsonify({
        'correct': is_correct,
        'points': LEVELS[int(data.get('level', 1))]['points'] if is_correct else 0
    })

# Identify the Sour Note Game
@app.route('/generate_sour_note_melody', methods=['POST'])
def generate_sour_note_melody():
    """Generate a melody with a sour note for the Sour Note game."""
    melody_length = 5  # Number of notes in the melody
    melody = random.choices(NOTES, k=melody_length)
    sour_index = random.randint(0, melody_length - 1)
    sour_note = f"{melody[sour_index]}_sour"
    melody[sour_index] = sour_note

    return jsonify({
        'melody': melody,
        'sour_index': sour_index  # This is for frontend verification
    })

@app.route('/check_sour_note', methods=['POST'])
def check_sour_note():
    """Check if the user's guess for the sour note is correct."""
    data = request.json
    guessed_index = data.get('guessed_index')
    correct_index = data.get('correct_index')

    if guessed_index == correct_index:
        return jsonify({'correct': True, 'message': 'Correct! You identified the sour note!'})
    return jsonify({'correct': False, 'message': 'Incorrect! Try again.'})

# Navarasa Emotion Game
@app.route('/navarasa')
def navarasa():
    """Serve the Navarasa Emotion Game."""
    session['score'] = 0
    session['questions'] = list(NAVARASA_AUDIO.items())
    random.shuffle(session['questions'])
    return render_template('navarasa.html')

@app.route('/get_question', methods=['GET'])
def get_question():
    """Serve the next Navarasa question."""
    session['questions'] = session.get('questions', list(NAVARASA_AUDIO.items()))
    random.shuffle(session['questions'])

    if session['questions']:
        emotion, audio_path = session['questions'].pop()
        session['current_emotion'] = emotion
        return jsonify({"audio": audio_path, "options": list(NAVARASA_AUDIO.keys())})
    else:
        return jsonify({"audio": None, "options": None})

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Check the user's answer for the Navarasa game."""
    data = request.json
    user_answer = data['answer']
    correct_answer = session.get('current_emotion', '')

    if user_answer == correct_answer:
        session['score'] = session.get('score', 0) + 1

    return jsonify({
        "correct": user_answer == correct_answer,
        "correct_answer": correct_answer,
        "score": session.get('score', 0)
    })

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
