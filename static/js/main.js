// Navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
});

// Initialize Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Safely attach predictionForm handler only if the element exists
    const predictionForm = document.getElementById('predictionForm');
    const predictionSearch = document.getElementById('predictionSearch');

    if (predictionForm && predictionSearch) {
        predictionForm.addEventListener('submit', function(e) {
            const location = predictionSearch.value.trim();
            if (!location) return;

            // Optional AJAX hook if predictionResults container exists
            const resultsContainer = document.getElementById('predictionResults');
            if (!resultsContainer) return; // Allow natural form submit

            e.preventDefault();
            fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `location=${encodeURIComponent(location)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    const resultLoc = document.getElementById('resultLocation');
                    if (resultLoc) resultLoc.textContent = data.location;
                    resultsContainer.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Prediction fetch error:', error);
            });
        });
    }
});