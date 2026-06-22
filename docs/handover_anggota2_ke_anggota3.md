# Handover – Anggota 2 → Anggota 3

## Apa yang telah diserahkan
- **Dataset gabungan**: `dataset/final_dataset.csv`
- **CSV per skenario** (dibuat otomatis):
  - `dataset/ddos_labeled.csv`
  - `dataset/malware_labeled.csv`
  - `dataset/socialeng_labeled.csv`
- **Laporan ringkasan** (JSON) berada di `dataset/handover_report.json`

## Statistik Ringkas per Skenario
| Skenario | Total alert | True Positives (TP) | False Positives (FP) | Persen TP | Persen FP |
|----------|-------------|---------------------|----------------------|-----------|-----------|
| ddos | 6276 | 689 | 5587 | 10.98 % | 89.02 % |
| malware | 8531 | 8 | 8523 | 0.09 % | 99.91 % |
| socialeng | 9347 | 3 | 9344 | 0.03 % | 99.97 % |

## Langkah Berikutnya untuk Anggota 3
1. **Pengembangan model**
   - Muat CSV yang sesuai (misalnya `malware_labeled.csv`) untuk rekayasa fitur dan pelatihan.
   - Kolom `label` menjadi target (1 = TP, 0 = FP).
2. **Pertimbangan fitur**
   - Konversi `timestamp` menjadi epoch atau ekstrak fitur jam/hari minggu.
   - Kolom kategorikal (`rule.id`, `agent.name`, `decoder.name`, `syscheck.path`) dapat diencode dengan one‑hot atau hashing.
3. **Evaluasi**
   - Karena rasio FP sangat tinggi, fokus pada trade‑off precision‑recall, gunakan class‑weighting atau oversampling.
4. **Dokumentasi**
   - Simpan semua percobaan di folder `ai-model/` sesuai dengan README utama.

Jika membutuhkan skrip pra‑proses tambahan atau bantuan dalam pelatihan model, silakan hubungi saya.

## What has been delivered
- **Full merged dataset**: `dataset/final_dataset.csv`
- **Per‑scenario CSVs** (generated automatically):
  - `dataset/ddos_labeled.csv`
  - `dataset/malware_labeled.csv`
  - `dataset/socialeng_labeled.csv`
- **Summary report** (JSON) located at `dataset/handover_report.json`

## Summary statistics per scenario
| Scenario | Total alerts | True Positives (TP) | False Positives (FP) | TP % | FP % |
|----------|--------------|--------------------|----------------------|------|------|
| ddos | 6276 | 689 | 5587 | 10.98 % | 89.02 % |
| malware | 8531 | 8 | 8523 | 0.09 % | 99.91 % |
| socialeng | 9347 | 3 | 9344 | 0.03 % | 99.97 % |

## Next steps for Anggota 3
1. **Model development**
   - Load the appropriate per‑scenario CSV (e.g., `malware_labeled.csv`) for feature engineering and training.
   - The `label` column is the target (1 = TP, 0 = FP).
2. **Feature considerations**
   - Timestamp can be converted to epoch or engineered into time‑of‑day / weekday features.
   - Categorical fields (`rule.id`, `agent.name`, `decoder.name`, `syscheck.path`) may need one‑hot encoding or hashing.
3. **Evaluation**
   - Because FP rates are very high, focus on precision‑recall trade‑offs and consider techniques such as class weighting or oversampling.
4. **Documentation**
   - Keep any experiments logged in `ai-model/` as described in the main README.

Feel free to ask if you need further preprocessing scripts or assistance with model training.
