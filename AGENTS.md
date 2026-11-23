# UI/UX & Product Design Rules (Stageshow Standard)

When designing, modifying, or implementing UI components, landing pages, marketing mockups, animations, or visual elements in this project, the agent MUST strictly adhere to these design laws.

---

## 1. Core Philosophy: The Anti-AI-Slop Standard
* **Believable Production Quality**: Interfaces must look like real, shippable software crafted by top-tier product designers (Linear, Stripe, Apple, Vercel), never generic AI sketches.
* **Eliminate the 5 Classic AI Failures**:
  1. **Too Much**: Do not cram every row with dense text, arbitrary numbers, and busy cards.
  2. **Wireframe**: Avoid minimalist gray boxes with a lone button that lack product identity.
  3. **Boxed**: Never paste an entire window into a card with huge borders like a tiny screenshot.
  4. **Flat**: Ensure clear visual hierarchy. Avoid making every element share identical weights, borders, and backgrounds.
  5. **Bland / Generic AI**: Strictly forbid generic purple/violet gradients, sparkle/wand "AI" icons, and decorative badges without functional meaning.

---

## 2. Restraint & Content Budget
* **Word Budget (3 to 7 Real Strings)**:
  - Focus real copy strictly on what the focal user story or action is (e.g., flight mission name, altitude, waypoint target, active CTA).
  - Use structured, muted skeleton bars or subtle structural lines for peripheral context.
  - **Never** place gray placeholder bars where the eye lands first. The focal point must carry crisp, authentic text.
* **Domain-Authentic Content**:
  - Always use realistic drone telemetry and flight control context (e.g., DJI RC 2 / RC Pro controllers, GPS coordinates, AGL altitude, battery %, waypoint contours).
  - Use a single, cohesive icon set (e.g., Lucide / system icons) at consistent stroke weights (14–16px). Never mix icon styles or draw crude hand-drawn glyphs.

---

## 3. Framing & Composition (Product Shot, Not Screenshot)
* **Intentional Crop & Scale**:
  - Hero UI elements must fill at least 65%–85% of the stage width.
  - Allow 10% to 40% of secondary UI (lists, table rows, sidebars) to bleed off-stage. This establishes depth, focus, and realistic scale.
  - Never crop through labeled controls, buttons, or active payoffs. Only filler and repeating rows may bleed.
* **Hero & Satellites**:
  - Compose **one primary hero object** and at most **1 or 2 satellites** (e.g., a telemetry badge, waypoint toast, or companion controller card).
  - Satellites must **straddle the hero edge** (~50% inside, 50% outside) over chrome or margins—never obscuring critical data or actions.
* **Single Gutter & Alignment**:
  - Maintain a uniform gutter across all edges of the composition.
  - Strictly avoid near-tangents (edges 1–3px apart). Either align exactly or separate by at least 8–12px.

---

## 4. Spacing, Typography & Geometry
* **Typography Hierarchy (WanDrone Tokens)**:
  - **Headings & Display**: `Barlow Semi Condensed` (bold, technical, industrial precision).
  - **Body & UI Labels**: `IBM Plex Sans` (clean, highly readable).
  - **Data, Telemetry & Code**: `JetBrains Mono` (tabular numbers, coordinate grids, specs).
  - Minimum line-height of 1.3 for UI labels.
* **Optical Centering & Spacing**:
  - Button and control clearances: 8px to 12px gap from adjacent inputs/borders.
  - Optical alignment: Center text based on cap-height rather than font line-box. Center numeric figures by the digits themselves (hanging unit/currency symbols outside if needed).

---

## 5. Color Palette & Dark Aero Material
* **Color System**:
  - Ground & Canvas: Deep Ink (`#0A0E16`), Slate (`#1E293B` / `#3A4657`), Surface Dark (`#111827`).
  - Brand Accent: Tactical Teal (`#2DD4BF`), Deep Teal (`#0F766E`).
  - Lines & Borders: Crisp hairlines (`rgba(232, 238, 244, 0.12)` or `1px solid #1F2937`).
* **Surface Elevation**:
  - Subtle, multi-layered ambient drop shadows for floating cards and satellites (`0 12px 32px -8px rgba(0,0,0,0.5)`).
  - Keep elevation crisp with a 1px border highlight (`rgba(255, 255, 255, 0.08)`).

---

## 6. Choreography & Motion
* **Motion with Cause**: Every animation or cursor interaction must have a clear cause (user gesture, incoming telemetry) and an immediate visual payoff.
* **Coordinated Transitions**: When a surface resizes, adjacent rows glide into place smoothly without squashing or jarring text jumps.
* **Loop Discipline**: Any looping animation must hold the payoff state long enough to be read and understood before gracefully resetting.
