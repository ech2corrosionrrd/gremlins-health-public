import React, { useEffect, useState } from 'react';
import confetti from 'canvas-confetti';

import { FogOfWarMap } from './components/FogOfWarMap';
import { GremlinCompanion } from './components/GremlinCompanion';
import { Marketplace } from './components/Marketplace';
import { Navbar } from './components/Navbar';
import { Profile } from './components/Profile';
import { RaidBoss } from './components/RaidBoss';
import { SecureCamera } from './components/SecureCamera';
import { TabNavigation, TabType } from './components/TabNavigation';
import { WalletConnectModal } from './components/WalletConnectModal';
import { LanguageProvider } from './i18n/LanguageContext';
import { useGameState } from './hooks/useGameState';
import { haptic, initTelegram, shareTelegramUrl, showAlert } from './lib/telegram';
import { NFTItem } from './types';

const DemoBanner: React.FC<{ reason: string | null }> = ({ reason }) => (
  <div className="bg-amber-500/15 border-b border-amber-500/40 px-4 py-2 text-[11px] text-amber-300 text-center font-medium">
    <strong>Demo mode</strong> — local data only, nothing is saved to your account
    {reason ? ` (${reason})` : ''}
  </div>
);

const Toast: React.FC<{ message: string; onDismiss: () => void }> = ({
  message,
  onDismiss,
}) => {
  useEffect(() => {
    const t = setTimeout(onDismiss, 4000);
    return () => clearTimeout(t);
  }, [message, onDismiss]);

  return (
    <div
      role="status"
      className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 max-w-[22rem] w-[90%] bg-dark-800/95 backdrop-blur-md border border-dark-600 text-slate-100 text-xs px-4 py-3 rounded-2xl shadow-2xl cursor-pointer active:scale-95 transition-transform"
      onClick={onDismiss}
    >
      {message}
    </div>
  );
};

const MainAppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('gremlin');
  const [isWalletModalOpen, setIsWalletModalOpen] = useState<boolean>(false);
  const game = useGameState();

  useEffect(() => {
    initTelegram();
  }, []);

  const handleSelectTab = (tab: TabType) => {
    haptic('selection');
    setActiveTab(tab);
  };

  const handleFeed = async () => {
    await game.feed();
    haptic('success');
  };

  const handleEvolve = async () => {
    await game.evolve();
    haptic('heavy');
  };

  const handleSimulateWalk = async () => {
    await game.simulateWalk();
    haptic('success');
    confetti({ particleCount: 40, spread: 70 });
  };

  const handleMint = async (input: {
    title: string;
    story_note?: string;
    original_photo_url: string;
    location_name: string;
  }) => {
    await game.mintNFT(input);
    haptic('success');
    setActiveTab('market');
  };

  const handleBuyNFT = (nft: NFTItem) => {
    haptic('tap');
    showAlert(`Buying "${nft.title}" is not available yet.`);
  };

  const handleContributeSteps = () => {
    haptic('heavy');
    game.contributeToBoss();
    confetti({ particleCount: 50, spread: 80 });
  };

  const handleUseStreakFreeze = async () => {
    await game.useStreakFreeze();
    haptic('success');
  };

  const handleOpenWalletModal = () => {
    haptic('tap');
    setIsWalletModalOpen(true);
  };

  const handleConnectWalletAddress = async (address: string) => {
    await game.connectWallet(address);
    haptic('success');
    confetti({ particleCount: 30, spread: 60 });
  };

  const handleDisconnectWallet = async () => {
    await game.disconnectWallet();
    haptic('tap');
  };

  const handleShareAchievement = () => {
    haptic('tap');
    shareTelegramUrl(
      'https://t.me/GremlinsHealthBot/app',
      `I just hiked with my Gremlin in Gremlins Health! https://t.me/GremlinsHealthBot/app`,
    );
  };

  if (game.mode === 'loading') {
    return (
      <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col items-center justify-center space-y-3">
        <div className="w-12 h-12 rounded-full border-4 border-gremlin-green border-t-transparent animate-spin" />
        <span className="text-xs font-mono text-gremlin-frost tracking-wider">GREMLINS HEALTH 2.0</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col max-w-md mx-auto relative shadow-2xl overflow-x-hidden">
      {game.mode === 'demo' && <DemoBanner reason={game.demoReason} />}

      <Navbar user={game.user} onConnectWallet={handleOpenWalletModal} />

      <main
        className="flex-1 px-4 pt-3 pb-28 sm:pb-32 overflow-y-auto"
        aria-busy={game.busy}
        style={{ opacity: game.busy ? 0.6 : 1, transition: 'opacity 120ms' }}
      >
        {activeTab === 'gremlin' && (
          <GremlinCompanion
            gremlin={game.gremlin}
            onFeed={handleFeed}
            onEvolve={handleEvolve}
            onSimulateWalk={handleSimulateWalk}
          />
        )}

        {activeTab === 'map' && <FogOfWarMap />}

        {activeTab === 'camera' && (
          <SecureCamera
            onMint={handleMint}
            canMint={game.mintableActivityId !== null}
            busy={game.busy}
          />
        )}

        {activeTab === 'market' && (
          <Marketplace nfts={game.nfts} onBuyNFT={handleBuyNFT} />
        )}

        {activeTab === 'raid' && (
          <RaidBoss
            boss={game.boss}
            quests={game.quests}
            onContributeSteps={handleContributeSteps}
          />
        )}

        {activeTab === 'profile' && (
          <Profile
            user={game.user}
            onUseStreakFreeze={handleUseStreakFreeze}
            onShare={handleShareAchievement}
            onConnectWallet={handleOpenWalletModal}
          />
        )}
      </main>

      {game.error && <Toast message={game.error} onDismiss={game.clearError} />}

      <TabNavigation activeTab={activeTab} onSelectTab={handleSelectTab} />

      {/* Real Solana Wallet Connection Modal */}
      <WalletConnectModal
        isOpen={isWalletModalOpen}
        currentWallet={game.user.solana_wallet}
        onClose={() => setIsWalletModalOpen(false)}
        onConnect={handleConnectWalletAddress}
        onDisconnect={handleDisconnectWallet}
      />
    </div>
  );
};

export const App: React.FC = () => (
  <LanguageProvider>
    <MainAppContent />
  </LanguageProvider>
);

export default App;
