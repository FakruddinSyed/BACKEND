import pandas as pd
from sklearn.linear_model import LinearRegression
from flask import Flask, jsonify
import numpy as np
import os
from datetime import datetime, timedelta

app = Flask(__name__)

print("Current working directory:", os.getcwd())
print("Files here:", os.listdir('.'))

# --- Model Training Function ---
def train_rainfall_predictor():
    FILE_PATH = 'icrisat_weather.csv'
    if not os.path.exists(FILE_PATH):
        print(f"❌ ML ERROR: File not found at {FILE_PATH}. Model training skipped.")
        return None

    try:
        df = pd.read_csv(FILE_PATH)
        print("✅ Data read successfully as CSV.")
    except Exception as e:
        print(f"❌ ML ERROR: Could not read data file. Details: {e}")
        return None

    # 2. Select and Clean Data (Uses columns: Date, MaxT, Rain)
    try:
        df = df[['Date', 'MaxT', 'Rain']].dropna() 
    except KeyError as e:
        print(f"❌ ML ERROR: Column {e} not found. Check that your file headers are exactly 'Date', 'MaxT', and 'Rain'.")
        return None

    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df.set_index('Date', inplace=True)
    
    # 3. Feature Engineering
    df['Rain_Tomorrow'] = df['Rain'].shift(-1)
    df['MaxT_Today'] = df['MaxT']
    df['Rain_Yesterday'] = df['Rain'].shift(1)
    df.dropna(inplace=True)
    
    # 4. Train Model
    X = df[['MaxT_Today', 'Rain_Yesterday']]
    Y = df['Rain_Tomorrow']
    model = LinearRegression()
    model.fit(X, Y)
    
    print("✅ ML Model Trained successfully using ICRISAT data.")
    return model

# Train the model once when the Flask app starts
RAIN_MODEL = train_rainfall_predictor()

# --- API Endpoint ---
@app.route('/predict/rainfall', methods=['GET'])
def predict_rainfall():
    if RAIN_MODEL is None:
        return jsonify({"error": "ML model failed to load/train. Check server log for details."}), 503 

    # Start forecast simulation with plausible current conditions
    current_max_t = 30.0 
    current_rain_yesterday = 5.0
    
    forecast = []
    for i in range(1, 4):
        input_data = np.array([[current_max_t, current_rain_yesterday]])
        predicted_rain = max(0, RAIN_MODEL.predict(input_data)[0]) 
        current_max_t = current_max_t + np.random.normal(0, 0.5) 
        current_rain_yesterday = predicted_rain 
        forecast.append({
            "day": i,
            "date_offset": (datetime.today() + timedelta(days=i)).strftime('%Y-%m-%d'),
            "predicted_rainfall_mm": round(predicted_rain, 2),
            "predicted_max_temp_c": round(current_max_t, 2)
        })

    return jsonify({
        "success": True, 
        "model_used": "Simplified Linear Regression",
        "forecast_days": forecast
    })

if __name__ == '__main__':
    print("Starting ML Flask Service on [http://0.0.0.0:5000](http://0.0.0.0:5000)...")
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)
