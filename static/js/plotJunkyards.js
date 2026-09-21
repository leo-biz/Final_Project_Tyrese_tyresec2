// Collect info from context data 
const RESULTS_DATA = JSON.parse(document.querySelector('#yard_data').textContent);
const AVG_LAT = RESULTS_DATA['avg_lat'];
const AVG_LONG = RESULTS_DATA['avg_long'];
var map = null;
var markers = [];
var selectedJunkyard = null;

function initMap(){
    map = L.map('map').setView(center = [AVG_LAT, AVG_LONG], 9);
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        minZoom: 2,
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
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
        <div class="min-w-[230px] py-2">
            <p class="mb-1 text-xs font-bold uppercase tracking-wide text-primary">ScrapHounds yard</p>
            <h3 class="mb-2 text-base font-bold">${yard.meta.name}</h3>
            <p class="text-sm text-muted-foreground">${yard.meta.address}</p>
            <p class="mb-3 text-sm text-muted-foreground">${yard.meta.city}, ${yard.meta.state}</p>
            <div class="flex items-center justify-between">
                <button 
                    onclick="showInventory(${yard.meta.junkyard_id})"
                    class="w-full rounded-md border-2 border-primary px-3 py-2 text-sm font-bold text-primary transition-colors hover:bg-primary hover:text-primary-foreground"
                >
                    See ${yard.num_results + suffix} 
                </button>
            </div>
        </div>
    `;
}

function createMarkerIcon(isSelected = false) {
    const size = isSelected ? 48 : 40;
    
    return L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                background: rgb(var(--color-primary));
                width: ${size}px;
                height: ${size}px;
                border-radius: 12px 12px 12px 0;
                transform: rotate(-45deg);
                border: ${isSelected ? '4' : '3'}px solid rgb(var(--color-card));
                box-shadow: ${isSelected ? '0 0 0 6px rgb(var(--color-primary) / 0.2), 0 10px 24px rgba(0, 0, 0, 0.35)' : '0 8px 20px rgba(0, 0, 0, 0.28)'};
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <span style="transform: rotate(45deg); color: rgb(var(--color-primary-foreground)); font-weight: 800; font-size: ${isSelected ? '14' : '12'}px;">SH</span>
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
