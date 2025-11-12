import pandas as pd
from sklearn.linear_model import LinearRegression
from flask import Flask, jsonify
import numpy as np
import os
from datetime import datetime, timedelta
import io

app = Flask(__name__)

# --- Model Training Function ---
def train_rainfall_predictor():
    # File is assumed to be renamed to a clean CSV name
    FILE_PATH = 'icrisat_weather.xlsx' 
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ ML ERROR: File not found at {FILE_PATH}. Model training skipped.")
        print("💡 HINT: Ensure your ICRISAT file is in the 'ml-service' folder and named 'icrisat_weather.csv'.")
        return None

    df = None
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    # 1. Robust File Reading Attempt (Handle Unicode and Format Errors)
    for encoding in encodings:
        try:
            # Try reading as CSV with various encodings
            df = pd.read_csv(FILE_PATH, encoding=encoding)
            print(f"✅ Data read successfully using {encoding} encoding.")
            break
        except UnicodeDecodeError:
            continue
        except pd.errors.ParserError:
            # If it fails as a CSV structure, it might be an Excel file
            try:
                # Try reading as Excel (XLSX)
                df = pd.read_excel(FILE_PATH, engine='openpyxl')
                print("✅ Data read successfully as Excel (XLSX).")
                break
            except Exception:
                continue
        except Exception as e:
            print(f"❌ ML ERROR: Failed with encoding {encoding}. Details: {e}")
            continue

    if df is None:
        print("❌ ML ERROR: Data file could not be read using any common encoding or format.")
        return None
    
    # 2. Select and Clean Data (Uses columns: Date, MaxT, Rain)
    try:
        df = df[['Date', 'MaxT', 'Rain']].dropna() 
    except KeyError as e:
        print(f"❌ ML ERROR: Column {e} not found. Check that your file headers are exactly 'Date', 'MaxT', and 'Rain'.")
        return None

    df['Date'] = pd.to_datetime(df['Date'])
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

# --- API Endpoints ---

@app.route('/predict/rainfall', methods=['GET'])
def predict_rainfall():
    if RAIN_MODEL is None:
        return jsonify({"error": "ML model failed to load/train. Check Python terminal for details."}), 503 

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
    print("Starting ML Flask Service on http://0.0.0.0:5000...")
    # FIX: Use host='0.0.0.0' for stable connection with Node.js
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)