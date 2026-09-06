/**
 * Gremlins Health — Telegram WebApp SDK Bridge
 * Derived from production-tested sibling architecture.
 */

type ThemeParams = Record<string, string>;

interface TelegramWebApp {
  initData: string;
  initDataUnsafe?: {
    user?: { id: number; first_name?: string; username?: string; language_code?: string };
    start_param?: string;
  };
  themeParams?: ThemeParams;
  colorScheme?: 'light' | 'dark';
  ready(): void;
  expand(): void;
  close(): void;
  setHeaderColor(color: string): void;
  setBackgroundColor(color: string): void;
  enableClosingConfirmation?(): void;
  openTelegramLink(url: string): void;
  showAlert?(message: string, callback?: () => void): void;
  openLink?(url: string, options?: { try_instant_view?: boolean }): void;
  onEvent(event: string, handler: () => void): void;
  offEvent(event: string, handler: () => void): void;
  HapticFeedback?: {
    impactOccurred(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): void;
    notificationOccurred(type: 'error' | 'success' | 'warning'): void;
    selectionChanged(): void;
  };
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

export const tg = (): TelegramWebApp | undefined => window.Telegram?.WebApp;

export const isStandalone = (): boolean => !tg()?.initData;

export function getInitData(): string {
  return tg()?.initData ?? '';
}

export function getUserName(): string {
  return tg()?.initDataUnsafe?.user?.first_name ?? '';
}

export const APP_BG_COLOR = '#0B0F17';

/**
 * Initializes Telegram Mini App environment:
 * Expands window to full height, sets dark header and background colors,
 * and enables exit confirmation.
 */
export function initTelegram(): () => void {
  const app = tg();
  if (!app) return () => {};

  app.ready();
  app.expand();
  app.setHeaderColor(APP_BG_COLOR);
  app.setBackgroundColor(APP_BG_COLOR);
  
  if (app.enableClosingConfirmation) {
    app.enableClosingConfirmation();
  }

  return () => {};
}

/**
 * Native mobile haptic feedback.
 */
export function haptic(type: 'success' | 'error' | 'warning' | 'tap' | 'heavy' | 'selection'): void {
  const hf = tg()?.HapticFeedback;
  if (!hf) return;

  switch (type) {
    case 'tap':
      hf.impactOccurred('light');
      break;
    case 'heavy':
      hf.impactOccurred('heavy');
      break;
    case 'selection':
      hf.selectionChanged();
      break;
    case 'success':
    case 'error':
    case 'warning':
      hf.notificationOccurred(type);
      break;
  }
}

/**
 * Native Telegram alert.
 *
 * window.alert() blocks the WebView thread and freezes the Mini App, so it is
 * only used when Telegram's own dialog is unavailable (plain browser).
 */
export function showAlert(message: string): void {
  const app = tg();
  if (app?.showAlert) {
    app.showAlert(message);
    return;
  }
  // eslint-disable-next-line no-alert
  window.alert(message);
}

export function openBotChat(startParam = ''): void {
  const username = 'GremlinsHealthBot';
  const url = `https://t.me/${username}${startParam ? `?start=${startParam}` : ''}`;
  openExternal(url);
}

export function openExternal(url: string): void {
  const app = tg();
  if (url.startsWith('https://t.me/') && app?.openTelegramLink) {
    app.openTelegramLink(url);
    return;
  }
  if (app?.openLink) {
    app.openLink(url, { try_instant_view: false });
    return;
  }
  window.open(url, '_blank', 'noopener,noreferrer');
}

export function telegramShareHref(url: string, text: string): string {
  return `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
}

export function shareTelegramUrl(url: string, text: string): void {
  const href = telegramShareHref(url, text);
  const app = tg();
  if (app) app.openTelegramLink(href);
  else window.open(href, '_blank');
}
