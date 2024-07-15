import { get_query } from './services.js';
//////////////////////////////////////////////////////////////////////
// Initialize the map
const map = new ol.Map({
  target: 'map',
  layers: [
    new ol.layer.Tile({
      source: new ol.source.OSM()
    })
  ],
  view: new ol.View({
    center: ol.proj.fromLonLat([-4.7240425, 39.7825346]),
    zoom: 7
  })
});

// Function to update the list of layers
function updateLayerList() {
  const layerUl = document.getElementById('layerUl');
  layerUl.innerHTML = ""; // Clear the current list

  map.getLayers().forEach((layer, index) => {
    const layerLi = document.createElement('li');

    // Create an input field for the layer name
    const layerNameInput = document.createElement('input');
    layerNameInput.type = 'text';
    layerNameInput.value = layer.get('name') || `Capa ${index}`;
    layerNameInput.addEventListener('change', function() {
      layer.set('name', this.value);
      updateLayerList(); // Update the list to reflect the new name
    });

    // Create an input field for opacity
    const opacityInput = document.createElement('input');
    opacityInput.type = 'range';
    opacityInput.min = 0;
    opacityInput.max = 1;
    opacityInput.step = 0.1;
    opacityInput.value = layer.getOpacity();
    opacityInput.addEventListener('change', function() {
      // layer.setOpacity(this.value);
      layer.set('opacity', this.value);
      updateLayerList(); // Update the list to reflect the new name
    });

    // Create a delete button for the layer
    const deleteButton = document.createElement('button');
    deleteButton.innerHTML = 'X';
    deleteButton.addEventListener('click', function() {
      map.removeLayer(layer);
      updateLayerList(); // Update the list after removal
    });

    // Create a button to toggle visibility
    const visibilityButton = document.createElement('button');
    visibilityButton.innerHTML = layer.getVisible() ? 'Hide' : 'Show';
    visibilityButton.addEventListener('click', function() {
      layer.setVisible(!layer.getVisible());
      visibilityButton.innerHTML = layer.getVisible() ? 'Hide' : 'Show';
    });

    // Append elements to the list item
    layerLi.appendChild(layerNameInput);
    layerLi.appendChild(opacityInput);
    layerLi.appendChild(visibilityButton);
    layerLi.appendChild(deleteButton);

    // Append the list item to the list
    layerUl.appendChild(layerLi);
  });
}

// Listen for changes to the layer collection and update the layer list
map.getLayers().on(['add', 'remove'], updateLayerList);

// Call the function once to initialize the layer list
updateLayerList();


//////////////////////////////////////////////////////////////////////
// Initialize the Flatpickr calendar
flatpickr('#calendar-range', {
  mode: "range",
  dateFormat: "Y-m-d",
  onChange: function(selectedDates, dateStr, instance) {
      console.log(selectedDates, dateStr, instance);
  }
});

// Toggle API Key visibility
const apiKeyInput = document.getElementById('apiKey');
const toggleApiKeyButton = document.getElementById('toggleApiKey');

toggleApiKeyButton.addEventListener('click', function() {
    if (apiKeyInput.type === 'password') {
        apiKeyInput.type = 'text';
        toggleApiKeyButton.textContent = 'Hide';
    } else {
        apiKeyInput.type = 'password';
        toggleApiKeyButton.textContent = 'Show';
    }
});


//////////////////////////////////////////////////////////////////////
let globalData;
let productBundles;

// Load data from JSON files
Promise.all([
  fetch('./planet_catalog.json').then(response => response.json()),
  fetch('./orders_product_bundle_2023-02-24.json').then(response => response.json())
]).then(data => {
  globalData = data[0];
  productBundles = data[1];
  initializeMissionComboBox(globalData);
}).catch(error => console.error('Error al cargar los archivos JSON:', error));

function initializeMissionComboBox(data) {
  const missionSelect = document.getElementById('missionSelect');
  const uniqueMissions = [...new Set(data.map(item => item.ITEM_TYPE))];  // Get unique missions

  uniqueMissions.forEach(mission => {
    const option = document.createElement('option');
    option.value = mission;
    option.textContent = mission;
    missionSelect.appendChild(option);
  });

  missionSelect.addEventListener('change', function() {
    const selectedMission = this.value;
    initializeBandComboBox(selectedMission);
  });
}

function initializeBandComboBox(selectedMission) {
  const bandSelect = document.getElementById('bandSelect');
  bandSelect.innerHTML = 'Select a asset type';

  const relevantProduct = globalData.find(item => item.ITEM_TYPE === selectedMission);

  if (relevantProduct && Array.isArray(relevantProduct.ASSET_TYPE)) {
    relevantProduct.ASSET_TYPE.forEach(band => {
      const option = document.createElement('option');
      option.value = band;
      option.textContent = band;
      bandSelect.appendChild(option);
    });
  }
}

// Add event listener to update bundles when band is selected
const bandSelect = document.getElementById('bandSelect');
bandSelect.addEventListener('change', function() {
  const selectedMission = document.getElementById('missionSelect').value;
  const selectedAsset = bandSelect.value;
  updateBundleComboBox(selectedMission, selectedAsset);
});

function updateBundleComboBox(selectedMission, selectedAsset) {
    const bundleSelect = document.getElementById('bundleSelect');
    bundleSelect.textContent = 'Select a product bundle';
  

    // Filter product bundles based on selected mission and asset
    const availableBundles = Object.keys(productBundles).filter(bundleKey => {
    const bundle = productBundles[bundleKey];
    return bundle.assets && bundle.assets[selectedMission] && bundle.assets[selectedMission].includes(selectedAsset);
  });

    availableBundles.forEach(bundleKey => {
      const option = document.createElement('option');
      option.value = bundleKey;
      option.textContent = bundleKey;
      bundleSelect.appendChild(option);
    });
  
    if (availableBundles.length === 0) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'No bundles available';
      bundleSelect.appendChild(option);
    }
  }

 

// Update the cloud cover value dynamically
const cloudCoverSlider = document.getElementById('cloudCoverSlider');
const cloudCoverValue = document.getElementById('cloudCoverValue');

cloudCoverSlider.addEventListener('input', function() {
    cloudCoverValue.innerText = cloudCoverSlider.value;
});


//////////////////////////////////////////////////////////////////////
// First, define the source and vector layer
let source = new ol.source.Vector();
let vector = new ol.layer.Vector({
  source: source
});

// Add the layer to the map
map.addLayer(vector);

// Define a function that adds the draw interaction to the map
let draw;
function addDrawInteraction(type) {
  if (draw) {
    map.removeInteraction(draw);
  }
  draw = new ol.interaction.Draw({
    source: source,
    type: type === 'Rectangle' ? 'Circle' : type,
    geometryFunction: type === 'Rectangle' ? ol.interaction.Draw.createRegularPolygon(4) : undefined
  });
  map.addInteraction(draw);
  
  draw.on('drawend', function(evt) {
    let geometry = evt.feature.getGeometry();
    console.log(geometry.getCoordinates());
  });
}

// Add event listeners for the buttons
document.getElementById('drawPoint').addEventListener('click', function() {
  vector = addDrawInteraction('Point');
});
document.getElementById('drawRectangle').addEventListener('click', function() {
  vector = addDrawInteraction('Rectangle');
});
document.getElementById('drawPolygon').addEventListener('click', function() {
  vector = addDrawInteraction('Polygon');
});
document.getElementById('drawClear').addEventListener('click', function() {
  source.clear();
  // Cancel the draw interaction
  map.removeInteraction(draw);
});

//////////////////////////////////////////////////////////////////////
// Get elements from the DOM in a function
document.getElementById('getDataButton').addEventListener('click', async function() {
  // Get the value of the mission select
  const itemName = document.getElementById('missionSelect').value;
  const selectedAsset = document.getElementById('bandSelect').value;
  const cloudCover = document.getElementById('cloudCoverSlider').value/100;
  const apiKey = document.getElementById('apiKey').value;

  // Get the geometry drawn (if exists)
  const features = source.getFeatures();
  let geometry;
  if (features.length > 0) {
    geometry = features[0].getGeometry();
  }

  // Get the dates from the Flatpickr calendar
  const dateRange = document.getElementById('calendar-range')._flatpickr.selectedDates;
  const startDate = dateRange.length > 0 ? dateRange[0].toLocaleDateString('en-CA') : null;
  const endDate = dateRange.length > 1 ? dateRange[1].toLocaleDateString('en-CA') : null;


  await get_query(apiKey, geometry, itemName, startDate, endDate,
                  cloudCover, selectedAsset);
});