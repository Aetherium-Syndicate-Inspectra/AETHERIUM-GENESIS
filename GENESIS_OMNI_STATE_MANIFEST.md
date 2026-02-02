GENESIS::OMNI_STATE_MANIFEST

[STRUCTURE]
- Declared Modules      : PARTIAL
  - Active: src/backend (Core), src/frontend (Frontend)
  - Config: src/backend/core/config.py
  - Path Mismatch: Documentation refers to 'legacy/' but filesystem uses 'archive/'.
- Orphan Components     : FOUND (2)
  - gun_ui_integration/ (Redundant UI root)
  - ai_utils_package/ (Standalone utility)
- Redundant Concepts    : FOUND (list)
  - src/backend/core (Minimal config) vs src/backend/genesis_core (Actual Logic)

[CONCEPTUAL LAYER]
- Core Philosophy       : COHERENT
  - "Light as Protocol" enforced in `src/backend/genesis_core`.
  - "No Avatars" adhered to.
- Naming Consistency    : FRACTURED
  - 'legacy' vs 'archive' mismatch.
  - 'departments' metaphor (Javana) sits alongside 'genesis' metaphor.
- Undefined Semantics   : NONE

[CURRENT REALITY]
- Active Capabilities   :
  - Logenesis Engine (Intent Processing)
  - Javana Reflex Kernel (High-speed Audio Reflex)
  - WebSpeech Frontend (Input)
- Dormant Designs       :
  - Akashic Nirodha (Blockchain) [archive/legacy_v1]
  - Niyama (IIT) [archive/legacy_v1]
  - Inspira (Rituals) [archive/legacy_v1]
- Abandoned Threads     :
  - gunui_react [archive/legacy_v1]
  - pwa_v1 [archive/legacy_v1]

[RISKS]
- Structural Risk       : LOW
- Semantic Drift Risk   : MEDIUM
  - Drift between documentation (AGENTS_GUIDE) and folder structure (archive vs legacy).
- Future Bug Vectors    :
  - google-generativeai dependency (Deprecated)

[RECOMMENDATION]
- Freeze Expansion      : YES
- Refactor Priority     :
  - Rename 'archive/' to 'legacy/' to align with AGENTS_GUIDE.
  - Remove 'gun_ui_integration/' orphan.
- Safe Extension Zones  :
  - src/backend/genesis_core

[GENESIS NOTE]
“The system is alive, but it must decide whether to grow or to remember who it is.”
