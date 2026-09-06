import logging
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

logger = logging.getLogger(__name__)
router = Router()

COMMUNITY_URL = "https://t.me/gremlins_health"


def build_start_keyboard(web_app_url: str, open_label: str, help_label: str, community_label: str):
    rows = []
    notice = None

    if web_app_url.startswith("https://"):
        rows.append([
            InlineKeyboardButton(text=open_label, web_app=WebAppInfo(url=web_app_url))
        ])
    else:
        logger.warning(
            "TELEGRAM_WEBAPP_URL is %r, not HTTPS - the Mini App button is "
            "omitted from /start because Telegram would reject it.",
            web_app_url,
        )
        notice = (
            "\n\n⚠️ <b>Development mode</b>\n"
            f"TELEGRAM_WEBAPP_URL is <code>{web_app_url}</code>. Telegram only "
            "accepts HTTPS for Mini App buttons, so the launch button is hidden.\n"
            "Expose the dev server over HTTPS (for example "
            "<code>cloudflared tunnel --url http://localhost:5173</code>) and set "
            "the resulting URL in <code>backend/.env</code>."
        )

    rows.append([
        InlineKeyboardButton(text=help_label, callback_data="help_main"),
        InlineKeyboardButton(text=community_label, url=COMMUNITY_URL),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows), notice


def build_help_keyboard(lang: str, web_app_url: str):
    is_uk = lang == "uk"
    rows = [
        [
            InlineKeyboardButton(
                text="🐾 " + ("Гремліни та Догляд" if is_uk else "Gremlins & Care"),
                callback_data="help_gremlin",
            ),
            InlineKeyboardButton(
                text="🏔️ " + ("Карта та Вершини" if is_uk else "Map & Summits"),
                callback_data="help_map",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📸 " + ("Камера та cNFT" if is_uk else "Camera & cNFT"),
                callback_data="help_camera",
            ),
            InlineKeyboardButton(
                text="⚔️ " + ("Рейд-боси та Клани" if is_uk else "Raid Bosses & Clans"),
                callback_data="help_raid",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🛡️ " + ("Античит та Безпека" if is_uk else "Anticheat & Security"),
                callback_data="help_security",
            ),
            InlineKeyboardButton(
                text="💎 " + ("Solana Гаманець" if is_uk else "Solana Wallet"),
                callback_data="help_wallet",
            ),
        ],
    ]

    if web_app_url.startswith("https://"):
        rows.append([
            InlineKeyboardButton(
                text="🎮 " + ("Відкрити гру" if is_uk else "Open Game App"),
                web_app=WebAppInfo(url=web_app_url),
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_back_keyboard(lang: str, web_app_url: str):
    is_uk = lang == "uk"
    rows = [
        [
            InlineKeyboardButton(
                text="↩️ " + ("Назад до довідки" if is_uk else "Back to Help"),
                callback_data="help_main",
            )
        ]
    ]
    if web_app_url.startswith("https://"):
        rows.append([
            InlineKeyboardButton(
                text="🎮 " + ("Відкрити гру" if is_uk else "Open Game App"),
                web_app=WebAppInfo(url=web_app_url),
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


MESSAGES = {
    "uk": {
        "welcome": (
            "🌲 <b>Ласкаво просимо до GREMLINS HEALTH 2.0!</b>\n\n"
            "Перетворюйте свої реальні щоденні кроки та гірські походи на живих цифрових "
            "<b>Гремлінів-супутників (Solana cNFT)</b> за концепцією <i>Proof-of-Adventure</i>.\n\n"
            "🐾 <b>Ваші можливості:</b>\n"
            "• 🏃 <b>Ходіть та досліджуйте:</b> заробляйте Stamina та розвивайте свого Тамагочі-Гремліна\n"
            "• 🗺️ <b>Відкривайте карту Карпат:</b> розвіюйте туман війни на реальних вершинах\n"
            "• 📸 <b>Робіть захищені фото:</b> апаратна верифікація та мінт унікальних cNFT\n"
            "• ⚔️ <b>Боріться з рейд-босами:</b> об'єднуйтесь у клани за призовий пул токенів $GRLN\n\n"
            "<i>Оберіть дію нижче або натисніть «Довідка» для повного гіда по грі:</i>"
        ),
        "open_app_btn": "🎮 Відкрити Gremlins App",
        "help_btn": "📖 Довідка та Гід",
        "community_btn": "💬 Спільнота",
        "help_main": (
            "📚 <b>База знань та Довідка Gremlins Health 2.0</b>\n\n"
            "Оберіть тему, яка вас цікавить, щоб дізнатися всі подробиці гри та механік:\n\n"
            "• 🐾 <b>Гремліни та Догляд:</b> показники HP/Голод/Настрій, еволюція та біоми\n"
            "• 🏔️ <b>Карта та Вершини:</b> туман війни, сітка H3, Говерла, Петрос, Піп Іван\n"
            "• 📸 <b>Камера та cNFT:</b> апаратний анклав, AI-арт FLUX.1 LoRA, мінт Solana\n"
            "• ⚔️ <b>Рейд-боси:</b> глобальні боси, спільні атаки кроками, $GRLN та квести\n"
            "• 🛡️ <b>Античит та Безпека:</b> перевірка каденсу, приватні зони біля дому\n"
            "• 💎 <b>Solana Гаманець:</b> вбудований MPC гаманець, токеноміка $GRLN"
        ),
        "help_gremlin": (
            "🐾 <b>Гремліни та Догляд за Супутником</b>\n\n"
            "Гремлін — ваш персональний віртуальний супутник, який росте разом із вашою активністю:\n\n"
            "• ❤️ <b>Здоров'я (HP):</b> підтримується регулярною активністю та щоденними прогулянками.\n"
            "• 🍖 <b>Голод (Hunger):</b> зростає з часом. Годування коштує 15 Стаміни (заробляється кроками).\n"
            "• ✨ <b>Настрій (Mood):</b> покращується від погладжувань та подолання гірських трейлів.\n"
            "• 🧬 <b>Рівні та Еволюція:</b> досягнувши ліміту XP, еволюціонуйте Гремліна! "
            "На рівні 2 з'являються кришталеві роги, на рівні 3+ — величні магічні крила.\n\n"
            "❄️ <b>Біоми та Адаптація:</b>\n"
            "- <i>Крижані Гори (Mountain Frost):</i> розвивається на висотах понад 1,500м.\n"
            "- <i>Володар Шторму (Stormbringer):</i> активується під час дощу та вітряної погоди.\n"
            "- <i>Охоронець Лісу (Forest Guardian):</i> розвивається в густих лісових масивах.\n"
            "- <i>Кібер Тінь (Cyber Shadow):</i> адаптація для нічних міських прогулянок."
        ),
        "help_map": (
            "🏔️ <b>Глобальна Карта та Туман Війни (Fog of War)</b>\n\n"
            "Додаток працює в будь-якій точці планети — у вашому місті, парку, лісі чи на гірських хребтах:\n\n"
            "• 🌐 <b>Гексагональна сітка Uber H3 (Res 9):</b> весь світ розбито на гексагони ~100м. "
            "Кожен ваш реальний крок на свіжому повітрі назавжди розсіює туман навколо вас.\n"
            "• 📍 <b>Live GPS та Трекінг:</b> додаток автоматично центруються на ваших реальних координатах, "
            "визначає висоту, швидкість пересування та малює маршрут активності.\n"
            "• 🎯 <b>Локальні точки та Вершини:</b> система динамічно генерує найближчі чекпоїнти (вершини, трейли, схованки), "
            "вираховує точну відстань до них та нараховує нагороди за їх дослідження."
        ),
        "help_camera": (
            "📸 <b>Захищена Камера та Solana cNFT</b>\n\n"
            "Створюйте неповторні цифрові реліквії ваших реальних подорожей:\n\n"
            "• 🛡️ <b>Hardware Enclave Attestation:</b> камера здійснює захищений знімок із перевіркою апаратних сенсорів (GPS, гіроскоп, висотомір), що гарантує 100% справжність фото.\n"
            "• 🎨 <b>FLUX.1 LoRA AI-Synthesis:</b> нейромережа комбінує ваше фото гори з параметрами вашого Гремліна, накладаючи снігові та висотні шейдери.\n"
            "• ⚡ <b>Solana Compressed NFT (Bubblegum):</b> мінт коштує всього $0.00005 завдяки технології стиснення стану на блокчейні Solana. Ваші cNFT зберігаються у вашому гаманці та можуть продаватися на маркетплейсі."
        ),
        "help_raid": (
            "⚔️ <b>Кланові Рейд-Боси та Брендові Квести</b>\n\n"
            "Об'єднуйте зусилля з іншими мандрівниками для перемоги над титанами:\n\n"
            "• 🌋 <b>Світовий Бос (World Step Titan):</b> бос має величезний запас здоров'я у кроках (наприклад, 2,000,000 кроків). Кожен гравець клану спрямовує свої кроки на атаку боса.\n"
            "• 💰 <b>Розподіл пулу $GRLN:</b> після перемоги над босом токенний фонд пропорційно ділиться між учасниками рейду відповідно до їхнього внеску.\n"
            "• 🎁 <b>Спонсорські челенджі:</b> виконуйте тематичні походи від outdoor-брендів та вигравайте пули нагород у USDC та ексклюзивний мерч."
        ),
        "help_security": (
            "🛡️ <b>Античит та Захист Приватності</b>\n\n"
            "Gremlins Health розроблено для чесних спортсменів та мандрівників:\n\n"
            "• 🛑 <b>Багаторівневий Античит:</b>\n"
            "  - <i>Micro-cadence variance:</i> алгоритм відрізняє природний біомеханічний крок людини від шейкерів і маятників.\n"
            "  - <i>Обмеження швидкості:</i> швидкість понад 15 км/год під час ходьби або вертикальний набір понад 1,200 м/год маркується як поїздка на транспорті.\n"
            "  - <i>Апаратна цілісність:</i> захист від емуляторів та підроблених GPS-координат.\n"
            "• 🔒 <b>Privacy Safe Zones:</b> радіус 1 км навколо вашого дому автоматично маскується, гарантуючи повну приватність вашого проживання."
        ),
        "help_wallet": (
            "💎 <b>Підключення Solana Гаманця та Токеноміка</b>\n\n"
            "Ви можете підключити будь-який зручний для вас гаманець Solana:\n\n"
            "• 🟣 <b>Phantom Wallet:</b> підключення через додаток або введення адреси.\n"
            "• 🔥 <b>Solflare Wallet:</b> підтримка мобільного та десктопного гаманця.\n"
            "• 🎒 <b>Backpack Wallet:</b> швидка інтеграція.\n"
            "• 🤖 <b>Telegram Session MPC Vault:</b> автоматичний гаманець для швидкого старту без налаштувань.\n"
            "• ✍️ <b>Власна Solana адреса:</b> введіть або вставте будь-яку свою публічну адресу Solana (Base58).\n\n"
            "<i>Щоб підключити гаманець: відкрийте додаток, перейдіть у «Профіль» або натисніть кнопку «Гаманець» у верхньому меню!</i>"
        ),
    },
    "en": {
        "welcome": (
            "🌲 <b>Welcome to GREMLINS HEALTH 2.0!</b>\n\n"
            "Turn your real physical steps and mountain hiking into living, evolving "
            "<b>Gremlin Companions (Solana cNFT)</b> powered by <i>Proof-of-Adventure</i>.\n\n"
            "🐾 <b>Your Journey Starts Now:</b>\n"
            "• 🏃 <b>Walk & Explore:</b> earn stamina and nurture your Tamagotchi Gremlin\n"
            "• 🗺️ <b>Clear Carpathian Map:</b> lift the Fog of War across mountain trails\n"
            "• 📸 <b>Capture Verified Photos:</b> hardware enclave attestation & cNFT minting\n"
            "• ⚔️ <b>Battle Raid Bosses:</b> unite in clans for massive $GRLN token prize pools\n\n"
            "<i>Select an action below or tap «Help & Guide» for full documentation:</i>"
        ),
        "open_app_btn": "🎮 Open Gremlins App",
        "help_btn": "📖 Help & Guide",
        "community_btn": "💬 Community",
        "help_main": (
            "📚 <b>Gremlins Health 2.0 Knowledge Base & Guide</b>\n\n"
            "Select a topic below to explore game mechanics, proof of adventure, and features:\n\n"
            "• 🐾 <b>Gremlins & Care:</b> HP/Hunger/Mood stats, evolution & biomes\n"
            "• 🏔️ <b>Map & Summits:</b> fog of war, H3 grid, Hoverla, Petros, Pip Ivan\n"
            "• 📸 <b>Camera & cNFT:</b> hardware enclave, FLUX.1 LoRA AI art, Solana mint\n"
            "• ⚔️ <b>Raid Bosses:</b> world step titans, clan raids, $GRLN rewards & quests\n"
            "• 🛡️ <b>Anticheat & Security:</b> micro-cadence verification, safe zones\n"
            "• 💎 <b>Solana Wallet:</b> embedded MPC wallet, zero gas cNFTs"
        ),
        "help_gremlin": (
            "🐾 <b>Gremlin Companion & Tamagotchi Care</b>\n\n"
            "Your Gremlin is an evolving digital creature tied directly to your physical movement:\n\n"
            "• ❤️ <b>Health (HP):</b> maintained through consistent daily step activity.\n"
            "• 🍖 <b>Hunger:</b> increases over time. Feeding costs 15 Stamina (earned via walking).\n"
            "• ✨ <b>Mood:</b> boosted by petting and conquering mountain trails.\n"
            "• 🧬 <b>Leveling & Evolution:</b> earn XP on trails to evolve your companion. "
            "Level 2 unlocks frost horns; Level 3+ manifests mythical crystal wings!\n\n"
            "❄️ <b>Biome Affinities:</b>\n"
            "- <i>Mountain Frost:</i> blooms above 1,500m elevation in snowy alpine conditions.\n"
            "- <i>Stormbringer:</i> awakens in rainy, high-wind mountain ridge weather.\n"
            "- <i>Forest Guardian:</i> thrives in deep pine woodlands and lush valleys.\n"
            "- <i>Cyber Shadow:</i> urban trail specialist for night hiking."
        ),
        "help_map": (
            "🏔️ <b>Trail Matrix & Fog of War</b>\n\n"
            "The world map is blanketed in mystery. Real movement unlocks it permanently:\n\n"
            "• 🌐 <b>Uber H3 Hex Resolution 9:</b> the globe is divided into ~100m hex tiles. "
            "Visiting new terrain clears the fog on your personal adventure map.\n"
            "• 🏔️ <b>Carpathian Peaks:</b>\n"
            "  1. <i>Mount Hoverla (2,061 m)</i> — Salomon Frost cNFT Drop\n"
            "  2. <i>Mount Petros (2,020 m)</i> — Petros Storm Rune\n"
            "  3. <i>Pip Ivan (2,028 m)</i> — White Elephant Armor\n"
            "  4. <i>Mount Rebra (2,001 m)</i> — Highland Essence\n"
            "  5. <i>Gutyn Tomnatyk (2,016 m)</i> — Glacial Shard\n"
            "  6. <i>Lake Nesamovyte (1,750 m)</i> — Stormbringer Seed\n\n"
            "📍 <b>Real GPS:</b> Live device GPS coordinates verify altitude gain and trail completion."
        ),
        "help_camera": (
            "📸 <b>Secure Camera & Solana cNFT Minting</b>\n\n"
            "Transform trail moments into verified digital collectibles:\n\n"
            "• 🛡️ <b>Hardware Enclave Attestation:</b> in-app camera samples hardware sensors (GPS, barometer, IMU) to cryptographically attest you were physically present.\n"
            "• 🎨 <b>FLUX.1 LoRA AI Synthesis:</b> fuses your summit photograph with your Gremlin's visual traits and environmental telemetry.\n"
            "• ⚡ <b>Solana Compressed NFT (Bubblegum):</b> mints on Solana for $0.00005, preserving your proof of adventure forever on-chain."
        ),
        "help_raid": (
            "⚔️ <b>Clan Raid Bosses & Brand Quests</b>\n\n"
            "Team up with fellow adventurers to conquer colossal world step titans:\n\n"
            "• 🌋 <b>World Step Titan:</b> bosses possess millions of HP. Clan members deploy verified steps to inflict damage.\n"
            "• 💰 <b>$GRLN Prize Pool:</b> upon defeating the boss, the reward pool distributes proportionally based on verified step contributions.\n"
            "• 🎁 <b>B2B Brand Quests:</b> complete brand challenges (Salomon, outdoor sponsors) for USDC prize pools and limited gear."
        ),
        "help_security": (
            "🛡️ <b>Anticheat & Privacy Protocols</b>\n\n"
            "Engineered to reward authentic physical effort:\n\n"
            "• 🛑 <b>Multi-Layer Anticheat:</b>\n"
            "  - <i>Micro-cadence variance:</i> detects step irregularities to reject mechanical step shakers.\n"
            "  - <i>Speed and climb caps:</i> speeds >15 km/h or ascent rates >1,200 m/h flag vehicle usage.\n"
            "  - <i>Device integrity:</i> rejects emulators and mock GPS providers.\n"
            "• 🔒 <b>Privacy Safe Zones:</b> a 1km perimeter around your home is automatically redacted from public heatmaps."
        ),
        "help_wallet": (
            "💎 <b>Solana MPC Wallet & $GRLN Economy</b>\n\n"
            "Seamless Web3 onboarding without seed phrase anxiety:\n\n"
            "• 🔐 <b>Embedded MPC Wallet:</b> generated directly for your Telegram session via threshold cryptography.\n"
            "• 🪙 <b>$GRLN Token:</b> primary in-game utility token for companion evolution, biome breeding, and marketplace trading.\n"
            "• 🚀 <b>Zero Gas Friction:</b> Solana cNFT architecture eliminates gas fees for end users."
        ),
    },
}


def get_lang(user_lang: str | None) -> str:
    if user_lang and user_lang.startswith("uk"):
        return "uk"
    return "en"


@router.message(CommandStart())
async def cmd_start(message: Message, web_app_url: str):
    lang = get_lang(message.from_user.language_code if message.from_user else None)
    t = MESSAGES[lang]

    keyboard, dev_notice = build_start_keyboard(
        web_app_url, t["open_app_btn"], t["help_btn"], t["community_btn"]
    )

    await message.answer(
        t["welcome"] + (dev_notice or ""),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message, web_app_url: str):
    lang = get_lang(message.from_user.language_code if message.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_help_keyboard(lang, web_app_url)
    await message.answer(t["help_main"], reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("gremlin"))
async def cmd_gremlin(message: Message, web_app_url: str):
    lang = get_lang(message.from_user.language_code if message.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    await message.answer(t["help_gremlin"], reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("map"))
async def cmd_map(message: Message, web_app_url: str):
    lang = get_lang(message.from_user.language_code if message.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    await message.answer(t["help_map"], reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("camera"))
async def cmd_camera(message: Message, web_app_url: str):
    lang = get_lang(message.from_user.language_code if message.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    await message.answer(t["help_camera"], reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("raid"))
async def cmd_raid(message: Message, web_app_url: str):
    lang = get_lang(message.from_user.language_code if message.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    await message.answer(t["help_raid"], reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("security"))
async def cmd_security(message: Message, web_app_url: str):
    lang = get_lang(message.from_user.language_code if message.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    await message.answer(t["help_security"], reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("wallet"))
async def cmd_wallet(message: Message, web_app_url: str):
    lang = get_lang(message.from_user.language_code if message.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    await message.answer(t["help_wallet"], reply_markup=keyboard, parse_mode="HTML")


# --------------------------------------------------------------------------
# Callback Query Handlers for Interactive Help Navigation
# --------------------------------------------------------------------------

@router.callback_query(F.data == "help_main")
async def cb_help_main(callback: CallbackQuery, web_app_url: str):
    lang = get_lang(callback.from_user.language_code if callback.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_help_keyboard(lang, web_app_url)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(t["help_main"], reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help_gremlin")
async def cb_help_gremlin(callback: CallbackQuery, web_app_url: str):
    lang = get_lang(callback.from_user.language_code if callback.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(t["help_gremlin"], reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help_map")
async def cb_help_map(callback: CallbackQuery, web_app_url: str):
    lang = get_lang(callback.from_user.language_code if callback.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(t["help_map"], reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help_camera")
async def cb_help_camera(callback: CallbackQuery, web_app_url: str):
    lang = get_lang(callback.from_user.language_code if callback.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(t["help_camera"], reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help_raid")
async def cb_help_raid(callback: CallbackQuery, web_app_url: str):
    lang = get_lang(callback.from_user.language_code if callback.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(t["help_raid"], reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help_security")
async def cb_help_security(callback: CallbackQuery, web_app_url: str):
    lang = get_lang(callback.from_user.language_code if callback.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(t["help_security"], reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help_wallet")
async def cb_help_wallet(callback: CallbackQuery, web_app_url: str):
    lang = get_lang(callback.from_user.language_code if callback.from_user else None)
    t = MESSAGES[lang]
    keyboard = build_back_keyboard(lang, web_app_url)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(t["help_wallet"], reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
