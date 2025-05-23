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

NOTES = ['Sa', 'Re', 'Ga', 'Ma', 'Pa', 'Dha', 'Ni', 'Sa2', 'Re2', 'Ga2', 'Ma2', 'Pa2']
NAVARASA_AUDIO = {
    "Shanta": "static/audio/shanta.mp3",
    "Veera": "static/audio/veera.mp3",
    "Shringara": "static/audio/shringara.mp3",
    "Karuna": "static/audio/karuna.mp3",
    "Adbhuta": "static/audio/adbhuta.mp3",
    "Bhayanaka": "static/audio/bhayanaka.mp3"
}

def convert_to_wav(input_file, ext=".wav"):
    wav_path = tempfile.mktemp(suffix=ext)
    audio = AudioSegment.from_file(input_file)
    audio.export(wav_path, format="wav")
    return wav_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare')
def compare_page():
    return render_template('compare.html')

@app.route('/compare_audio', methods=['POST'])
def compare_audio():
    try:
        orig = request.files['original']
        rec = request.files['recorded']

        orig_path = convert_to_wav(orig)
        rec_path = convert_to_wav(rec)

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

        return jsonify({'image': img_base64, 'swara_similarity': swara_similarity})
    except Exception as e:
        print("Comparison error:", e)
        return jsonify({'error': str(e)}), 500
