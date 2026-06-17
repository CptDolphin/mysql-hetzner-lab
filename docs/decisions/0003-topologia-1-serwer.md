# ADR-0003 — Topologia: 1 serwer (cx22) + Hetzner Storage Box

- **Status:** zaakceptowany
- **Kontekst:** lab/portfolio, mały budżet, cel = nauka self-managed MySQL z backupem/PITR i hardeningiem.

## Decyzja
**Jeden serwer cx22** z MySQL i apką demo (Docker) na tej samej maszynie; MySQL słucha na `127.0.0.1`.
Offsite = **Hetzner Storage Box** (tani SFTP/restic).

## Konsekwencje
- (+) Tanio (~€5-8/mc) i prosto; pełna kontrola; szybka reprodukcja „od zera".
- (−) **SPOF** — brak HA; awaria serwera = przestój. Akceptowane: utrata danych pokryta przez PITR (inny wektor niż dostępność).
- (−) Apka i baza dzielą blast-radius → wymagana **izolacja zasobów** (Docker limits + OOM-protect mysqld; per-user limity MySQL) — patrz [security.md](../explanation/security.md).

## Alternatywy odrzucone
- **2 serwery (app publiczny ⟂ DB prywatny)** — lepsza izolacja i czystsza historia anty-DDoS, ale drożej; w labie nadmiar.
- **S3 / Backblaze B2 na offsite** — OK, ale Storage Box tańszy i prostszy (SFTP) dla tego zakresu.
