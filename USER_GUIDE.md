# Poultry Management — User Guide

For farm managers, supervisors, veterinarians and accounts staff using the
Poultry app on ERPNext v16.

---

## 1. The idea in one page

The **flock is the spine**. Every number in this system hangs off a flock: the
feed it ate, the birds it lost, the eggs it laid, the vaccines it got, and what
it cost. Nothing is entered twice.

Two numbers a day are mandatory: **mortality** and **feed**. From those, plus
the placement details and the breed standard, the system derives livability,
FCR, ADG, EEF, HDP and full costing. Everything else on every screen is optional
— a farm that gives more data gets more back, and a farm that gives only the two
numbers still gets a complete performance picture.

Three rules worth knowing, because they explain most of the behaviour:

| Rule | What it means for you |
|---|---|
| **Derived, never entered** | Age, closing count, FCR, EEF, HDP are greyed out. You cannot type them, and you never need to. |
| **Recomputed, never incremented** | Totals are re-added from the daily entries each time. Cancel or amend a wrong day and every total corrects itself. |
| **Standards are snapshotted** | The breed standard is frozen onto the flock at placement. Editing the master later never rewrites history. |

---

## 2. Getting around

Open the **Poultry** app from the app switcher (top-left). The sidebar gives you:

| Screen | Use it for |
|---|---|
| **Poultry Control Tower** | The morning check. Every flock as a card, worst first. |
| **Flock 360** | One flock, end to end, plotted against its standard. |
| **Daily Flock Entry** | The daily record. |
| **Flock** | Placing, tracking and closing flocks. |
| **Shed** | Which shed holds what, and how long the empty ones have been idle. |
| **Vaccination Entry / Medication Entry** | Health records and withdrawal control. |
| **Poultry Setup / Health / Analytics** | Masters, health module, all reports. |

### The Control Tower

The board you open first each day.

- **Eight tiles** across the top: birds on hand, sheds occupied, eggs and feed
  today, losses today, entries still pending, overdue vaccinations, and flocks
  that cannot be sold.
- **Flock cards**, sorted so anything needing action is first. The colour strip
  on the left is the verdict:
  - **Red** — an alert fired in the last three days, or the flock is under
    withdrawal.
  - **Amber** — today's entry has not been made yet.
  - **Green** — nothing to do.
- Click any card to open **Flock 360** for that flock.
- Two panels at the bottom: overdue vaccinations (with how late each is) and
  the alerts raised this week.

### Flock 360

Pick a flock at the top, or arrive by clicking a card.

- KPI tiles change with the flock type — broilers show **FCR and EEF**, layers
  show **HDP and eggs per bird housed**.
- **Body weight vs standard** and **cumulative mortality vs standard** are
  plotted day by day. The grey line is the standard this flock was measured
  against; the coloured line is reality. The gap between them is the story.
- Below: the vaccination plan with status, the last fourteen daily entries, and
  any medication with its withdrawal date.

---

## 3. Setting up a farm

Do this once per site, in order. **Poultry Setup** workspace.

1. **Farm** — name, type (Broiler / Layer / Rearing / Breeder), company,
   capacity, village and district, contact mobile. Set a **Cost Center** here;
   flocks inherit it.
2. **Shed** — pick the farm, give a shed code and capacity, choose the housing
   system. On save the shed **creates its own warehouse** (`<Farm> <Shed> - <ABBR>`).
   You do not create warehouses by hand; a missing warehouse is the most common
   cause of failed stock entries.
3. **Breed** and **Strain** — Cobb, Ross, Hy-Line, BV and so on. Strain carries
   the supplier and typical cycle length.
4. **Breed Standard** — one row per age in days: target body weight, daily and
   cumulative feed, expected cumulative mortality, and for layers the hen-day
   production curve. Tick **Is Default for Strain** so flocks pick it up
   automatically.
5. **Feed Type** — links a feed to an **Item**, an age window and a bag weight.
   The age window is what makes the app suggest the right feed for the flock's
   age.
6. **Egg Grade** — grade code, weight band, the **Item** it stocks as, and
   whether it is saleable, a hatching egg or a reject.
7. **Vaccine**, **Poultry Medication**, **Poultry Disease**, **Mortality Reason**
   — the health masters. Medication carries **withdrawal days**, which is what
   later blocks sales.
8. **Vaccination Schedule Template** — age in days plus vaccine and route. Mark
   one as default per flock type.
9. **Poultry Settings** — see §8.

---

## 4. Running a flock

### 4.1 Placing

**Flock → New.** Fill in: name, farm, shed, flock type, breed and strain,
placement date, bird item, and the number placed. Optionally record
**parent flock age in weeks** — chicks from very young or very old breeders
behave differently, and this is often the field that explains an otherwise
unexplained result.

Save, then run **Place Flock**. In one step this:

- creates the ERPNext **Batch** named after the flock,
- **snapshots the breed standard** onto the flock,
- opens a **Project** as the costing container,
- generates the **Flock Vaccination Plan** with real due dates,
- marks the shed **Occupied**,
- posts a **Stock Entry** receiving the day-old chicks into the shed warehouse.

Two things the system will tell you:

- Placing more birds than the shed's capacity gives a **warning, not a block**.
  Overcrowding is a business decision, not a data error.
- Placing a second flock in an occupied shed **is blocked**. All-in all-out is a
  biosecurity requirement.

### 4.2 The daily entry

**Daily Flock Entry → New**, or from the Control Tower. One per flock per day,
enforced.

Enter only what you have:

| Field | Notes |
|---|---|
| **Mortality / Culls** | The first mandatory number. Add a mortality detail row to say why. |
| **Feed** | The second. Enter **bags** — the system converts to kg using the feed type's bag weight. |
| Water, body weight, uniformity | Optional. Weekly weighing is enough. |
| Eggs | Enter **trays**; the system converts at 30 per tray. |
| Environment | Temperature, humidity, litter, light hours. Optional. |

Everything else fills itself: age, opening count (read from the ledger, not
carried forward), closing count, mortality %, cumulative mortality %, cumulative
feed, feed per bird, water:feed ratio and hen-day production.

**On submit**, the entry posts up to three stock entries: feed issued from the
shed warehouse, dead and culled birds written off to the mortality expense
account, and eggs received into the cold store — all tagged to the flock.

Cancel an entry and those stock entries reverse and the flock totals
re-aggregate. Nothing drifts.

### 4.3 What the system will argue with

These are deliberate. They catch the mistyped figure before it reaches the
ledger.

| Situation | What happens |
|---|---|
| Deaths exceed birds alive | **Blocked.** |
| More than 5% of the flock lost in a day | Warning; confirm and continue. |
| Feed above 250 g per bird per day | Warning; confirm and continue. |
| Duplicate entry for the same flock and date | **Blocked.** |
| Date before placement, or in the future | **Blocked.** |
| Backdated beyond the window (default 30 days) | **Blocked** — a manager raises the limit in Poultry Settings. |

Backdating **within** the window is allowed on purpose. Farms miss days, and
late data is far more useful than absent data.

### 4.4 Alerts

Every submitted entry is checked and, if something is off, carries an alert that
appears on the entry, on the Control Tower and in the reports:

- daily mortality above the spike threshold (default 0.5%),
- body weight more than ±10% from standard for the age,
- cumulative mortality more than 1.5× the standard,
- water:feed more than 1.25× standard — this one often moves *before* anything
  is visible in the shed,
- the flock is inside a medication withdrawal window.

### 4.5 Weighing

**Bird Weighing** — enter how many birds you weighed and the total grams. The
average, the standard for that age and the variance are calculated. A weighing
outranks the estimate on a daily entry when the flock's KPIs are computed.

### 4.6 Closing

**Flock → Close Flock**, giving the closure date, the live weight actually sold
and the revenue. This freezes the KPIs into a **Flock Closure** document, marks
the flock Closed, completes the Project, and sends the shed to **Cleaning** so
downtime starts accruing.

---

## 5. Health and compliance

### Vaccination

The plan is generated at placement from the schedule template, with due dates
calculated from the placement date. Record the real event as a **Vaccination
Entry**, including the **vial batch and serial** — that is what an audit asks
for. Submitting the entry closes the matching planned dose, so the compliance
report reflects reality rather than a parallel tick-list.

**Vaccination Compliance** report shows planned against done, how late each dose
was, and what is overdue right now.

### Medication and withdrawal — the important one

Record a **Medication Entry** with the drug, dates and dose. The system sets
**withdrawal clear date = end date + withdrawal days**.

From that moment until the clear date:

- the flock shows a withdrawal warning on the Control Tower and Flock 360,
- it appears in the **Withdrawal Period Alert** report,
- and any **Delivery Note or Sales Invoice** carrying that flock's batch is
  **blocked on submit**, naming the drug and the date it clears.

This is the highest-value control in the system. Residue violations are what get
consignments rejected and licences reviewed.

---

## 6. Reports

**Poultry Analytics** workspace.

| Report | Read it when |
|---|---|
| **Flock Performance vs Standard** | You want the day-by-day story of one flock, actual beside standard. |
| **Broiler Batch Summary** | Ranking finished and running batches by EEF, with cost per kg. |
| **Layer Production Curve** | Checking HDP against standard by week, and persistency after peak. |
| **Mortality Analysis** | Grouped by reason, category, age band, shed, farm or flock. |
| **Feed Consumption and FCR Trend** | Feed drawn per week with cost, FCR to date, and feed cost per dozen eggs. |
| **Vaccination Compliance** | Before an audit, or when something went wrong. |
| **Withdrawal Period Alert** | Before committing a load to a buyer. |
| **Shed Utilisation and Downtime** | Which sheds are earning and which are standing empty. |

**How to read EEF:** below 250 is poor, around 300 average, 350+ good, 400+
excellent.

---

## 7. What lands in ERPNext

The app never replaces ERPNext's own documents — it drives them. After a month
of use you can open standard ERPNext and find:

- **Stock Ledger** — chicks in, feed out per shed, mortality written off, eggs
  in. Every line tagged with its flock.
- **Stock Balance** — live birds per shed and eggs in the cold store.
- **Batch** — one per flock, so a tray of eggs traces back to the flock, its
  feed and its medication history.
- **Project** — one per flock, carrying the cost.
- **Purchase Receipt / Sales Invoice** — feed bought, eggs and birds sold.
- **Profit and Loss** — with mortality write-off as its own expense line.

---

## 8. Poultry Settings

| Setting | What it controls |
|---|---|
| **Modules** | Turn egg management, hatchery, processing, contract farming, breeder and feed mill on or off. |
| **Data Tier** | Tier 1 = mortality and feed only. Tier 2 adds eggs, weight and water. Tier 3 adds environment. |
| **Allow Backdated Entry / Max Backdate Days** | The window for late entry. Default 30 days. |
| **Default Bag Weight / Eggs per Tray** | The conversion factors. Default 50 kg and 30. |
| **Alert thresholds** | Mortality spike %, weight deviation %, cumulative mortality factor, water:feed factor. |
| **Post Stock Entries on Daily Entry** | Whether daily entries move stock. On by default. |
| **Mortality Expense Account** | Where dead birds are written off. |
| **Default Egg Warehouse** | Where collected eggs are received. |
| **Auto Create Vaccination Plan** | Generate the plan at placement. |

---

## 9. Roles

| Role | Can do |
|---|---|
| **Farm Supervisor** | Create and submit daily entries, vaccinations and weighings. Read-only elsewhere. |
| **Farm Manager** | Full operational access. Create and close flocks. No settings. |
| **Veterinarian** | Full health module; read access to flocks and entries across farms. |
| **Poultry Accounts** | Costing and reporting; read-only on operations. |
| **Poultry Manager** | Everything, including settings and masters. |

Restrict a user to their own farms with standard **User Permissions** on the
Farm doctype — it cascades to sheds, flocks and every flock-linked transaction.

---

## 10. Field data capture

The desk is a laptop application. For staff in a shed, the app exposes a REST
API for a lightweight field client:

| Endpoint | Purpose | Method |
|---|---|---|
| `poultry.api.get_my_flocks` | Active flocks with entry status and days pending | GET |
| `poultry.api.get_flock` | Everything one entry screen needs, incl. suggested feed | GET |
| `poultry.api.get_flock_status` | A status colour and one plain sentence | GET |
| `poultry.api.submit_daily_entry` | The single write; accepts bags and trays | **POST** |
| `poultry.api.submit_nothing_happened` | Zero deaths, standard feed, one tap | **POST** |
| `poultry.api.sync_batch` | Bulk upload of queued offline rows | **POST** |

Two things a client author must know:

- **Writes are POST only.** ERPNext v16 rejects state-changing whitelisted
  methods called over GET. This is the single most likely integration failure.
- **Writes are idempotent on (flock, date)**, so an offline client can retry a
  queued row safely. In a `sync_batch`, each row succeeds or fails on its own —
  one bad day never blocks the rest.

---

## 11. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| "Shed already holds active flock X" | All-in all-out is enforced. Close the existing flock first. |
| "Entry is N days old; the limit is 30" | Raise **Max Backdate Days** in Poultry Settings, or have a manager enter it. |
| Sale blocked with a drug name | The flock is inside a withdrawal window. The message gives the date it clears. |
| Feed issue fails with insufficient stock | Feed has not been received into that **shed's** warehouse. Post the Purchase Receipt against the shed warehouse. |
| Flock KPIs look stale | They recompute on submit and nightly. Cancel-and-amend any wrong entry; totals re-aggregate. |
| Stock Balance disagrees with the flock | Backdated postings queue **Repost Item Valuation** jobs. Let the scheduler finish, or run the repost manually. |
