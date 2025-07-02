// Navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

document.getElementById('predictionForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const location = document.getElementById('predictionSearch').value;
    
    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `location=${encodeURIComponent(location)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            // Update basic info
            document.getElementById('resultLocation').textContent = data.location;
            document.getElementById('predictedRate').textContent = data.predicted_crime_rate;
            document.getElementById('predictedYear').textContent = data.predicted_year;
            document.getElementById('confidenceBadge').textContent = 
                data.confidence === 'high' ? 'High Confidence' : 
                data.confidence === 'medium' ? 'Medium Confidence' : 'Low Confidence';
            
            // Update recommendations
            const recList = document.getElementById('recommendations');
            recList.innerHTML = '';
            const recommendations = [
                'Increase police patrols in high-risk areas',
                'Implement community awareness programs',
                'Enhance street lighting in identified hotspots',
                'Deploy mobile surveillance units'
            ];
            recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = rec;
                recList.appendChild(li);
            });
            
            // Show charts (would need Chart.js included)
            if (typeof Chart !== 'undefined') {
                renderHistoryChart(data.historical_data);
            }
            
            document.getElementById('predictionResults').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while fetching prediction');
    });
});

function renderHistoryChart(historyData) {
    const ctx = document.getElementById('historyChart').getContext('2d');
    const years = Object.keys(historyData).sort();
    const rates = years.map(year => historyData[year]);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [{
                label: 'Crime Rate (per 100,000)',
                data: rates,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Crime Rate: ${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Crime Rate'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Year'
                    }
                }
            }
        }
    });
}

function renderCrimeCharts() {
    // This function will be called from analysis.html
    // Plotly charts are already rendered in the template
    console.log("Crime analysis charts initialized");
}