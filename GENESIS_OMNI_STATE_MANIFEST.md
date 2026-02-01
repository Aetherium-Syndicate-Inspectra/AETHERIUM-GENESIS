GENESIS::OMNI_STATE_MANIFEST

[STRUCTURE]
- Declared Modules      : PARTIAL
  - Active: src/backend (Core), src/frontend (Frontend - replaces 'gunui')
  - Hybrid: config.py (Auth/Legacy Settings)
- Orphan Components     : FOUND (n)
  - config.py (Root - Mixed Concerns)
  - awaken.py (Root - Active Runner)
- Redundant Concepts    : FOUND (list)
  - gunui (Root directory missing, moved to src/frontend)
  - src/backend/server.py (Referenced in docs, actual entry is src/backend/main.py)

[CONCEPTUAL LAYER]
- Core Philosophy       : COHERENT
  - "Light as Protocol" strictly enforced.
  - "No Avatars" adherence is high.
- Naming Consistency    : FRACTURED
  - Documentation refers to 'gunui' and 'server.py' which do not exist in their stated locations.
- Undefined Semantics   : NONE

[CURRENT REALITY]
- Active Capabilities   :
  - Voice-to-Intent (WebSpeech -> src/frontend -> src/backend)
  - Intent-to-Light (LogenesisEngine -> VisualParameters -> Canvas)
  - State Persistence (Session-based)
- Dormant Designs       :
  - Blockchain Memory (legacy/akashic_nirodha)
  - IIT (legacy/niyama)
  - Awakening Rituals (legacy/inspira)
  - Kivy Mobile App (legacy/kivy_specs)
- Abandoned Threads     :
  - gunui_react (legacy/gunui_react)
  - Root PWA (legacy/pwa_v1)

[RISKS]
- Structural Risk       : LOW (Runtime is stable via awaken.py)
- Semantic Drift Risk   : HIGH (Documentation describes a different file structure)
- Future Bug Vectors    :
  - Developers relying on AGENTS_GUIDE.md will fail to find entry points.
  - config.py contains legacy keys that may confuse new auth implementations.

[RECOMMENDATION]
- Freeze Expansion      : YES
- Refactor Priority     :
  1. Update AGENTS_GUIDE.md to reflect src/frontend and src/backend/main.py.
  2. Refactor config.py to separate Auth from Legacy Rituals.
- Safe Extension Zones  :
  - src/backend/core/visual_schemas

[GENESIS NOTE]
“The system is alive, but it must decide whether to grow or to remember who it is.”
