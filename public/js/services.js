import { valid_geometry } from './utils.js';

const host = "http://0.0.0.0:8000";

///////////////////////////////////////////////////////////////////////
// Async functions to call the API
//////////////////////////////////////////////////////////////////////

const get_query = async function (apiKey, geometry, itemName, startDate, endDate,  cloudCover, selectedAsset){
  let coordinates;
  coordinates = valid_geometry(geometry);
  // Crear la URL con todos los parámetros necesarios
  const url = `${host}/planet/search`;
  const body = {
    api_key: apiKey, 
    geometry: JSON.stringify(coordinates), 
    item_type: itemName,
    start_date: startDate,
    end_date: endDate,
    cloud_cover: parseFloat(cloudCover),
    asset: selectedAsset
  };

  try {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        throw new Error(`Error: ${response.status} - ${await response.text()}`);
    }

    const data = await response.json();
    return data;
} catch (error) {
    console.error('Error al realizar la descarga:', error);
}
};

const displayQueryResults = function(data, apiKey) {
  const resultContainer = document.getElementById('resultContainer');
  resultContainer.innerHTML = ''; // Clear previous results

  const selectedItems = new Set(); // Set to store selected item IDs

  const itemsPerPage = 3;
  let currentPage = 1;
  const items = Object.values(data);

  function renderPage(page) {
      resultContainer.innerHTML = '';
      const start = (page - 1) * itemsPerPage;
      const end = page * itemsPerPage;
      const paginatedItems = items.slice(start, end);
  
      paginatedItems.forEach(item => {
        console.log('Processing item:', item);
        const itemElement = document.createElement('div');
        itemElement.className = 'result-item';

        const checkboxLabel = document.createElement('label');
        checkboxLabel.className = 'item-checkbox-label';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'item-checkbox';
        checkbox.value = item.id;
        checkbox.checked = selectedItems.has(item.id); 
        checkbox.addEventListener('change', () => handleCheckboxChange(item.id, checkbox.checked));
        itemElement.appendChild(checkbox);

        const itemId = document.createElement('h3');
        itemId.innerText = `ID: ${item.id}`;
        itemElement.appendChild(itemId);

        const itemType = document.createElement('p');
        itemType.innerText = `Item type: ${item.properties.item_type}`;
        itemElement.appendChild(itemType);

        const acquiredDate = document.createElement('p');
        acquiredDate.innerText = `Acquired date: ${item.properties.acquired}`;
        itemElement.appendChild(acquiredDate);

        const instrument = document.createElement('p');
        instrument.innerText = `Instrument: ${item.properties.instrument || 'N/A'}`;
        itemElement.appendChild(instrument);

        const thumbnailImage = document.createElement('img');
        thumbnailImage.src = `${item._links.thumbnail}?api_key=${apiKey}`;
        itemElement.appendChild(thumbnailImage);

        resultContainer.appendChild(itemElement);
    });

    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = end >= items.length;
}

function updateSelectedItemsList() {
  const selectedItemsList = document.getElementById('selectedItemsList');
  selectedItemsList.innerHTML = ''; // Clear previous list items

  selectedItems.forEach(itemId => {
      const listItem = document.createElement('li');
      listItem.textContent = itemId;
      selectedItemsList.appendChild(listItem);
  });
}

  function handleCheckboxChange(itemId, isChecked) {
    if (isChecked) {
        selectedItems.add(itemId);
    } else {
        selectedItems.delete(itemId);
    }
    console.log('Selected item IDs:', Array.from(selectedItems));
    updateSelectedCount();
    updateSelectedItemsList();
  }

  function updateSelectedCount() {
    document.getElementById('selectedCount').innerText = `Selected items: ${selectedItems.size}/${items.length}`;
  }

  function updateSelectedItemsList() {
    const selectedItemsList = document.getElementById('selectedItemsList');
    selectedItemsList.innerHTML = ''; // Clear previous list items

    selectedItems.forEach(itemId => {
        const listItem = document.createElement('li');
        listItem.textContent = itemId;
        selectedItemsList.appendChild(listItem);
    });
}
  document.getElementById('prevPage').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        renderPage(currentPage);
    }
  });

  document.getElementById('nextPage').addEventListener('click', () => {
    if (currentPage * itemsPerPage < items.length) {
        currentPage++;
        renderPage(currentPage);
    }
});

renderPage(currentPage)
}

const order_download = async function (apiKey, itemName, itemList, geometry, SavePath, productBundle){ 
    let coordinates;
    coordinates = valid_geometry(geometry);

    // Crear la URL con todos los parámetros necesarios
    const url2 = `${host}/planet/download`;
    const body2 = {
    api_key: apiKey, 
    item_type: itemName,
    item_list: String(itemList),
    geometry: JSON.stringify(coordinates),
    order_dir: String(SavePath),    
    product_bundle: productBundle
    };

    try {
      const response2 = await fetch(url2, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify(body2)
      });

      if (!response2.ok) {
          throw new Error(`Error: ${response2.status} - ${await response2.text()}`);
      }

      const data2 = await response2.json();
      return data2
  } catch (error) {
      console.error('Error al realizar la descarga:', error);
  }
  };

export {get_query, displayQueryResults, order_download};