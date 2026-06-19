# docs/ — mapa wiedzy

Dokumentacja żyje tu (nie w `CLAUDE.md`, nie w opisie issue). Gatunek = folder (Diátaxis-lite).

| Folder | Co zawiera | Status |
|--------|------------|--------|
| `explanation/` | jak działa: `architecture` · `security` · `backup-and-recovery` · `ci-cd-and-testing` · `observability` | jest |
| `decisions/` | ADR-y — DLACZEGO tak zdecydowano (MADR) | 0001–0006 |
| `runbooks/` | procedury krok-po-kroku | `under-attack` jest; restore/pitr/rotacja → Fazy 5/6/8 |

Top-level: [`reuse-from-kontrahentcheck.md`](reuse-from-kontrahentcheck.md) — co kopiować z bliźniaczego repo.
Postmortemy (blameless) → `docs/incidents/<data>.md` (folder zakładamy przy pierwszym incydencie, nie z góry).

## Decision-tree „gdzie szukać / co pisać"
- Chcę **zrozumieć, jak coś działa** → `explanation/`.
- **Czemu** tak, nie inaczej → `decisions/` (ADR).
- Muszę coś **wykonać** (restore, rotacja, reakcja na atak) → `runbooks/`.
- **Co jest do zrobienia / status** → `../TASKS.md`.
- **Jak mam pracować** (proces, bramki, git) → `../CLAUDE.md`.

Zasada: kod i docs w jednym PR (docs nie dryfują). ADR = niezmienny zapis „dlaczego"; explanation = bieżący stan „jak".
