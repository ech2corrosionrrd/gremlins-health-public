import React, { useState } from 'react';
import { Heart, ShieldCheck, Award, X, Copy, Check } from 'lucide-react';
import { NFTItem, GremlinRarity } from '../types';
import { useLanguage } from '../i18n/LanguageContext';
import { haptic } from '../lib/telegram';

interface MarketplaceProps {
  nfts: NFTItem[];
  onBuyNFT: (nft: NFTItem) => void;
}

/**
 * Ціна живе на лістингу, а не на самому NFT: щойно змінтований ассет ще не
 * виставлений. Раніше тут виводилось `{nft.price_sol} SOL`, і без ціни на
 * картці зʼявлялось буквальне «undefined SOL».
 */
const isListed = (nft: NFTItem): boolean => typeof nft.price_sol === 'number';

/**
 * Артворк генерує MockAIRenderService, і він повертає URL на example.invalid —
 * тобто картинки не існує. Замість зламаної іконки показуємо справжнє фото
 * користувача, а якщо і його нема — ховаємо <img> і лишаємо тло картки.
 */
const handleArtError = (
  event: React.SyntheticEvent<HTMLImageElement>,
  fallback: string,
): void => {
  const img = event.currentTarget;
  if (fallback && img.src !== fallback) {
    img.src = fallback;
    return;
  }
  img.style.display = 'none';
};

export const Marketplace: React.FC<MarketplaceProps> = ({ nfts, onBuyNFT }) => {
  const { t } = useLanguage();
  const [selectedRarity, setSelectedRarity] = useState<string>('All');
  const [selectedNFT, setSelectedNFT] = useState<NFTItem | null>(null);
  const [copiedId, setCopiedId] = useState(false);

  const filteredNFTs =
    selectedRarity === 'All' ? nfts : nfts.filter((n) => n.rarity === selectedRarity);

  const trailMilestonesAlbum = [
    { name: '5km Trail Pioneer', completed: true, icon: '🌲' },
    { name: 'Summit Vista 500m+', completed: true, icon: '🏔️' },
    { name: '10k Step Streak', completed: true, icon: '🔥' },
    { name: 'Night Trail Master', completed: false, icon: '🌙' },
    { name: 'Clan Boss Slayer', completed: false, icon: '⚔️' },
    { name: 'Solana cNFT Legend', completed: false, icon: '💎' },
  ];

  const getRarityBadge = (rarity: GremlinRarity) => {
    switch (rarity) {
      case 'Legendary':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'Epic':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/40';
      case 'Rare':
        return 'bg-sky-500/20 text-sky-400 border-sky-500/40';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  const handleCopyAssetId = (id: string) => {
    haptic('tap');
    navigator.clipboard?.writeText(id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 1500);
  };

  return (
    <div className="flex flex-col space-y-4 pb-6 pt-1">
      {/* Carpathian Trail Master Passport Card */}
      <div className="bg-gradient-to-r from-dark-800 via-dark-800 to-dark-700 border border-gremlin-gold/30 p-4 rounded-3xl shadow-xl flex flex-col space-y-2.5 backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-xl bg-gremlin-gold/15 text-gremlin-gold flex items-center justify-center shadow-md">
              <Award className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-xs text-slate-100">{t.market.albumTitle}</h3>
              <span className="text-[10px] text-slate-400">{t.market.albumDesc}</span>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-gremlin-gold bg-gremlin-gold/10 px-2 py-0.5 rounded-full border border-gremlin-gold/20">
            {t.market.verifiedCount}
          </span>
        </div>

        {/* Mini Peak Grid */}
        <div className="grid grid-cols-3 gap-1.5 pt-1">
          {trailMilestonesAlbum.map((p, i) => (
            <div
              key={i}
              className={`p-1.5 rounded-xl border text-[10px] flex items-center space-x-1 shadow-sm ${
                p.completed
                  ? 'bg-gremlin-green/15 border-gremlin-green/40 text-gremlin-green font-semibold'
                  : 'bg-dark-900/50 border-dark-700 text-slate-500'
              }`}
            >
              <span>{p.completed ? '✅' : p.icon}</span>
              <span className="truncate">{p.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-1.5 overflow-x-auto pb-1 scrollbar-none">
        {['All', 'Rare', 'Epic', 'Legendary'].map((r) => (
          <button
            key={r}
            onClick={() => {
              haptic('selection');
              setSelectedRarity(r);
            }}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition active:scale-95 shadow-sm ${
              selectedRarity === r
                ? 'bg-gremlin-green text-dark-900 font-bold shadow-gremlin-green/20'
                : 'bg-dark-800/90 border border-dark-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            {r === 'All' ? t.market.filters.all : r}
          </button>
        ))}
      </div>

      {/* cNFT Marketplace Grid */}
      <div className="grid grid-cols-2 gap-3">
        {filteredNFTs.map((nft) => (
          <div
            key={nft.id}
            onClick={() => {
              haptic('tap');
              setSelectedNFT(nft);
            }}
            className="group bg-dark-800/90 hover:bg-dark-800 border border-dark-700/80 hover:border-dark-600 rounded-2xl overflow-hidden shadow-lg transition-all duration-200 flex flex-col cursor-pointer active:scale-98"
          >
            <div className="relative w-full aspect-square bg-dark-900 overflow-hidden">
              <img
                src={nft.rendered_art_url}
                alt={nft.title}
                loading="lazy"
                onError={(e) => handleArtError(e, nft.original_photo_url)}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <span
                className={`absolute top-2 left-2 px-2 py-0.5 rounded-md text-[10px] font-bold border backdrop-blur-md shadow-md ${getRarityBadge(
                  nft.rarity
                )}`}
              >
                {nft.rarity}
              </span>
              <span className="absolute bottom-2 right-2 bg-dark-900/90 backdrop-blur-md px-2 py-0.5 rounded-lg text-xs font-mono font-bold text-gremlin-green border border-dark-700 shadow-md">
                {isListed(nft) ? `${nft.price_sol} SOL` : t.market.notListed}
              </span>
              {nft.is_onchain === false && (
                /* Мінт поки симульований — картка не має вдавати протилежне. */
                <span className="absolute top-2 left-2 bg-amber-500/20 border border-amber-500/50 text-amber-300 px-1.5 py-0.5 rounded-md text-[9px] font-bold tracking-wide">
                  SIM
                </span>
              )}
            </div>

            <div className="p-2.5 flex flex-col space-y-1">
              <h4 className="font-bold text-xs text-slate-100 truncate">{nft.title}</h4>
              <span className="text-[10px] text-slate-400 truncate">{nft.location_name}</span>

              <div className="flex items-center justify-between pt-1 border-t border-dark-700/80 text-[10px] text-slate-400 font-mono">
                <span className="flex items-center space-x-1">
                  <Heart className="w-3 h-3 text-rose-500 fill-rose-500" />
                  <span>{nft.likes_count}</span>
                </span>
                <span className="text-slate-400 font-bold">
                  {isListed(nft) ? `$${nft.price_usd_approx}` : '—'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* NFT Detail Modal */}
      {selectedNFT && (
        <div className="fixed inset-0 z-50 bg-dark-950/85 backdrop-blur-md flex items-end sm:items-center justify-center p-3 animate-in fade-in duration-150">
          <div className="w-full max-w-md bg-dark-900 border border-dark-700 rounded-3xl p-5 shadow-2xl flex flex-col space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center">
              <span
                className={`px-2.5 py-0.5 rounded-md text-xs font-bold border ${getRarityBadge(
                  selectedNFT.rarity
                )}`}
              >
                {selectedNFT.rarity}
              </span>
              <button
                onClick={() => {
                  haptic('tap');
                  setSelectedNFT(null);
                }}
                className="w-8 h-8 rounded-full bg-dark-800 border border-dark-700 text-slate-400 hover:text-white flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="relative w-full aspect-video rounded-2xl overflow-hidden bg-dark-800 shadow-inner">
              <img
                src={selectedNFT.rendered_art_url}
                alt={selectedNFT.title}
                onError={(e) => handleArtError(e, selectedNFT.original_photo_url)}
                className="w-full h-full object-cover"
              />
            </div>

            <div>
              <div className="flex items-center justify-between">
                <h3 className="font-black text-base text-slate-100">{selectedNFT.title}</h3>
                <span className="text-sm font-bold font-mono text-gremlin-green">
                  {isListed(selectedNFT) ? `${selectedNFT.price_sol} SOL` : t.market.notListed}
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1">{selectedNFT.story_note}</p>
            </div>

            <div className="bg-dark-800/90 border border-gremlin-green/30 p-3.5 rounded-2xl flex flex-col space-y-2 text-xs shadow-md">
              <div className="flex items-center space-x-1.5 text-gremlin-green font-semibold">
                <ShieldCheck className="w-4 h-4" />
                <span>{t.market.solanaCnftBadge}</span>
              </div>
              <div className="flex justify-between items-center text-[11px] text-slate-400 font-mono">
                <span>{t.market.assetId}:</span>
                <button
                  onClick={() => handleCopyAssetId(selectedNFT.solana_asset_id || '')}
                  className="text-slate-200 flex items-center space-x-1 hover:text-white bg-dark-900/60 px-2 py-0.5 rounded border border-dark-700"
                >
                  <span className="truncate max-w-[150px]">{selectedNFT.solana_asset_id || 'cNFT_Pending'}</span>
                  {copiedId ? <Check className="w-3 h-3 text-gremlin-green" /> : <Copy className="w-3 h-3 text-slate-400" />}
                </button>
              </div>
              <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                <span>{t.market.elevationProof}:</span>
                <span className="text-sky-300 font-bold">{selectedNFT.attributes.Elevation_m} m</span>
              </div>
            </div>

            <div className="flex space-x-2 pt-2">
              <button
                onClick={() => setSelectedNFT(null)}
                className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 text-slate-300 rounded-2xl font-semibold text-xs transition"
              >
                {t.market.closeBtn}
              </button>
              {isListed(selectedNFT) && (
                <button
                  onClick={() => {
                    onBuyNFT(selectedNFT);
                    setSelectedNFT(null);
                  }}
                  className="flex-2 py-3 bg-gradient-to-r from-gremlin-green to-gremlin-frost text-dark-900 font-bold rounded-2xl text-xs transition active:scale-95 shadow-lg shadow-gremlin-green/20"
                >
                  {t.market.buyBtn} {selectedNFT.price_sol} SOL (~${selectedNFT.price_usd_approx})
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
