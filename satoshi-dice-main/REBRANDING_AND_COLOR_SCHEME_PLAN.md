# Rebranding & Color Scheme Update Plan
## From "Satoshi Dice" to "BitcoinOnly"

### Overview
This plan outlines the changes needed to:
1. **Rebrand** from "Satoshi Dice" to "BitcoinOnly"
2. **Update color scheme** to: White text, Black background, Orange accent
3. **Make BTC orange** throughout the application

---

## Phase 1: Branding Text Changes

### 1.1 Package & Project Name
**File**: `satoshi-dice-main/package.json`
- Change `"name": "satoshi-dice"` → `"name": "bitcoin-only"`

### 1.2 Navbar Component
**File**: `satoshi-dice-main/src/components/navbar/index.js`
- Line 140: `"The Ghost of Satoshi"` → `"The Ghost of Bitcoin"` or remove reference
- Update any "Satoshi" references in the "How To Play" modal

### 1.3 Footer Component
**File**: `satoshi-dice-main/src/components/footer/index.js`
- Line 16: `"Contact SatoshiDice DAPP:"` → `"Contact BitcoinOnly:"`
- Line 16: `support@satoshidice.com` → Update email (or keep as placeholder)

### 1.4 Provably Fair Page
**File**: `satoshi-dice-main/src/app/fair/page.js`
- Line 61: `"SatoshiDice DAPP is a provably fair on-chain Bitcoin game."` → `"BitcoinOnly is a provably fair on-chain Bitcoin game."`

### 1.5 Rules Page (if exists)
**File**: `satoshi-dice-main/src/app/rules/page.js`
- Replace all "Satoshi Dice", "SatoshiDice", "Satoshi" references with "BitcoinOnly"
- Update references from "Bitcoin Cash" to "Bitcoin" (if applicable)

### 1.6 Main Page
**File**: `satoshi-dice-main/src/app/page.js`
- Check for any hardcoded "Satoshi" references in text

### 1.7 Logo Image
**File**: `satoshi-dice-main/public/logo.png`
- **Note**: Logo file may need to be replaced with a new "BitcoinOnly" logo
- All references to `/logo.png` will automatically use the new logo once replaced

---

## Phase 2: Color Scheme Updates

### 2.1 Global Styles
**File**: `satoshi-dice-main/src/app/globals.css`
- Add CSS variables for the new color scheme:
  ```css
  :root {
    --bg-primary: #000000;      /* Black background */
    --text-primary: #FFFFFF;    /* White text */
    --accent-orange: #FF8C00;   /* Orange accent (Bitcoin orange) */
    --accent-orange-light: #FFA500;
    --accent-orange-dark: #FF7F00;
  }
  ```

### 2.2 Navbar Component
**File**: `satoshi-dice-main/src/components/navbar/index.js`
- Line 11: `bg-[#222222]` → `bg-black` or `bg-[#000000]`
- Line 25: Button colors → Use orange accent (`bg-[#FF8C00]` or similar)
- Line 30-36: Link hover colors → Orange accent
- Line 98: Modal background `bg-[#222222]` → `bg-black`
- Line 110: "Bitcoin Cash" → "Bitcoin" (if present)
- Line 120, 136, 149: Green colors (`text-green-400`) → Orange accent

### 2.3 Footer Component
**File**: `satoshi-dice-main/src/components/footer/index.js`
- Line 8: `bg-[#222222]` → `bg-black`
- Line 16: Link color `text-[#74888C]` → Orange accent or white

### 2.4 Main Page (Game Page)
**File**: `satoshi-dice-main/src/app/page.js`

#### Background Colors:
- Line 428: `bg-[url('/bg.png')]` → Keep or update background image
- Line 430: `bg-[rgba(0,0,0,0.20)]` → `bg-[rgba(0,0,0,0.80)]` (darker overlay)
- Line 439: `bg-white/50` → `bg-black/50` or `bg-[rgba(0,0,0,0.50)]`
- Line 444: Selected button `bg-white` → `bg-[#FF8C00]` (orange)
- Line 446-447: Text colors `text-black` → `text-white`

#### Slider Colors:
- Line 463: Gradient `linear-gradient(90deg, #8360C3 0%, #2EBF91 100%)` → Orange gradient
  - New: `linear-gradient(90deg, #FF8C00 0%, #FFA500 100%)`
- Line 470: Slider handle `bg-white` → `bg-[#FF8C00]` or keep white with orange border

#### Multiplier Badges:
- Line 485: Gradient `linear-gradient(135deg, #7B5FC7 0%, #34A89A 100%)` → Orange gradient
  - New: `linear-gradient(135deg, #FF8C00 0%, #FFA500 100%)`

#### Bet Amount Section:
- Line 499: Panel background → Ensure black/dark
- Line 520: Slider track → Black with orange accent
- Line 540: Bet amount display → White text, orange accent for BTC amounts

#### QR Code Section:
- Line 716: Panel background → Black/dark
- Line 718: "Send BTC to Play" → White text
- Line 742: Copy button `bg-[#222]` → `bg-[#FF8C00]` (orange) with white text

#### Recent Games Section:
- Line 650: Panel background → Black/dark
- Line 652: Section title → White text
- Line 679, 689: BTC amounts → **Orange color** (`text-[#FF8C00]`)
- Win/loss indicators → Orange for wins, red/white for losses

### 2.5 Provably Fair Page
**File**: `satoshi-dice-main/src/app/fair/page.js`
- Line 55: `bg-white` → `bg-black`
- Line 58: `text-white` → Keep white
- Line 96: Button `bg-[#222]` → `bg-[#FF8C00]` (orange)
- Line 125-128: Table headers → White text on black/dark background
- Line 135: Table rows → Black background with white text
- Line 144: Hash color `text-[#8eaaaf]` → Orange accent
- Line 150: Plaintext color → White or light gray

### 2.6 Bet History Page
**File**: `satoshi-dice-main/src/components/gameHistory/index.js`
- Background colors → Black
- Text colors → White
- BTC amounts → **Orange color** (`text-[#FF8C00]`)
- Win indicators → Orange
- Loss indicators → Red or white
- Transaction links → Orange accent
- Filter tabs → Orange accent for active state
- Cards → Black background with white text

---

## Phase 3: BTC-Specific Orange Styling

### 3.1 BTC Amount Display
**All Files**: Wherever BTC amounts are displayed:
- Use orange color: `text-[#FF8C00]` or `text-orange-500`
- Examples:
  - `satoshi-dice-main/src/app/page.js`: Bet amount displays, recent games BTC amounts
  - `satoshi-dice-main/src/components/gameHistory/index.js`: All BTC amounts in bet history

### 3.2 BTC Icons/Symbols
- Bitcoin symbol (₿) → Orange color
- Any Bitcoin-related icons → Orange accent

### 3.3 QR Code Section
- "Send BTC to Play" text → White with orange accent on "BTC"
- Address display → White text
- Copy button → Orange background

---

## Phase 4: Component-Specific Color Updates

### 4.1 Buttons
**Pattern**: 
- Primary buttons: Orange background (`bg-[#FF8C00]`), white text
- Secondary buttons: Black background with orange border, white text
- Hover states: Lighter orange (`#FFA500`)

### 4.2 Cards/Panels
**Pattern**:
- Background: `bg-[rgba(0,0,0,0.80)]` or `bg-black`
- Text: White
- Borders: Subtle gray or orange accent

### 4.3 Sliders
**Pattern**:
- Track: Black or dark gray
- Fill: Orange gradient
- Handle: Orange or white with orange border

### 4.4 Links
**Pattern**:
- Default: White or light gray
- Hover: Orange accent
- Active: Orange accent

### 4.5 Status Indicators
- Success/Win: Orange
- Error/Loss: Red or white
- Loading: Orange spinner

---

## Phase 5: Files to Update

### 5.1 Core Files
1. `satoshi-dice-main/package.json` - Project name
2. `satoshi-dice-main/src/app/globals.css` - Global color variables
3. `satoshi-dice-main/src/components/navbar/index.js` - Navbar colors & branding
4. `satoshi-dice-main/src/components/footer/index.js` - Footer colors & branding
5. `satoshi-dice-main/src/app/page.js` - Main game page colors
6. `satoshi-dice-main/src/app/fair/page.js` - Provably fair page colors
7. `satoshi-dice-main/src/components/gameHistory/index.js` - Bet history colors

### 5.2 Optional Files (if they exist)
8. `satoshi-dice-main/src/app/rules/page.js` - Rules page branding & colors
9. `satoshi-dice-main/public/logo.png` - Logo replacement (manual)

---

## Phase 6: Color Palette Reference

### Primary Colors
- **Background**: `#000000` (Black)
- **Text**: `#FFFFFF` (White)
- **Accent**: `#FF8C00` (Dark Orange - Bitcoin orange)
- **Accent Light**: `#FFA500` (Orange)
- **Accent Dark**: `#FF7F00` (Dark Orange)

### Secondary Colors
- **Gray Dark**: `#222222` → Replace with black
- **Gray Medium**: `#74888C` → Replace with white or orange
- **Gray Light**: For subtle borders/separators

### BTC-Specific
- **BTC Text**: `#FF8C00` (Orange)
- **BTC Icons**: `#FF8C00` (Orange)

---

## Phase 7: Implementation Checklist

### Branding
- [ ] Update `package.json` name
- [ ] Replace "Satoshi Dice" with "BitcoinOnly" in navbar
- [ ] Replace "Satoshi Dice" with "BitcoinOnly" in footer
- [ ] Replace "Satoshi Dice" with "BitcoinOnly" in provably fair page
- [ ] Replace "Satoshi Dice" with "BitcoinOnly" in rules page (if exists)
- [ ] Update email/contact references
- [ ] Replace logo image (manual)

### Colors - Global
- [ ] Add CSS variables to `globals.css`
- [ ] Update navbar background to black
- [ ] Update footer background to black
- [ ] Update all page backgrounds to black

### Colors - Components
- [ ] Update button colors to orange
- [ ] Update slider colors to orange gradient
- [ ] Update multiplier badges to orange
- [ ] Update card/panel backgrounds to black
- [ ] Update all text to white
- [ ] Update links to orange accent

### Colors - BTC Specific
- [ ] Make all BTC amounts orange
- [ ] Make Bitcoin symbol (₿) orange
- [ ] Update BTC-related icons to orange
- [ ] Update "Send BTC to Play" with orange accent

### Testing
- [ ] Test on desktop view
- [ ] Test on mobile view
- [ ] Verify all text is readable (white on black)
- [ ] Verify orange accents are visible
- [ ] Verify BTC amounts are orange
- [ ] Check all pages (main, history, provably fair, rules)

---

## Notes

1. **Logo**: The logo file (`/logo.png`) will need to be manually replaced with a new "BitcoinOnly" logo. The code will automatically use the new logo once the file is replaced.

2. **Background Images**: The background images (`/bg.png`, `/bng.png`) may need to be updated to match the new black theme, or kept as-is if they work with the new color scheme.

3. **Orange Shades**: Bitcoin orange is typically `#FF8C00` (dark orange) or `#F7931A` (Bitcoin Core orange). We'll use `#FF8C00` as the primary accent, with variations for hover states.

4. **Accessibility**: Ensure sufficient contrast between white text and black background. Orange accents should be visible and not too bright.

5. **Gradients**: Replace existing purple/green gradients with orange gradients throughout.

---

## Estimated Impact

- **Files Modified**: ~7-9 files
- **Lines Changed**: ~200-300 lines
- **Components Affected**: Navbar, Footer, Main Page, Provably Fair Page, Bet History, Rules (if exists)
- **Time Estimate**: 2-3 hours for complete implementation

---

## Ready for Implementation?

This plan covers all aspects of the rebranding and color scheme update. Once approved, we can proceed with the implementation phase by phase.
