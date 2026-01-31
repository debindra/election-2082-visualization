import React, { useRef, useEffect, useCallback } from 'react';
import maplibregl from 'maplibre-gl';

const SOURCE_ID = 'election-geojson';
const FILL_LAYER_ID = 'election-fill';
const LINE_LAYER_ID = 'election-line';

// Nepal center and default view
const NEPAL_CENTER = [84.12, 28.39];
const NEPAL_ZOOM = 6;
const NEPAL_BOUNDS = [[80.0, 26.3], [88.2, 30.4]];

// Theme: slate blue #1e3a5f, muted red #b91c1c
const FILL_COLOR = '#1e3a5f';
const FILL_OPACITY = 0.45;
const LINE_COLOR = '#1e3a5f';
const LINE_WIDTH = 1.2;
const HOVER_FILL_OPACITY = 0.7;

/**
 * Geographic map that renders GeoJSON from the API (provinces, districts, constituencies)
 * using MapLibre GL. Supports drill-down on feature click.
 */
const GeoMap = ({
  mapData,
  currentLevel,
  onDrillDown,
  language = 'ne',
}) => {
  const containerRef = useRef(null);
  const mapRef = useRef(null);

  const updateSource = useCallback((map, data) => {
    if (!map || !data) return;
    try {
      const source = map.getSource(SOURCE_ID);
      const geojson = {
        type: 'FeatureCollection',
        features: data.features || [],
        metadata: data.metadata,
      };
      if (source) {
        source.setData(geojson);
      } else {
        map.addSource(SOURCE_ID, { type: 'geojson', data: geojson });
        if (!map.getLayer(FILL_LAYER_ID)) {
          map.addLayer({
            id: FILL_LAYER_ID,
            type: 'fill',
            source: SOURCE_ID,
            paint: {
              'fill-color': FILL_COLOR,
              'fill-opacity': FILL_OPACITY,
              'fill-outline-color': LINE_COLOR,
            },
          });
        }
        if (!map.getLayer(LINE_LAYER_ID)) {
          map.addLayer({
            id: LINE_LAYER_ID,
            type: 'line',
            source: SOURCE_ID,
            paint: {
              'line-color': LINE_COLOR,
              'line-width': LINE_WIDTH,
            },
          });
        }
      }
      // Fit to Nepal if we have features, with padding
      if (geojson.features.length > 0) {
        const bounds = new maplibregl.LngLatBounds();
        geojson.features.forEach((f) => {
          if (f.geometry && f.geometry.coordinates) {
            const coords = f.geometry.coordinates;
            if (f.geometry.type === 'Polygon' && coords[0]) {
              coords[0].forEach(([lng, lat]) => bounds.extend([lng, lat]));
            } else if (f.geometry.type === 'MultiPolygon') {
              coords.forEach((ring) => {
                if (ring[0]) ring[0].forEach(([lng, lat]) => bounds.extend([lng, lat]));
              });
            }
          }
        });
        if (!bounds.isEmpty()) {
          map.fitBounds(bounds, { padding: 40, maxZoom: 10, duration: 500 });
        } else {
          map.fitBounds(NEPAL_BOUNDS, { padding: 40, maxZoom: NEPAL_ZOOM, duration: 0 });
        }
      } else {
        map.fitBounds(NEPAL_BOUNDS, { padding: 40, maxZoom: NEPAL_ZOOM, duration: 0 });
      }
    } catch (err) {
      console.warn('GeoMap updateSource:', err);
    }
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center: NEPAL_CENTER,
      zoom: NEPAL_ZOOM,
      attributionControl: true,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.on('load', () => {
      const data = mapData && mapData.features && mapData.features.length > 0 ? mapData : null;
      if (data) updateSource(map, data);
    });

    map.on('click', FILL_LAYER_ID, (e) => {
      e.originalEvent.preventDefault();
      const feature = e.features?.[0];
      if (feature && feature.properties && onDrillDown) {
        const props = feature.properties;
        if (props.drilldown_to && props.drilldown_to !== 'null') {
          onDrillDown(props);
        }
      }
    });

    map.on('mouseenter', FILL_LAYER_ID, () => {
      map.getCanvas().style.cursor = 'pointer';
      map.setPaintProperty(FILL_LAYER_ID, 'fill-opacity', HOVER_FILL_OPACITY);
    });
    map.on('mouseleave', FILL_LAYER_ID, () => {
      map.getCanvas().style.cursor = '';
      map.setPaintProperty(FILL_LAYER_ID, 'fill-opacity', FILL_OPACITY);
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapData?.features?.length) return;
    const apply = () => updateSource(map, mapData);
    if (map.isStyleLoaded()) {
      apply();
    } else {
      map.once('idle', apply);
    }
  }, [mapData, updateSource]);

  if (!mapData || !mapData.features || mapData.features.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-[#1e3a5f]/5 rounded-xl border border-[#1e3a5f]/20">
        <div className="text-center text-[#1e3a5f]/70">
          <p className="text-lg font-medium">
            {language === 'en' ? 'Select a level to view the map' : 'नक्शा हेर्न स्तर छान्नुहोस्'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col rounded-xl overflow-hidden border border-[#1e3a5f]/20 shadow-lg">
      <div className="flex-none px-3 py-2 bg-gradient-to-r from-[#1e3a5f] to-[#0f172a] text-white text-sm font-medium">
        {currentLevel === 'province' && (language === 'en' ? 'Provinces' : 'प्रदेश')}
        {currentLevel === 'district' && (language === 'en' ? 'Districts' : 'जिल्ला')}
        {currentLevel === 'constituency' && (language === 'en' ? 'Election areas' : 'निर्वाचन क्षेत्र')}
        {' · '}
        {mapData.features.length} {language === 'en' ? 'areas' : 'क्षेत्र'}
      </div>
      <div ref={containerRef} className="flex-1 min-h-[280px] sm:min-h-[350px] lg:min-h-[400px]" />
    </div>
  );
};

export default GeoMap;
