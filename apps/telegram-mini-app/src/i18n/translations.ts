export type Language = 'en' | 'uk' | 'pl' | 'de' | 'es';

export interface Translations {
  // Common & Nav
  appName: string;
  reputation: string;
  streakDays: string;
  stamina: string;
  connectWallet: string;
  connected: string;
  tabs: {
    gremlin: string;
    map: string;
    camera: string;
    market: string;
    raid: string;
    profile: string;
  };
  // Gremlin Companion
  gremlin: {
    tapToPet: string;
    xpProgress: string;
    health: string;
    hunger: string;
    mood: string;
    feedBtn: string;
    evolveBtn: string;
    simulateWalkTitle: string;
    simulateWalkDesc: string;
    walkBtn: string;
    biomes: {
      common: string;
      mountain_frost: string;
      forest_guardian: string;
      cyber_shadow: string;
      stormbringer: string;
      desert_solar: string;
    };
  };
  // Map
  map: {
    title: string;
    resolution: string;
    fogCleared: string;
    gpsVerified: string;
    sponsorBounty: string;
    distance: string;
  };
  // Camera
  camera: {
    hardwareAttested: string;
    synthesizingAI: string;
    applyingShaders: string;
    mintBtn: string;
    needActivity: string;
    attestationNotice: string;
  };
  // Market
  market: {
    albumTitle: string;
    albumDesc: string;
    verifiedCount: string;
    filters: {
      all: string;
      rare: string;
      epic: string;
      legendary: string;
    };
    buyBtn: string;
    notListed: string;
    closeBtn: string;
    solanaCnftBadge: string;
    assetId: string;
    elevationProof: string;
  };
  // Raid
  raid: {
    activeBoss: string;
    endsIn: string;
    worldTitan: string;
    remainingHp: string;
    totalPrizePool: string;
    attackBtn: string;
    sponsorQuests: string;
    goal: string;
    claimed: string;
  };
  // Profile
  profile: {
    telegramId: string;
    streakFreezeTitle: string;
    streakFreezeDesc: string;
    useFreezeBtn: string;
    securityTitle: string;
    safeZones: string;
    deviceIntegrity: string;
    mpcWallet: string;
    active: string;
    attested: string;
    language: string;
    shareAchievement: string;
  };
}

export const translations: Record<Language, Translations> = {
  en: {
    appName: "Gremlins Health",
    reputation: "Rep",
    streakDays: "d",
    stamina: "Stamina",
    connectWallet: "Wallet",
    connected: "Connected",
    tabs: {
      gremlin: "Gremlin",
      map: "Explore",
      camera: "Camera",
      market: "Market",
      raid: "Raid",
      profile: "Profile",
    },
    gremlin: {
      tapToPet: "Tap companion to pet & boost mood!",
      xpProgress: "XP Progress",
      health: "Health",
      hunger: "Hunger",
      mood: "Mood",
      feedBtn: "Feed (15 Stamina)",
      evolveBtn: "Evolve Companion",
      simulateWalkTitle: "Simulate Outdoor Trail",
      simulateWalkDesc: "+12,500 steps • 850m elevation gain",
      walkBtn: "Walk Trail",
      biomes: {
        common: "Common",
        mountain_frost: "Mountain Frost",
        forest_guardian: "Forest Guardian",
        cyber_shadow: "Cyber Shadow",
        stormbringer: "Stormbringer",
        desert_solar: "Desert Solar",
      }
    },
    map: {
      title: "Global Trail Matrix",
      resolution: "Uber H3 Hex Resolution: 9",
      fogCleared: "Fog Cleared",
      gpsVerified: "Live GPS Active",
      sponsorBounty: "Waypoint Bounty",
      distance: "Distance",
    },
    camera: {
      hardwareAttested: "Hardware Enclave Attested",
      synthesizingAI: "Synthesizing Trail Gremlin via FLUX.1 LoRA...",
      applyingShaders: "Applying elevation and outdoor shaders",
      mintBtn: "Mint Solana Compressed NFT ($0.00005)",
      needActivity: "Log a hike first — minting needs a verified activity.",
      attestationNotice: "Photos taken through in-app camera receive cryptographic hardware attestation to unlock Epic & Legendary cNFT minting.",
    },
    market: {
      albumTitle: "Global Trailblazer Passport",
      albumDesc: "Complete outdoor milestones to earn status & brand yield",
      verifiedCount: "3 / 6 Completed",
      filters: {
        all: "All",
        rare: "Rare",
        epic: "Epic",
        legendary: "Legendary",
      },
      buyBtn: "Buy for",
      notListed: "Not listed",
      closeBtn: "Close",
      solanaCnftBadge: "Solana Compressed NFT (Bubblegum)",
      assetId: "Asset ID",
      elevationProof: "Elevation Proof",
    },
    raid: {
      activeBoss: "Active Global Raid Boss",
      endsIn: "Ends in 5d 14h",
      worldTitan: "World Step Titan • Weakness: Mountain Frost",
      remainingHp: "Remaining HP",
      totalPrizePool: "Total Clan Prize Pool",
      attackBtn: "Attack (Deploy 5,000 Steps)",
      sponsorQuests: "Global Outdoor Sponsor Quests",
      goal: "Goal",
      claimed: "Claimed",
    },
    profile: {
      telegramId: "Telegram ID",
      streakFreezeTitle: "Streak Freeze Protection",
      streakFreezeDesc: "freeze shields available",
      useFreezeBtn: "Use Freeze",
      securityTitle: "Security & Privacy Protocol",
      safeZones: "Privacy Safe Zones (1km Home Redacted)",
      deviceIntegrity: "Apple / Google Play Hardware Integrity",
      mpcWallet: "Solana Connected Wallet",
      active: "Active",
      attested: "Attested",
      language: "Interface Language",
      shareAchievement: "Share Achievement",
    },
  },

  uk: {
    appName: "Gremlins Health",
    reputation: "Репутація",
    streakDays: "дн",
    stamina: "Витривалість",
    connectWallet: "Гаманець",
    connected: "Підключено",
    tabs: {
      gremlin: "Гремлін",
      map: "Карта",
      camera: "Камера",
      market: "Ринок",
      raid: "Рейд",
      profile: "Профіль",
    },
    gremlin: {
      tapToPet: "Торкніться супутника, щоб погладити та підняти настрій!",
      xpProgress: "Прогрес досвіду XP",
      health: "Здоров'я",
      hunger: "Голод",
      mood: "Настрій",
      feedBtn: "Годувати (15 Стаміни)",
      evolveBtn: "Еволюціонувати",
      simulateWalkTitle: "Симулювати трейл-прогулянку",
      simulateWalkDesc: "+12,500 кроків • 850м підйом",
      walkBtn: "Пройти трейл",
      biomes: {
        common: "Звичайний",
        mountain_frost: "Крижані Гори",
        forest_guardian: "Охоронець Лісу",
        cyber_shadow: "Кібер Тінь",
        stormbringer: "Володар Шторму",
        desert_solar: "Сонячна Пустеля",
      }
    },
    map: {
      title: "Глобальна Матриця Трейлів",
      resolution: "Гексагональна сітка Uber H3: 9",
      fogCleared: "Відкрито туману",
      gpsVerified: "Live GPS Активний",
      sponsorBounty: "Нагорода точки",
      distance: "Дистанція",
    },
    camera: {
      hardwareAttested: "Апаратний анклав підтверджено",
      synthesizingAI: "Генерація Гремліна через FLUX.1 LoRA...",
      applyingShaders: "Накладання шейдерів рельєфу та висоти",
      mintBtn: "Мінтувати Solana Compressed NFT ($0.00005)",
      needActivity: "Спершу зарахуйте похід — мінт потребує верифікованої активності.",
      attestationNotice: "Знімки через захищену камеру отримують криптографічний підпис заліза для відкриття мінту Epic та Legendary cNFT.",
    },
    market: {
      albumTitle: "Глобальний Паспорт Мандрівника",
      albumDesc: "Виконуйте досягнення на трейлах для отримання нагород",
      verifiedCount: "3 / 6 Виконано",
      filters: {
        all: "Всі",
        rare: "Rare",
        epic: "Epic",
        legendary: "Legendary",
      },
      buyBtn: "Купити за",
      notListed: "Не виставлено",
      closeBtn: "Закрити",
      solanaCnftBadge: "Solana Compressed NFT (Bubblegum)",
      assetId: "Asset ID",
      elevationProof: "Доказ висоти",
    },
    raid: {
      activeBoss: "Активний Глобальний Рейд-Бос",
      endsIn: "Залишилось 5д 14г",
      worldTitan: "Титан Трейлів • Вразливість: Крижані Гори",
      remainingHp: "Залишок HP",
      totalPrizePool: "Загальний пул клану",
      attackBtn: "Атакувати (5,000 кроків)",
      sponsorQuests: "Світові Брендові Челенджі",
      goal: "Ціль",
      claimed: "Виконано",
    },
    profile: {
      telegramId: "Telegram ID",
      streakFreezeTitle: "Захист серії (Streak Freeze)",
      streakFreezeDesc: "захисних щитів доступно",
      useFreezeBtn: "Застосувати",
      securityTitle: "Протокол Безпеки та Приватності",
      safeZones: "Зони приватності (1км біля дому приховано)",
      deviceIntegrity: "Апаратна цілісність Apple / Google Play",
      mpcWallet: "Підключений Solana Гаманець",
      active: "Активно",
      attested: "Підтверджено",
      language: "Мова інтерфейсу",
      shareAchievement: "Поділитися досягненням",
    },
  },

  pl: {
    appName: "Gremlins Health",
    reputation: "Reputacja",
    streakDays: "d",
    stamina: "Wytrzymałość",
    connectWallet: "Portfel",
    connected: "Połączono",
    tabs: {
      gremlin: "Gremlin",
      map: "Odkrywaj",
      camera: "Aparat",
      market: "Rynek",
      raid: "Rajd",
      profile: "Profil",
    },
    gremlin: {
      tapToPet: "Dotknij towarzysza, aby poprawić mu humor!",
      xpProgress: "Postęp XP",
      health: "Zdrowie",
      hunger: "Głód",
      mood: "Nastrój",
      feedBtn: "Nakarm (15 Energii)",
      evolveBtn: "Ewoluuj Towarzysza",
      simulateWalkTitle: "Symuluj szlak outdoor",
      simulateWalkDesc: "+12,500 kroków • 850m przewyższenia",
      walkBtn: "Przejdź Szlak",
      biomes: {
        common: "Zwykły",
        mountain_frost: "Mroźne Góry",
        forest_guardian: "Strażnik Lasu",
        cyber_shadow: "Cyfrowy Cień",
        stormbringer: "Władca Burzy",
        desert_solar: "Słoneczna Pustynia",
      }
    },
    map: {
      title: "Globalna Matryca Szlaków",
      resolution: "Siatka Uber H3: 9",
      fogCleared: "Odkryto mgły",
      gpsVerified: "Live GPS Aktywny",
      sponsorBounty: "Nagroda Punktu",
      distance: "Dystans",
    },
    camera: {
      hardwareAttested: "Sprzętowo Poświadczone",
      synthesizingAI: "Generowanie Gremlina przez FLUX.1 LoRA...",
      applyingShaders: "Nakładanie efektów wysokości",
      mintBtn: "Wybij Solana Compressed NFT ($0.00005)",
      needActivity: "Najpierw zalicz wędrówkę — mint wymaga zweryfikowanej aktywności.",
      attestationNotice: "Zdjęcia wykonane w aplikacji otrzymują podpis kryptograficzny umożliwiający wybijanie NFT Epic i Legendary.",
    },
    market: {
      albumTitle: "Globalny Paszport Odkrywcy",
      albumDesc: "Zdobywaj osiągnięcia, aby zdobywać nagrody kwartalne",
      verifiedCount: "3 / 6 Wykonano",
      filters: {
        all: "Wszystkie",
        rare: "Rare",
        epic: "Epic",
        legendary: "Legendary",
      },
      buyBtn: "Kup za",
      notListed: "Nie wystawiono",
      closeBtn: "Zamknij",
      solanaCnftBadge: "Solana Compressed NFT (Bubblegum)",
      assetId: "ID Aktywa",
      elevationProof: "Dowód Wysokości",
    },
    raid: {
      activeBoss: "Globalny Boss Rajdu",
      endsIn: "Koniec za 5d 14h",
      worldTitan: "Tytan Szlaków • Słabość: Mroźne Góry",
      remainingHp: "Pozostałe HP",
      totalPrizePool: "Pula Klanowa",
      attackBtn: "Atakuj (5,000 Kroków)",
      sponsorQuests: "Wyzwania Globalnych Sponsorów",
      goal: "Cel",
      claimed: "Odebrano",
    },
    profile: {
      telegramId: "Telegram ID",
      streakFreezeTitle: "Ochrona Serii (Streak Freeze)",
      streakFreezeDesc: "dostępne tarcze ochronne",
      useFreezeBtn: "Użyj Tarczy",
      securityTitle: "Protokół Bezpieczeństwa i Prywatności",
      safeZones: "Strefy Bezpieczne (1km wokół domu ukryte)",
      deviceIntegrity: "Integralność Apple / Google Play",
      mpcWallet: "Połączony Portfel Solana",
      active: "Aktywny",
      attested: "Poświadczony",
      language: "Język interfejsu",
      shareAchievement: "Udostępnij osiągnięcie",
    },
  },

  de: {
    appName: "Gremlins Health",
    reputation: "Reputation",
    streakDays: "T",
    stamina: "Ausdauer",
    connectWallet: "Wallet",
    connected: "Verbunden",
    tabs: {
      gremlin: "Gremlin",
      map: "Entdecken",
      camera: "Kamera",
      market: "Markt",
      raid: "Raid",
      profile: "Profil",
    },
    gremlin: {
      tapToPet: "Begleiter streicheln für bessere Laune!",
      xpProgress: "XP Fortschritt",
      health: "Gesundheit",
      hunger: "Hunger",
      mood: "Laune",
      feedBtn: "Füttern (15 Ausdauer)",
      evolveBtn: "Begleiter Entwickeln",
      simulateWalkTitle: "Outdoor-Pfad Simulieren",
      simulateWalkDesc: "+12.500 Schritte • 850m Höhengewinn",
      walkBtn: "Pfad Gehen",
      biomes: {
        common: "Gewöhnlich",
        mountain_frost: "Bergfrost",
        forest_guardian: "Waldwächter",
        cyber_shadow: "Kyberschatten",
        stormbringer: "Sturmbringer",
        desert_solar: "Sonnige Wüste",
      }
    },
    map: {
      title: "Globale Pfad-Matrix",
      resolution: "Uber H3 Hex Auflösung: 9",
      fogCleared: "Nebel Gelichtet",
      gpsVerified: "Live GPS Aktiv",
      sponsorBounty: "Wegpunkt-Prämie",
      distance: "Distanz",
    },
    camera: {
      hardwareAttested: "Hardware Enclave Bestätigt",
      synthesizingAI: "Erstelle Gremlin via FLUX.1 LoRA...",
      applyingShaders: "Höhen- und Umgebungseffekte anwenden",
      mintBtn: "Solana Compressed NFT Prägen ($0.00005)",
      needActivity: "Erfasse zuerst eine Wanderung — Minten braucht eine verifizierte Aktivität.",
      attestationNotice: "In-App Fotos erhalten eine kryptografische Signatur für Epic & Legendary cNFTs.",
    },
    market: {
      albumTitle: "Globaler Entdecker-Pass",
      albumDesc: "Erreiche Meilensteine für Belohnungen",
      verifiedCount: "3 / 6 Abgeschlossen",
      filters: {
        all: "Alle",
        rare: "Rare",
        epic: "Epic",
        legendary: "Legendary",
      },
      buyBtn: "Kaufen für",
      notListed: "Nicht gelistet",
      closeBtn: "Schließen",
      solanaCnftBadge: "Solana Compressed NFT (Bubblegum)",
      assetId: "Asset ID",
      elevationProof: "Höhennachweis",
    },
    raid: {
      activeBoss: "Aktiver Globaler Raid Boss",
      endsIn: "Endet in 5T 14Std",
      worldTitan: "Schritte-Titan • Schwäche: Bergfrost",
      remainingHp: "Verbleibende HP",
      totalPrizePool: "Clan-Belohnungspool",
      attackBtn: "Angreifen (5.000 Schritte)",
      sponsorQuests: "Globale Sponsoren Quests",
      goal: "Ziel",
      claimed: "Eingelöst",
    },
    profile: {
      telegramId: "Telegram ID",
      streakFreezeTitle: "Serien-Schutz (Streak Freeze)",
      streakFreezeDesc: "Schutzschilde verfügbar",
      useFreezeBtn: "Schutz Aktivieren",
      securityTitle: "Sicherheits- & Datenschutzprotokoll",
      safeZones: "Privatzonen (1km um Wohnort maskiert)",
      deviceIntegrity: "Apple / Google Play Hardware-Integrität",
      mpcWallet: "Verbundene Solana Wallet",
      active: "Aktiv",
      attested: "Bestätigt",
      language: "Sprache",
      shareAchievement: "Erfolg teilen",
    },
  },

  es: {
    appName: "Gremlins Health",
    reputation: "Reputación",
    streakDays: "d",
    stamina: "Resistencia",
    connectWallet: "Billetera",
    connected: "Conectado",
    tabs: {
      gremlin: "Gremlin",
      map: "Explorar",
      camera: "Cámara",
      market: "Mercado",
      raid: "Incursión",
      profile: "Perfil",
    },
    gremlin: {
      tapToPet: "¡Toca para acariciar y mejorar su ánimo!",
      xpProgress: "Progreso de XP",
      health: "Salud",
      hunger: "Hambre",
      mood: "Ánimo",
      feedBtn: "Alimentar (15 Energía)",
      evolveBtn: "Evolucionar Compañero",
      simulateWalkTitle: "Simular Sendero Outdoor",
      simulateWalkDesc: "+12,500 pasos • 850m elevación",
      walkBtn: "Caminar Sendero",
      biomes: {
        common: "Común",
        mountain_frost: "Escarcha de Montaña",
        forest_guardian: "Guardián del Bosque",
        cyber_shadow: "Sombra Cibernética",
        stormbringer: "Portador de Tormentas",
        desert_solar: "Desierto Solar",
      }
    },
    map: {
      title: "Matriz Global de Senderos",
      resolution: "Resolución Hex Uber H3: 9",
      fogCleared: "Niebla Despejada",
      gpsVerified: "Live GPS Activo",
      sponsorBounty: "Recompensa de Punto",
      distance: "Distancia",
    },
    camera: {
      hardwareAttested: "Atestiguado por Hardware",
      synthesizingAI: "Sintetizando Gremlin con FLUX.1 LoRA...",
      applyingShaders: "Aplicando efectos de altura y entorno",
      mintBtn: "Mintear Solana Compressed NFT ($0.00005)",
      needActivity: "Registra primero una caminata: el minteo requiere una actividad verificada.",
      attestationNotice: "Las fotos en la app reciben certificación criptográfica para desbloquear cNFTs Épicos y Legendarios.",
    },
    market: {
      albumTitle: "Pasaporte Global de Explorador",
      albumDesc: "Completa hitos para ganar recompensas",
      verifiedCount: "3 / 6 Completado",
      filters: {
        all: "Todos",
        rare: "Rare",
        epic: "Epic",
        legendary: "Legendary",
      },
      buyBtn: "Comprar por",
      notListed: "No listado",
      closeBtn: "Cerrar",
      solanaCnftBadge: "Solana Compressed NFT (Bubblegum)",
      assetId: "ID de Activo",
      elevationProof: "Prueba de Elevación",
    },
    raid: {
      activeBoss: "Jefe de Incursión Global",
      endsIn: "Termina en 5d 14h",
      worldTitan: "Titán de Pasos • Debilidad: Escarcha",
      remainingHp: "HP Restante",
      totalPrizePool: "Pozo del Clan",
      attackBtn: "Atacar (5,000 Pasos)",
      sponsorQuests: "Misiones Patrocinadas Globales",
      goal: "Meta",
      claimed: "Reclamado",
    },
    profile: {
      telegramId: "Telegram ID",
      streakFreezeTitle: "Protección de Racha (Streak Freeze)",
      streakFreezeDesc: "escudos de protección disponibles",
      useFreezeBtn: "Usar Escudo",
      securityTitle: "Protocolo de Seguridad y Privacidad",
      safeZones: "Zonas Seguras (1km alrededor de casa oculto)",
      deviceIntegrity: "Integridad de Hardware Apple / Google",
      mpcWallet: "Billetera Solana Conectada",
      active: "Activo",
      attested: "Certificado",
      language: "Idioma",
      shareAchievement: "Compartir logro",
    },
  }
};
