# Handover – Anggota 3 → Anggota 4

## Proyek
**Reducing SOC False Alarms through Human-AI Collaboration**

Anggota 3 bertugas menyiapkan pipeline AI/ML untuk mengklasifikasikan alert Wazuh sebagai **TP** atau **FP**, lalu menyerahkan model terlatih ke Anggota 4 untuk integrasi SOAR.

---

## Ringkasan Hasil

- **Dataset utama**: `dataset/final_dataset.csv`
- **Model terlatih**: `ai-model/artifacts/alert_tp_fp_model.joblib`
- **Metrik evaluasi**: `ai-model/artifacts/metrics.json`
- **Ringkasan fitur penting**: `ai-model/artifacts/top_features.json`
- **Scoring script**: `ai-model/score_alert.py`

Model sudah selesai dilatih dan siap dipakai oleh Anggota 4 sebagai komponen prediksi sebelum alert diteruskan ke SOAR.

---

## Status Model

Model yang digunakan adalah `LogisticRegression` dengan feature engineering dari data alert terstruktur, termasuk:

- `rule.id` dan `rule.level`
- `rule.groups`
- `agent.name` dan `decoder.name`
- fitur waktu dari `timestamp`
- fitur teks ringan dari `full_log` dan `syscheck.path`
- frekuensi `srcip` di data pelatihan

### Hasil training terbaru

- **Accuracy**: `0.999793`
- **Precision**: `0.992908`
- **Recall**: `1.000000`
- **F1-score**: `0.996441`

### Confusion matrix

```text
[[4690, 1],
 [0, 140]]
```

### Kesimpulan singkat

Model sudah cukup baik untuk diteruskan ke Anggota 4 karena:

- performanya sangat tinggi pada split uji,
- recall sempurna pada kelas positif,
- pipeline scoring sudah disiapkan,
- artifact model sudah disimpan dan bisa langsung dipanggil.

---

## Kenapa Training Cepat

Training selesai cepat karena:

- dataset berukuran relatif kecil untuk ML tabular,
- model yang dipakai ringan (`LogisticRegression`),
- feature engineering sederhana dan langsung dari kolom alert,
- tidak ada grid search, cross-validation berat, atau deep learning.

Jadi waktu training yang singkat itu normal dan bukan tanda model belum dilatih.

---

## Cara Pakai untuk Anggota 4

### 1) Load model

Gunakan artifact berikut:

```bash
ai-model/artifacts/alert_tp_fp_model.joblib
```

### 2) Scoring alert baru

Contoh menjalankan scoring:

```bash
python ai-model/score_alert.py \
  --model ai-model/artifacts/alert_tp_fp_model.joblib \
  --input path/to/alert.json
```

### 3) Integrasi SOAR

Anggota 4 dapat memakai output probabilitas TP/FP untuk membuat keputusan otomatis, misalnya:

- alert dengan probabilitas TP tinggi → diteruskan ke workflow respons,
- alert dengan probabilitas FP tinggi → ditandai sebagai noise / low priority,
- alert ambigu → tetap dipantau manual.

---

## File yang Diserahkan

### Kode

- `ai-model/src/alert_model.py`
- `ai-model/train_model.py`
- `ai-model/score_alert.py`

### Artifact

- `ai-model/artifacts/alert_tp_fp_model.joblib`
- `ai-model/artifacts/metrics.json`
- `ai-model/artifacts/top_features.json`

### Dokumentasi

- `ai-model/README.md`

---

## Catatan Teknis

- Dataset final yang dipakai: `dataset/final_dataset.csv`
- Label target: `1 = TP`, `0 = FP`
- Script scoring sudah mendukung input alert JSON Wazuh dan file dataset CSV
- Model ini cocok sebagai komponen prediksi awal sebelum orkestrasi SOAR dijalankan Anggota 4

---

## Rekomendasi untuk Anggota 4

1. Gunakan model artifact yang sudah tersedia tanpa retraining ulang.
2. Integrasikan output scoring ke alur SOAR.
3. Tambahkan threshold keputusan jika ingin membedakan alert prioritas tinggi dan rendah.
4. Jika diperlukan, lakukan retraining berkala saat dataset baru tersedia.
