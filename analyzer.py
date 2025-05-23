import librosa, numpy as np, os, matplotlib.pyplot as plt
from collections import defaultdict
from sklearn.preprocessing import MinMaxScaler
from scipy.spatial.distance import cosine

class EnhancedCarnaticAnalyzer:
    def __init__(self, sr=22050):
        self.sr = sr
        self.note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def hz_to_note(self, frequency):
        if frequency <= 0:
            return None
        midi = librosa.hz_to_midi(frequency)
        note_idx = int(midi % 12)
        octave = int(midi // 12) - 1
        return f"{self.note_names[note_idx]}{octave}"

    def extract_pitch_features(self, audio_file):
        y, sr = librosa.load(audio_file, sr=self.sr, mono=True, duration=15)
        pitches, mags = librosa.piptrack(y=y, sr=sr, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        pitch_sequence = []
        for t in range(pitches.shape[1]):
            idx = np.argmax(mags[:, t])
            pitch = pitches[idx, t]
            if pitch > 0:
                pitch_sequence.append(pitch)

        note_sequence = [self.hz_to_note(hz) for hz in pitch_sequence]
        return {
            'pitch_sequence': pitch_sequence,
            'note_sequence': [n for i, n in enumerate(note_sequence) if n and (i == 0 or n != note_sequence[i - 1])]
        }

    def analyze_note_distribution(self, note_sequence):
        count = defaultdict(int)
        for note in note_sequence:
            base = note[:-1] if note else None
            if base:
                count[base] += 1
        total = sum(count.values())
        return {k: v / total for k, v in count.items()} if total > 0 else {}

    def swara_similarity(self, dist1, dist2):
        keys = sorted(set(dist1) | set(dist2))
        sim = 0
        for key in keys:
            diff = abs(dist1.get(key, 0) - dist2.get(key, 0))
            sim += (1 - diff)
        return sim / len(keys) if keys else 0

    def pattern_similarity(self, p1, p2):
        keys = sorted(set(p1 + p2))
        v1 = [p1.count(k) for k in keys]
        v2 = [p2.count(k) for k in keys]
        return 1 - cosine(v1, v2)

    def visualize_comparison(self, f1, f2):
        feat1 = self.extract_pitch_features(f1)
        feat2 = self.extract_pitch_features(f2)
        dist1 = self.analyze_note_distribution(feat1['note_sequence'])
        dist2 = self.analyze_note_distribution(feat2['note_sequence'])

        all_notes = sorted(set(dist1.keys()) | set(dist2.keys()))
        sim_scores = [1 - abs(dist1.get(n, 0) - dist2.get(n, 0)) for n in all_notes]

        fig, ax = plt.subplots(3, 1, figsize=(12, 10))

        x = np.arange(len(all_notes))
        ax[0].bar(x - 0.2, [dist1.get(n, 0) for n in all_notes], width=0.4, label='Original')
        ax[0].bar(x + 0.2, [dist2.get(n, 0) for n in all_notes], width=0.4, label='Recorded')
        ax[0].set_xticks(x)
        ax[0].set_xticklabels(all_notes)
        ax[0].set_title('Note Distribution')
        ax[0].legend()

        t1 = np.arange(len(feat1['pitch_sequence'])) * 512 / self.sr
        t2 = np.arange(len(feat2['pitch_sequence'])) * 512 / self.sr
        ax[1].plot(t1, feat1['pitch_sequence'], label='Original', color='blue', alpha=0.6)
        ax[1].plot(t2, feat2['pitch_sequence'], label='Recorded', color='red', alpha=0.6)
        ax[1].set_title('Pitch Contours')
        ax[1].set_xlabel('Time (s)')
        ax[1].set_ylabel('Frequency (Hz)')
        ax[1].legend()

        ax[2].bar(all_notes, sim_scores, color='green')
        ax[2].set_ylim(0, 1)
        ax[2].set_title('Note Similarity')
        ax[2].text(len(all_notes) - 1, 0.9, f'Swara Sim: {self.swara_similarity(dist1, dist2):.2f}', ha='right')

        plt.tight_layout()
        return fig
