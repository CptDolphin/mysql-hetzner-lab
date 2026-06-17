# ADR-0001 — Provisioning: Terraform (infra) + Ansible (config)

- **Status:** zaakceptowany
- **Kontekst:** trzeba powtarzalnie tworzyć infrę w Hetzner Cloud i konfigurować maszynę (OS, MySQL, Docker), tak by dało
  się odtworzyć stack „od zera".

## Decyzja
**Terraform = infra** (serwer, firewall, Volume, Storage Box, klucz SSH). **Ansible = konfiguracja** wszystkiego na
maszynie (hardening, MySQL, backup, apka). Twarda granica — bez providerów konfiguracyjnych w TF i bez stawiania VM z Ansible.

## Konsekwencje
- (+) Czytelny `plan/diff` infry i mały blast-radius; jasny podział odpowiedzialności; spójność z `k8s-hetzner-lab`; dobry sygnał portfolio.
- (−) Dwa narzędzia do utrzymania i dwa stany mentalne; trzeba pilnować granicy.
- Stan Terraform poza repo; `prevent_destroy` na zasobach, których utrata boli.

## Alternatywy odrzucone
- **Pure Ansible (kolekcja `hetzner.hcloud`)** — jedno narzędzie, ale miesza warstwy i daje słabszy `plan/diff` infry.
- **Pure Terraform (provisioners/cloud-init do configu)** — antywzorzec do zarządzania konfiguracją w czasie.
