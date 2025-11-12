// 1. Load environment variables first
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db'); 
const sensorRoutes = require('./routes/sensorRoutes'); // <-- Import is good

// --- A. CONNECT TO DATABASE ---
connectDB();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware Setup (This should be first)
app.use(cors()); 
app.use(express.json()); 

// --- B. ENDPOINTS (Routes) ---

// 1. Register API Routes (THIS IS THE CORRECT LOCATION)
// Any request starting with /api/v1/sensors will go to sensorRoutes.js
app.use('/api/v1/sensors', sensorRoutes); 

// 2. Health Check Endpoint (GET /)
app.get('/', (req, res) => {
    res.status(200).json({
        message: 'AquaMapper Backend is online!',
        status: 'OK'
    });
});

// --- C. START SERVER ---
app.listen(PORT, () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`);
});