document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const predictionSearch = document.getElementById('predictionSearch');
    
    if (searchInput) {
        setupAutocomplete(searchInput);
    }
    
    if (predictionSearch) {
        setupAutocomplete(predictionSearch);
    }
    
    function setupAutocomplete(inputElement) {
        inputElement.addEventListener('input', function() {
            const query = this.value;
            if (query.length < 2) return;
            
            fetch(`/autocomplete?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    // For demo, we'll just show the first result
                    if (data.length > 0) {
                        // In a real app, you would show a dropdown with all results
                        this.setAttribute('list', 'autocompleteOptions');
                        
                        let datalist = document.getElementById('autocompleteOptions');
                        if (!datalist) {
                            datalist = document.createElement('datalist');
                            datalist.id = 'autocompleteOptions';
                            document.body.appendChild(datalist);
                        }
                        
                        datalist.innerHTML = '';
                        data.forEach(item => {
                            const option = document.createElement('option');
                            option.value = item;
                            datalist.appendChild(option);
                        });
                        
                        this.setAttribute('list', 'autocompleteOptions');
                    }
                })
                .catch(error => console.error('Error:', error));
        });
    }
});