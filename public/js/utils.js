const valid_geometry = (geometry) => {
    let coordinates;
    // console.log(geometry.getCoordinates());
    if (geometry) {
        if (geometry.getType() === 'Point') {
                return ol.proj.transform(geometry.getCoordinates(), 'EPSG:3857', 'EPSG:4326');
        } else {
            coordinates = geometry.getCoordinates()[0].map(coord => {
                return ol.proj.transform(coord, 'EPSG:3857', 'EPSG:4326');
            });
        }
    } else {
        coordinates = null;
    }
    return coordinates;
  };

export { valid_geometry };