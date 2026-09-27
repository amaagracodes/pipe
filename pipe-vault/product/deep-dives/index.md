---
title: "Product Deep Dives: Underexploited Enterprise Professions"
date_created: 2026-09-27
tags:
  - product/deep-dive
  - enterprise-llm
  - console-architecture
---

# Product Deep Dives: Enterprise LLM Console

Welcome to the product research and architectural vault for `pipe`'s enterprise vertical consoles.

This vault catalogs and models high-productivity, mission-critical enterprise professions that govern billions in capital and risk, yet suffer from acute **technology underexposure**.

---

## 🧭 Vault Navigation & Deep-Dive Reports

- **[[underexploited-enterprise-professions-report|Master Strategic Report: Underexploited Professions & Layered Architecture]]**
  The master analysis examining why horizontal chatbots fail, decomposing expert cognitive work layer-by-layer (general vs. specific cases), scoring candidate industries, and establishing the #1 first point of call.

- **[[medtech-regulatory-console|Deep Dive: MedTech Regulatory Affairs Console (FDA 510k & EU MDR)]]**
  The #1 beachhead console blueprint: persona, pain point ($50k/day delay cost), RTA checklist auditor, substantial equivalence comparator, and full `pipe` implementation.

- **[[trade-compliance-console|Deep Dive: Global Trade & Customs Compliance Console (10-Digit HTS)]]**
  The #2 wave-1 console blueprint: 10-digit tariff classification using General Rules of Interpretation (GIRs), section note reconciliation, and anti-dumping risk gating.

---

## 📊 Dynamic Catalog of Analyzed Professions (Dataview)

> [!NOTE] Dataview Query
> Below is a live query rendered by the **Dataview** plugin across all deep-dive files in this vault.

```dataview
TABLE sector AS "Sector", capital_leverage AS "Capital Leverage / Desk", cost_of_error AS "Cost of Error / Delay", strategic_tier AS "Wave / Tier"
FROM "product/deep-dives"
WHERE file.name != "index"
SORT strategic_tier ASC
```

---

## 🎯 Strategic Prioritization Matrix

| Wave | Wedge Classification | Target Professions | Core Primitive |
| :--- | :--- | :--- | :--- |
| **Wave 1** | **Immediate Beachheads (Tier 1)** | MedTech RA, Customs Brokerage, GovCon FAR Flow-Downs, Reinsurance Treaty Slips | Pure text/tabular + rigid statutory authority + zero tolerance for hallucination |
| **Wave 2** | **Enterprise Expanders (Tier 2)** | Clinical Trial TMFs, Hospital Denial Appeals, Aviation MRO Records, Transfer Pricing | Cross-system data linking + multi-party negotiation + historical ledger tracing |
| **Wave 3** | **Hybrid Physical Moats (Tier 3)** | Construction Quantity Surveying, Environmental NEPA, Grid Interconnection | Bridges unstructured legal text with CAD, BIM, GIS, and power flow telemetry |

---

## 🔗 Architecture Linkage to `pipe`

All consoles built in this vault are powered by the shared functional runtime in [`pipe.lib.experts`](file:///Volumes/workplace/amaagracodes/pipe/src/pipe/lib/experts):
- [`Expert[I, O]`](file:///Volumes/workplace/amaagracodes/pipe/src/pipe/lib/experts/base.py) & [`AIBasedExpert[I, O]`](file:///Volumes/workplace/amaagracodes/pipe/src/pipe/lib/experts/ai.py): Typed cognitive micro-actions.
- [`ScopedRegistry`](file:///Volumes/workplace/amaagracodes/pipe/src/pipe/lib/shared/scoped_registry.py): Hierarchical jurisdiction & statutory authority scoping.
- [`SeverityGate`](file:///Volumes/workplace/amaagracodes/pipe/src/pipe/lib/experts/generic.py): Non-stochastic threshold enforcement.
- [`Workflow`](file:///Volumes/workplace/amaagracodes/pipe/src/pipe/lib/experts/workflow.py): Composable `>>` pipelines with immutable envelopes.
