import librosa, numpy as np, os, matplotlib.pyplot as plt
from collections import defaultdict
from sklearn.preprocessing import MinMaxScaler
from scipy.spatial.distance import cosine

class EnhancedCarnaticAnalyzer:
    def __init__(self, sr=22050):
        self.sr = sr
        self.note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.scaler = MinMaxScaler()

    def hz_to_note(self, frequency):
        if frequency <= 0:
            return None
        midi = librosa.hz_to_midi(frequency)
        note_idx = int(midi % 12)
        octave = int(midi // 12) - 1
        return f"{self.note_names[note_idx]}{octave}"

    def extract_pitch_features(self, audio_file):
        y, sr = librosa.load(audio_file, sr=self.sr)
        pitches, mags = librosa.piptrack(y=y, sr=sr, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))

        pitch_seq = []
        conf_seq = []
        for t in range(pitches.shape[1]):
            idx = mags[:, t].argmax()
            pitch = pitches[idx, t]
            conf = mags[idx, t]
            if conf > 0.1:
                pitch_seq.append(pitch)
                conf_seq.append(conf)

        note_seq = [self.hz_to_note(hz) for hz in pitch_seq if hz > 0]
        return {
            'pitch_sequence': pitch_seq,
            'confidence_sequence': conf_seq,
            'note_sequence': note_seq,
        }

    def analyze_note_distribution(self, note_seq):
        count = defaultdict(int)
        for note in note_seq:
            base = note[:-1] if note else None
            if base:
                count[base] += 1
        total = sum(count.values())
        return {k: v / total for k, v in count.items()} if total else {}

    def swara_similarity(self, dist1, dist2):
        base_notes = {'S', 'R', 'G', 'M', 'P', 'D', 'N'}
        group1, group2 = defaultdict(list), defaultdict(list)

        for note, val in dist1.items():
            if note[0] in base_notes:
                group1[note[0]].append((note, val))
        for note, val in dist2.items():
            if note[0] in base_notes:
                group2[note[0]].append((note, val))

        similarity, comparisons = 0, 0
        for base in base_notes:
            notes1, notes2 = group1[base], group2[base]
            if notes1 and notes2:
                n1, v1 = max(notes1, key=lambda x: x[1])
                n2, v2 = max(notes2, key=lambda x: x[1])
                if n1 != n2 and v1 > 0.05 and v2 > 0.05:
                    similarity += 0.1
                else:
                    similarity += np.exp(-10 * abs(v1 - v2))
                comparisons += 1
            elif notes1 or notes2:
                similarity += 0.1
                comparisons += 1
        return similarity / comparisons if comparisons else 0

    def pattern_similarity(self, p1, p2):
        all_notes = sorted(set(p1) | set(p2))
        v1 = [p1.count(n) for n in all_notes]
        v2 = [p2.count(n) for n in all_notes]
        return 1 - cosine(v1, v2)

    def visualize_comparison(self, file1, file2):
        f1 = self.extract_pitch_features(file1)
        f2 = self.extract_pitch_features(file2)

        dist1 = self.analyze_note_distribution(f1['note_sequence'])
        dist2 = self.analyze_note_distribution(f2['note_sequence'])

        all_notes = sorted(set(dist1) | set(dist2))
        sim_scores = [1 - abs(dist1.get(n, 0) - dist2.get(n, 0)) for n in all_notes]

        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        x = np.arange(len(all_notes))
        w = 0.35

        # 1. Note distribution
        axes[0].bar(x - w/2, [dist1.get(n, 0) for n in all_notes], width=w, label='Original')
        axes[0].bar(x + w/2, [dist2.get(n, 0) for n in all_notes], width=w, label='Recorded')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(all_notes)
        axes[0].set_title("Note Distribution")
        axes[0].legend()

        # 2. Pitch contours
        t1 = np.arange(len(f1['pitch_sequence'])) * 512 / self.sr
        t2 = np.arange(len(f2['pitch_sequence'])) * 512 / self.sr
        axes[1].plot(t1, f1['pitch_sequence'], label="Original", color='blue', alpha=0.6)
        axes[1].plot(t2, f2['pitch_sequence'], label="Recorded", color='red', alpha=0.6)
        axes[1].set_title("Pitch Contours")
        axes[1].set_xlabel("Time (s)")
        axes[1].set_ylabel("Frequency (Hz)")
        axes[1].legend()

        # 3. Similarity scores
        axes[2].bar(all_notes, sim_scores, color='green')
        axes[2].set_ylim(0, 1)
        axes[2].set_title("Note Similarity Score")
        axes[2].text(len(all_notes)-1, 0.92, f'Swara Sim: {self.swara_similarity(dist1, dist2):.3f}', ha='right')

        plt.tight_layout()
        return fig
