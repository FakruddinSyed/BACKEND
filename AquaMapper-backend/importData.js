const fs = require('fs');
const csv = require('csv-parser');
const path = require('path');
require('dotenv').config();
const connectDB = require('./config/db');
const SensorData = require('./models/SensorData');

// --- Configuration ---
const INPUT_CSV = 'hyderabad_sensor_data.csv'; 
const filePath = path.join(__dirname, INPUT_CSV);

// Define the hardcoded coordinates used for the simulation
const STATION_COORDINATES = {
    // Lat, Lon pairs for 5 realistic locations in Hyderabad/Telangana
    'HYD_SANATHNAGAR_1745_7851': [78.5172, 17.4521], // Lon, Lat (for GeoJSON)
    'HYD_HITEC_CITY_1744_7862': [78.6283, 17.4426],
    'HYD_AMEERPET_1744_7845': [78.4599, 17.4396],
    'HYD_UPPAL_1739_7856': [78.5614, 17.3916],
    'HYD_KUKATPALLY_1748_7840': [78.4069, 17.4851]
};

// Simple simulation function (pure JavaScript equivalent of the Python logic)
const simulateWaterMetrics = (records) => {
    let baseLevel = 5.0; // Starting water level
    const formattedData = [];

    for (const item of records) {
        // --- 1. Data Cleaning and Parsing ---
        const stationId = item.sensor_id;
        
        // Skip records for stations not in our 5-station map (if the file has more)
        if (!STATION_COORDINATES[stationId]) {
            continue;
        }

        const lat = parseFloat(item.latitude);
        const lon = parseFloat(item.longitude);
        const rainfall = parseFloat(item.rainfall_mm) || 0; // Use 0 if missing/invalid

        // --- 2. Water Level Simulation Logic ---
        const declineRate = 0.005; 
        const rainInfluence = rainfall * 0.1; 

        // Calculate new level
        let newLevel = baseLevel + rainInfluence - declineRate + (Math.random() * 0.02 - 0.01); 
        newLevel = Math.max(1.0, Math.min(10.0, newLevel)); // Clamp between 1m and 10m
        baseLevel = newLevel; // Update base level for the next timestamp

        // --- 3. pH Level Simulation Logic ---
        const basePh = 7.5;
        const phNoise = Math.random() * 0.1 - 0.05;
        const rainPhEffect = rainfall > 5 ? (rainfall / 50) * -0.2 : 0;
        const ph = Math.max(6.5, Math.min(8.5, basePh + phNoise + rainPhEffect));

        // --- 4. Prepare for MongoDB ---
        formattedData.push({
            station_id: stationId,
            timestamp: new Date(item.timestamp),
            water_level_m: parseFloat(newLevel.toFixed(2)),
            rainfall_mm: parseFloat(rainfall.toFixed(2)),
            ph_level: parseFloat(ph.toFixed(2)),
            location: {
                type: 'Point',
                coordinates: [lon, lat] // [Longitude, Latitude] for GeoJSON
            }
        });
    }
    return formattedData;
};

const importData = async () => {
    // 1. Connect to DB
    await connectDB();

    try {
        console.log(`Starting data import from ${INPUT_CSV}...`);
        
        // Read CSV and collect all records first
        const records = [];
        await new Promise((resolve, reject) => {
            fs.createReadStream(filePath)
                .pipe(csv())
                .on('data', (data) => records.push(data))
                .on('end', () => resolve())
                .on('error', (error) => reject(error));
        });

        // Process records to simulate metrics and format GeoJSON
        const formattedData = simulateWaterMetrics(records);

        // 2. Clear existing data
        await SensorData.deleteMany();
        console.log('Database cleared of existing sensor data.');

        // 3. Insert bulk data into MongoDB
        await SensorData.insertMany(formattedData, { ordered: false }); 

        console.log(`✅ Data Successfully Imported! Total documents: ${formattedData.length}`);
        process.exit();

    } catch (error) {
        if (error.code === 'ENOENT') {
            console.error(`❌ File Not Found: Please ensure ${INPUT_CSV} is in the root project folder.`);
        } else {
            console.error('❌ Error during data import:', error.message);
        }
        process.exit(1);
    }
};

importData();