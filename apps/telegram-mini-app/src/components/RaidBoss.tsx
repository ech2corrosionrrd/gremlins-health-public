import React, { useState } from 'react';
import { ShieldAlert, Swords, Gift, Timer, Flame } from 'lucide-react';
import { ClanRaidBoss, BrandQuest } from '../types';
import { useLanguage } from '../i18n/LanguageContext';
import { haptic } from '../lib/telegram';

interface RaidBossProps {
  boss: ClanRaidBoss;
  quests: BrandQuest[];
  onContributeSteps: () => void;
}

export const RaidBoss: React.FC<RaidBossProps> = ({ boss, quests, onContributeSteps }) => {
  const { t } = useLanguage();
  const [isAttacking, setIsAttacking] = useState(false);
  const hpPercent = Math.max(
    0,
    Math.round((boss.current_health_steps / boss.total_health_steps) * 100)
  );

  const handleAttack = () => {
    haptic('heavy');
    setIsAttacking(true);
    onContributeSteps();
    setTimeout(() => setIsAttacking(false), 600);
  };

  return (
    <div className="flex flex-col space-y-4 pb-6 pt-1">
      {/* Clan Raid Boss Card */}
      <div
        className={`relative overflow-hidden rounded-3xl bg-gradient-to-b from-rose-950/50 via-dark-900 to-dark-950 border border-rose-500/40 p-5 shadow-2xl flex flex-col space-y-3.5 backdrop-blur-xl transition-all duration-300 ${
          isAttacking ? 'scale-[0.98] border-rose-400' : ''
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-rose-400 font-bold text-xs uppercase tracking-wider">
            <ShieldAlert className="w-5 h-5 animate-pulse" />
            <span>{t.raid.activeBoss}</span>
          </div>
          <div className="flex items-center space-x-1 bg-dark-900/90 border border-dark-700/80 px-2.5 py-1 rounded-full text-[10px] font-mono text-slate-300 shadow-sm">
            <Timer className="w-3.5 h-3.5 text-amber-400" />
            <span>{t.raid.endsIn}</span>
          </div>
        </div>

        <div className="flex items-center space-x-4 my-1">
          <div
            className={`w-18 h-18 rounded-2xl bg-dark-900 border-2 border-rose-500/50 flex items-center justify-center text-4xl shadow-2xl shadow-rose-900/50 shrink-0 select-none transition-transform duration-300 ${
              isAttacking ? 'scale-110 rotate-6' : 'animate-pulse-slow'
            }`}
          >
            🌋
          </div>
          <div>
            <h3 className="font-black text-lg text-slate-100">{boss.boss_name}</h3>
            <span className="text-xs text-rose-300/80 flex items-center space-x-1 mt-0.5">
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              <span>{t.raid.worldTitan}</span>
            </span>
          </div>
        </div>

        {/* Boss Health Bar */}
        <div className="w-full flex flex-col space-y-1.5">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400">{t.raid.remainingHp}:</span>
            <span className="font-bold text-rose-400">
              {boss.current_health_steps.toLocaleString()} / {boss.total_health_steps.toLocaleString()} Steps
            </span>
          </div>
          <div className="w-full h-3.5 bg-dark-950 rounded-full overflow-hidden border border-rose-950/80 p-0.5 shadow-inner">
            <div
              className="h-full bg-gradient-to-r from-rose-600 via-amber-500 to-rose-500 rounded-full transition-all duration-500 shadow-lg shadow-rose-500/30"
              style={{ width: `${hpPercent}%` }}
            />
          </div>
        </div>

        {/* Clan Action */}
        <div className="flex items-center justify-between pt-2 border-t border-dark-700/80">
          <div>
            <span className="text-[10px] text-slate-400 block">{t.raid.totalPrizePool}</span>
            <span className="text-sm font-black font-mono text-gremlin-gold">
              {boss.reward_grln_pool.toLocaleString()} $GRLN
            </span>
          </div>
          <button
            onClick={handleAttack}
            className="flex items-center space-x-2 bg-gradient-to-r from-rose-500 to-amber-500 hover:from-rose-400 hover:to-amber-400 text-dark-950 font-bold px-4 py-2.5 rounded-xl text-xs transition active:scale-95 shadow-xl shadow-rose-500/25"
          >
            <Swords className="w-4 h-4 stroke-[2.5]" />
            <span>{t.raid.attackBtn}</span>
          </button>
        </div>
      </div>

      {/* Brand Sponsored Quests Section */}
      <div className="flex flex-col space-y-2.5">
        <h4 className="font-bold text-xs uppercase tracking-wider text-slate-400 px-1 flex items-center space-x-1.5">
          <Gift className="w-3.5 h-3.5 text-gremlin-green" />
          <span>{t.raid.sponsorQuests}</span>
        </h4>

        {quests.map((q) => (
          <div
            key={q.id}
            className="bg-dark-800/90 border border-dark-700/80 p-3.5 rounded-2xl flex flex-col space-y-2 shadow-lg backdrop-blur-md"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-100 flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-gremlin-green animate-pulse" />
                <span>{q.sponsor_brand}</span>
              </span>
              <span className="text-[10px] font-mono font-bold text-gremlin-gold bg-gremlin-gold/10 px-2 py-0.5 rounded-full border border-gremlin-gold/30">
                +${q.reward_pool_usdc} USDC Pool
              </span>
            </div>

            <h5 className="font-bold text-xs text-slate-200">{q.title}</h5>
            <p className="text-[11px] text-slate-400">{q.description}</p>

            <div className="flex items-center justify-between pt-2 border-t border-dark-700/80 text-[11px] text-slate-400 font-mono">
              <span>
                {t.raid.goal}: {q.required_steps.toLocaleString()} ({q.required_elevation_gain_m}m)
              </span>
              <span className="text-gremlin-green font-bold">
                {q.current_claimants} / {q.max_claimants} {t.raid.claimed}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
