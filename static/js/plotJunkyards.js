// Collect info from context data 
const RESULTS_DATA = JSON.parse(document.querySelector('#yard_data').textContent);
const AVG_LAT = RESULTS_DATA['avg_lat'];
const AVG_LONG = RESULTS_DATA['avg_long'];
var map = null;
var markers = [];
var selectedJunkyard = null;

function initMap(){
    map = L.map('map').setView(center = [AVG_LAT, AVG_LONG], 9);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        minZoom: 2,
        attribution: '© <a href="https://carto.com/attributions">CARTO</a>'
      }).addTo(map);
    createMarkers();
}
function removeMarkers(){
    markers.map(marker => {marker.remove()});
    markers = [];
}
function createMarkers(){
    // Create markers for each junkyard
    RESULTS_DATA['yard_data'].map(yard => {
        const isSelected = selectedJunkyard && selectedJunkyard.meta.junkyard_id == yard.meta.junkyard_id;
        const popupContent = createPopupContent(yard);
        var marker = L.marker([yard.meta.lat, yard.meta.long], { icon: createMarkerIcon(isSelected) }).addTo(map);
        marker.addEventListener('click', (marker)=>handleMarkerClick(yard));
        marker.bindPopup(popupContent, {
            permanent: true,
            direction: 'top',
            offset: [-3, 10], // Adjust position slightly upwards
            className: 'custom-tooltip' // Add a custom CSS class
            });
        marker['junkyard_id'] = yard.meta.junkyard_id;
        markers.push(marker);
    });
}
function handleMarkerClick(yard) {
    selectedJunkyard = yard;
    removeMarkers();
    createMarkers();
    markers.map(marker=> {
        if (marker.junkyard_id == yard.meta.junkyard_id)
            marker.openPopup();
            map.flyTo([yard.meta.lat + 0.05, yard.meta.long ], 10);
    });
}
function createPopupContent(yard){
    var suffix = yard.num_results > 1 ?  " vehicles" : " vehicle";
    return `
        <div class="py-2 min-w[250px]">
            <div class="flex items-center gap-2 mb-2">
                <span class="text-lg lg:2xl"></span>
            </div>
            <h3 class="font-bold text-base mb-2">${yard.meta.name}</h3>
            <h6 class="text-sm text-muted-foreground">${yard.meta.address}</h6>
            <h6 class="text-sm text-muted-foreground mb-2">${yard.meta.city}, ${yard.meta.state}</h6>
            <div class="flex items-center justify-between pt-2">
                <button 
                    onclick="showInventory(${yard.meta.junkyard_id})"
                    class="text-sm w-full px-3 py-1 border-2 border-orange text-primary rounded hover:bg-primary/90 hover:text-white transition-colors"
                >
                    See ${yard.num_results + suffix} 
                </button>
            </div>
        </div>
    `;
}

function createMarkerIcon(isSelected = false) {
    const size = isSelected ? 48 : 40;
    const emoji = '🔧';
    
    return L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                background: linear-gradient(135deg, hsl(22, 75%, ${isSelected ? '60' : '50'}%), hsl(35, 80%, ${isSelected ? '65' : '55'}%));
                width: ${size}px;
                height: ${size}px;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                border: ${isSelected ? '4' : '3'}px solid white;
                box-shadow: ${isSelected ? '0 0 20px rgba(230, 104, 41, 0.8), 0 6px 16px rgba(0, 0, 0, 0.5)' : '0 4px 12px rgba(0, 0, 0, 0.4)'};
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <span style="transform: rotate(45deg); font-size: ${isSelected ? '24' : '20'}px;">${emoji}</span>
            </div>
        `,
        iconSize: [size, size],
        iconAnchor: [size / 2, size],
        popupAnchor: [2, -size - 6]
    });
}

// Scroll to junkyard inventory and open table
function showInventory(junkyardId) {
    
    // Scroll to inventory table
    const element = document.getElementById(`inventory-${junkyardId}`);
    const table = document.getElementById(`table-${junkyardId}`);
    if (element) {
        toggleTable(junkyardId, justshow=true);
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
}


if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMap);
} else {
    initMap();
}
/*



function initMap(){
    map = L.map('map').setView(center = [avg_lat, avg_long], 9);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map); 
    {% for yard in fetched_yard_data %}
        var junkyard = {

            'lat':{{yard.lat}},
            'long':{{yard.long}},
            'name':'{{yard.name}}',
            'address':'{{yard.meta.address}}',
            'city':'{{yard.meta.city}}',
            'state':'{{yard.meta.state}}',
            'num_results':'{{yard.num_results}}',
            'id':'{{yard.meta.pk}}',

        };
        junkyards.push(junkyard);
        var suffix = junkyard.num_results > 1 ?  " vehicles" : " vehicle";
        var marker = L.marker([junkyard.lat, junkyard.long], { icon: createMarkerIcon() })
            .addTo(map);
        var popupContent = `
            <div class="p-2 min-w-[200px]">
                <div class="flex items-center gap-2 mb-2">
                    <span class="text-lg lg:2xl"></span>
                </div>
                <h3 class="font-bold text-base mb-2">${junkyard.name}</h3>
                <h6 class="text-sm text-muted-foreground">${junkyard.address}</h6>
                <h6 class="text-sm text-muted-foreground mb-2">${junkyard.city}, ${junkyard.state}</h6>
                <div class="flex items-center justify-between pt-2">
                    <button 
                        onclick="showInventory(${junkyard.id})"
                        class="text-sm flex-1 px-3 py-1 border-2 border-orange text-primary rounded hover:bg-primary/90 hover:text-white transition-colors"
                    >
                        See ${junkyard.num_results + suffix} 
                    </button>
                </div>
            </div>
        `;
            
        marker.bindPopup(popupContent, {
                permanent: true,
                direction: 'top',
                offset: [-3, 10], // Adjust position slightly upwards
                className: 'custom-tooltip' // Add a custom CSS class
                });
    {% endfor %}
}

 */