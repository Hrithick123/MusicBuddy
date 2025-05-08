import librosa
import numpy as np
import os
import matplotlib.pyplot as plt
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
        midi_number = librosa.hz_to_midi(frequency)
        note_idx = int(midi_number % 12)
        octave = int(midi_number // 12) - 1
        return f"{self.note_names[note_idx]}{octave}"

    def extract_pitch_features(self, audio_file):
        y, sr = librosa.load(audio_file, sr=self.sr)
        hop_length = 512
        fmin = librosa.note_to_hz('C2')
        fmax = librosa.note_to_hz('C7')
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, fmin=fmin, fmax=fmax, hop_length=hop_length)

        pitch_sequence = []
        confidence_sequence = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            confidence = magnitudes[index, t]
            if confidence > 0.1:
                pitch_sequence.append(pitch)
                confidence_sequence.append(confidence)

        note_sequence = [self.hz_to_note(hz) for hz in pitch_sequence if hz > 0]
        return {
            'pitch_sequence': pitch_sequence,
            'confidence_sequence': confidence_sequence,
            'note_sequence': note_sequence,
        }

    def analyze_note_distribution(self, note_sequence):
        note_counts = defaultdict(int)
        for note in note_sequence:
            if note:
                base_note = note[:-1]
                note_counts[base_note] += 1

        total_notes = sum(note_counts.values())
        return {note: count / total_notes for note, count in note_counts.items()}

    def pattern_similarity(self, pattern1, pattern2):
        all_notes = sorted(set(pattern1) | set(pattern2))
        vector1 = [pattern1.count(note) for note in all_notes]
        vector2 = [pattern2.count(note) for note in all_notes]
        return 1 - cosine(vector1, vector2)

    def swara_similarity(self, note_distribution1, note_distribution2):
        all_notes = sorted(set(note_distribution1.keys()) | set(note_distribution2.keys()))
        base_notes = {'S', 'R', 'G', 'M', 'P', 'D', 'N'}
        notes_by_base1 = defaultdict(list)
        notes_by_base2 = defaultdict(list)

        for note in note_distribution1.keys():
            base = note[0]
            if base in base_notes:
                notes_by_base1[base].append((note, note_distribution1[note]))

        for note in note_distribution2.keys():
            base = note[0]
            if base in base_notes:
                notes_by_base2[base].append((note, note_distribution2[note]))

        similarity = 0
        total_comparisons = 0
        note_differences = []

        for base_note in base_notes:
            notes1 = notes_by_base1[base_note]
            notes2 = notes_by_base2[base_note]

            if notes1 and notes2:
                note1, dist1 = max(notes1, key=lambda x: x[1])
                note2, dist2 = max(notes2, key=lambda x: x[1])
                if note1 != note2 and dist1 > 0.05 and dist2 > 0.05:
                    note_differences.append((note1, note2))
                    similarity += 0.1
                else:
                    diff = abs(dist1 - dist2)
                    similarity += np.exp(-10 * diff)
                total_comparisons += 1
            elif notes1 or notes2:
                note_differences.append((notes1[0][0] if notes1 else "None", notes2[0][0] if notes2 else "None"))
                similarity += 0.1
                total_comparisons += 1

        final_similarity = similarity / total_comparisons if total_comparisons > 0 else 0
        return final_similarity

    def visualize_comparison(self, file1, file2):
        features1 = self.extract_pitch_features(file1)
        features2 = self.extract_pitch_features(file2)

        note_distribution1 = self.analyze_note_distribution(features1['note_sequence'])
        note_distribution2 = self.analyze_note_distribution(features2['note_sequence'])

        all_notes = sorted(set(note_distribution1.keys()) | set(note_distribution2.keys()))
        note_similarity_scores = [
            1 - abs(note_distribution1.get(note, 0) - note_distribution2.get(note, 0))
            for note in all_notes
        ]
        overall_similarity = sum(note_similarity_scores) / len(all_notes)
        pattern_sim = self.pattern_similarity(features1['note_sequence'], features2['note_sequence'])
        swara_sim = self.swara_similarity(note_distribution1, note_distribution2)

        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        x = np.arange(len(all_notes))
        width = 0.35

        axes[0].bar(x - width / 2, [note_distribution1.get(note, 0) for note in all_notes], width, label=os.path.basename(file1))
        axes[0].bar(x + width / 2, [note_distribution2.get(note, 0) for note in all_notes], width, label=os.path.basename(file2))
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(all_notes)
        axes[0].set_title('Note Distribution Comparison')
        axes[0].legend()

        time1 = np.arange(len(features1['pitch_sequence'])) * 512 / self.sr
        time2 = np.arange(len(features2['pitch_sequence'])) * 512 / self.sr

        axes[1].scatter(time1, features1['pitch_sequence'], alpha=0.6, label=os.path.basename(file1), color='blue')
        axes[1].scatter(time2, features2['pitch_sequence'], alpha=0.6, label=os.path.basename(file2), color='red')
        axes[1].set_title('Pitch Contour Comparison')
        axes[1].set_xlabel('Time (s)')
        axes[1].set_ylabel('Frequency (Hz)')
        axes[1].legend()

        axes[2].bar(all_notes, note_similarity_scores, color='green')
        axes[2].set_title('Note Similarity (1 - Absolute Difference)')
        axes[2].set_ylabel('Similarity Score')
        axes[2].set_ylim(0, 1)
        axes[2].text(len(all_notes) - 1, 0.9, f'Note Sim: {overall_similarity:.3f}', ha='right')
        axes[2].text(len(all_notes) - 1, 0.85, f'Pattern Sim: {pattern_sim:.3f}', ha='right')
        axes[2].text(len(all_notes) - 1, 0.8, f'Swara Sim: {swara_sim:.3f}', ha='right', color='red' if swara_sim < 0.5 else 'green')

        plt.tight_layout()
        return fig
