import { valid_geometry } from './utils.js';

const host = "http://127.0.0.1:8000";

///////////////////////////////////////////////////////////////////////
// Async functions to call the API
//////////////////////////////////////////////////////////////////////

async function get_query(apiKey, geometry, itemName, startDate, endDate, 
                         cloudCover, selectedAsset){
  let coordinates;
  coordinates = valid_geometry(geometry);
  // Crear la URL con todos los parámetros necesarios
  const url = `${host}/planet/search`;
  const body = {
    api_key: apiKey, 
    geometry_json: JSON.stringify(coordinates), 
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
      const error = await response.text();
      throw new Error(`Error: ${response.status} - ${error}`);
    }
    
    const data = await response.json();
    if (data.status === 'success') {
      alert(data.message); // Display success message
      displayQueryResults(data, apiKey);
    }
  } catch (error) {
    console.error('Error al realizar la búsqueda:', error);
    alert(`Error al realizar la búsqueda: ${error.message}`);
  } 
};

function displayQueryResults(data, apiKey) {
  const resultContainer = document.getElementById('resultContainer');
  resultContainer.innerHTML = ''; // Clear previous results

  Object.values(data).forEach(item => {
    console.log('Processing item:', item);
    const itemElement = document.createElement('div');
    itemElement.className = 'result-item';

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
    thumbnailImage.src = `${item._links.thumbnail}?auth_api=${apiKey}`;
    itemElement.appendChild(thumbnailImage);

    resultContainer.appendChild(itemElement);
  });

  // Append the result container to the body or a specific container
  const oldResultContainer = document.getElementById('resultContainer');
  if (oldResultContainer) {
    oldResultContainer.replaceWith(resultContainer);
  } else {
    document.body.appendChild(resultContainer);
  }
}

export {get_query};

// const post_download = async (apiKey, itemName, selectedAsset, 
//                             selectedBundle, cloudCover, 
//                             geometry, startDate, endDate) => {
//     let coordinates;
//     coordinates = valid_geometry(geometry);
//     // Crear la URL con todos los parámetros necesarios
//     const url = `${host}/post-download`;
//     const body = {
//     api_key: apiKey, 
//     geometry_json: JSON.stringify(coordinates),
//     item_type: itemName,
//     start_date: startDate,
//     end_date: endDate,
//     cloud_cover: cloudCover,
//     asset: selectedAsset,
//     bundle: selectedBundle
//     };

//     const response = await fetch(url, {
//     method: 'POST',
//     headers: {
//     'Content-Type': 'application/json'
//     },
//     body: JSON.stringify(body)
//   });

//   const data = await response.text();
//   return data; 
//   };

// export {post_thumbnail, post_download};
