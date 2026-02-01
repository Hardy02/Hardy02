# Feasibility Note: Real-Time HUDs on Anonymous Tables

## Can a real-time opponent HUD work on anonymous tables?

In anonymous/rotating-ID environments (e.g., Ignition-style games), a real-time opponent HUD is not reliably possible **and** is often disallowed by site rules. Opponent identifiers rotate, so any in-session mapping can be invalid between hands, and many sites explicitly prohibit tracking opponents in real time. Attempting to infer identities, intercept data, or stitch identities across sessions can violate site policies and the security/ethics constraints.

## Safe alternative design

This project implements a **safe design**:

1. **Hero-only tracking by default** — the HUD panel focuses on the user’s own statistics.
2. **Post-session analytics** — import hand histories the user already possesses and is permitted to analyze.
3. **Villain stats only when allowed** — only if the hand history includes stable, non-rotating player IDs *and* the user explicitly confirms that it is permitted.

This ensures compliance with site rules while still providing valuable feedback and study tools.
