"""Fixed evaluation question set, per docs/EVALUATION.md.

Three categories, each designed so a *different* retrieval mode should win
— not three phrasings of the same question:

- **structural_favorable**: "what tickets are on file for tower X" — a pure
  location lookup with no symptom language. Graph recall (CONCERNS edges)
  should be complete; vector search has no location signal in ticket text
  to match against, so it should do poorly.
- **semantic_favorable**: "have customers reported <exact symptom>" — a
  pure symptom lookup with no location mentioned. Vector search should find
  it by similarity; graph recall has no entity to resolve, so it should do
  poorly (or fail to resolve an entity at all).
- **hybrid_favorable**: "what's likely causing the outage near router X" —
  root-cause questions where the true answer is a *specific* incident
  cluster, not every ticket near that router (routine tickets can also
  concern the same infrastructure by chance) and not every semantically
  similar ticket in the whole dataset (other incidents use similar generic
  symptom language too). Fusion's overlap-boost is the mechanism designed
  for exactly this case.

Ground truth for each is computed independently of any retrieval code —
see ground_truth.py — so this isn't circular (the system grading itself).
"""

QUESTIONS = [
    # --- structural_favorable: location lookup, no symptom language ---
    {
        "id": "S1",
        "category": "structural_favorable",
        "question": "What support tickets are on file for tower-032?",
        "ground_truth": {"kind": "concerns_target", "target_id": "tower-032"},
    },
    {
        "id": "S2",
        "category": "structural_favorable",
        "question": "What support tickets are on file for tower-016?",
        "ground_truth": {"kind": "concerns_target", "target_id": "tower-016"},
    },
    {
        "id": "S3",
        "category": "structural_favorable",
        "question": "What support tickets are on file for tower-028?",
        "ground_truth": {"kind": "concerns_target", "target_id": "tower-028"},
    },
    # --- semantic_favorable: exact symptom, no location ---
    {
        "id": "V1",
        "category": "semantic_favorable",
        "question": "Have any customers reported intermittent dropouts during calls?",
        "ground_truth": {"kind": "symptom_substring", "substring": "intermittent dropouts during calls"},
    },
    {
        "id": "V2",
        "category": "semantic_favorable",
        "question": "Have any customers reported text messages arriving 10-20 minutes late?",
        "ground_truth": {"kind": "symptom_substring", "substring": "text messages arriving 10-20 minutes late"},
    },
    {
        "id": "V3",
        "category": "semantic_favorable",
        "question": "Have any customers reported video calls freezing every few minutes?",
        "ground_truth": {"kind": "symptom_substring", "substring": "video calls freezing every few minutes"},
    },
    # --- hybrid_favorable: root cause, ground truth is a specific incident cluster ---
    {
        "id": "H1",
        "category": "hybrid_favorable",
        "question": "What's likely causing the outage tickets near router-028?",
        "ground_truth": {"kind": "incident", "router_id": "router-028"},
    },
    {
        "id": "H2",
        "category": "hybrid_favorable",
        "question": "What's likely causing the outage tickets near router-011?",
        "ground_truth": {"kind": "incident", "router_id": "router-011"},
    },
    {
        "id": "H3",
        "category": "hybrid_favorable",
        "question": "What's likely causing the outage tickets near router-025?",
        "ground_truth": {"kind": "incident", "router_id": "router-025"},
    },
]
