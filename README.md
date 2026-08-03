# Poultry Management

A poultry operations app for **Frappe Framework v16 / ERPNext v16**: flock
management, feed, mortality, egg production, vaccination, batch traceability and
costing that rolls up to a true cost per bird and per kilogram.

Built to the *Poultry Management System — Software Design Document v1.1*.
Section references in the source (`§3.4`, `§7.5`, …) point back to it.

---

## What it does

| Module | Contents |
|---|---|
| **Poultry Setup** | Farm, Shed, Breed, Strain, Breed Standard, Feed Type, Egg Grade, Vaccine, Medication, Disease, Mortality Reason, Poultry Settings |
| **Flock Management** | Flock, Daily Flock Entry (+ mortality / feed / egg detail), Bird Weighing, Flock Closure |
| **Health & Biosecurity** | Vaccination Schedule Template, Flock Vaccination Plan, Vaccination Entry, Medication Entry, withdrawal enforcement |
| **Analytics** | 8 script reports, 2 desk dashboards, 8 number cards, 4 charts |

**Not yet built:** Hatchery, Processing, Contract Farming and the feed mill
(design doc modules 6, 7, 8 and part of 3). The flock spine, costing and
compliance are complete; those modules bolt on without changing them.

## Design decisions worth knowing

- **The flock is the spine.** Every transaction links to one. A doctype without
  a flock link is either a master or does not belong here.
- **Warehouse = shed.** Each shed auto-creates its warehouse on save.
- **Batch = flock.** One ERPNext Batch per flock, so a tray of eggs traces back
  to the flock, its feed and its medication history.
- **Derived, never entered.** Age, counts, FCR, ADG, EEF, HDP are computed.
- **Recomputed, never incremented.** Flock totals re-aggregate from submitted
  entries, so a cancel or amend self-corrects instead of drifting.
- **Standards are snapshotted at placement**, so editing a master never rewrites
  what a historical flock was measured against.
- **ERPNext core is never forked.** Item, Warehouse, Stock Entry, Batch, Project,
  Delivery Note stay native; the app adds doctypes that *drive* them plus custom
  fields.

## Requirements

- Frappe Framework v16, ERPNext v16
- Python 3.11+ (3.14 tested), Node 24 LTS, MariaDB 10.6+, Redis
- Stock Settings → **Activate Serial / Batch No for Item** must be on (batch
  tracking on bird items depends on it)

## Install

```bash
cd ~/frappe-bench
bench get-app poultry <repo-url> --branch version-16
bench --site <site> install-app poultry
```

`after_install` creates the custom fields, roles, workspaces, number cards,
charts, desk pages, icons and the reference masters (breeds, strains, breed
standards, vaccines, feed types, egg grades, vaccination schedules).

Then open **Poultry Settings** and set the mortality expense account and the
default egg warehouse.

### Demo data (optional)

Loads three farms, twelve sheds, nine flocks and roughly a month of daily
entries with real stock movement. Never run this on a production site.

```bash
bench --site <site> execute poultry.demo.install
```

### Health check

```bash
bench --site <site> execute poultry.doctor.run
```

Verifies the schema, the custom fields, the derived KPIs, stock-vs-flock
agreement, every report, the desk objects and the alert and withdrawal rules.

## Field client API

Writes are **POST only** — v16 rejects state-changing whitelisted methods over
GET, and this is the most likely integration failure.

| Endpoint | Method |
|---|---|
| `poultry.api.get_my_flocks` | GET |
| `poultry.api.get_flock` | GET |
| `poultry.api.get_flock_status` | GET |
| `poultry.api.submit_daily_entry` | POST |
| `poultry.api.submit_nothing_happened` | POST |
| `poultry.api.sync_batch` | POST |

Writes are idempotent on `(flock, posting_date)`, so an offline client can retry
safely; in `sync_batch` each row succeeds or fails independently.

## Layout

```
poultry/
├── poultry_management/
│   ├── doctype/          26 doctypes
│   ├── report/            8 script reports
│   ├── page/              2 desk dashboards
│   └── workspace/         4 workspaces
├── setup/                 install-time build: desk objects, icons, masters
├── demo/                  demo dataset (not installed by default)
├── api.py                 field-client endpoints
├── dashboard.py           data for the desk dashboards
├── compliance.py          withdrawal enforcement on outbound documents
├── poultry_utils.py       shared calculations
├── tasks.py               scheduled jobs
└── public/icons/          purpose-drawn poultry icon set
```

## Documentation

- [USER_GUIDE.md](USER_GUIDE.md) — how to run a farm on it, day to day.

## Licence

MIT
