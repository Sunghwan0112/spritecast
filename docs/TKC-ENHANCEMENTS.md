# TKC → SpriteCast enhancements

TKC (talent-support-dashboard, Nonarkara/tkc-new-chapter) contributes four things to SpriteCast:

## 1. Wada Plate 094 palette pack

**File:** `skills/spritecast/palettes/wada094.hex`
**Doc:** `skills/spritecast/reference/wada.md`

32 colours from Sanzo Wada's 1930s colour research, carried through TKC's design system (`src/palette/tkc-theme.ts`, `tkc3d/src/core/palette.ts`) and into SpriteCast as a pixel-art palette. Use with `--palette wada094` or `--colours 32 --palette wada094`.

## 2. Shadow-proxy optimization

**File:** `skills/spritecast/scripts/render.html`

TKC's `shadow-proxy.ts` (tkc3d) merges all shadow-casting geometry into one position-only proxy mesh, collapsing ~870 shadow draw calls to a handful on TKC's campus. Applied to SpriteCast's `render.html`: `shadowShot()` now merges all prop geometries into a single proxy before projecting the shadow, instead of cloning the entire prop and re-materializing every mesh. Complex props (server racks, copiers, multi-part furniture) render their shadow in a single draw call.

## 3. Quality tier system for 3D guide rendering

**File:** `skills/spritecast/scripts/render.html`

TKC's `quality.ts` (tkc3d) defines three tiers (low/medium/high) with MSAA samples, pixel-ratio caps and render-scale multipliers, plus adaptive resolution control. Applied to SpriteCast's `render.html`: the `SPRITECAST_QUALITY` env var (already read for OpenAI image generation) now also sets the 3D renderer's MSAA, pixel ratio and render scale. A slow machine gets a clean guide fast; a fast machine gets crisp thin geometry (rack edges, chair legs, screen bezels).

## 4. TKC tech-kit prop examples

**Files:** `examples/tkc_copier/`, `examples/tkc_rack42u/`

TKC's `tkc3d/src/world/tech-kit.ts` builds real-world office and data-centre props at real scale (server racks, desks, chairs, copiers, NOC consoles, water coolers). Two are ported as SpriteCast spec examples:

- `tkc_copier` — office copier (0.64×0.6×1.14 m): white plastic body, three paper trays, tilted control panel with screen, finisher with stacked output trays, side vents, status LEDs
- `tkc_rack42u` — 42U server rack (0.6×1.07×2.0 m): side posts, top/base plates, perforated doors, mounting rails, patch panel, top-of-rack switch with port LEDs, cable manager, blanking panels, server units with link LEDs, vertical cable managers

Run them with SpriteCast's normal flow:

```bash
# Copier guide (free)
PYTHON skills/spritecast/scripts/isoprop.py render examples/tkc_copier/tkc_copier.json

# Copier drawn (~$0.07)
PYTHON skills/spritecast/scripts/isoprop.py draw examples/tkc_copier/tkc_copier.json --yes

# Rack guide (free)
PYTHON skills/spritecast/scripts/isoprop.py render examples/tkc_rack42u/tkc_rack42u.json

# Rack drawn (~$0.07)
PYTHON skills/spritecast/scripts/isoprop.py draw examples/tkc_rack42u/tkc_rack42u.json --yes
```

## Provenance

All TKC contributions carry TKC's design law (Wada plate 094, zero border-radius, no gradients, no drop shadows, non-looped Thai faces, MSH — Massacre Spatial Hallucination — compliance). TKC's design system is documented in `talent-support-dashboard/STYLE.md` and `tkc3d/src/core/palette.ts`.
