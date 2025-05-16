document.addEventListener('DOMContentLoaded', function() {
    // Initialiser la carte
    var map = L.map('map').setView([userLat, userLng], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Ajouter le marqueur de l'utilisateur
    var userMarker = L.marker([userLat, userLng], {
        icon: L.divIcon({
            className: 'user-marker',
            html: '<i class="fas fa-user-circle" style="color: #007bff; font-size: 24px;"></i>'
        })
    }).addTo(map);

    // Récupérer tous les professionnels depuis le DOM
    var professionals = [];
    document.querySelectorAll('.professional-card').forEach(function(card) {
        professionals.push({
            lat: parseFloat(card.dataset.lat),
            lng: parseFloat(card.dataset.lng),
            type: card.dataset.type,
            name: card.dataset.name,
            specialite: card.dataset.specialite || '',
            horaires: card.dataset.horaires || '',
            element: card
        });
    });

    // Créer les marqueurs par type
    var markers = {medecin: [], laboratoire: [], pharmacie: []};
    professionals.forEach(function(pro) {
        var marker = L.marker([pro.lat, pro.lng], {
            icon: L.divIcon({
                className: 'professional-marker',
                html: `<i class="fas fa-${pro.type === 'medecin' ? 'user-md' : pro.type === 'laboratoire' ? 'flask' : 'prescription-bottle'}" 
                           style="color: ${pro.type === 'medecin' ? '#007bff' : pro.type === 'laboratoire' ? '#dc3545' : '#28a745'}; font-size: 24px;"></i>`
            })
        }).bindPopup(`<strong>${pro.name}</strong><br>${pro.specialite}<br>${pro.horaires ? '<b>Horaires:</b> ' + pro.horaires : ''}`);
        pro.marker = marker;
        markers[pro.type].push(marker);
    });

    // Fonction pour calculer la distance (Haversine)
    function getDistance(lat1, lng1, lat2, lng2) {
        function toRad(x) { return x * Math.PI / 180; }
        var R = 6371; // km
        var dLat = toRad(lat2 - lat1);
        var dLng = toRad(lng2 - lng1);
        var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
                Math.sin(dLng/2) * Math.sin(dLng/2);
        var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    // Fonction pour afficher les marqueurs et la liste filtrés
    function updateDisplay(type) {
        // Distance max
        var maxDist = parseFloat(document.getElementById('distanceRange').value);
        // Retirer tous les marqueurs
        Object.values(markers).flat().forEach(m => map.removeLayer(m));
        // Filtrer les professionnels
        var filtered = professionals.filter(function(pro) {
            return pro.type === type && getDistance(userMarker.getLatLng().lat, userMarker.getLatLng().lng, pro.lat, pro.lng) <= maxDist;
        });
        // Afficher les marqueurs filtrés
        filtered.forEach(pro => pro.marker.addTo(map));
        // Afficher la bonne liste
        ['medecinsList', 'laboratoiresList', 'pharmaciesList'].forEach(id => {
            var el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        var listId = type === 'medecin' ? 'medecinsList' : type === 'laboratoire' ? 'laboratoiresList' : 'pharmaciesList';
        var el = document.getElementById(listId);
        if (el) {
            el.style.display = 'block';
            // Afficher/masquer les éléments de la liste selon le filtre distance
            var items = el.querySelectorAll('.professional-card, .list-group-item');
            var i = 0;
            items.forEach(function(item) {
                if (filtered[i] && item.dataset && item.dataset.lat && item.dataset.lng) {
                    var plat = parseFloat(item.dataset.lat);
                    var plng = parseFloat(item.dataset.lng);
                    if (getDistance(userMarker.getLatLng().lat, userMarker.getLatLng().lng, plat, plng) <= maxDist) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                } else {
                    item.style.display = '';
                }
                i++;
            });
        }
    }

    // Gestion des filtres
    document.querySelectorAll('.filter-button').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-button').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            var type = this.dataset.type;
            updateDisplay(type);
        });
    });

    // Gestion du slider distance
    document.getElementById('distanceRange').addEventListener('input', function() {
        var type = document.querySelector('.filter-button.active').dataset.type;
        document.getElementById('distanceValue').textContent = this.value + ' km';
        updateDisplay(type);
    });

    // Affichage initial : médecins
    updateDisplay('medecin');

    // Géolocalisation navigateur
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(function(position) {
            var lat = position.coords.latitude;
            var lng = position.coords.longitude;
            userMarker.setLatLng([lat, lng]);
            map.setView([lat, lng], 13);
            fetch('', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: `location=${lat},${lng}`
            });
            // Mettre à jour l'affichage avec la nouvelle position
            var type = document.querySelector('.filter-button.active').dataset.type;
            updateDisplay(type);
        });
    }

    // Scroll chat en bas
    var chatContainer = document.getElementById('chatContainer');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}); 