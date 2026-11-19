# Wada Plate 094 palette — TKC design system chord

A pixel-art palette from Sanzo Wada's 1930s colour research, used as TKC's
secondary accent lineage (TKC's `src/palette/tkc-theme.ts` names plate 094 as
its Wada lineage; TKC3D's `tkc3d/src/core/palette.ts` carries the same chord
into the 3D world). The 32 colours below are screen reconstructions of the
printed inks, not claims about the original ink.

## Colours

| # | Hex | TKC role |
|---|-----|----------|
| 1 | #f4eedf | paper — warm card-stock ground |
| 2 | #e4dece | ground — console tabletop |
| 3 | #202b29 | ink — primary text on light surfaces |
| 4 | #525d57 | muted — captions, 5.1:1 on plate ground |
| 5 | #183d38 | room — recessed openings, signage ink |
| 6 | #c5ccb4 | floor — TKC3D plaza stone |
| 7 | #9cae98 | wall — TKC3D wall tone |
| 8 | #83917d | rule — hairlines and 1px borders |
| 9 | #f59e0b | amber — TKC house signal accent |
| 10 | #efe6d2 | stone — light architectural stone |
| 11 | #e2d6bd | stoneMid — mid stone |
| 12 | #c9bb9c | stoneDark — deep stone |
| 13 | #8a6a45 | wood — warm timber |
| 14 | #6b5136 | woodDark — deep timber |
| 15 | #b8443a | roofRed — terracotta roof |
| 16 | #8e3229 | roofRedDark — deep terracotta |
| 17 | #d9a441 | gold — warm gold accent |
| 18 | #efc463 | goldBright — bright gold |
| 19 | #4a8fa8 | water — TKC3D canal teal |
| 20 | #2f6b83 | waterDeep — deep canal teal |
| 21 | #5f8f43 | leaf — foliage |
| 22 | #7cae55 | leafLight — light foliage |
| 23 | #4e7a3a | palm — palm frond |
| 24 | #7a5c3d | trunk — tree trunk |
| 25 | #9a9384 | rock — stone rock |
| 26 | #b9bec4 | steel — brushed steel |
| 27 | #7d848c | steelDark — deep steel |
| 28 | #9fd4dd | glass — glazed tile |
| 29 | #1d4a52 | screen — dark screen |
| 30 | #64e2d0 | screenGlow — screen glow |
| 31 | #f2f4f2 | labCoat — lab coat white |
| 32 | #ffd489 | lamp — warm lamp light |

## Usage

```bash
# List all palettes (wada094 appears here)
$PYTHON skills/spritecast/scripts/pixelart.py hero.json --palette list

# Apply the Wada094 palette to finished pixel sheets (nothing is redrawn)
$PYTHON skills/spritecast/scripts/pixelart.py hero.json --palette wada094

# Or limit the drawing to Wada094 colours from the start
$PYTHON skills/spritecast/scripts/pixelart.py hero.json --colours 32 --palette wada094 --yes
```

## Design notes

- **One job per colour** — per TKC's Palette field-guide, each colour has an assigned role; none are decorative.
- **Contrast measured** — ink (#202b29) on paper (#f4eedf) is 4.53:1, just over the 4.5:1 WCAG AA floor; muted (#525d57) on paper is 5.1:1.
- **Source boundary** — these are digital screen sRGB conversions of Wada's printed plate colours; they are not claims about the original printed inks.
- **TKC provenance** — the same colours appear in TKC's `src/palette/tkc-theme.ts` (TKC_CHORD) and `tkc3d/src/core/palette.ts` (TKC3D's scene palette), so sprites made with this palette sit inside TKC's product family.

## Source

TKC's Wada colour catalogue: `src/palette/wada.ts` (159 entries from the Nonarkara/palette exhibition; plates 001-348).
TKC's plate 094 chord: `src/palette/tkc-theme.ts`.
TKC3D's scene palette: `tkc3d/src/core/palette.ts`.
