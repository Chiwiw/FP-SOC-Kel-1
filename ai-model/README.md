# AI Model

> [!NOTE]
> Modul ini dikerjakan oleh **Anggota 3**.

## Tujuan
Folder ini berisi pipeline AI/ML untuk memprediksi apakah sebuah alert Wazuh berlabel `TP` atau `FP`.

Model yang dipakai saat ini adalah `LogisticRegression` dengan feature engineering dari kolom alert terstruktur, termasuk:
- `rule.id` dan `rule.level`
- `rule.groups`
- `agent.name` dan `decoder.name`
- fitur waktu dari `timestamp`
- fitur tekstual ringan dari `full_log` dan `syscheck.path`
- frekuensi source IP yang muncul di dataset training

## Isi Folder
- `src/alert_model.py` - definisi feature engineering dan pipeline model
- `train_model.py` - script training, evaluasi, dan penyimpanan artifact
- `score_alert.py` - script scoring untuk satu alert baru atau file alert
- `requirements.txt` - dependensi Python yang dibutuhkan
- `artifacts/` - output model, metrik, dan ringkasan fitur hasil training

## Cara Pakai
Install dependensi terlebih dahulu:

```bash
python -m pip install -r ai-model/requirements.txt
```

Training model default:

```bash
python ai-model/train_model.py --data FP-SOC-Kel-1/dataset/final_dataset.csv
```

Hasil training akan disimpan ke `ai-model/artifacts/`.

Scoring alert dari file JSON Wazuh:

```bash
python ai-model/score_alert.py --model ai-model/artifacts/alert_tp_fp_model.joblib --input path/to/alert.json
```

## Output Training
- `alert_tp_fp_model.joblib` - pipeline preprocessing + model terlatih
- `metrics.json` - accuracy, precision, recall, F1, confusion matrix
- `classification_report.json` - classification report lengkap
- `top_features.json` - fitur paling berpengaruh untuk label `TP` dan `FP`

## Hasil Training Terbaru
Training pada `dataset/final_dataset.csv` menghasilkan:
- Accuracy: `0.999793`
- Precision: `0.992908`
- Recall: `1.000000`
- F1-score: `0.996441`

Confusion matrix pada split uji:
```text
[[4690, 1],
 [0, 140]]
```

Fitur yang paling kuat untuk kelas positif didominasi oleh pola DDoS dan malware, misalnya `rule.id_100003`, `has_http_keyword`, dan `rule.level`.

## Catatan
- Dataset final yang dipakai adalah `dataset/final_dataset.csv`.
- Label target: `1 = TP`, `0 = FP`.
- Script scoring bisa membaca alert Wazuh mentah yang masih berbentuk JSON nested dan akan menormalkannya sebelum prediksi.
