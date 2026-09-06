import React, { useState, useEffect } from 'react';
import { Gremlin } from '../types';

interface GremlinAvatarProps {
  gremlin: Gremlin;
  isInteracting?: boolean;
  size?: number;
}

export const GremlinAvatar: React.FC<GremlinAvatarProps> = ({
  gremlin,
  isInteracting = false,
  size = 180,
}) => {
  const [blink, setBlink] = useState(false);

  // Periodic blinking effect
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlink(true);
      setTimeout(() => setBlink(false), 180);
    }, 3800 + Math.random() * 2000);

    return () => clearInterval(blinkInterval);
  }, []);

  const getBiomeColors = () => {
    switch (gremlin.biome_affinity) {
      case 'mountain_frost':
        return {
          bodyGrad1: '#38BDF8',
          bodyGrad2: '#0284C7',
          bellyGrad1: '#E0F2FE',
          bellyGrad2: '#BAE6FD',
          eyeColor: '#0EA5E9',
          pupilGlow: '#7DD3FC',
          hornColor: '#BAE6FD',
          hornHighlight: '#FFFFFF',
          wingColor: 'rgba(56, 189, 248, 0.45)',
          auraColor: '#38BDF8',
          particleSymbol: '❄️',
        };
      case 'stormbringer':
        return {
          bodyGrad1: '#A855F7',
          bodyGrad2: '#6366F1',
          bellyGrad1: '#F3E8FF',
          bellyGrad2: '#DDD6FE',
          eyeColor: '#8B5CF6',
          pupilGlow: '#C084FC',
          hornColor: '#DDD6FE',
          hornHighlight: '#FAF5FF',
          wingColor: 'rgba(168, 85, 247, 0.45)',
          auraColor: '#A855F7',
          particleSymbol: '⚡',
        };
      case 'forest_guardian':
        return {
          bodyGrad1: '#10B981',
          bodyGrad2: '#047857',
          bellyGrad1: '#ECFDF5',
          bellyGrad2: '#A7F3D0',
          eyeColor: '#059669',
          pupilGlow: '#6EE7B7',
          hornColor: '#A7F3D0',
          hornHighlight: '#D1FAE5',
          wingColor: 'rgba(168, 85, 247, 0.45)',
          auraColor: '#10B981',
          particleSymbol: '🍃',
        };
      case 'cyber_shadow':
        return {
          bodyGrad1: '#EC4899',
          bodyGrad2: '#8B5CF6',
          bellyGrad1: '#FDF2F8',
          bellyGrad2: '#FBCFE8',
          eyeColor: '#D946EF',
          pupilGlow: '#F472B6',
          hornColor: '#F5D0FE',
          hornHighlight: '#06B6D4',
          wingColor: 'rgba(236, 72, 153, 0.45)',
          auraColor: '#EC4899',
          particleSymbol: '✨',
        };
      default:
        return {
          bodyGrad1: '#10B981',
          bodyGrad2: '#059669',
          bellyGrad1: '#ECFDF5',
          bellyGrad2: '#A7F3D0',
          eyeColor: '#10B981',
          pupilGlow: '#34D399',
          hornColor: '#A7F3D0',
          hornHighlight: '#FFFFFF',
          wingColor: 'rgba(16, 185, 129, 0.4)',
          particleSymbol: '⭐',
        };
    }
  };

  const colors = getBiomeColors();
  const hasHorns = gremlin.visual_traits?.horns !== 'none' || gremlin.level >= 2;
  const hasWings = gremlin.visual_traits?.wings !== 'none' || gremlin.level >= 3;

  return (
    <div
      className="relative flex items-center justify-center select-none"
      style={{ width: size, height: size }}
    >
      {/* Background Radial Glow */}
      <div
        className="absolute inset-0 rounded-full blur-2xl opacity-60 animate-pulse-slow"
        style={{
          background: `radial-gradient(circle, ${colors.bodyGrad1} 0%, transparent 70%)`,
        }}
      />

      {/* Dynamic Animated Vector SVG */}
      <svg
        viewBox="0 0 200 200"
        className={`w-full h-full filter drop-shadow-2xl transition-transform duration-300 ${
          isInteracting ? 'scale-105 rotate-2' : ''
        }`}
      >
        <defs>
          <linearGradient id={`bodyGrad-${gremlin.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={colors.bodyGrad1} />
            <stop offset="100%" stopColor={colors.bodyGrad2} />
          </linearGradient>

          <linearGradient id={`bellyGrad-${gremlin.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={colors.bellyGrad1} />
            <stop offset="100%" stopColor={colors.bellyGrad2} />
          </linearGradient>

          <linearGradient id={`hornGrad-${gremlin.id}`} x1="0%" y1="100%" x2="50%" y2="0%">
            <stop offset="0%" stopColor={colors.hornColor} />
            <stop offset="100%" stopColor={colors.hornHighlight} />
          </linearGradient>

          <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Wings (Level 3+ or Visual Trait) */}
        {hasWings && (
          <g className="animate-pulse-slow" style={{ transformOrigin: '100px 105px' }}>
            {/* Left Wing */}
            <path
              d="M 60 100 C 20 70, 10 110, 45 130 C 52 120, 58 112, 65 108 Z"
              fill={colors.wingColor}
              stroke={colors.bodyGrad1}
              strokeWidth="2"
              strokeDasharray="3 2"
            />
            {/* Right Wing */}
            <path
              d="M 140 100 C 180 70, 190 110, 155 130 C 148 120, 142 112, 135 108 Z"
              fill={colors.wingColor}
              stroke={colors.bodyGrad1}
              strokeWidth="2"
              strokeDasharray="3 2"
            />
          </g>
        )}

        {/* Horns / Antlers (Level 2+ or Visual Trait) */}
        {hasHorns && (
          <g>
            {/* Left Horn */}
            <path
              d="M 68 62 C 55 35, 40 40, 48 20 C 58 35, 75 48, 78 60 Z"
              fill={`url(#hornGrad-${gremlin.id})`}
              stroke={colors.hornHighlight}
              strokeWidth="1.5"
            />
            {/* Right Horn */}
            <path
              d="M 132 62 C 145 35, 160 40, 152 20 C 142 35, 125 48, 122 60 Z"
              fill={`url(#hornGrad-${gremlin.id})`}
              stroke={colors.hornHighlight}
              strokeWidth="1.5"
            />
          </g>
        )}

        {/* Large Ears */}
        {/* Left Ear */}
        <path
          d="M 52 82 C 15 65, 25 105, 56 102 Z"
          fill={`url(#bodyGrad-${gremlin.id})`}
          stroke="rgba(255,255,255,0.2)"
          strokeWidth="1.5"
        />
        <path d="M 48 84 C 28 72, 35 98, 52 97 Z" fill={colors.bellyGrad2} opacity="0.6" />

        {/* Right Ear */}
        <path
          d="M 148 82 C 185 65, 175 105, 144 102 Z"
          fill={`url(#bodyGrad-${gremlin.id})`}
          stroke="rgba(255,255,255,0.2)"
          strokeWidth="1.5"
        />
        <path d="M 152 84 C 172 72, 165 98, 148 97 Z" fill={colors.bellyGrad2} opacity="0.6" />

        {/* Main Body (Cute round dumpling silhouette) */}
        <ellipse
          cx="100"
          cy="116"
          rx="56"
          ry="52"
          fill={`url(#bodyGrad-${gremlin.id})`}
          stroke="rgba(255,255,255,0.25)"
          strokeWidth="2"
        />

        {/* Soft Belly Patch */}
        <ellipse
          cx="100"
          cy="126"
          rx="36"
          ry="32"
          fill={`url(#bellyGrad-${gremlin.id})`}
          opacity="0.9"
        />

        {/* Cute Feet */}
        <ellipse cx="74" cy="164" rx="14" ry="9" fill={colors.bodyGrad2} />
        <ellipse cx="126" cy="164" rx="14" ry="9" fill={colors.bodyGrad2} />

        {/* Cute Tiny Paws */}
        <ellipse cx="64" cy="128" rx="8" ry="7" fill={colors.bodyGrad2} opacity="0.95" />
        <ellipse cx="136" cy="128" rx="8" ry="7" fill={colors.bodyGrad2} opacity="0.95" />

        {/* Cheeks Blush */}
        <ellipse cx="68" cy="112" rx="7" ry="4" fill="#F43F5E" opacity="0.45" />
        <ellipse cx="132" cy="112" rx="7" ry="4" fill="#F43F5E" opacity="0.45" />

        {/* Eyes & Emotion */}
        {blink || isInteracting ? (
          // Happy squint eyes (^_^)
          <g stroke="#0F172A" strokeWidth="3.5" strokeLinecap="round" fill="none">
            <path d="M 72 98 Q 80 90 88 98" />
            <path d="M 112 98 Q 120 90 128 98" />
          </g>
        ) : (
          // Big expressive glossy anime eyes
          <g>
            {/* Left Eye */}
            <ellipse cx="80" cy="96" rx="13" ry="15" fill="#0F172A" />
            <ellipse cx="80" cy="96" rx="10" ry="12" fill={colors.eyeColor} />
            <ellipse cx="80" cy="96" rx="6" ry="8" fill="#020617" />
            {/* Eye Highlights */}
            <circle cx="76" cy="91" r="4.5" fill="#FFFFFF" />
            <circle cx="84" cy="101" r="2" fill="#FFFFFF" />

            {/* Right Eye */}
            <ellipse cx="120" cy="96" rx="13" ry="15" fill="#0F172A" />
            <ellipse cx="120" cy="96" rx="10" ry="12" fill={colors.eyeColor} />
            <ellipse cx="120" cy="96" rx="6" ry="8" fill="#020617" />
            {/* Eye Highlights */}
            <circle cx="116" cy="91" r="4.5" fill="#FFFFFF" />
            <circle cx="124" cy="101" r="2" fill="#FFFFFF" />
          </g>
        )}

        {/* Cute Snout & Smile */}
        <ellipse cx="100" cy="106" rx="4.5" ry="3" fill="#0F172A" />
        <path
          d={isInteracting ? 'M 93 112 Q 100 122 107 112' : 'M 95 111 Q 100 116 105 111'}
          stroke="#0F172A"
          strokeWidth="2.5"
          strokeLinecap="round"
          fill={isInteracting ? '#F43F5E' : 'none'}
        />

        {/* Biome Crystal Forehead Sigil */}
        <polygon
          points="100,72 105,79 100,86 95,79"
          fill={colors.hornHighlight}
          stroke={colors.bodyGrad1}
          strokeWidth="1"
          filter="url(#softGlow)"
        />
      </svg>

      {/* Floating Biome Symbols */}
      <span className="absolute top-2 right-4 text-xs animate-bounce opacity-80 select-none">
        {colors.particleSymbol}
      </span>
    </div>
  );
};
