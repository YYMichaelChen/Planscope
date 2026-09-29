# Product Roadmap

## v1.0

Core skill: SKILL.md, templates, helper CLI, four-tool compatibility,
install script, test suite. (Complete.)

## v1.1

Public GitHub release and verified four-tool install. (Complete —
v1.0 published; marketplace manifest done via v1.1.0 T-302; remaining
three-tool verification moved to v1.1.0 P4.)

## v1.1.0

Lifecycle/context/distribution hardening: coherent release activation
and clearing, single-active-release invariant, strict phase statuses,
`plan sync`, expanded doctor, collision-safe LOG rotation, unified
project install, patch versions. (Complete — tagged v1.1.0.)

## v1.1.1

Distribution and validation patch: proper Claude plugin root with
manifest, mechanically generated plugin payload from the canonical
skill, distribution drift detection, close gates for missing PLAN.md
and zero-phase plans, full PLAN → INDEX projection drift detection.
(Complete — tagged v1.1.1.)

## v1.1.2

Governance boundary hardening: Project Authority Boundary and
Recoverability Rule as core invariants, routing-first PROJECT.md with
Authority Map, destination-classified semantic close, PLAN closeout
checklist enforced by `plan close`, structural closeout validation in
`plan doctor`. (Complete — tagged v1.1.2.)

## Later

Post-v1.1 real-usage observation (per v1.1.0 spec §36) before any new
architecture: how large active context becomes, how often manual
compaction and INDEX drift occur, how often archive is reopened, which
documents grow too fast, which CLI operations actually save agent
work. Includes fresh-install verification in Codex CLI, opencode and
Kimi Code (deferred T-404..T-406). Only after v1.x usage proves the
need: machine-readable plan state, semantic compaction aids, plugin
marketplace polish.
