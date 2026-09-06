import React from 'react';
import { UserProfile } from '../types';
import { ShieldCheck, Snowflake, Wallet, Lock, Globe, Share2 } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';
import { haptic } from '../lib/telegram';

interface ProfileProps {
  user: UserProfile;
  onUseStreakFreeze: () => void;
  onShare: () => void;
  onConnectWallet: () => void;
}

export const Profile: React.FC<ProfileProps> = ({
  user,
  onUseStreakFreeze,
  onShare,
  onConnectWallet,
}) => {
  const { t, language, setLanguage, availableLanguages } = useLanguage();

  const handleFreeze = () => {
    haptic('success');
    onUseStreakFreeze();
  };

  const handleShare = () => {
    haptic('tap');
    onShare();
  };

  const handleLangChange = (code: any) => {
    haptic('selection');
    setLanguage(code);
  };

  return (
    <div className="flex flex-col space-y-4 pb-6 pt-1">
      {/* Profile Header Card */}
      <div className="bg-gradient-to-b from-dark-800 to-dark-900 border border-dark-700/80 p-5 rounded-3xl shadow-xl flex items-center space-x-4 backdrop-blur-md">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-gremlin-green to-gremlin-frost flex items-center justify-center text-2xl font-black text-dark-900 shadow-lg shadow-gremlin-green/30 shrink-0">
          🌲
        </div>
        <div>
          <div className="flex items-center space-x-1.5">
            <h3 className="font-black text-base text-slate-100">{user.username}</h3>
            {user.is_device_verified && (
              <span title={t.camera.hardwareAttested}>
                <ShieldCheck className="w-4 h-4 text-gremlin-green" />
              </span>
            )}
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {t.profile.telegramId}: #{user.telegram_id}
          </span>
          <div className="flex items-center space-x-2 mt-1">
            <span className="bg-gremlin-green/15 text-gremlin-green border border-gremlin-green/30 text-[10px] font-bold px-2 py-0.5 rounded-md">
              {t.reputation}: {user.reputation_score}%
            </span>
          </div>
        </div>
      </div>

      {/* Share Achievement */}
      <button
        onClick={handleShare}
        className="w-full bg-dark-800/90 border border-dark-700/80 hover:border-gremlin-frost/50 p-3.5 rounded-2xl flex items-center justify-center space-x-2 text-xs font-bold text-gremlin-frost transition active:scale-[0.98] shadow-md backdrop-blur-md"
      >
        <Share2 className="w-4 h-4" />
        <span>{t.profile.shareAchievement}</span>
      </button>

      {/* Language Selection Card */}
      <div className="bg-dark-800/90 border border-dark-700/80 p-4 rounded-2xl flex flex-col space-y-2.5 shadow-md backdrop-blur-md">
        <div className="flex items-center space-x-2 text-slate-200">
          <Globe className="w-4 h-4 text-gremlin-frost" />
          <h4 className="font-bold text-xs">{t.profile.language}</h4>
        </div>
        <div className="grid grid-cols-2 gap-2 pt-1">
          {availableLanguages.map((l) => (
            <button
              key={l.code}
              onClick={() => handleLangChange(l.code)}
              className={`p-2.5 rounded-xl border text-xs flex items-center space-x-2 transition shadow-sm active:scale-95 ${
                language === l.code
                  ? 'bg-gremlin-green/20 border-gremlin-green text-gremlin-green font-bold shadow-gremlin-green/10'
                  : 'bg-dark-900/60 border-dark-700 text-slate-400 hover:text-slate-200'
              }`}
            >
              <span className="text-base">{l.flag}</span>
              <span>{l.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Streak Protection (Campfire Freeze) */}
      <div className="bg-dark-800/90 border border-dark-700/80 p-4 rounded-2xl flex items-center justify-between shadow-md backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/15 text-sky-400 flex items-center justify-center">
            <Snowflake className="w-5 h-5 animate-spin-slow" />
          </div>
          <div>
            <h4 className="font-bold text-xs text-slate-100">{t.profile.streakFreezeTitle}</h4>
            <span className="text-[11px] text-slate-400">
              {user.streak_freeze_count} {t.profile.streakFreezeDesc}
            </span>
          </div>
        </div>
        <button
          onClick={handleFreeze}
          disabled={user.streak_freeze_count <= 0}
          className="bg-sky-500/20 hover:bg-sky-500/30 border border-sky-500/40 text-sky-300 font-bold px-3.5 py-2 rounded-xl text-xs transition active:scale-95 disabled:opacity-50 shadow-sm"
        >
          {t.profile.useFreezeBtn}
        </button>
      </div>

      {/* Privacy & Hardware Security Status */}
      <div className="bg-dark-800/80 border border-dark-700/80 p-4 rounded-2xl flex flex-col space-y-3 shadow-md backdrop-blur-md">
        <h4 className="font-bold text-xs uppercase tracking-wider text-slate-400">
          {t.profile.securityTitle}
        </h4>

        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-300 flex items-center space-x-2">
            <Lock className="w-4 h-4 text-gremlin-green" />
            <span>{t.profile.safeZones}</span>
          </span>
          <span className="text-gremlin-green font-bold">{t.profile.active}</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-300 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-gremlin-green" />
            <span>{t.profile.deviceIntegrity}</span>
          </span>
          <span className="text-gremlin-green font-bold">{t.profile.attested}</span>
        </div>

        {/* Solana Wallet Row (Clickable) */}
        <div
          onClick={() => {
            haptic('tap');
            onConnectWallet();
          }}
          className="flex items-center justify-between text-xs bg-dark-900/60 p-2.5 rounded-xl border border-gremlin-purple/30 hover:border-gremlin-purple/60 cursor-pointer active:scale-98 transition"
        >
          <span className="text-slate-300 flex items-center space-x-2">
            <Wallet className="w-4 h-4 text-gremlin-purple" />
            <span>{t.profile.mpcWallet}</span>
          </span>
          <span className="text-gremlin-purple font-mono text-[11px] font-bold truncate max-w-[130px]">
            {user.solana_wallet ? user.solana_wallet : 'Connect'}
          </span>
        </div>
      </div>
    </div>
  );
};
