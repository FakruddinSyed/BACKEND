const mongoose = require('mongoose');

const SensorDataSchema = mongoose.Schema({
    station_id: {
        type: String,
        required: true,
        index: true
    },
    timestamp: {
        type: Date,
        required: true,
        index: true
    },
    water_level_m: {
        type: Number,
        required: true
    },
    rainfall_mm: {
        type: Number,
        default: 0
    },
    ph_level: {
        type: Number
    },
    location: { // Stored in GeoJSON Point format for MongoDB
        type: {
            type: String,
            enum: ['Point'],
            required: true
        },
        coordinates: { // MUST be [longitude, latitude]
            type: [Number],
            required: true
        }
    }
}, {
    collection: 'sensor_readings',
    timestamps: false
});

// Create the 2dsphere index for geospatial queries (crucial for map functions)
SensorDataSchema.index({ location: '2dsphere' });

module.exports = mongoose.model('SensorData', SensorDataSchema);