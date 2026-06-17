# molecule-template — harness testowy ról

Wzorzec scenariusza Molecule dla **każdej** roli (zasada z `CLAUDE.md`: rola = test w jej PR).

## Użycie (przy tworzeniu roli `<rola>`)
```bash
cp -r ansible/molecule-template ansible/roles/<rola>/molecule
# w converge.yml zamień REPLACE_WITH_ROLE_NAME na <rola>
cd ansible/roles/<rola> && molecule test
```
`molecule test` = create → **converge** → **idempotence** (2. run = 0 changed) → **verify** (Testinfra) → destroy.

## Co sprawdzamy
- **Idempotencja** — drugi `converge` nie zmienia stanu (gate w CI).
- **Testinfra** (`tests/test_default.py`) — serwis up, port słucha/zamknięty, config/usery poprawne.

CI uruchamia to dla każdej roli mającej `molecule/default/` (workflow `ansible-test.yml`).
