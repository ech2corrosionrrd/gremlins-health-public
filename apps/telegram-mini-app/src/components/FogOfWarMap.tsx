import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Compass, Crosshair, Navigation, Sparkles, MapPin, Layers, Footprints, Mountain } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';
import { haptic } from '../lib/telegram';

interface Waypoint {
  id: string;
  name: string;
  lat: number;
  lng: number;
  elevation: number;
  type: 'summit' | 'trailhead' | 'viewpoint' | 'cache';
  reward: string;
  cleared: boolean;
}

// Haversine distance in km
function calculateDistanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

// Generate dynamic local exploration waypoints around user's real GPS coordinates
function generateLocalWaypoints(centerLat: number, centerLng: number, baseElevation: number): Waypoint[] {
  return [
    {
      id: 'wp-1',
      name: 'Nearby Summit Vista',
      lat: centerLat + 0.0082,
      lng: centerLng + 0.0065,
      elevation: Math.round(baseElevation + 180),
      type: 'summit',
      reward: '50 XP & Frost Rune',
      cleared: true,
    },
    {
      id: 'wp-2',
      name: 'Forest Greenway Trailhead',
      lat: centerLat - 0.0065,
      lng: centerLng + 0.0092,
      elevation: Math.round(baseElevation + 45),
      type: 'trailhead',
      reward: '30 Stamina Bonus',
      cleared: true,
    },
    {
      id: 'wp-3',
      name: 'Ridge Viewpoint',
      lat: centerLat + 0.0125,
      lng: centerLng - 0.0084,
      elevation: Math.round(baseElevation + 240),
      type: 'viewpoint',
      reward: 'cNFT Discovery Drop',
      cleared: false,
    },
    {
      id: 'wp-4',
      name: 'Highland Landmark Cache',
      lat: centerLat - 0.011,
      lng: centerLng - 0.0075,
      elevation: Math.round(baseElevation + 95),
      type: 'cache',
      reward: '75 $GRLN Bounty',
      cleared: false,
    },
    {
      id: 'wp-5',
      name: 'Pioneer Trail Crossroad',
      lat: centerLat + 0.004,
      lng: centerLng - 0.0135,
      elevation: Math.round(baseElevation + 130),
      type: 'viewpoint',
      reward: 'Rare Biome Shard',
      cleared: false,
    },
  ];
}

// Generate H3-style hexagonal polygon vertices around a center point
function createHexagonCoords(centerLat: number, centerLng: number, radiusKm = 0.35): [number, number][] {
  const coords: [number, number][] = [];
  const latOffset = (radiusKm / 111.32);
  const lngOffset = (radiusKm / (111.32 * Math.cos((centerLat * Math.PI) / 180)));

  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i;
    const pLat = centerLat + latOffset * Math.sin(angle);
    const pLng = centerLng + lngOffset * Math.cos(angle);
    coords.push([pLat, pLng]);
  }
  return coords;
}

export const FogOfWarMap: React.FC = () => {
  const { t } = useLanguage();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const userMarkerRef = useRef<L.Marker | null>(null);
  const userAccuracyCircleRef = useRef<L.Circle | null>(null);
  const userPathLineRef = useRef<L.Polyline | null>(null);
  const waypointsGroupRef = useRef<L.LayerGroup | null>(null);
  const fogGridGroupRef = useRef<L.LayerGroup | null>(null);

  const [userLocation, setUserLocation] = useState<{
    lat: number;
    lng: number;
    accuracy: number;
    altitude: number;
    speed: number | null;
  } | null>(null);

  const [gpsActive, setGpsActive] = useState<boolean>(false);
  const [waypoints, setWaypoints] = useState<Waypoint[]>([]);
  const [selectedWaypoint, setSelectedWaypoint] = useState<Waypoint | null>(null);
  const [fogClearedPercent, setFogClearedPercent] = useState<number>(38);
  const [trackedPath, setTrackedPath] = useState<[number, number][]>([]);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Default global view (Europe/Global) until user's real GPS resolves
    const map = L.map(mapContainerRef.current, {
      center: [50.4501, 30.5234], // Kyiv / Central Europe neutral center
      zoom: 13,
      zoomControl: false,
      attributionControl: false,
    });

    // Dark Matter CartoDB Basemap
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map);

    waypointsGroupRef.current = L.layerGroup().addTo(map);
    fogGridGroupRef.current = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Live Geolocation Tracking anywhere in the world
  useEffect(() => {
    if (!navigator.geolocation) return;

    let hasCenteredInitial = false;

    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude, accuracy, altitude, speed } = pos.coords;
        const currentAltitude = altitude ? Math.round(altitude) : 180;
        const currentSpeed = speed ? Math.round(speed * 3.6) : 0; // km/h

        setUserLocation({
          lat: latitude,
          lng: longitude,
          accuracy,
          altitude: currentAltitude,
          speed: currentSpeed,
        });
        setGpsActive(true);

        const map = mapInstanceRef.current;
        if (!map) return;

        // On first real GPS fix, smoothly fly to user's real location anywhere on Earth
        if (!hasCenteredInitial) {
          hasCenteredInitial = true;
          map.flyTo([latitude, longitude], 15, { duration: 1.2 });

          // Generate dynamic local exploration waypoints around the user's real coordinates
          const localWps = generateLocalWaypoints(latitude, longitude, currentAltitude);
          setWaypoints(localWps);
          setSelectedWaypoint(localWps[0]);

          // Render Dynamic Hexagonal Fog of War Grid around user's location
          if (fogGridGroupRef.current) {
            fogGridGroupRef.current.clearLayers();

            // Create a 7-hex cluster around user
            const offsets = [
              [0, 0, true], // center - cleared
              [0.005, 0.005, true],
              [-0.005, 0.005, true],
              [0.005, -0.005, false],
              [-0.005, -0.005, false],
              [0.009, 0, false],
              [-0.009, 0, false],
            ];

            offsets.forEach(([dLat, dLng, isCleared]) => {
              const hexCoords = createHexagonCoords(latitude + (dLat as number), longitude + (dLng as number), 0.4);
              const hexPolygon = L.polygon(hexCoords, {
                color: isCleared ? '#10B981' : '#334155',
                weight: 1.5,
                fillColor: isCleared ? '#10B981' : '#0F172A',
                fillOpacity: isCleared ? 0.12 : 0.65,
                dashArray: isCleared ? undefined : '4, 4',
              });
              hexPolygon.addTo(fogGridGroupRef.current!);
            });
          }
        }

        // Update User Path
        setTrackedPath((prev) => {
          const next = [...prev, [latitude, longitude] as [number, number]];
          if (userPathLineRef.current) {
            userPathLineRef.current.setLatLngs(next);
          } else if (map) {
            userPathLineRef.current = L.polyline(next, {
              color: '#38BDF8',
              weight: 3.5,
              opacity: 0.9,
            }).addTo(map);
          }
          return next;
        });

        // User GPS Dot Marker
        const userIcon = L.divIcon({
          className: 'user-gps-dot',
          html: `
            <div style="
              width: 20px;
              height: 20px;
              background: #38BDF8;
              border: 3px solid #FFFFFF;
              border-radius: 50%;
              box-shadow: 0 0 16px #38BDF8;
              display: flex;
              align-items: center;
              justify-content: center;
            ">
              <div style="width: 6px; height: 6px; background: #FFFFFF; border-radius: 50%;"></div>
            </div>
          `,
          iconSize: [20, 20],
          iconAnchor: [10, 10],
        });

        if (userMarkerRef.current) {
          userMarkerRef.current.setLatLng([latitude, longitude]);
        } else {
          userMarkerRef.current = L.marker([latitude, longitude], { icon: userIcon }).addTo(map);
        }

        if (userAccuracyCircleRef.current) {
          userAccuracyCircleRef.current.setLatLng([latitude, longitude]);
          userAccuracyCircleRef.current.setRadius(accuracy);
        } else {
          userAccuracyCircleRef.current = L.circle([latitude, longitude], {
            radius: Math.max(accuracy, 25),
            color: '#38BDF8',
            fillColor: '#38BDF8',
            fillOpacity: 0.1,
            weight: 1,
          }).addTo(map);
        }
      },
      (err) => {
        console.warn('Geolocation notice:', err.message);
        setGpsActive(false);
      },
      {
        enableHighAccuracy: true,
        maximumAge: 3000,
        timeout: 10000,
      }
    );

    return () => {
      navigator.geolocation.clearWatch(watchId);
    };
  }, []);

  // Update Waypoint Markers on the Map
  useEffect(() => {
    const map = mapInstanceRef.current;
    const group = waypointsGroupRef.current;
    if (!map || !group || waypoints.length === 0) return;

    group.clearLayers();

    waypoints.forEach((wp) => {
      const isCleared = wp.cleared;
      const borderColor = isCleared ? '#10B981' : '#64748B';
      const bgColor = isCleared ? '#064E3B' : '#1E293B';
      const iconEmoji = wp.type === 'summit' ? '🏔️' : wp.type === 'trailhead' ? '🌲' : wp.type === 'cache' ? '💎' : '📍';

      const customIcon = L.divIcon({
        className: 'custom-wp-marker',
        html: `
          <div style="
            width: 32px;
            height: 32px;
            background: ${bgColor};
            border: 2px solid ${borderColor};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.6);
            cursor: pointer;
          ">
            ${iconEmoji}
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const marker = L.marker([wp.lat, wp.lng], { icon: customIcon }).addTo(group);
      marker.on('click', () => {
        haptic('tap');
        setSelectedWaypoint(wp);
        map.flyTo([wp.lat, wp.lng], 15, { duration: 0.8 });
      });
    });
  }, [waypoints]);

  const handleCenterOnUser = () => {
    haptic('selection');
    if (!userLocation || !mapInstanceRef.current) {
      alert('Locating GPS position. Please ensure location permissions are enabled in your browser/device.');
      return;
    }
    mapInstanceRef.current.flyTo([userLocation.lat, userLocation.lng], 16, { duration: 1.0 });
  };

  const handleSelectWaypoint = (wp: Waypoint) => {
    haptic('tap');
    setSelectedWaypoint(wp);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([wp.lat, wp.lng], 15, { duration: 0.8 });
    }
  };

  const handleZoom = (delta: number) => {
    haptic('tap');
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setZoom(mapInstanceRef.current.getZoom() + delta);
    }
  };

  const distanceToSelected =
    userLocation && selectedWaypoint
      ? calculateDistanceKm(userLocation.lat, userLocation.lng, selectedWaypoint.lat, selectedWaypoint.lng)
      : null;

  return (
    <div className="flex flex-col space-y-3 pb-6 pt-1">
      {/* Real-time Global Map Header HUD */}
      <div className="flex items-center justify-between bg-dark-800/90 border border-dark-700/80 p-3.5 rounded-2xl backdrop-blur-md shadow-xl">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-gremlin-green/15 text-gremlin-green flex items-center justify-center">
            <Compass className="w-4 h-4 animate-spin-slow" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-100 flex items-center space-x-1.5">
              <span>{t.map.title}</span>
              <span className={`w-2 h-2 rounded-full ${gpsActive ? 'bg-gremlin-green animate-pulse' : 'bg-amber-400'}`} />
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              {gpsActive ? 'Global GPS Active (H3 Res 9)' : 'Searching for device GPS...'}
            </span>
          </div>
        </div>

        <div className="text-right">
          <span className="text-[10px] text-slate-400 font-medium block">{t.map.fogCleared}</span>
          <span className="text-xs font-black font-mono text-gremlin-green">{fogClearedPercent}%</span>
        </div>
      </div>

      {/* Real Leaflet Map Container */}
      <div className="relative w-full h-[380px] rounded-3xl overflow-hidden border-2 border-dark-700 shadow-2xl">
        <div ref={mapContainerRef} className="w-full h-full" />

        {/* Floating Map Controls */}
        <div className="absolute top-3 right-3 z-20 flex flex-col space-y-2">
          {/* Recenter GPS */}
          <button
            onClick={handleCenterOnUser}
            className="w-10 h-10 rounded-2xl bg-dark-900/95 border border-dark-600 text-sky-400 hover:text-white flex items-center justify-center shadow-2xl backdrop-blur-md active:scale-95 transition"
            title="Center on My GPS Location"
          >
            <Crosshair className="w-5 h-5" />
          </button>

          {/* Zoom In */}
          <button
            onClick={() => handleZoom(1)}
            className="w-10 h-10 rounded-2xl bg-dark-900/95 border border-dark-600 text-slate-300 hover:text-white flex items-center justify-center shadow-2xl backdrop-blur-md active:scale-95 transition font-mono font-bold text-base"
          >
            +
          </button>

          {/* Zoom Out */}
          <button
            onClick={() => handleZoom(-1)}
            className="w-10 h-10 rounded-2xl bg-dark-900/95 border border-dark-600 text-slate-300 hover:text-white flex items-center justify-center shadow-2xl backdrop-blur-md active:scale-95 transition font-mono font-bold text-base"
          >
            -
          </button>
        </div>

        {/* Live GPS Coordinates & Altitude HUD Banner */}
        <div className="absolute bottom-3 left-3 right-3 z-20 bg-dark-900/95 backdrop-blur-md border border-dark-700 px-3.5 py-2 rounded-2xl text-[11px] flex items-center justify-between font-mono shadow-xl">
          <div className="flex items-center space-x-2 truncate">
            <Navigation className="w-3.5 h-3.5 text-gremlin-green rotate-45 shrink-0" />
            <span className="text-slate-200 truncate">
              {userLocation
                ? `${userLocation.lat.toFixed(4)}°, ${userLocation.lng.toFixed(4)}° (±${Math.round(userLocation.accuracy)}m)`
                : 'Acquiring GPS fix...'}
            </span>
          </div>
          {userLocation && (
            <span className="text-amber-400 font-bold shrink-0 ml-2">
              ALT: {userLocation.altitude}m
            </span>
          )}
        </div>
      </div>

      {/* Selected Waypoint / Landmark Info Card */}
      {selectedWaypoint && (
        <div className="bg-dark-800/90 border border-dark-700/80 p-4 rounded-2xl flex flex-col space-y-2 shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-xl bg-sky-500/15 text-sky-400 flex items-center justify-center text-base">
                {selectedWaypoint.type === 'summit' ? '🏔️' : selectedWaypoint.type === 'trailhead' ? '🌲' : '💎'}
              </div>
              <div>
                <h4 className="font-bold text-xs text-slate-100">{selectedWaypoint.name}</h4>
                <span className="text-[10px] text-slate-400 font-mono">
                  Elevation: {selectedWaypoint.elevation}m • {selectedWaypoint.type.toUpperCase()}
                </span>
              </div>
            </div>
            <span
              className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                selectedWaypoint.cleared
                  ? 'bg-gremlin-green/15 border-gremlin-green/40 text-gremlin-green'
                  : 'bg-slate-800 border-slate-700 text-slate-400'
              }`}
            >
              {selectedWaypoint.cleared ? 'Unlocked' : 'In Fog'}
            </span>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-dark-700/80 text-xs text-slate-300">
            <span>
              Bounty: <b className="text-amber-400">{selectedWaypoint.reward}</b>
            </span>
            <span className="text-gremlin-frost font-mono font-bold">
              {distanceToSelected !== null ? `${distanceToSelected.toFixed(2)} km away` : 'Calculating...'}
            </span>
          </div>
        </div>
      )}

      {/* Waypoint Selector Carousel */}
      {waypoints.length > 0 && (
        <div className="flex space-x-2 overflow-x-auto pb-1 scrollbar-none">
          {waypoints.map((wp) => (
            <button
              key={wp.id}
              onClick={() => handleSelectWaypoint(wp)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition active:scale-95 border flex items-center space-x-1.5 shadow-sm ${
                selectedWaypoint?.id === wp.id
                  ? 'bg-gremlin-green/20 border-gremlin-green text-gremlin-green shadow-gremlin-green/10'
                  : 'bg-dark-800/80 border-dark-700 text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>{wp.type === 'summit' ? '🏔️' : wp.type === 'trailhead' ? '🌲' : '📍'}</span>
              <span>{wp.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
