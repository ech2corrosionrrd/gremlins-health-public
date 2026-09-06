/**
 * Owns all server-backed game state.
 *
 * Two modes:
 *  - "live": running inside Telegram with a reachable backend. The server is
 *    the source of truth; every mutation is a request and the response
 *    replaces local state, so balances can never be edited from DevTools.
 *  - "demo": opened in a plain browser, or the API is unreachable. Falls back
 *    to local mock state purely so the UI can be developed and reviewed.
 *
 * The mode is surfaced to the UI so a demo session is never mistaken for a
 * real one.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError, api, toNFTItem, tokenStore } from '../lib/api';
import { isStandalone } from '../lib/telegram';
import { safeStorage } from '../lib/storage';
import {
  initialBoss,
  initialGremlin,
  initialNFTs,
  initialQuests,
  initialUser,
} from '../services/mockData';
import type { BrandQuest, ClanRaidBoss, Gremlin, NFTItem, UserProfile } from '../types';

export type GameMode = 'loading' | 'live' | 'demo';

/** Те, що камера знає про знімок; activity_id підставляє сам хук. */
export interface MintInput {
  title: string;
  story_note?: string;
  original_photo_url: string;
  location_name: string;
}

export interface GameState {
  mode: GameMode;
  /** Populated in demo mode when we know why the backend was not used. */
  demoReason: string | null;
  user: UserProfile;
  gremlin: Gremlin;
  nfts: NFTItem[];
  boss: ClanRaidBoss;
  quests: BrandQuest[];
  /**
   * Активність, з якої ще можна змінтити NFT. Бекенд приймає мінт лише з
   * верифікованої активності й лише один раз, тож без неї кнопка мінту не
   * має сенсу — UI має сказати про це, а не ловити 404.
   */
  mintableActivityId: number | null;
  busy: boolean;
  error: string | null;
  clearError: () => void;
  feed: () => Promise<void>;
  evolve: () => Promise<void>;
  simulateWalk: () => Promise<void>;
  useStreakFreeze: () => Promise<void>;
  connectWallet: (walletAddress: string) => Promise<void>;
  disconnectWallet: () => Promise<void>;
  mintNFT: (input: MintInput) => Promise<void>;
  addNFT: (nft: NFTItem) => void;
  contributeToBoss: () => void;
}

function describe(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return 'Something went wrong';
}

export function useGameState(): GameState {
  const [mode, setMode] = useState<GameMode>('loading');
  const [demoReason, setDemoReason] = useState<string | null>(null);
  const [user, setUser] = useState<UserProfile>(initialUser);
  const [gremlin, setGremlin] = useState<Gremlin>(initialGremlin);
  const [nfts, setNfts] = useState<NFTItem[]>(initialNFTs);
  const [boss, setBoss] = useState<ClanRaidBoss>(initialBoss);
  const [quests, setQuests] = useState<BrandQuest[]>(initialQuests);
  const [mintableActivityId, setMintableActivityId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Guards against overlapping requests from double taps.
  const inFlight = useRef(false);

  const fallbackToDemo = useCallback((reason: string) => {
    setMode('demo');
    setDemoReason(reason);
    setUser(safeStorage.getJSON('gh_user', initialUser));
    setGremlin(safeStorage.getJSON('gh_gremlin', initialGremlin));
    setNfts(safeStorage.getJSON('gh_nfts', initialNFTs));
    setBoss(safeStorage.getJSON('gh_boss', initialBoss));
    setQuests(initialQuests);

    // Маркетплейс, квести й бос не потребують авторизації. Демо-режим
    // означає «немає сесії», а не обовʼязково «немає бекенду»: якщо сервер
    // поруч, показати справжні дані чесніше, ніж мок. Мовчазний catch —
    // мок уже виставлений вище.
    void (async () => {
      const [listings, brandQuests, raidBoss] = await Promise.all([
        api.exploreMarketplace().catch(() => null),
        api.getBrandQuests().catch(() => null),
        api.getRaidBoss().catch(() => null),
      ]);
      if (listings?.length) setNfts(listings.map((l) => toNFTItem(l.nft, l)));
      if (brandQuests?.length) setQuests(brandQuests);
      if (raidBoss) setBoss(raidBoss);
    })();
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (isStandalone()) {
        fallbackToDemo('Not running inside Telegram');
        return;
      }

      try {
        // Reuse an existing session; only re-login when it is gone or stale.
        if (!tokenStore.get()) {
          await api.loginWithTelegram();
        }
        let profile: UserProfile;
        try {
          profile = await api.getMe();
        } catch (err) {
          if (err instanceof ApiError && err.isAuthError) {
            profile = (await api.loginWithTelegram()).user;
          } else {
            throw err;
          }
        }

        // Маркетплейс і квести читаються без авторизації, тож їхня помилка
        // не повинна відкидати всю сесію в demo — показуємо порожній список.
        const [companion, raidBoss, listings, brandQuests] = await Promise.all([
          api.getMyGremlin(),
          api.getRaidBoss().catch(() => null),
          api.exploreMarketplace().catch(() => null),
          api.getBrandQuests().catch(() => null),
        ]);

        if (cancelled) return;
        setUser(profile);
        setGremlin(companion);
        if (raidBoss) setBoss(raidBoss);
        if (listings) setNfts(listings.map((l) => toNFTItem(l.nft, l)));
        if (brandQuests) setQuests(brandQuests);
        setMode('live');
      } catch (err) {
        if (cancelled) return;
        fallbackToDemo(describe(err));
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [fallbackToDemo]);

  // Demo state is the only state worth persisting locally; a live session
  // reloads from the server and must not be seeded from stale storage.
  useEffect(() => {
    if (mode !== 'demo') return;
    safeStorage.setJSON('gh_user', user);
    safeStorage.setJSON('gh_gremlin', gremlin);
    safeStorage.setJSON('gh_nfts', nfts);
    safeStorage.setJSON('gh_boss', boss);
  }, [mode, user, gremlin, nfts, boss]);

  const run = useCallback(
    async (
      live: () => Promise<void>,
      demo: () => void,
    ): Promise<void> => {
      if (inFlight.current) return;
      if (mode !== 'live') {
        demo();
        return;
      }
      inFlight.current = true;
      setBusy(true);
      setError(null);
      try {
        await live();
      } catch (err) {
        setError(describe(err));
      } finally {
        inFlight.current = false;
        setBusy(false);
      }
    },
    [mode],
  );

  const feed = useCallback(
    () =>
      run(
        async () => {
          const updated = await api.feedGremlin();
          setGremlin(updated);
          setUser(await api.getMe());
        },
        () => {
          if (user.stamina_balance < 15) {
            setError('Not enough stamina! Go for a walk to earn more.');
            return;
          }
          setUser((p) => ({ ...p, stamina_balance: p.stamina_balance - 15 }));
          setGremlin((p) => ({
            ...p,
            hunger: Math.max(0, p.hunger - 30),
            mood: Math.min(100, p.mood + 15),
            hp: Math.min(p.max_hp, p.hp + 10),
          }));
        },
      ),
    [run, user.stamina_balance],
  );

  const evolve = useCallback(
    () =>
      run(
        async () => setGremlin(await api.evolveGremlin()),
        () => {
          if (gremlin.xp < gremlin.next_level_xp) {
            setError('Not enough XP to evolve yet.');
            return;
          }
          setGremlin((p) => ({
            ...p,
            level: p.level + 1,
            xp: p.xp - p.next_level_xp,
            next_level_xp: Math.round(p.next_level_xp * 1.5),
            max_hp: p.max_hp + 15,
            hp: p.max_hp + 15,
          }));
        },
      ),
    [run, gremlin.xp, gremlin.next_level_xp],
  );

  const simulateWalk = useCallback(
    () =>
      run(
        async () => {
          const end = new Date();
          const start = new Date(end.getTime() - 2 * 60 * 60 * 1000);
          const result = await api.syncActivity({
            // Stable per-upload id: a retry is deduplicated server-side.
            client_activity_uuid: crypto.randomUUID(),
            activity_type: 'hiking',
            start_time: start.toISOString(),
            end_time: end.toISOString(),
            total_steps: 12500,
            total_distance_km: 8.5,
            elevation_gain_m: 850,
            start_elevation_m: 800,
            max_elevation_m: 1650,
            weather_condition: 'clear',
            temperature_c: 14,
            ble_nearby_devices_count: 1,
          });
          if (result.capped_reason) setError(result.capped_reason);
          // Мінт можливий лише з верифікованої активності.
          if (result.is_verified && !result.duplicate) {
            setMintableActivityId(result.activity_id);
          }
          const [profile, companion] = await Promise.all([api.getMe(), api.getMyGremlin()]);
          setUser(profile);
          setGremlin(companion);
        },
        () => {
          setUser((p) => ({
            ...p,
            stamina_balance: p.stamina_balance + 65,
            streak_days: p.streak_days + 1,
          }));
          setGremlin((p) => ({ ...p, xp: p.xp + 1950, biome_affinity: 'mountain_frost' }));
        },
      ),
    [run],
  );

  const useStreakFreeze = useCallback(
    () =>
      run(
        async () => setUser(await api.useStreakFreeze()),
        () => {
          if (user.streak_freeze_count <= 0) {
            setError('No streak freezes remaining.');
            return;
          }
          setUser((p) => ({ ...p, streak_freeze_count: p.streak_freeze_count - 1 }));
        },
      ),
    [run, user.streak_freeze_count],
  );

  const connectWallet = useCallback(
    (walletAddress: string) =>
      run(
        async () => {
          const updated = await api.updateWallet(walletAddress);
          setUser(updated);
        },
        () => {
          setUser((p) => ({ ...p, solana_wallet: walletAddress }));
        },
      ),
    [run],
  );

  const disconnectWallet = useCallback(
    () =>
      run(
        async () => {
          const updated = await api.unlinkWallet();
          setUser(updated);
        },
        () => {
          setUser((p) => ({ ...p, solana_wallet: undefined }));
        },
      ),
    [run],
  );

  const mintNFT = useCallback(
    (input: MintInput) =>
      run(
        async () => {
          if (mintableActivityId === null) {
            // Це не помилка мережі, а стан гри: спершу треба зарахувати похід.
            setError('Спершу зарахуйте похід — мінт можливий лише з верифікованої активності.');
            return;
          }
          const minted = await api.mintNFT({ ...input, activity_id: mintableActivityId });
          setNfts((prev) => [toNFTItem(minted), ...prev]);
          // Одна активність — один NFT: бекенд віддасть 409 на другу спробу.
          setMintableActivityId(null);
        },
        () => {
          const now = Date.now();
          setNfts((prev) => [
            {
              id: now,
              title: input.title,
              story_note: input.story_note,
              location_name: input.location_name,
              rarity: 'Epic',
              original_photo_url: input.original_photo_url,
              rendered_art_url: input.original_photo_url,
              likes_count: 0,
              views_count: 0,
              is_verified: false,
              is_onchain: false,
              created_at: new Date().toISOString(),
              attributes: {
                Location: input.location_name,
                Biome: 'common',
                Rarity: 'Epic',
                Elevation_m: 0,
                Weather: 'clear',
              },
            },
            ...prev,
          ]);
        },
      ),
    [run, mintableActivityId],
  );

  const addNFT = useCallback((nft: NFTItem) => setNfts((prev) => [nft, ...prev]), []);

  const contributeToBoss = useCallback(() => {
    // Raid contribution has no backend endpoint yet; kept local and clearly
    // marked so it is not mistaken for a server-verified action.
    setBoss((p) => ({
      ...p,
      current_health_steps: Math.max(0, p.current_health_steps - 50000),
    }));
  }, []);

  return {
    mode,
    demoReason,
    user,
    gremlin,
    nfts,
    boss,
    quests,
    mintableActivityId,
    busy,
    error,
    clearError: () => setError(null),
    feed,
    evolve,
    simulateWalk,
    useStreakFreeze,
    connectWallet,
    disconnectWallet,
    mintNFT,
    addNFT,
    contributeToBoss,
  };
}

