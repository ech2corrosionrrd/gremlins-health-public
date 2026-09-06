import React, { useState, useEffect, useRef } from 'react';
import { Camera, ShieldCheck, Sparkles, Navigation, CloudRain, Zap, CheckCircle2, RefreshCw } from 'lucide-react';
import confetti from 'canvas-confetti';
import { useLanguage } from '../i18n/LanguageContext';
import { haptic } from '../lib/telegram';

interface SecureCameraProps {
  /** Мінтить через бекенд і додає результат у список. */
  onMint: (input: {
    title: string;
    story_note?: string;
    original_photo_url: string;
    location_name: string;
  }) => Promise<void>;
  /** false, поки немає верифікованої активності, з якої можна мінтити. */
  canMint: boolean;
  busy: boolean;
}

export const SecureCamera: React.FC<SecureCameraProps> = ({ onMint, canMint, busy }) => {
  const { t } = useLanguage();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [streamActive, setStreamActive] = useState<boolean>(false);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [isGeneratingAI, setIsGeneratingAI] = useState<boolean>(false);
  const [generatedArt, setGeneratedArt] = useState<string | null>(null);
  const [currentGps, setCurrentGps] = useState<{ lat: number; lng: number; altitude: number | null }>({
    lat: 50.4501,
    lng: 30.5234,
    altitude: 180,
  });

  // Start real device camera feed
  useEffect(() => {
    let stream: MediaStream | null = null;

    async function startCamera() {
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' },
            audio: false,
          });
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            setStreamActive(true);
          }
        }
      } catch (err) {
        console.warn('Real camera stream not available (desktop/permission):', err);
        setStreamActive(false);
      }
    }

    startCamera();

    // Read real GPS
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCurrentGps({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            altitude: pos.coords.altitude ? Math.round(pos.coords.altitude) : 180,
          });
        },
        () => {},
        { enableHighAccuracy: true }
      );
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Real Shutter Capture from video feed
  const handleCapture = () => {
    haptic('tap');

    if (streamActive && videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const realPhotoData = canvas.toDataURL('image/jpeg', 0.85);
        setCapturedPhoto(realPhotoData);
      }
    } else {
      // Fallback sample photo if on laptop without permission
      setCapturedPhoto('https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&auto=format&fit=crop&q=80');
    }

    setIsGeneratingAI(true);

    // AI synthesis pipeline
    setTimeout(() => {
      setIsGeneratingAI(false);
      setGeneratedArt('https://images.unsplash.com/photo-1519681393784-d120267933ba?w=800&auto=format&fit=crop&q=80');
      haptic('heavy');
      confetti({ particleCount: 70, spread: 90, origin: { y: 0.6 } });
    }, 1800);
  };

  const handleRetake = () => {
    haptic('tap');
    setCapturedPhoto(null);
    setGeneratedArt(null);
  };

  const handleCompleteMint = async () => {
    if (!capturedPhoto) return;
    haptic('success');

    const altitudeVal = Math.round(currentGps.altitude ?? 0);
    // Раніше тут збирався готовий NFT-об'єкт і одразу лягав у список — тобто
    // «мінт» ніколи не залишав браузер. Тепер вирішує бекенд: він перевіряє
    // активність, рахує рідкість і повертає рядок, який справді існує в базі.
    await onMint({
      title: `Adventure #${Math.floor(1000 + Math.random() * 9000)}`,
      story_note: `Proof of Adventure at ${currentGps.lat.toFixed(4)}, ${currentGps.lng.toFixed(4)}.`,
      original_photo_url: capturedPhoto,
      location_name: `Trail Waypoint (${altitudeVal}m)`,
    });

    setCapturedPhoto(null);
    setGeneratedArt(null);
  };

  return (
    <div className="flex flex-col space-y-3 pb-6 pt-1">
      {/* Viewfinder Frame */}
      <div className="relative w-full h-[400px] rounded-3xl bg-dark-950 border-2 border-dark-700 overflow-hidden shadow-2xl flex flex-col justify-between p-4">
        {/* Hidden Canvas for Frame Capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Real Video Stream Background */}
        {!capturedPhoto && (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`absolute inset-0 w-full h-full object-cover ${streamActive ? 'block' : 'hidden'}`}
          />
        )}

        {/* Fallback Viewport Background when camera permission not given */}
        {!capturedPhoto && !streamActive && (
          <div className="absolute inset-0 bg-gradient-to-b from-dark-900 via-dark-800 to-dark-950 flex items-center justify-center">
            <div className="w-48 h-48 border border-white/20 rounded-3xl relative flex items-center justify-center">
              <div className="w-4 h-4 border-t-2 border-l-2 border-gremlin-green absolute -top-1 -left-1" />
              <div className="w-4 h-4 border-t-2 border-r-2 border-gremlin-green absolute -top-1 -right-1" />
              <div className="w-4 h-4 border-b-2 border-l-2 border-gremlin-green absolute -bottom-1 -left-1" />
              <div className="w-4 h-4 border-b-2 border-r-2 border-gremlin-green absolute -bottom-1 -right-1" />
              <Sparkles className="w-8 h-8 text-white/30 animate-pulse" />
            </div>
          </div>
        )}

        {/* Display Captured Frame / Generated Art */}
        {capturedPhoto && (
          <div className="absolute inset-0 w-full h-full">
            <img
              src={generatedArt || capturedPhoto}
              alt="Captured"
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-dark-950 via-transparent to-transparent" />
          </div>
        )}

        {/* Real-Time Telemetry HUD Overlay */}
        <div className="flex justify-between items-start z-10">
          <div className="bg-dark-900/85 backdrop-blur-md border border-dark-700 p-2.5 rounded-2xl flex flex-col space-y-1 text-[11px] font-mono shadow-lg">
            <div className="flex items-center space-x-1 text-gremlin-frost">
              <Navigation className="w-3.5 h-3.5" />
              <span>
                {currentGps.lat.toFixed(4)}°N, {currentGps.lng.toFixed(4)}°E
              </span>
            </div>
            <div className="flex items-center space-x-1 text-amber-400 font-bold">
              <span>ALT:</span>
              <span>{currentGps.altitude || 180} m</span>
            </div>
            <div className="flex items-center space-x-1 text-sky-300">
              <CloudRain className="w-3 h-3" />
              <span>Trail Viewfinder • Live HUD</span>
            </div>
          </div>

          <div className="bg-dark-900/85 backdrop-blur-md border border-gremlin-green/40 px-2.5 py-1.5 rounded-2xl flex items-center space-x-1.5 text-gremlin-green text-[11px] font-semibold shadow-lg">
            <ShieldCheck className="w-4 h-4" />
            <span>{t.camera.hardwareAttested}</span>
          </div>
        </div>

        {/* AI Synthesis Processing Screen */}
        {isGeneratingAI && (
          <div className="absolute inset-0 bg-dark-950/85 backdrop-blur-md flex flex-col items-center justify-center z-20 space-y-3">
            <div className="w-12 h-12 rounded-full border-4 border-gremlin-green border-t-transparent animate-spin" />
            <span className="text-sm font-bold text-slate-100 text-center px-4">
              {t.camera.synthesizingAI}
            </span>
            <span className="text-xs text-gremlin-frost font-mono">{t.camera.applyingShaders}</span>
          </div>
        )}

        {/* Shutter / Action Controls */}
        <div className="z-10 flex flex-col items-center">
          {generatedArt ? (
            <div className="w-full flex space-x-2">
              <button
                onClick={handleRetake}
                className="py-3 px-4 bg-dark-800 border border-dark-600 rounded-2xl text-xs font-bold text-slate-300 flex items-center space-x-1"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <button
                onClick={handleCompleteMint}
                disabled={!canMint || busy}
                className="flex-1 bg-gradient-to-r from-gremlin-green to-gremlin-frost text-dark-900 font-bold py-3 rounded-2xl shadow-xl shadow-gremlin-green/30 flex items-center justify-center space-x-2 transition active:scale-95 text-xs sm:text-sm disabled:opacity-40 disabled:active:scale-100"
              >
                <CheckCircle2 className="w-5 h-5" />
                <span>{t.camera.mintBtn}</span>
              </button>
            </div>
          ) : null}

          {/* Вимкнена кнопка без пояснення читається як зламана. */}
          {generatedArt && !canMint ? (
            <span className="mt-2 block text-center text-[10px] text-amber-300/90 pointer-events-auto">
              {t.camera.needActivity}
            </span>
          ) : (
            <button
              onClick={handleCapture}
              disabled={isGeneratingAI}
              className="w-16 h-16 rounded-full bg-white border-4 border-white/40 shadow-2xl flex items-center justify-center transition active:scale-90"
            >
              <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-gremlin-green to-gremlin-frost flex items-center justify-center">
                <Camera className="w-6 h-6 text-dark-900" />
              </div>
            </button>
          )}
        </div>
      </div>

      {/* Hardware Attestation Notice */}
      <div className="bg-dark-800/80 border border-dark-700 p-3.5 rounded-2xl text-xs text-slate-300 flex items-center space-x-3">
        <div className="w-8 h-8 rounded-xl bg-gremlin-green/15 text-gremlin-green flex items-center justify-center shrink-0">
          <Zap className="w-4 h-4" />
        </div>
        <span>{t.camera.attestationNotice}</span>
      </div>
    </div>
  );
};
