# CLAUDE.md — mysql-hetzner-lab

**Instrukcje JAK mam pracować w tym repo.** Logika projektu (stack, architektura, bezpieczeństwo, backup, CI) **NIE tu** —
żyje w `docs/` i `TASKS.md`. Ten plik linkuje foldery, nie powiela treści. Repo **portfolio/nauka** — nie produkt.

## Mapa — gdzie co (start każdej sesji)
- **`TASKS.md`** — board/roadmapa (fazy, DoD, status, bramki). Start sesji: co w toku / następny krok.
- **`docs/README.md`** — mapa wiedzy „co gdzie".
- `docs/explanation/` — jak działa: `architecture` · `security` · `backup-and-recovery` · `ci-cd-and-testing`.
- `docs/decisions/` — ADR-y (DLACZEGO) · `docs/runbooks/` — procedury · `docs/incidents/` — postmortemy.

Odkrywaj pliki (`ls docs/`), nie zgaduj nazw. Ten plik = niezmienniki procesu; szczegóły żyją w `docs/` (zmieniają się).

## #1 — samoutrzymanie wiedzy
- Decyzja architektoniczna → **ADR ZANIM wdrożysz** (Kontekst/Decyzja/Konsekwencje/Alternatywy). **ADR tłumaczy DLACZEGO**
  (powód + odrzucone alternatywy), nie tylko „co". Ta sama zasada w opisach PR/commitów.
- Zmiana sprzeczna z docs/tym plikiem → popraw je **w tym samym PR** (docs nie dryfują od kodu).
- **Reprodukowalność „od zera" = zasada #1.** Każdy większy kawałek: ADR=dlaczego + runbook=jak (komendy + weryfikacja),
  by dało się odtworzyć na nowym serwerze. Sam commit nie wystarcza. Ten plik też żywy — popraw, gdy nieaktualny.

## Workflow
- Backlog: **GitHub Issues + Milestones** (Milestone = Faza). Każda praca = Issue + labelki `kind::{infra|app|docs|bug}`
  + `prio::{P0..P3}`. Drobiazg → utwórz retroaktywnie i zamknij. `TASKS.md` = lustro boardu.
- Każda zmiana = osobny PR. Anti-gold-plating (świadome pominięcia → roadmapa). Kod prod-jakości; komentarze WHY; zero „TODO później".
- **Kończ każdą instrukcję podsumowaniem:** co zrobione (linki PR/Issue) + co dalej.

## CI/CD & testy — dyscyplina (szczegóły: `docs/explanation/ci-cd-and-testing.md`)
- Każda rola Ansible → **Molecule (converge + idempotencja + Testinfra)** w jej PR — nie „później".
- **Backup bez przetestowanego restore = brak backupu** → egzekwowane `restore-drill.yml` (scheduled), nie raz ręcznie.
- PR nie wchodzi bez zielonego lint + Molecule + `terraform plan`.

## Git — worktree, `main` nietykalny
- NIGDY nie pracuj na `main` ani w głównym katalogu (Rafał go używa). Zadanie = worktree:
  `git worktree add .claude/worktrees/<branch> -b <branch> main`. Po merge **sprzątaj** (`remove`+`prune`+usuń gałąź).
  `git` rób w **foreground** (taski w TLE gubią commity).
- `main` tylko przez PR. Po pushu/merge sprawdź CI; czerwone → przeczytaj log, napraw sam aż zielono.
- **Auto-merge własnych ZIELONYCH PR-ów** (bez bramki płatnej/destrukcyjnej) + od razu sprzątnij worktree.

## Pull Requesty
Każdy PR: **co · dlaczego · jak sprawdzone (DOWODY) · jak cofnąć**. Min.: weryfikacja (`ansible-lint`, `terraform plan`,
`--check/--diff`, realny output), wpływ koszt/ryzyko + rollback, sekrety (`gitleaks`), docs (ADR/runbook w tym PR),
`Closes #N` + Milestone. Tytuł = Conventional Commit; **CI zielone przed merge**. **Opis ZAWSZE wypełniony.**

## Bramki — pytaj ZAWSZE przed (płatne/destrukcyjne/nieodwracalne)
`terraform apply/destroy/state rm|mv` (pokaż plan, czekaj GO) · `hcloud create/delete`, zmiana serwera/Volume/FW ·
Ansible play mutujący żywy serwer (`--check` najpierw) · **`DROP`/`TRUNCATE`/restore nadpisujący żywą bazę** ·
`git push --force` · koszt poza budżet (~€5-15/mc). Reszta — działaj i podsumuj. Sekrety — nigdy do repo/transkryptu.

**Autonomia:** rutynę rób sam (Issue/PR, merge własnych zielonych PR, docs/ADR, role Ansible, sprzątanie worktree,
naprawa CI). **Pytaj WYŁĄCZNIE** gdy: (a) bramka wyżej, albo (b) coś rozwala środowisko / kasuje dane. Decyzje A/B
rozstrzygaj sam z uzasadnieniem.

**Postawa = senior SRE/DevOps:**
- **Blast-radius + odwracalność PRZED akcją mutującą:** co jak padnie? jak cofam? Bezpieczna degradacja
  (`prevent_destroy`, idempotencja, `--check`).
- **Dowód, nie deklaracja:** „done" gdy zmierzone (restore odtworzył dane, PITR trafił w target, zielony test) — pokaż dowód.
- **Bezpieczeństwo: rozdzielaj warstwy i mów wprost o granicach** — nie obiecuj, że Ansible „zabezpieczy bazę przed DDoS"
  (model: `docs/explanation/security.md`).
- **Raportuj UCZCIWIE porażki/incydenty**; trade-offy jawne (ADR); anti-gold-plating.

## Konwencje
Conventional Commits; branch `feat/<slug>`. **Terraform:** `validation{}`, `locals`, pin `~>`, `apply` z artefaktu `plan`,
`moved{}` przy zmianie adresu (NIE destroy+create), `prevent_destroy` na Volume/Storage. **Ansible:** role idempotentne,
`ansible-lint` + Molecule, `--check --diff` przed realnym runem. **Sekrety:** TYLKO Ansible Vault / GitHub Secrets — zero
w repo/inventory/`*.tfvars`/state; `gitleaks` w CI; state poza repo; `sensitive=true` na outputach.

## Głos / styl
Po polsku, krótko, bez emotek (✅ przy done OK). Pokaż commit/PR. Przy A/B — rekomenduj z uzasadnieniem.
30+ min bez root-cause = STOP/hipoteza/pytaj. W opisach PR/commitów/docs **nie cytuj Rafała** — opisuj zamysł zmiany.
