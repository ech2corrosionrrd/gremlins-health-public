import React from 'react';
import { Heart, Compass, Camera, ShoppingBag, ShieldAlert, User } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';

export type TabType = 'gremlin' | 'map' | 'camera' | 'market' | 'raid' | 'profile';

interface TabNavigationProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
}

export const TabNavigation: React.FC<TabNavigationProps> = ({ activeTab, onSelectTab }) => {
  const { t } = useLanguage();

  const tabs = [
    { id: 'gremlin', label: t.tabs.gremlin, icon: Heart },
    { id: 'map', label: t.tabs.map, icon: Compass },
    { id: 'camera', label: t.tabs.camera, icon: Camera, highlight: true },
    { id: 'market', label: t.tabs.market, icon: ShoppingBag },
    { id: 'raid', label: t.tabs.raid, icon: ShieldAlert },
    { id: 'profile', label: t.tabs.profile, icon: User },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-dark-900/95 backdrop-blur-xl border-t border-dark-700/80 px-2 pt-1.5 pb-[max(0.5rem,env(safe-area-inset-bottom,0.5rem))] flex justify-around items-center max-w-md mx-auto shadow-2xl">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        if (tab.highlight) {
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id as TabType)}
              className="relative -top-3.5 flex flex-col items-center group active:scale-95 transition-transform"
            >
              <div className="w-13 h-13 p-3 rounded-full bg-gradient-to-tr from-gremlin-green to-gremlin-frost flex items-center justify-center text-dark-950 shadow-xl shadow-gremlin-green/30 group-hover:scale-105 transition-transform">
                <Icon className="w-6 h-6 text-dark-950 stroke-[2.5]" />
              </div>
              <span className="text-[10px] font-bold text-gremlin-frost mt-0.5 tracking-tight">
                {tab.label}
              </span>
            </button>
          );
        }

        return (
          <button
            key={tab.id}
            onClick={() => onSelectTab(tab.id as TabType)}
            className={`flex flex-col items-center py-1 px-2.5 rounded-xl transition-all duration-200 active:scale-90 ${
              isActive
                ? 'text-gremlin-green font-bold scale-105'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <div className="relative">
              <Icon
                className={`w-5 h-5 ${
                  isActive ? 'stroke-[2.5] text-gremlin-green' : 'stroke-[1.75]'
                } transition-colors`}
              />
              {isActive && (
                <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-gremlin-green rounded-full shadow-sm shadow-gremlin-green animate-pulse" />
              )}
            </div>
            <span className="text-[10px] mt-1.5">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
};
