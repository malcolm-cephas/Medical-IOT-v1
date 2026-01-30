const socket = io();

// DOM Elements
const hrValue = document.getElementById('hr-value');
const spo2Value = document.getElementById('spo2-value');
const tempValue = document.getElementById('temp-value');
const humValue = document.getElementById('hum-value');
const connectionStatus = document.getElementById('connection-status');

// Chart Configuration
const ctx = document.getElementById('ecgChart').getContext('2d');
const MAX_DATA_POINTS = 100; // Number of points to show on graph

const ecgChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: Array(MAX_DATA_POINTS).fill(''),
        datasets: [{
            label: 'ECG Signal',
            data: Array(MAX_DATA_POINTS).fill(0),
            borderColor: '#38bdf8',
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 0,
            fill: false
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false, // Disable animation for performance
        scales: {
            x: {
                display: false // Hide x-axis labels
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: '#94a3b8'
                },
                suggestedMin: 0,
                suggestedMax: 1024 // Arduino analog range
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    }
});

// Socket.io Events
socket.on('connect', () => {
    connectionStatus.textContent = 'Connected';
    connectionStatus.classList.remove('disconnected');
    connectionStatus.classList.add('connected');
});

socket.on('disconnect', () => {
    connectionStatus.textContent = 'Disconnected';
    connectionStatus.classList.remove('connected');
    connectionStatus.classList.add('disconnected');
});

socket.on('sensor_update', (msg) => {
    // Only update if the data belongs to the patient we are watching
    if (msg.patient_id !== PATIENT_ID) return;

    const data = msg.data;

    // Update Vital Signs
    if (data.hr) hrValue.textContent = data.hr;
    if (data.spo2) spo2Value.textContent = data.spo2;
    if (data.temp) tempValue.textContent = data.temp.toFixed(1);
    if (data.hum) humValue.textContent = data.hum.toFixed(1);

    // Update ECG Chart
    if (data.ecg !== undefined) {
        updateChart(data.ecg);
    }
});

function updateChart(newValue) {
    const data = ecgChart.data.datasets[0].data;

    // Remove oldest point and add new one
    data.shift();
    data.push(newValue);

    ecgChart.update();
}
