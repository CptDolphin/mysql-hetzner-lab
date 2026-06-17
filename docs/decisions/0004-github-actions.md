# ADR-0004 — Repo + CI/CD: GitHub + GitHub Actions

- **Status:** zaakceptowany
- **Kontekst:** potrzebny board (Issues/Milestones) oraz CI z piramidą testów Ansible i **scheduled** restore-drillami.

## Decyzja
**GitHub** jako repo i board, **GitHub Actions** jako CI/CD ([ci-cd-and-testing.md](../explanation/ci-cd-and-testing.md)).
Runnery GitHub-hosted do CI; deploy po **SSH (key-only)** do publicznego hosta (klucz w GitHub Secrets); sekrety w GitHub Secrets.

## Konsekwencje
- (+) Darmowe hostowane runnery, proste `schedule`, bogaty ekosystem akcji (`trivy`, SSH-deploy); niski próg wejścia.
- (−) Deploy po publicznym SSH — mitygacja: key-only + `fail2ban`. Domknięcie 22 (self-hosted runner z KontrahentCheck) zostaje opcją na roadmapie.
- Deploy nigdy z forka; akcje mutujące serwer za `environment` + approval.

## Alternatywy odrzucone
- **GitLab CI** — spójne z `k8s-hetzner-lab`, ale tutaj wybieramy GitHub dla hostowanych runnerów i prostoty bez własnego runnera.
- **Jenkins / Drone self-hosted** — dodatkowy serwer do utrzymania i hartowania; nadmiar w labie.
