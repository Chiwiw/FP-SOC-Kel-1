from flask import Flask, request, jsonify
import joblib
import pandas as pd
import json
import os
import sys

# To allow importing from ai-model directory when running from VM
ai_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai-model'))
if ai_model_path not in sys.path:
    sys.path.append(ai_model_path)

from src.alert_model import flatten_wazuh_alert

app = Flask(__name__)

# Load the model
# Adjust path based on where it's actually run (assuming it's run from inside ai-model/ or soar-integration/)
MODEL_PATH = os.path.join(ai_model_path, 'artifacts', 'alert_tp_fp_model.joblib')

try:
    pipeline = joblib.load(MODEL_PATH)
    print(f"Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    pipeline = None
    print(f"Warning: Could not load model from {MODEL_PATH}: {e}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/score', methods=['POST'])
def score_alert():
    if pipeline is None:
        return jsonify({"error": "Model not loaded"}), 500

    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Handle both single alert and list of alerts (Shuffle may send list or single dict)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        if not isinstance(data, dict):
             return jsonify({"error": "Invalid format, expected a JSON object"}), 400

        # Flatten the alert structure
        flat_alert = flatten_wazuh_alert(data)
        df = pd.DataFrame([flat_alert])

        # Drop label column if it exists (shouldn't for new alerts, but just in case)
        if "label" in df.columns:
            df = df.drop(columns=["label"])

        # Predict probability
        probabilities = pipeline.predict_proba(df)[:, 1]
        prediction = pipeline.predict(df)[0]
        
        prob = float(probabilities[0])
        
        # Threshold Logic from workflow
        if prob >= 0.80:
            decision = "High Confidence"
        elif prob >= 0.50:
            decision = "Manual Review"
        else:
            decision = "Likely False Positive"

        return jsonify({
            "tp_probability": prob,
            "prediction": int(prediction),
            "decision": decision
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run on 0.0.0.0 to allow Shuffle to connect
    app.run(host='0.0.0.0', port=5000)
