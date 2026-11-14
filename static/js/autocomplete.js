document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const locationInput = document.getElementById('locationInput');
    
    if (searchInput) {
        setupAutocomplete(searchInput, 'homeAutocompleteOptions');
    }
    
    if (locationInput) {
        setupAutocomplete(locationInput, 'predictionOptions');
    }
    
    function setupAutocomplete(inputElement, datalistId) {
        let debounceTimer;

        inputElement.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const query = this.value.trim();
            if (query.length < 2) return;
            
            debounceTimer = setTimeout(() => {
                fetch(`/autocomplete?q=${encodeURIComponent(query)}`)
                    .then(response => {
                        if (!response.ok) throw new Error('Network response was not ok');
                        return response.json();
                    })
                    .then(data => {
                        if (data && data.length > 0) {
                            let datalist = document.getElementById(datalistId);
                            if (!datalist) {
                                datalist = document.createElement('datalist');
                                datalist.id = datalistId;
                                document.body.appendChild(datalist);
                            }
                            
                            datalist.innerHTML = '';
                            data.forEach(item => {
                                const option = document.createElement('option');
                                option.value = item;
                                datalist.appendChild(option);
                            });
                            
                            inputElement.setAttribute('list', datalistId);
                        }
                    })
                    .catch(error => console.error('Autocomplete fetch error:', error));
            }, 250);
        });
    }
});