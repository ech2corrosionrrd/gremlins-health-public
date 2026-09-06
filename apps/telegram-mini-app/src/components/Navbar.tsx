import React, { useState, useEffect, useRef } from 'react';
import { Flame, Zap, ShieldCheck, Wallet } from 'lucide-react';
import { UserProfile } from '../types';
import { useLanguage } from '../i18n/LanguageContext';
import { haptic } from '../lib/telegram';

interface NavbarProps {
  user: UserProfile;
  onConnectWallet: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onConnectWallet }) => {
  const { language, setLanguage, availableLanguages, t } = useLanguage();
  const [showLangMenu, setShowLangMenu] = useState(false);
  const langMenuRef = useRef<HTMLDivElement>(null);

  const currentLang = availableLanguages.find((l) => l.code === language) || availableLanguages[0];

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (langMenuRef.current && !langMenuRef.current.contains(event.target as Node)) {
        setShowLangMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggleLang = () => {
    haptic('tap');
    setShowLangMenu((prev) => !prev);
  };

  const handleSelectLang = (code: any) => {
    haptic('selection');
    setLanguage(code);
    setShowLangMenu(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-dark-900/90 backdrop-blur-xl border-b border-dark-700/80 px-4 py-2.5 pt-[max(0.625rem,env(safe-area-inset-top,0.625rem))] flex items-center justify-between shadow-md">
      {/* User Brand & Identity */}
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-gremlin-green to-gremlin-frost flex items-center justify-center text-lg font-bold shadow-lg shadow-gremlin-green/20 shrink-0">
          🌲
        </div>
        <div>
          <div className="flex items-center space-x-1.5">
            <span className="font-bold text-sm text-slate-100 tracking-wide truncate max-w-[100px]">
              {user.username}
            </span>
            {user.is_device_verified && (
              <span title={t.camera.hardwareAttested}>
                <ShieldCheck className="w-3.5 h-3.5 text-gremlin-green" />
              </span>
            )}
          </div>
          <span className="text-[10px] text-slate-400 font-mono">
            {t.reputation}: {user.reputation_score}%
          </span>
        </div>
      </div>

      {/* Stats Balances & Controls */}
      <div className="flex items-center space-x-2">
        {/* Language Switcher Dropdown */}
        <div className="relative" ref={langMenuRef}>
          <button
            onClick={handleToggleLang}
            className="flex items-center space-x-1 bg-dark-800/90 border border-dark-700/90 px-2 py-1 rounded-full text-xs font-semibold text-slate-300 hover:text-white transition active:scale-95 shadow-sm"
            title={t.profile.language}
          >
            <span>{currentLang.flag}</span>
            <span className="uppercase text-[10px] font-mono font-bold">{currentLang.code}</span>
          </button>

          {showLangMenu && (
            <div className="absolute right-0 mt-2 w-36 bg-dark-800/95 backdrop-blur-xl border border-dark-600 rounded-2xl shadow-2xl py-1 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
              {availableLanguages.map((l) => (
                <button
                  key={l.code}
                  onClick={() => handleSelectLang(l.code)}
                  className={`w-full px-3 py-2 text-left text-xs flex items-center space-x-2 transition ${
                    language === l.code
                      ? 'bg-gremlin-green/20 text-gremlin-green font-bold'
                      : 'text-slate-300 hover:bg-dark-700/80'
                  }`}
                >
                  <span className="text-sm">{l.flag}</span>
                  <span>{l.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Streak Badge */}
        <div className="flex items-center space-x-1 bg-dark-800/90 border border-dark-700/80 px-2.5 py-1 rounded-full text-xs text-amber-400 shadow-sm">
          <Flame className="w-3.5 h-3.5 fill-amber-400 text-amber-500 animate-pulse" />
          <span className="font-bold font-mono">
            {user.streak_days}
            {t.streakDays}
          </span>
        </div>

        {/* Stamina Badge */}
        <div className="flex items-center space-x-1 bg-dark-800/90 border border-dark-700/80 px-2.5 py-1 rounded-full text-xs text-gremlin-green shadow-sm">
          <Zap className="w-3.5 h-3.5 fill-gremlin-green" />
          <span className="font-bold font-mono">{user.stamina_balance}</span>
        </div>

        {/* Solana Wallet Button */}
        <button
          onClick={onConnectWallet}
          className="flex items-center space-x-1 bg-gremlin-purple/15 hover:bg-gremlin-purple/25 border border-gremlin-purple/40 text-gremlin-purple px-2.5 py-1 rounded-full text-xs font-semibold transition active:scale-95 shadow-sm"
        >
          <Wallet className="w-3.5 h-3.5" />
          <span className="font-mono truncate max-w-[70px]">
            {user.solana_wallet ? user.solana_wallet : t.connectWallet}
          </span>
        </button>
      </div>
    </header>
  );
};
