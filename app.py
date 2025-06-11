from flask import Flask, render_template, jsonify, request, session
import random, os, tempfile, librosa, numpy as np, json, base64
from pydub import AudioSegment
from io import BytesIO
import warnings
from analyzer import EnhancedCarnaticAnalyzer

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.static_folder = 'static'

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Notes for the games
NOTES = ['Sa', 'Re', 'Ga', 'Ma', 'Pa', 'Dha', 'Ni', 'Sa2', 'Re2', 'Ga2', 'Ma2', 'Pa2']

# Navarasa audio mapping
NAVARASA_AUDIO = {
    "Shanta": "static/audio/shanta.mp3",
    "Veera": "static/audio/veera.mp3",
    "Shringara": "static/audio/shringara.mp3",
    "Karuna": "static/audio/karuna.mp3",
    "Adbhuta": "static/audio/adbhuta.mp3",
    "Bhayanaka": "static/audio/bhayanaka.mp3"
}

LEVELS = {
    1: {'pattern_length': 3, 'points': 10},
    2: {'pattern_length': 5, 'points': 20},
    3: {'pattern_length': 7, 'points': 30},
}

# --------------------------------------------
# 📥 Audio Conversion Helper
# --------------------------------------------
def convert_to_wav(input_file, ext=".wav"):
    wav_path = tempfile.mktemp(suffix=ext)
    audio = AudioSegment.from_file(input_file)
    audio.export(wav_path, format="wav")
    return wav_path

def freq_to_swara(freq, tonic=261.63):
    if freq <= 0: return None
    semitone = round(12 * np.log2(freq / tonic)) % 12
    return NOTES[semitone]

# --------------------------------------------
# 🌐 Routes
# --------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare')
def compare_page():
    return render_template('compare.html')

@app.route('/navarasa')
def navarasa():
    session['score'] = 0
    session['questions'] = list(NAVARASA_AUDIO.items())
    random.shuffle(session['questions'])
    return render_template('navarasa.html')

@app.route('/generate_pattern', methods=['POST'])
def generate_pattern():
    level = int(request.json.get('level', 1))
    pattern_length = LEVELS[level]['pattern_length']
    pattern = random.sample(NOTES, pattern_length)
    return jsonify({
        'pattern': pattern,
        'points': LEVELS[level]['points']
    })

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    user_pattern = data.get('user_pattern', [])
    correct_pattern = data.get('correct_pattern', [])
    is_correct = user_pattern == correct_pattern
    return jsonify({
        'correct': is_correct,
        'points': LEVELS[int(data.get('level', 1))]['points'] if is_correct else 0
    })

@app.route('/generate_sour_note_melody', methods=['POST'])
def generate_sour_note_melody():
    melody_length = 5
    melody = random.choices(NOTES, k=melody_length)
    sour_index = random.randint(0, melody_length - 1)
    melody[sour_index] = f"{melody[sour_index]}_sour"
    return jsonify({
        'melody': melody,
        'sour_index': sour_index
    })

@app.route('/check_sour_note', methods=['POST'])
def check_sour_note():
    data = request.json
    guessed_index = data.get('guessed_index')
    correct_index = data.get('correct_index')
    if guessed_index == correct_index:
        return jsonify({'correct': True, 'message': 'Correct! You identified the sour note!'})
    return jsonify({'correct': False, 'message': 'Incorrect! Try again.'})

@app.route('/get_question', methods=['GET'])
def get_question():
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

# --------------------------------------------
# 🎤 Audio Pitch Analysis (Short Pattern)
# --------------------------------------------
@app.route('/analyze_pitch', methods=['POST'])
def analyze_pitch():
    audio = request.files['audio']
    expected = json.loads(request.form['expected_notes'])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio.read())
        tmp_path = tmp.name

    try:
        y, sr = librosa.load(tmp_path)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = [pitches[i, np.argmax(magnitudes[i])] for i in range(pitches.shape[1])]
        pitch_values = [p for p in pitch_values if p > 0]

        notes_detected = [freq_to_swara(p) for p in pitch_values]
        note_sequence = [n for i, n in enumerate(notes_detected) if n and (i == 0 or n != notes_detected[i - 1])]

        correct = sum(1 for i, n in enumerate(expected) if i < len(note_sequence) and n == note_sequence[i])
        accuracy = (correct / len(expected)) * 100 if expected else 0

        os.remove(tmp_path)
        return jsonify({'accuracy': accuracy})
    except Exception as e:
        print("Pitch analysis error:", e)
        return jsonify({'accuracy': 0})

# --------------------------------------------
# 🎶 Full Audio Comparison with Plot
# --------------------------------------------
@app.route('/compare_audio', methods=['POST'])
def compare_audio():
    try:
        original = request.files['original']
        recorded = request.files['recorded']

        orig_path = convert_to_wav(original)
        rec_path = convert_to_wav(recorded)

        analyzer = EnhancedCarnaticAnalyzer()
        features1 = analyzer.extract_pitch_features(orig_path)
        features2 = analyzer.extract_pitch_features(rec_path)

        dist1 = analyzer.analyze_note_distribution(features1['note_sequence'])
        dist2 = analyzer.analyze_note_distribution(features2['note_sequence'])
        swara_similarity = analyzer.swara_similarity(dist1, dist2)

        fig = analyzer.visualize_comparison(orig_path, rec_path)
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')

        os.remove(orig_path)
        os.remove(rec_path)

        return jsonify({
            'image': img_base64,
            'swara_similarity': swara_similarity
        })
    except Exception as e:
        print("Comparison error:", e)
        return jsonify({'error': str(e)}), 500

# --------------------------------------------
# 🚀 Run the App
# --------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 4000))
    app.run(host="0.0.0.0", port=port)
