import React, { useState } from 'react';
import { Sparkles, Utensils, Award, Heart, RefreshCw, Activity } from 'lucide-react';
import confetti from 'canvas-confetti';
import { Gremlin } from '../types';
import { useLanguage } from '../i18n/LanguageContext';
import { haptic } from '../lib/telegram';
import { GremlinAvatar } from './GremlinAvatar';

interface GremlinCompanionProps {
  gremlin: Gremlin;
  onFeed: () => void;
  onEvolve: () => void;
  onSimulateWalk: () => void;
}

export const GremlinCompanion: React.FC<GremlinCompanionProps> = ({
  gremlin,
  onFeed,
  onEvolve,
  onSimulateWalk,
}) => {
  const { t } = useLanguage();
  const [isInteracting, setIsInteracting] = useState(false);
  const xpPercent = Math.min(100, Math.round((gremlin.xp / gremlin.next_level_xp) * 100));

  const handlePet = () => {
    haptic('tap');
    setIsInteracting(true);
    confetti({
      particleCount: 25,
      spread: 60,
      origin: { y: 0.6 },
    });
    setTimeout(() => setIsInteracting(false), 800);
  };

  const getBiomeName = (biome: string) => {
    return (t.gremlin.biomes as any)[biome] || biome;
  };

  const getBiomeGlowColor = () => {
    switch (gremlin.biome_affinity) {
      case 'mountain_frost':
        return 'from-sky-950/60 via-slate-900/90 to-dark-950 border-sky-400/30 text-sky-300';
      case 'stormbringer':
        return 'from-purple-950/60 via-slate-900/90 to-dark-950 border-purple-400/30 text-purple-300';
      case 'forest_guardian':
        return 'from-emerald-950/60 via-slate-900/90 to-dark-950 border-emerald-400/30 text-emerald-300';
      case 'cyber_shadow':
        return 'from-fuchsia-950/60 via-slate-900/90 to-dark-950 border-fuchsia-400/30 text-fuchsia-300';
      default:
        return 'from-gremlin-green/20 via-slate-900/90 to-dark-950 border-gremlin-green/30 text-gremlin-green';
    }
  };

  const getRarityBadge = () => {
    switch (gremlin.rarity) {
      case 'Legendary':
        return 'bg-amber-500/20 border-amber-500/50 text-amber-300';
      case 'Epic':
        return 'bg-purple-500/20 border-purple-500/50 text-purple-300';
      case 'Rare':
        return 'bg-sky-500/20 border-sky-500/50 text-sky-300';
      default:
        return 'bg-slate-800 border-slate-700 text-slate-300';
    }
  };

  return (
    <div className="flex flex-col space-y-4 pb-6 pt-1">
      {/* Gremlin Companion Showcase Card */}
      <div
        className={`relative overflow-hidden rounded-3xl bg-gradient-to-b ${getBiomeGlowColor()} p-6 border shadow-2xl backdrop-blur-xl flex flex-col items-center text-center`}
      >
        {/* Biome Tag */}
        <div className="absolute top-4 left-4 flex items-center space-x-1.5 bg-dark-900/90 border border-dark-700/80 px-3 py-1 rounded-full text-[11px] font-semibold tracking-wide shadow-md">
          <Sparkles className="w-3.5 h-3.5 text-gremlin-frost" />
          <span>{getBiomeName(gremlin.biome_affinity)}</span>
        </div>

        {/* Rarity Tier */}
        <div className={`absolute top-4 right-4 border px-2.5 py-0.5 rounded-full text-[11px] font-bold shadow-md ${getRarityBadge()}`}>
          {gremlin.rarity}
        </div>

        {/* Dynamic Vector Gremlin Avatar */}
        <div
          onClick={handlePet}
          className="relative my-2 cursor-pointer transition-transform duration-200 active:scale-95"
          role="button"
          tabIndex={0}
          title={t.gremlin.tapToPet}
        >
          <GremlinAvatar gremlin={gremlin} isInteracting={isInteracting} size={190} />
        </div>

        {/* Creature Name & Level */}
        <h2 className="text-xl font-black tracking-tight text-white flex items-center space-x-2 mt-1">
          <span>{gremlin.name}</span>
          <span className="bg-dark-900/90 text-gremlin-green text-xs font-mono font-bold px-2 py-0.5 rounded-lg border border-gremlin-green/30">
            Lvl {gremlin.level}
          </span>
        </h2>
        <p className="text-xs text-slate-300 mt-1 flex items-center space-x-1">
          <span>✨</span>
          <span>{t.gremlin.tapToPet}</span>
        </p>

        {/* XP Progress Bar */}
        <div className="w-full mt-4">
          <div className="flex justify-between text-[11px] font-medium text-slate-300 mb-1.5">
            <span className="flex items-center space-x-1">
              <Activity className="w-3.5 h-3.5 text-gremlin-green" />
              <span>{t.gremlin.xpProgress}</span>
            </span>
            <span className="font-mono font-bold text-gremlin-frost">
              {gremlin.xp} / {gremlin.next_level_xp} XP ({xpPercent}%)
            </span>
          </div>
          <div className="w-full h-3 bg-dark-950/80 rounded-full overflow-hidden border border-dark-700/80 p-0.5 shadow-inner">
            <div
              className="h-full bg-gradient-to-r from-gremlin-green via-emerald-400 to-gremlin-frost transition-all duration-500 rounded-full shadow-lg shadow-gremlin-green/30"
              style={{ width: `${xpPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Vitals Grid */}
      <div className="grid grid-cols-3 gap-2.5">
        {/* Health */}
        <div className="bg-dark-800/90 border border-dark-700/80 p-3 rounded-2xl flex flex-col shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between text-xs text-rose-400 mb-1">
            <span className="font-semibold">{t.gremlin.health}</span>
            <Heart className="w-3.5 h-3.5 fill-rose-400" />
          </div>
          <span className="text-base font-bold font-mono text-slate-100">
            {gremlin.hp}/{gremlin.max_hp}
          </span>
          <div className="w-full h-1.5 bg-dark-950 rounded-full mt-1.5 overflow-hidden">
            <div
              className="h-full bg-rose-500 rounded-full transition-all duration-300"
              style={{ width: `${(gremlin.hp / gremlin.max_hp) * 100}%` }}
            />
          </div>
        </div>

        {/* Hunger */}
        <div className="bg-dark-800/90 border border-dark-700/80 p-3 rounded-2xl flex flex-col shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between text-xs text-amber-400 mb-1">
            <span className="font-semibold">{t.gremlin.hunger}</span>
            <Utensils className="w-3.5 h-3.5" />
          </div>
          <span className="text-base font-bold font-mono text-slate-100">{gremlin.hunger}%</span>
          <div className="w-full h-1.5 bg-dark-950 rounded-full mt-1.5 overflow-hidden">
            <div
              className="h-full bg-amber-500 rounded-full transition-all duration-300"
              style={{ width: `${gremlin.hunger}%` }}
            />
          </div>
        </div>

        {/* Mood */}
        <div className="bg-dark-800/90 border border-dark-700/80 p-3 rounded-2xl flex flex-col shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between text-xs text-sky-400 mb-1">
            <span className="font-semibold">{t.gremlin.mood}</span>
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          </div>
          <span className="text-base font-bold font-mono text-slate-100">{gremlin.mood}%</span>
          <div className="w-full h-1.5 bg-dark-950 rounded-full mt-1.5 overflow-hidden">
            <div
              className="h-full bg-sky-400 rounded-full transition-all duration-300"
              style={{ width: `${gremlin.mood}%` }}
            />
          </div>
        </div>
      </div>

      {/* Action Controls */}
      <div className="grid grid-cols-2 gap-3 pt-1">
        {/* Feed Button */}
        <button
          onClick={onFeed}
          className="flex items-center justify-center space-x-2 bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 border border-amber-500/40 text-amber-300 font-bold py-3.5 px-4 rounded-2xl shadow-lg transition active:scale-95 text-xs sm:text-sm"
        >
          <Utensils className="w-4 h-4" />
          <span>{t.gremlin.feedBtn}</span>
        </button>

        {/* Evolve Button */}
        <button
          onClick={onEvolve}
          disabled={gremlin.xp < gremlin.next_level_xp}
          className={`flex items-center justify-center space-x-2 font-bold py-3.5 px-4 rounded-2xl shadow-lg transition active:scale-95 text-xs sm:text-sm ${
            gremlin.xp >= gremlin.next_level_xp
              ? 'bg-gradient-to-r from-gremlin-green to-gremlin-frost text-dark-900 border border-white/40 shadow-gremlin-green/30 animate-pulse'
              : 'bg-dark-800/90 border border-dark-700 text-slate-500 cursor-not-allowed'
          }`}
        >
          <Award className="w-4 h-4" />
          <span>{t.gremlin.evolveBtn}</span>
        </button>
      </div>

      {/* Quick Trail Walk Simulation */}
      <div className="bg-dark-800/60 border border-dashed border-dark-700 p-3.5 rounded-2xl flex items-center justify-between shadow-md">
        <div>
          <span className="text-xs font-semibold text-slate-200 block">{t.gremlin.simulateWalkTitle}</span>
          <span className="text-[10px] text-slate-400">{t.gremlin.simulateWalkDesc}</span>
        </div>
        <button
          onClick={onSimulateWalk}
          className="flex items-center space-x-1.5 bg-dark-700 hover:bg-dark-600 text-gremlin-green text-xs font-bold px-3.5 py-2 rounded-xl border border-gremlin-green/30 transition active:scale-95 shadow-md"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>{t.gremlin.walkBtn}</span>
        </button>
      </div>
    </div>
  );
};
