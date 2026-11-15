# Jury Q&A Playbook — SPHEREx Motion Explorer

**NASA Space Apps Challenge 2026 · v0.5.1 · prepared 3 November 2026**

This is the rehearsal document for judging. Every answer below is grounded in the verified numbers in this repository (README, pitch PDF, tech PDF, `verification/` evidence). Rehearse the **Must-Ask Fifteen** first, then the category banks, then the signature stories. If a question isn't here, the "universal answer frame" in the last section covers you.

---

## 0. Fill before judging day

- [ ] Exact official challenge title (copy verbatim from your Space Apps dashboard)
- [ ] Team name / registration ID / country
- [ ] Public demo URL printed by `start_public.bat`
- [ ] GitHub repo link: `github.com/shree-aru/spherex-motion-explorer`
- [ ] Demo video link (when uploaded)

---

## 1. Elevator pitches (memorize all three)

**10 seconds (one sentence):**
> "SPHEREx Motion Explorer is a browser workbench that turns NASA's live IRSA SPHEREx archive into a blink-comparison experience — anyone can retrieve real exposures of any patch of sky and watch what changed between them."

**30 seconds:**
> "SPHEREx maps the entire sky every six months in 102 infrared bands — more than a billion objects — and things like comets, brown dwarfs and variable stars reveal themselves by changing or moving between images. We built a public web tool that queries the official NASA/IPAC IRSA archive live, retrieves every compatible real exposure for any coordinate, reprojects the FITS frames onto a common sky grid, and lets you blink, split, difference and sequence them — plus per-pixel wavelength awareness, bit-correct quality masking, on-the-fly spectra, and a Gaia proper-motion overlay. Everything is real data: zero simulated images."

**90 seconds (use when the judge says "walk me through it"):**
> "Enter any RA/Dec — say Barnard's Star — pick a data release and field size, and hit *Find observations*. We query IRSA's SIA v2 service live; for Barnard's Star that returned 130 dated QR3 records across a 37-day baseline. Every record shows its detector, wavelength range, and off-axis angle so you pick frames that actually contain the target. One click selects the widest target-centred baseline; we download the official FITS cutouts, read their FLAGS, VARIANCE and spectral-WCS extensions, mask only the genuinely fatal quality bits, reproject both frames onto one celestial grid with a shared brightness stretch, and render them. From there: blink them, split them, difference them, or play a 2–8 frame sequence. Scroll down and *Extract spectrum* sweeps up to 40 archive exposures in parallel and builds an exploratory 0.8–4.8 µm spectrum from all six detectors. Toggle the Gaia overlay and every field star gets an epoch-propagated ring — anything moving faster than 1 arcsec/year gets an amber ring, a motion arrow, and its measured speed, which is how the tool automatically flags Barnard's Star at 10.4 arcsec/year. And every screen, every export, tells you exactly what the tool *cannot* claim — it's a research aid, not a discovery certifier."

---

## 2. The Must-Ask Fifteen (near-certain judge questions)

### Q1. "What does your project do?"
**A:** One line: it makes temporal changes in NASA's SPHEREx all-sky infrared archive easy for anyone to see, using only real data. Concretely: live IRSA search → registered multi-epoch frames → blink/split/difference/sequence comparison → exploratory spectrum → Gaia motion overlay → reproducible evidence export.

### Q2. "Which challenge are you solving, and how?"
**A:** *(insert exact challenge title)* — the challenge asked for a public-facing web tool that displays SPHEREx images of any patch of sky and makes temporal changes easy to see. We deliver exactly that: any RA/Dec, any field 1–18 arcmin, live archive retrieval, and a purpose-built comparison workflow (blink, split, mean, B−A, 2–8 frame sequences) — verified end-to-end on all five of the challenge's recommended targets.

### Q3. "Is this real data? Prove it."
**A:** Every image comes from NASA/IPAC IRSA — SIA v2 for discovery, IBE for cutouts, TAP for Gaia. There is no synthetic sky image anywhere in the app; synthetic fixtures exist *only* inside offline unit tests, which the README declares. Proof points: each frame's response headers carry base64url provenance metadata (source URL, observation ID, release); the Evidence JSON export records observation IDs like `2026W33_2A_0594_3`, the QR3 dataset DOI `10.26131/IRSA662`, and a reproducible view URL; and the backend accepts only official IRSA FITS URLs — there is no arbitrary URL fetcher.

### Q4. "What exactly did you build vs. what already existed?"
**A:** The archive, the FITS files and the Aladin atlas component are the pre-existing parts, and we credit them. The workbench itself — the UI, the epoch-selection workflow, the flag-masking engine, the per-pixel local-wavelength lookup, the parallel spectrum extractor, the Gaia proper-motion overlay, the two-layer AllWISE atlas integration, the evidence manifests — is ours, built from scratch. Aladin Lite is vendored *only* for reference-atlas context and is visually separated from SPHEREx science frames.

### Q5. "Why is this different from IRSA's own viewers or Aladin?"
**A:** Those are excellent discovery tools, but none is built around the *time-domain comparison* workflow the challenge asks for. Our differentiators: (1) multi-epoch blink/split/difference/sequence with one shared brightness stretch; (2) bit-correct SPHEREx flag masking — the naive approach erases the stars; (3) per-pixel local wavelength that exposes mismatches file-level metadata hides; (4) on-the-fly multi-exposure spectrophotometry; (5) an epoch-propagated Gaia overlay that auto-flags fast movers; (6) evidence exports that make any view reproducible from archive IDs. We're a complement to IRSA's tools, not a replacement — everything still flows through their official services.

### Q6. "Show me it works." *(demo failure = lost points)*
**A:** Follow `docs/DEMO_SCRIPT.md`: Barnard's Star → Find observations → Use widest baseline → show the coverage card (130 records, 37-day baseline) → Blink → B−A → Gaia overlay (amber ring, 10.4″/yr) → Extract spectrum → Evidence JSON. **If the network fails:** show the honest error state, open the saved query URL, then play the pre-verified real-data screenshots in `docs/` — never fake a live result.

### Q7. "What are the limitations? Be honest."
**A:** *(Judges reward honesty — answer without flinching.)* Local wavelengths are visualization-grade WCS-WAVE lookups, not survey-grade spectral WCS; difference modes are visual triage aids, not calibrated photometry — no PSF matching or absolute calibration yet; the spectrum is exploratory with statistical-only errors; proper-motion prediction is first-order and excludes parallax; SIA discovery caps at 600 records per query; the AllWISE context layer is bounded by the ~1.25° coadd tile. Every one of these is stated in the app itself — that's deliberate.

### Q8. "How would someone replicate your project?"
**A:** Clone the repo, double-click `run_windows.bat` (or `bash run_unix.sh`, or `docker build/run`) and open http://127.0.0.1:8000. No build step, no database, no API keys — just Python and outbound access to irsa.ipac.caltech.edu. The full pipeline is documented in the tech PDF, and the API spec is live at `/docs`.

### Q9. "Who is this for and what's the impact?"
**A:** Three audiences. Citizen scientists: a zero-install workbench mirroring the professional blink-comparison workflow that discovered Pluto in 1930. Educators/students: real mission data with the physics — variable filters, saturation, proper motion — made visible instead of hidden. Researchers: a fast triage layer over IRSA for wavelength-matched epoch selection, quick spectra, and reproducible evidence exports.

### Q10. "How did you use AI in building this?"
**A:** *(Space Apps requires transparency.)* Answer honestly, e.g.: "AI-assisted development tools accelerated coding, drafting and documentation under our direction; every scientific decision — flag-bit semantics, WCS handling, masking policy — was verified by us against the official SPHEREx Explanatory Supplement, and every performance number in our submission was measured live against the real archive. The tool contains no AI-generated sky content, and we're happy to point to any line of code and explain it."
**Before judging, agree internally on the exact disclosure wording you'll give — consistency matters.**

### Q11. "Who did what, and how long did it take?"
**A:** *(Fill in your real team split.)* Anchor on milestones: v0.2 offline prototype → v0.3 competition-hardened UI → v0.4 live-data verification → v0.5 science core (flags, λ, spectrum, Gaia) → v0.5.1 22/22 live checks on all five targets.

### Q12. "The archive goes down right now. What happens?"
**A:** The app retries (SIA ×3, cutouts ×3, TAP ×2, IBE ×3), then shows an explicit error state — it never substitutes invented imagery. Our backup plan: live error state + the official query URL to show the request was correct, then verified real-data screenshots/recording from `docs/` and `verification/`. A documented fallback demo field (ε Indi B or RW Aurigae) is also pre-tested in case one target has no coverage.

### Q13. "What's next for the project?"
**A:** Roadmap order: SIA pagination beyond 600 records; PSF-matched difference photometry using the EPSF extension; official IRSA spectrophotometry cross-checks; solar-system path overlays (MOST) so known asteroids are never mistaken for discoveries; multi-tile AllWISE mosaics; a hosted always-on deployment; then a Tauri-based Windows app reusing the same frontend.

### Q14. "Why should this win?"
**A:** Three reasons. **Verified, not claimed:** every number we present was measured against the live archive — 130 records, 40/40 spectrum points, 22/22 live checks on all five targets. **Science integrity as a feature:** we caught the flag-bit trap (bit 21) that makes naive tools blank out the stars, and we publish what our tool cannot do. **Real accessibility:** no build step, no keys, runs anywhere from a Windows laptop to Docker — the sky belongs to everyone, and honest tools make better discoveries.

### Q15. "Could this actually discover something?"
**A:** It's built to *enable* discovery and to *prevent false ones*. It gives humans the same triage workflow professionals use — multi-epoch comparison, wavelength matching, motion reference overlay — and exports the evidence needed to follow up. What it does not do is certify: residuals are review cues, not detections, and we say so on every screen. A citizen scientist using this would arrive at a professional follow-up with reproducible archive IDs — that's the right way for public tools to contribute.

---

## 3. Signature stories (your strongest 60-second assets)

Use these when you want a memorable answer, not just a correct one.

### Story 1 — The flag-bit trap (bit 21)
> "The first time we rendered real SPHEREx data, Barnard's Star was *invisible*. The naive approach — mask every pixel with any flag set — deleted 96% of the image, because SPHEREx sets bit 21, 'SOURCE', on pixels containing real star flux — on ~84% of pixels in typical fields. The fix wasn't our invention; it was reading the official Explanatory Supplement bit table (SSDC-DP-017 v2.0). Only genuinely fatal bits — saturation, non-linearity, persistence, satellite streaks — get masked; SOURCE and FULLSAMPLE are never masked. That restored 95% valid coverage, and the stars came back. It's why we distrust any tool that doesn't read the flag documentation."

### Story 2 — The hidden wavelength mismatch
> "Two exposures of the *same detector band* should be comparable, right? File-level metadata said both D3 frames span 1.63–2.43 µm. But SPHEREx uses linear variable filters — the sampled wavelength depends on where the target lands on the detector. We map the target through the exposure's WCS to the 9×9 WCS-WAVE lookup grid, and the two frames actually sampled **1.728 vs 2.224 µm** — a 0.50 µm mismatch invisible in the metadata. We also measured 0.776 vs 1.005 µm across two D1 epochs. Comparing frames without knowing this would silently corrupt any difference image. Our tool reports local λ at the target for every frame and verdicts every A/B pair."

### Story 3 — The auto-flagged fast mover
> "We overlay Gaia DR3 stars, propagated to the observation epoch, on every rendered frame. Then the tool checks each source's proper motion: anything faster than 1 arcsec/yr gets an amber ring, a motion arrow, and its measured speed. The first field we tried, it immediately flagged Barnard's Star at **10.4 arcsec per year** — the tool found the fastest-moving nearby star on its own, with no human hinting."

---

## 4. Category banks

### 4.1 Project & challenge

| Q | A |
|---|---|
| "Summarize the challenge in your own words." | Display SPHEREx imagery of any sky patch publicly, and make temporal changes (motion, variability) easy for anyone to see — without drowning in a billion-object archive. |
| "Why did you pick this challenge?" | SPHEREx is the newest all-sky infrared survey and the time-domain comparison workflow it enables is the same one that discovered Pluto — a perfect fit for a public tool. *(Add your genuine team reason.)* |
| "What is SPHEREx?" | NASA's all-sky near-infrared spectral survey mission: maps the entire sky every six months in 102 spectral bands (~0.75–5 µm) with six detectors and linear variable filters, returning images of over a billion objects. |
| "What are the five challenge targets?" | Barnard's Star (fast proper motion), ε Indi B (nearby brown-dwarf binary), WISE 0855−0714 (ultra-cold brown dwarf, epoch-sensitive coordinates), RW Aurigae (young variable star), R Draconis (Mira variable — variability, not fast motion). All five pass our 22/22 live verification sweep. |
| "Why blink comparison?" | It's the classic time-domain technique — Clyde Tombaugh discovered Pluto in 1930 by blinking photographic plates. Human vision excels at spotting what changes between two aligned frames. |
| "Is this official NASA software?" | No — an independent, educational/citizen-science application. NASA/SPHEREx/IRSA data and names are credited; no NASA insignia or logos are used; Aladin's native attribution is intact. |

### 4.2 Science & mission

| Q | A |
|---|---|
| "What is a linear variable filter (LVF)?" | A filter whose transmitted wavelength varies with position on the detector — so the wavelength sampled at a sky position depends on *where it lands* on the chip. That's why SPHEREx gets 102 bands without filter wheels, and why we compute per-target local wavelength instead of trusting band labels. |
| "Why do two frames of the same band sample different wavelengths?" | LVF position-dependence + the spacecraft pointing differing between visits. Verified example: 1.728 vs 2.224 µm on two D3 frames. |
| "What's in a SPHEREx FITS file?" | L2b products: IMAGE, FLAGS (32-bit status bitmap), VARIANCE, ZODI (zodiacal background model), plus celestial WCS and the 9×9 WCS-WAVE spectral lookup grid. We read all of them. |
| "Why does flag handling matter so much?" | Flags are status bitmaps, not booleans. Some bits are fatal (saturation, non-linearity, satellite streaks); bit 21 SOURCE marks star flux and must never be masked. Naive masking → 0.15% valid pixels → blank sky. |
| "How do you compute local wavelength?" | Map the target through the exposure's celestial WCS to a cutout pixel, convert via the alternate LINEAR 'A' WCS to original detector coordinates, then bilinearly interpolate the 9×9 WCS-WAVE grid. Visualization-grade, clearly labelled. |
| "How does the spectrum extraction work?" | Parallel sweep of up to 40 archive exposures (API allows 4–60): r=2 px aperture sum, 3–6 px annulus background, errors from the quadrature sum of the VARIANCE extension, each point's wavelength from its own exposure's spectral WCS. Saturated cores fall back to the display mask and are flagged `saturated_core=true` — a labelled lower limit, never a silent wrong number. |
| "Is your spectrum calibrated?" | It's exploratory spectrophotometry with statistical errors — verified 40/40 points from 0.795–4.836 µm, all six detectors, SNR 175–406 on Barnard's Star. Cross-check against IRSA's official spectrophotometry is on the roadmap. |
| "What is proper motion and how do you handle it?" | Apparent sky motion of nearby stars. Our overlay propagates Gaia DR3 positions to the observation epoch and flags >1″/yr movers. The target-search predictor is a first-order approximation, explicitly labelled as excluding parallax, radial velocity and orbital effects. |
| "Why is WISE 0855 tricky?" | Its coordinates are epoch-sensitive and it's a very high proper-motion object — historical catalogues can point you at empty sky. This is why we propagate to the observation epoch. |
| "Could you find Planet Nine?" | No — and we won't pretend. Those searches need deep difference imaging and certified photometry. But the *workflow* we expose (blink, wavelength-matched epochs, motion overlay) is genuinely how moving objects are found; it's an education-and-triage tool. |

### 4.3 Data & archive

| Q | A |
|---|---|
| "What is IRSA?" | NASA/IPAC Infrared Science Archive — the official permanent home of SPHEREx data, plus WISE, Gaia services and more. We use only IRSA-hosted sources. |
| "What are SIA, IBE, TAP?" | Three standard virtual-observatory services: SIA v2 (image metadata discovery), IBE (cutout/file access), TAP (catalogue queries — we use it for Gaia DR3). |
| "What is QR3? Why not higher releases?" | SPHEREx Quick Release 3 at IRSA — a documented, DOI'd dataset (10.26131/IRSA662). We support QR3 and QR2, wide and deep collections, with automatic QR3→QR2 fallback when QR3 lacks coverage. |
| "Wide vs deep?" | Two SPHEREx survey programmes with different cadence/depth; the UI switches collections and the records tell you which one you're in. |
| "How do you guarantee provenance?" | Only official IRSA URLs accepted (host + path + .fits allowlisted); provenance metadata in every render response header; Evidence JSON with observation IDs, DOI, caveats; reproducible view URLs. |
| "Empty result — what does it mean?" | Missing coverage, release mismatch, query limit, epoch-mismatched coordinates, or an off-detector frame. The app states this explicitly and never invents data. "Empty" ≠ "the object doesn't exist." |
| "Why cap at 600 records / 96 sampled rows?" | Responsiveness. UTC date filters and detector-range selection reduce sampling bias; full pagination is the top roadmap item. We disclose the cap rather than hide it. |
| "Your machine's network blocked CDS — how does the atlas still work?" | AllWISE mid-IR imagery comes from IRSA (always reachable for us) and is the default; Aladin Lite v3 is vendored locally (no CDN); CDS HiPS optical surveys are offered but honestly reported as unavailable when the network blocks them. |

### 4.4 Technical architecture

| Q | A |
|---|---|
| "Describe the architecture in one breath." | Vanilla HTML/CSS/JS frontend (3 files, no build step) → FastAPI same-origin backend (httpx with retries) → Astropy + reproject + numpy science core → NASA/IPAC IRSA. No database; bounded LRU caches. |
| "Why no React/Angular/bundler?" | Volunteers must be able to read and run every line; zero build step = zero toolchain failures on judging day, and it runs on any machine from a double-click. |
| "Why FastAPI + Python?" | The science is Python-native (astropy is the field standard for FITS/WCS); FastAPI gives validated, documented endpoints for free (spec at `/docs`). |
| "How does reprojection work?" | Each cutout's celestial WCS is reprojected onto a common TAN sky grid (reproject library), so A/B and sequence frames are pixel-aligned; sequence uses one common WCS and one shared brightness stretch. |
| "Walk me through a render request." | `/api/render` → validate tokens → fetch official cutout (≤28 MB) → read FLAGS/VARIANCE/ZODI/WCS → bit-aware mask → reproject → shared stretch → compose mode (a/b/mean/difference) → PNG + base64url provenance header. |
| "How are sequences built?" | 2–8 tokens → common WCS + shared stretch → chronological PNG frames + metadata; mixed detectors are allowed but explicitly marked unsuitable for quantitative comparison. |
| "What's cached?" | Bounded LRU caches: cutouts (48), rendered frames (24), atlas products (16). Stateless otherwise — scale by running more containers. |
| "Deployment story?" | Dockerfile (python:3.12-slim) runs uvicorn on $PORT as an unprivileged user — any container host. For zero-cost demos, `start_public.bat` launches server + Cloudflare quick tunnel and prints a public HTTPS URL. |
| "Mobile support?" | Responsive dark workbench UI; tested at mobile widths since v0.3. |

### 4.5 Security & integrity

| Q | A |
|---|---|
| "Any security measures?" | SSRF hardening (base64url tokens validated against allowlist: https, irsa.ipac.caltech.edu host, /ibe/data/spherex/ path, .fits only, no query strings/credentials); trusted-host checks; coordinate validation; bounded sizes (28 MB cutouts, 60 MB tiles, 8-frame sequences, 60-file sweeps); net-check hosts allowlisted. No arbitrary URL fetcher exists. |
| "Why does security matter in a read-only demo?" | Because it takes arbitrary user coordinates and fetches remote data — the classic SSRF pattern. We allowlist at the URL level, not just the UI level. |
| "How is the code tested?" | 29 offline unit tests: flag semantics (bit 21 never masked), palette-free rendering, aperture photometry on synthetic frames, spectral-WCS interpolation, file sampling, API validation, HTML/JS id contract. Plus a 22-check live verification sweep across all five challenge targets. |
| "Is user data collected?" | No accounts, no tracking, no local database. Share links encode the view in the URL itself. |
| "Licensing?" | MIT-style LICENSE + THIRD_PARTY.md crediting NASA/IRSA data, Aladin Lite (CDS), astropy/reproject ecosystems. |

### 4.6 Trust, honesty & the tough ones

| Q | A |
|---|---|
| "Everything says 'exploratory' — did you actually finish the challenge?" | Yes: the challenge's core ask — display any sky patch and make temporal changes easy to see — is fully delivered with live data. The 'exploratory' labels concern *calibration-level* claims (difference photometry, discovery certification). Declining to overclaim is the professional standard, not an incomplete build. |
| "Your B−A shows something bright — is that a discovery?" | It's a review cue, not a detection. Percentile-thresholded, display-pixel-only, no PSF matching or noise model. The correct next step is exactly what the Evidence JSON enables: reproducible archive IDs for professional follow-up. |
| "Why does the star vanish in B−A?" | Depending on mode and masking, saturated cores may behave differently between frames; difference modes are visual aids. If wavelengths differ at the target (check the λ-match verdict), brightness differences can be a filter effect, not a physical change. |
| "You say honest, but you exaggerate Gaia arrows 50×." | Deliberately and visibly: motion at 10″/yr is sub-pixel on most fields, so arrows are scaled 50× and labelled. The *measured speed* shown in text is real; the arrow is a visual amplifier. |
| "What claims can't you make?" | (From `docs/COMPETITION_READINESS.md`:) a residual is a confirmed object; B−A is calibrated photometry; detector ranges are uniform; the app measures motion significance; an empty response means the object is absent. We've written these prohibitions into our own docs — that's the point. |
| "Why should a judge trust numbers you generated yourselves?" | Because they're derived only from official archive services and open libraries, every value is traceable to observation IDs and the dataset DOI, the pipeline is unit-tested, and we publish our own limitations list. Reproduce it yourself in 60 seconds from the repo. |

### 4.7 Wildcards & hypotheticals

| Q | A |
|---|---|
| "What would you do differently?" | Start live-data verification on day one (we verified offline first and found the flag-bit trap only with real data); build pagination earlier. *(Personalize.)* |
| "If NASA gave you a year…" | PSF-matched calibrated difference photometry with uncertainty maps, MOST solar-system overlays, full pagination, six-detector coadds with official calibration, hosted deployment, and classroom lesson plans. |
| "How would you scale to all users?" | Stateless containers behind any load balancer; IRSA carries the data load. The honest bottleneck is IRSA rate limits, not our stack — caching and pagination are the levers. |
| "Coadds/cubes exist — why use L2b exposures?" | Coadded cubes average over time — they're the wrong product for detecting change between epochs. L2b per-exposure frames are exactly what time-domain comparison needs. |
| "Why is the UI dark / what's the design language?" | An original instrument-style dark workbench (astronomy-standard), hand-authored — no cloned dashboard template. Designed so metadata, λ verdicts and caution cards sit beside the data, not behind menus. |
| "Does it work offline?" | No — by design it's a live archive client. It refuses to fake data offline; unit tests are the only place synthetic fixtures exist. |
| "What's the hardest bug you hit?" | The flag-bit blank-sky bug (Story 1), followed by the non-square spectral-image cutout geometry that required size compensation. |
| "One feature you'd remove?" | *(Honest reflection, e.g.,)* the 96-row SIA sampling heuristic — pagination would replace it properly. |

---

## 5. Numbers cheat sheet (quote exactly)

| Number | Meaning |
|---|---|
| **102** | spectral bands, ~0.75–5 µm, whole sky every **6 months**, **1B+** objects |
| **6** | detectors (D1–D6) — verified spectrum uses all six |
| **130 / 37 d** | QR3 records / temporal baseline verified for Barnard's Star |
| **40/40** | spectrum points extracted, 0 failures; 0.795–4.836 µm; SNR 175–406 |
| **10.4″/yr** | Barnard's Star proper motion, auto-flagged by Gaia overlay (>1″/yr threshold) |
| **~300** | Gaia DR3 reference stars overlaid per field |
| **95% vs 0.15%** | valid pixel coverage: bit-correct masking vs naive `flags != 0` |
| **0.50 µm** | hidden wavelength mismatch found inside one D3 band (1.728 vs 2.224 µm) |
| **22/22** | live verification checks passing on all five challenge targets |
| **29** | offline unit tests |
| **600 / 96 / 18′ / 28 MB / 8** | SIA cap / sampled rows / max FOV / cutout cap / max sequence frames |
| **×3 ×3 ×2 ×3** | retries: SIA, cutouts, TAP, IBE |
| **10.26131/IRSA662** | SPHEREx QR3 dataset DOI |
| **3 files / 0 build steps / 0 API keys / 0 DBs** | frontend footprint |
| **Example obs ID** | `2026W33_2A_0594_3` — 2026-08-16T15:06 UTC, D3, 1.6301–2.4346 µm |

---

## 6. Claims discipline (never say / always say)

**Never say:**
- "We discovered / detected / confirmed…" anything.
- "The B−A image is calibrated difference photometry."
- "Same detector = same wavelength."
- "An empty result means the object isn't there."
- "Our app measures motion significance / validates discoveries."
- "Official NASA software."

**Always say:**
- "Live data from NASA/IPAC IRSA — verified, DOI'd, reproducible."
- "Exploratory / review aid / research aid — and here's exactly what that means."
- "Here's what the tool cannot tell you." *(this sentence wins trust)*

**If you don't know an answer:** "That's outside what we've verified so far — here's what we *do* know about it, and here's how we'd find out." Never guess a number not in this document.

---

## 7. Questions to ask the judges back

- "Would this be useful in your own workflow / classroom?"
- "Which of our honesty features did you find most valuable — or most surprising?"
- "Is there an IRSA capability we should integrate next?"
- "What would make you trust a citizen-science tool enough to act on its output?"

---

*Sources: README.md, docs/COMPETITION_READINESS.md, docs/DEMO_SCRIPT.md, docs/gen_pitch.py, docs/gen_tech.py, verification/spherex_evidence_2026-11-02.json. If any answer conflicts with a live demo, the live demo wins — and we say so.*
