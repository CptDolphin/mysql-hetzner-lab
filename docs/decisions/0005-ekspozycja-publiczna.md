# ADR-0005 — Ekspozycja: aplikacja publiczna, obrona host/proxy (bez CDN/VPN)

- **Status:** zaakceptowany (zastępuje wcześniejszy szkic „zero portów / Cloudflare Tunnel + Tailscale")
- **Kontekst:** aplikacja **musi** być publicznie dostępna (to ona jest produktem i celem ataków). Baza nie jest publiczna.
  **Świadomie rezygnujemy z CDN/WAF (Cloudflare) i z VPN (Tailscale)** — celem jest nauczyć się i pokazać obronę
  pojedynczego, **publicznego** hosta, a nie schować go za cudzą infrastrukturą.

## Decyzja
- **Aplikacja publiczna** na 80/443 za reverse-proxy **nginx** (TLS przez certbot/Let's Encrypt + rate-limit + timeouty + limity ciała/połączeń).
- **SSH publiczny, utwardzony:** key-only, no-root, `fail2ban`, ew. port niestandardowy.
- **MySQL niepubliczny** — bind `127.0.0.1` (przez ProxySQL z apki).
- **Hetzner Cloud Firewall:** allow 22/80/443, reszta deny.
- **Obrona DDoS warstwowo na hoście:** sieć Hetznera (wolumetryczny L3/L4 — auto) + `nftables` (synproxy, conn-limit) +
  sysctl (SYN-cookies) + `fail2ban` + rate-limit w nginx + **izolacja zasobów apka⟂baza**.

## Konsekwencje
- (+) Uczciwa, mocniejsza historia portfolio: „utwardzony publiczny host", nie „DDoS robi za nas Cloudflare". Prościej (mniej usług zewnętrznych).
- (−) **Brak edge/CDN = twardy sufit:** dużego floodu L7 ani wolumetryki ponad auto-mitygację Hetznera **pojedynczy VM nie
  odbije** — i nie ma na to magii w Ansible. Origin-IP jest jawny. **Mówimy o tym wprost** ([security.md](../explanation/security.md) → Granice).
- (−) SSH publiczny = większa powierzchnia niż VPN; mitygacja: key-only + `fail2ban` (+ opcjonalnie self-hosted runner z
  KontrahentCheck, jeśli zechcemy zamknąć 22). Gra toczy się o: utwardzić host/proxy → ochronić bazę → szybko wstać.

## Alternatywy odrzucone
- **Cloudflare Tunnel + Tailscale (zero portów)** — najsilniejsze technicznie, ale (a) chcemy chronić publiczny host, nie chować;
  (b) ukrywa właściwy problem (obronę robi CF). Na roadmapie jako opcjonalna warstwa, nie teraz.
- **Sam Cloudflare proxy** — odrzucony wraz z rezygnacją z Cloudflare.
- **Model KontrahentCheck (Caddy + CF Access + UFW-z-CF-IP)** — sprawdzony, ale oparty o Cloudflare; nie kopiujemy.
  **Reverse-proxy piszemy sami na `nginx`** (bardziej znany niż Caddy, łatwiejszy do utrzymania przez innych) ([reuse-from-kontrahentcheck.md](../reference/reuse-from-kontrahentcheck.md)).
