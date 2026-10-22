document.addEventListener('DOMContentLoaded', () => {
    fetch('/locations')
        .then(response => response.json())
        .then(data => {
            const startSelect = document.getElementById('start');
            const stopsSelect = document.getElementById('stops');
            const destSelect = document.getElementById('dest');
            
            for (const [id, loc] of Object.entries(data)) {
                const optionText = `${loc.name} (${id})`;
                startSelect.add(new Option(optionText, id));
                stopsSelect.add(new Option(optionText, id));
                destSelect.add(new Option(optionText, id));
            }
            
            if (destSelect.options.length > 1) {
                destSelect.selectedIndex = 1;
            }
        });

    document.getElementById('navForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const payload = {
            start: document.getElementById('start').value,
            dest: document.getElementById('dest').value,
            stops: document.getElementById('stops').value
        };

        fetch('/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            const resultDiv = document.getElementById('result');
            const directionsDiv = document.getElementById('directions');
            
            resultDiv.style.display = 'block';
            directionsDiv.innerHTML = '';

            if (data.error) {
                directionsDiv.innerHTML = `<div class="error">${data.error}</div>`;
            } else {
                let html = `
                    <div class="stats">
                        <p>Optimized Algorithm: <strong>${data.algorithm}</strong></p>
                        <p>Total distance: <strong>${data.cost} units</strong></p>
                    </div>
                    <ol>
                `;
                
                data.path.forEach(loc => {
                    html += `<li><strong>${loc.name}</strong> (${loc.building}, Floor ${loc.floor})</li>`;
                });
                
                html += '</ol>';
                directionsDiv.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('result').style.display = 'block';
            document.getElementById('directions').innerHTML = '<div class="error">An error occurred while calculating the route.</div>';
        });
    });
});