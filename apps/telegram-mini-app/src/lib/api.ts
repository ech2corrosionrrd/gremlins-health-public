/**
 * Typed client for the Gremlins Health backend.
 *
 * Auth model: the Mini App sends Telegram initData to /auth/login, which
 * verifies its HMAC server-side and returns a JWT. The raw initData is never
 * trusted by the backend and the token is the only thing we persist.
 */
import { safeStorage } from './storage';
import { getInitData } from './telegram';
import type {
  ActivitySyncResult,
  BrandQuest,
  ClanRaidBoss,
  Gremlin,
  NFTItem,
  UserProfile,
} from '../types';

const TOKEN_KEY = 'gh_access_token';

// Falls back to a same-origin /api prefix, which is what nginx serves in
// production, so a missing build-time variable does not break the app.
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? '/api';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  /** The session is gone or was never valid; the caller should re-login. */
  get isAuthError(): boolean {
    return this.status === 401 || this.status === 403;
  }
}

export const tokenStore = {
  get: (): string | null => safeStorage.getItem(TOKEN_KEY),
  set: (token: string): void => safeStorage.setItem(TOKEN_KEY, token),
  clear: (): void => safeStorage.removeItem(TOKEN_KEY),
};

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  auth?: boolean;
  timeoutMs?: number;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true, timeoutMs = 15000 } = options;

  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  if (auth) {
    const token = tokenStore.get();
    if (!token) throw new ApiError(401, 'Not authenticated');
    headers.Authorization = `Bearer ${token}`;
  }

  // A Mini App on a mountain trail sees flaky connectivity; never hang forever.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(0, 'Request timed out');
    }
    throw new ApiError(0, 'Network unavailable');
  } finally {
    clearTimeout(timer);
  }

  if (response.status === 204) return undefined as T;

  const raw = await response.text();
  let parsed: unknown = undefined;
  if (raw) {
    try {
      parsed = JSON.parse(raw);
    } catch {
      parsed = raw;
    }
  }

  if (!response.ok) {
    if (response.status === 401) tokenStore.clear();
    const detail =
      parsed && typeof parsed === 'object' && 'detail' in parsed
        ? (parsed as { detail: unknown }).detail
        : parsed;
    const message = typeof detail === 'string' ? detail : `Request failed (${response.status})`;
    throw new ApiError(response.status, message, detail);
  }

  return parsed as T;
}

// ---------------------------------------------------------------------------
// Wire types
// ---------------------------------------------------------------------------

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

/** Server response; extends the shared shape with the new guard-rail fields. */
export interface ActivitySyncResponse extends ActivitySyncResult {
  duplicate: boolean;
  capped_reason: string | null;
}

export interface ActivitySyncPayload {
  client_activity_uuid: string;
  activity_type: string;
  start_time: string;
  end_time: string;
  total_steps: number;
  total_distance_km: number;
  elevation_gain_m: number;
  start_elevation_m: number;
  max_elevation_m: number;
  weather_condition: string;
  temperature_c: number;
  ble_nearby_devices_count: number;
}

/** Те, що реально повертає бекенд для NFT. */
export interface NFTResponse {
  id: number;
  activity_id: number;
  creator_id: number;
  title: string;
  story_note: string | null;
  location_name: string;
  rarity: string;
  original_photo_url: string;
  rendered_art_url: string;
  solana_asset_id: string | null;
  arweave_metadata_uri: string | null;
  likes_count: number;
  views_count: number;
  is_onchain: boolean;
  created_at: string;
  attributes: Record<string, unknown>;
}

export interface NFTListingResponse {
  id: number;
  nft_id: number;
  seller_id: number;
  price_sol: number;
  price_usd_approx: number;
  is_sold: boolean;
  listed_at: string;
  nft: NFTResponse;
}

/**
 * Зводить відповідь бекенду до NFTItem, яким оперує UI.
 *
 * Ціна живе на лістингу, а не на самому NFT: щойно змінтований ассет її не
 * має, і це нормально — Marketplace показує таку картку без цінника.
 */
export function toNFTItem(nft: NFTResponse, listing?: NFTListingResponse): NFTItem {
  const attrs = (nft.attributes ?? {}) as Record<string, unknown>;
  return {
    id: nft.id,
    title: nft.title,
    story_note: nft.story_note ?? undefined,
    location_name: nft.location_name,
    rarity: nft.rarity as NFTItem['rarity'],
    original_photo_url: nft.original_photo_url,
    rendered_art_url: nft.rendered_art_url,
    solana_asset_id: nft.solana_asset_id ?? undefined,
    likes_count: nft.likes_count,
    views_count: nft.views_count,
    price_sol: listing?.price_sol,
    price_usd_approx: listing?.price_usd_approx,
    // Активність, з якої мінтили, вже пройшла античит — інакше бекенд
    // повернув би 400. is_onchain при цьому окремо каже правду про мережу.
    is_verified: true,
    is_onchain: nft.is_onchain,
    created_at: nft.created_at,
    attributes: {
      Location: String(attrs.Location ?? nft.location_name),
      Biome: String(attrs.Biome ?? 'common'),
      Rarity: String(attrs.Rarity ?? nft.rarity),
      Elevation_m: Number(attrs.Elevation_m ?? 0),
      Weather: String(attrs.Weather ?? 'clear'),
    },
  };
}

export interface MintPayload {
  activity_id: number;
  title: string;
  story_note?: string;
  original_photo_url: string;
  location_name: string;
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export const api = {
  /** Exchanges signed Telegram initData for a JWT. */
  async loginWithTelegram(): Promise<TokenResponse> {
    const initData = getInitData();
    if (!initData) throw new ApiError(400, 'Not running inside Telegram');

    const result = await request<TokenResponse>('/v1/auth/login', {
      method: 'POST',
      auth: false,
      body: { telegram_init_data: initData },
    });
    tokenStore.set(result.access_token);
    return result;
  },

  getMe: () => request<UserProfile>('/v1/users/me'),
  getMyGremlin: () => request<Gremlin>('/v1/gremlins/my'),

  feedGremlin: (foodType = 'energy_berry') =>
    request<Gremlin>('/v1/gremlins/feed', {
      method: 'POST',
      body: { food_type: foodType },
    }),

  evolveGremlin: () => request<Gremlin>('/v1/gremlins/evolve', { method: 'POST' }),

  syncActivity: (payload: ActivitySyncPayload) =>
    request<ActivitySyncResponse>('/v1/activities/sync', { method: 'POST', body: payload }),

  useStreakFreeze: () => request<UserProfile>('/v1/users/streak/freeze', { method: 'POST' }),

  updateWallet: (walletAddress: string) =>
    request<UserProfile>('/v1/users/wallet', {
      method: 'POST',
      body: { wallet_address: walletAddress },
    }),

  // Unlinking is its own verb. Posting an empty string to updateWallet fails
  // the address validator, so the disconnect button used to 422.
  unlinkWallet: () =>
    request<UserProfile>('/v1/users/wallet', { method: 'DELETE' }),

  mintNFT: (payload: MintPayload) =>
    request<NFTResponse>('/v1/marketplace/mint', { method: 'POST', body: payload }),

  exploreMarketplace: () =>
    request<NFTListingResponse[]>('/v1/marketplace/explore', { auth: false }),

  getRaidBoss: () => request<ClanRaidBoss | null>('/v1/quests/raid-boss', { auth: false }),

  getBrandQuests: () => request<BrandQuest[]>('/v1/quests/brand-bounties', { auth: false }),
};
