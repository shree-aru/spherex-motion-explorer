// Project QoreX — Space Apps 2026 demo deck (6 slides, <=7 rule)
// Palette: white / mission red / near-black. Fonts: Arial Black + Arial + Consolas.
const pptxgen = require("pptxgenjs");

const BG = "FFFFFF", DARK = "0B0B0D", RED = "C8102E", REDD = "8E0E22",
      TINT = "FBECEE", INK = "111111", PAPER = "F5F5F3", MUT = "6A6A6A",
      MUTD = "9C9C9C", HAIR = "E0E0E0";
const D = "Arial Black", B = "Arial", M = "Consolas";
const W = 13.33, H = 7.5, MG = 0.5;
const LIVE = process.env.QOREX_LIVE_URL || "";

const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "Team QoreX";
p.title = "Project QoreX — Planet X and SPHEREx";

// helpers (fresh option objects everywhere; margin 0 for alignment)
const T = (s, t, o = {}) => s.addText(t, { fontFace: B, color: INK, margin: 0, ...o });
const MO = (s, t, o = {}) => T(s, t, { fontFace: M, ...o });
const SQ = (s, x, y, sz, c = RED) => s.addShape("rect", { x, y, w: sz, h: sz, fill: { color: c } });
const LN = (s, x1, y1, x2, y2, o = {}) => s.addShape("line", {
  x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
  line: { color: HAIR, width: 1, ...o.line }
});
function reticle(s, cx, cy, r, ring = RED) {
  s.addShape("ellipse", { x: cx - r, y: cy - r, w: 2 * r, h: 2 * r, fill: { color: DARK, transparency: 100 }, line: { color: ring, width: 2 } });
  const t = 0.3;
  LN(s, cx, cy - r, cx, cy - r - t, { line: { color: ring, width: 2 } });
  LN(s, cx, cy + r, cx, cy + r + t, { line: { color: ring, width: 2 } });
  LN(s, cx - r, cy, cx - r - t, cy, { line: { color: ring, width: 2 } });
  LN(s, cx + r, cy, cx + r + t, cy, { line: { color: ring, width: 2 } });
  s.addShape("ellipse", { x: cx - 0.055, y: cy - 0.055, w: 0.11, h: 0.11, fill: { color: ring } });
}
function kicker(s, txt) {
  MO(s, txt, { x: MG, y: 0.42, w: 8, h: 0.3, fontSize: 12.5, color: RED, charSpacing: 2, bold: true });
}
function marker(s, n, dark = false) {
  MO(s, `0${n} / 06`, { x: 11.55, y: 0.42, w: 1.28, h: 0.3, fontSize: 12, color: dark ? MUTD : MUT, align: "right" });
}

/* ---------------- SLIDE 1 — COVER (dark) ---------------- */
let s = p.addSlide();
s.background = { color: DARK };
MO(s, "NASA SPACE APPS CHALLENGE 2026  ·  CHALLENGE — PLANET X AND SPHEREX", { x: MG, y: 0.45, w: 11, h: 0.3, fontSize: 12.5, color: MUTD, charSpacing: 2 });
T(s, "QOREX", { x: MG, y: 1.35, w: 8, h: 1.85, fontFace: D, fontSize: 108, color: PAPER, charSpacing: 3 });
MO(s, "SPHEREx MOTION WORKBENCH", { x: 0.53, y: 3.28, w: 7.5, h: 0.35, fontSize: 16, color: RED, charSpacing: 4, bold: true });
T(s, "Blink the sky. Find what moves. A live window into NASA/IPAC SPHEREx Quick Release data — built for the search for Planet X.", { x: 0.53, y: 3.85, w: 7.2, h: 1.3, fontSize: 17, color: PAPER, lineSpacing: 26 });
reticle(s, 10.85, 3.45, 1.4);
MO(s, "RA 269.4528°   DEC +04.6856°", { x: 8.85, y: 5.38, w: 4.0, h: 0.28, fontSize: 12, color: MUTD, align: "center" });
MO(s, "BARNARD'S STAR — LIVE-VERIFIED TARGET", { x: 8.85, y: 5.68, w: 4.0, h: 0.28, fontSize: 12, color: PAPER, align: "center", bold: true });
MO(s, "TEAM QOREX", { x: MG, y: 6.85, w: 4, h: 0.3, fontSize: 12.5, color: MUTD, charSpacing: 2 });
s.addShape("rect", { x: 8.2, y: 6.72, w: 4.63, h: 0.56, fill: { color: DARK, transparency: 100 }, line: { color: RED, width: 1.5 } });
MO(s, "WORKING PROTOTYPE · VERIFIED ON LIVE DATA", { x: 8.2, y: 6.72, w: 4.63, h: 0.56, fontSize: 12, color: PAPER, align: "center", valign: "middle", bold: true });
s.addNotes("Project QoreX. Team QoreX. A motion workbench for SPHEREx Quick Release data — the instrument for the Planet X search that anyone can drive.");

/* ---------------- SLIDE 2 — PROBLEM (white) ---------------- */
s = p.addSlide();
s.background = { color: BG };
kicker(s, "01 — THE PROBLEM"); marker(s, 2);
T(s, "Planet X hides in plain sight.", { x: MG, y: 0.92, w: 12.3, h: 0.75, fontFace: D, fontSize: 40, color: INK });
T(s, "A cold planet hundreds of AU away barely glows — but it moves against the fixed stars. SPHEREx is the first all-sky infrared instrument built to catch exactly that signal. Nobody has handed it to the public.", { x: MG, y: 1.78, w: 11.9, h: 0.85, fontSize: 16.5, color: MUT, lineSpacing: 24 });
const stats = [
  ["102", "INFRARED CHANNELS PER SKY PIXEL (0.75–5\u00A0µm)"],
  ["2\u00D7", "FULL-SKY SURVEYS EVERY YEAR — MOTION IS BUILT IN"],
  ["7", "ARCMINUTES OF APPARENT SHIFT PER YEAR AT ~500 AU (EST.)"],
];
stats.forEach((st, i) => {
  const x = 0.5 + i * 4.28;
  T(s, st[0], { x, y: 2.95, w: 3.9, h: 1.2, fontFace: D, fontSize: 64, color: RED });
  MO(s, st[1], { x, y: 4.25, w: 3.75, h: 0.75, fontSize: 12.5, color: INK, lineSpacingMultiple: 1.15, bold: true });
});
LN(s, 4.4, 3.05, 4.4, 4.9); LN(s, 8.68, 3.05, 8.68, 4.9);
s.addShape("rect", { x: 0, y: 5.45, w: W, h: 1.42, fill: { color: TINT } });
T(s, "WISE had WiseView — and the public made hundreds of discoveries with it.", { x: 0.9, y: 5.68, w: 11.6, h: 0.35, fontSize: 17, color: INK });
T(s, "SPHEREx Quick Release shipped in 2026 with no motion workbench. QoreX closes that gap.", { x: 0.9, y: 6.08, w: 11.6, h: 0.35, fontSize: 17, color: INK, bold: true });
MO(s, "Sources — SPHEREx mission specifications (NASA/IPAC IRSA); NASA Space Apps 2026 challenge brief; parallax estimate for a ~500 AU orbit.", { x: MG, y: 7.05, w: 12.3, h: 0.28, fontSize: 12, color: MUT });
s.addNotes("Frame the gap: the instrument exists, the data ships weekly, but there is no WiseView for SPHEREx. The motion signal is the whole game for Planet X.");

/* ---------------- SLIDE 3 — SOLUTION (white) ---------------- */
s = p.addSlide();
s.background = { color: BG };
kicker(s, "02 — WHAT WE BUILT"); marker(s, 3);
T(s, "A blink comparator for the SPHEREx era.", { x: MG, y: 0.92, w: 12.3, h: 0.62, fontFace: D, fontSize: 32, color: INK });
const feats = [
  ["Blink & B\u2212A residuals", "Two dates, one sky grid, one shared brightness stretch — what moves is real, not an artifact."],
  ["Gaia DR3 reference overlay", "Proper motions propagated to each observation epoch; 10.4\"/yr movers flagged automatically."],
  ["Live exploratory spectra", "Up to 40 exposures swept in parallel, 0.8–4.8 µm, per-point errors from the VARIANCE layer."],
  ["Honest-science engineering", "Bit-exact SPHEREx flag masking, IRSA-only provenance, zero invented pixels — ever."],
];
feats.forEach((f, i) => {
  const y = 1.95 + i * 1.14;
  SQ(s, 0.5, y + 0.06, 0.16);
  T(s, f[0], { x: 0.88, y, w: 7.3, h: 0.32, fontSize: 17, bold: true });
  T(s, f[1], { x: 0.88, y: y + 0.36, w: 7.3, h: 0.62, fontSize: 13.5, color: MUT, lineSpacing: 18 });
});
s.addShape("rect", { x: 8.55, y: 1.6, w: 4.28, h: 5.0, fill: { color: RED } });
MO(s, "VERIFIED LIVE — QR3 · BARNARD'S STAR", { x: 8.85, y: 1.88, w: 3.75, h: 0.3, fontSize: 12.5, color: PAPER, charSpacing: 1.5, bold: true });
const ev = [
  ["130", "ARCHIVE RECORDS IN ONE SESSION"],
  ["37", "DAYS ON THE WIDEST A–B BASELINE"],
  ["10.4", "\"/yr PROPER MOTION, AUTO-FLAGGED (GAIA DR3)"],
];
ev.forEach((e, i) => {
  const y = 2.32 + i * 0.98;
  T(s, e[0], { x: 8.85, y, w: 3.7, h: 0.55, fontFace: D, fontSize: 30, color: PAPER });
  MO(s, e[1], { x: 8.85, y: y + 0.52, w: 3.7, h: 0.42, fontSize: 12, color: PAPER, lineSpacingMultiple: 1.05 });
});
LN(s, 8.85, 5.32, 12.53, 5.32, { line: { color: "E86A7C", width: 1 } });
MO(s, "22/22 LIVE CHECKS · 5 CHALLENGE TARGETS", { x: 8.85, y: 5.5, w: 3.7, h: 0.55, fontSize: 13, color: PAPER, bold: true, lineSpacingMultiple: 1.1 });
MO(s, "All numbers from the repository's live verification sweep — NASA/IPAC IRSA QR3 (DOI 10.26131/IRSA662), November 2026.", { x: MG, y: 7.05, w: 12.3, h: 0.28, fontSize: 12, color: MUT });
s.addNotes("Four capabilities, then the evidence panel: every number on the right is from our November 2026 live sweep against IRSA QR3, not a mock.");

/* ---------------- SLIDE 4 — HOW IT WORKS (white) ---------------- */
s = p.addSlide();
s.background = { color: BG };
kicker(s, "03 — HOW IT WORKS"); marker(s, 4);
T(s, "One pipeline. Zero shortcuts.", { x: MG, y: 0.92, w: 12.3, h: 0.62, fontFace: D, fontSize: 32, color: INK });
T(s, "From raw archive metadata to a blinked, Gaia-crossmatched field — five steps, all live.", { x: MG, y: 1.56, w: 11.9, h: 0.32, fontSize: 15.5, color: MUT });
const steps = [
  ["01", "FIND", "IRSA SIA v2 lists every SPHEREx exposure at your target — QR3, with QR2 fallback."],
  ["02", "FETCH", "Official cutout service delivers IMAGE, FLAGS, VARIANCE and WCS-WAVE FITS layers."],
  ["03", "REGISTER", "Bit-aware flag masking; every epoch reprojected to one shared sky grid."],
  ["04", "COMPARE", "Blink, split, B\u2212A residual and 2–8 frame sequences on one brightness scale."],
  ["05", "IDENTIFY", "Gaia DR3 cross-match, live spectra, evidence JSON export with dataset DOIs."],
];
steps.forEach((st, i) => {
  const x = 0.49 + i * 2.52, bw = 2.28;
  s.addShape("rect", { x, y: 2.05, w: bw, h: 1.92, fill: { color: BG }, line: { color: RED, width: 1.25 } });
  T(s, st[0], { x: x + 0.18, y: 2.2, w: 1.0, h: 0.4, fontFace: D, fontSize: 20, color: RED });
  T(s, st[1], { x: x + 0.18, y: 2.62, w: bw - 0.36, h: 0.3, fontSize: 15, bold: true });
  T(s, st[2], { x: x + 0.18, y: 2.95, w: bw - 0.36, h: 0.92, fontSize: 12, color: MUT, lineSpacing: 15.5 });
  if (i < 4) s.addShape("line", { x: x + bw + 0.03, y: 3.0, w: 0.18, h: 0, line: { color: RED, width: 1.75, endArrowType: "triangle" } });
});
SQ(s, 0.5, 4.42, 0.14);
T(s, "Every pixel traces back to IRSA — nothing simulated, nothing cached, nothing invented.", { x: 0.82, y: 4.33, w: 11.9, h: 0.34, fontSize: 16.5, bold: true });
const chips = ["PYTHON", "FASTAPI", "ASTROPY", "REPROJECT", "VANILLA JS", "ALADIN LITE V3", "DOCKER"];
let cx = 0.5;
chips.forEach(c => {
  const cw = 0.107 * c.length + 0.36;
  s.addShape("roundRect", { x: cx, y: 4.95, w: cw, h: 0.44, rectRadius: 0.05, fill: { color: TINT } });
  MO(s, c, { x: cx, y: 4.95, w: cw, h: 0.44, fontSize: 12.5, color: INK, align: "center", valign: "middle", bold: true });
  cx += cw + 0.17;
});
MO(s, "Runs from one double-click on Windows · Linux/macOS shell scripts · Docker image (port 7860) for any cloud host.", { x: 0.5, y: 5.62, w: 12.3, h: 0.3, fontSize: 12.5, color: MUT });
const trio = [
  "ZERO INVENTED PIXELS, EVER",
  "EVIDENCE JSON WITH DATASET DOIs",
  "29 OFFLINE TESTS · 22 LIVE CHECKS",
];
trio.forEach((t, i) => {
  const x = 0.5 + i * 4.28;
  s.addShape("rect", { x, y: 6.1, w: 3.9, h: 0.62, fill: { color: BG }, line: { color: HAIR, width: 1 } });
  SQ(s, x + 0.16, 6.35, 0.12);
  MO(s, t, { x: x + 0.44, y: 6.1, w: 3.4, h: 0.62, fontSize: 12, color: INK, valign: "middle", bold: true });
});
MO(s, "Source — NASA/IPAC IRSA SIA v2 + cutout service + TAP (Gaia DR3); SPHEREx QR3 DOI 10.26131/IRSA662.", { x: MG, y: 7.05, w: 12.3, h: 0.28, fontSize: 12, color: MUT });
s.addNotes("Walk the five steps left to right. Emphasize: IRSA is the only data source, and the honesty boxes are engineering claims backed by tests, not slogans.");

/* ---------------- SLIDE 5 — PROTOTYPE (dark) ---------------- */
s = p.addSlide();
s.background = { color: DARK };
kicker(s, "04 — THE WORKBENCH, LIVE"); marker(s, 5, true);
T(s, "Real data. Real sky. Real motion.", { x: MG, y: 0.92, w: 12.3, h: 0.62, fontFace: D, fontSize: 32, color: PAPER });
const imgY = 1.85, imgH = 3.3;
const L = { path: "docs/interface-v0.5-atlas-wise.png", w: 3.3 * (920 / 520) };
const R = { path: "docs/interface-v0.5-gaia-overlay.png", w: 3.3 * (900 / 480) };
s.addImage({ path: L.path, x: 0.5, y: imgY, w: L.w, h: imgH });
s.addShape("rect", { x: 0.5, y: imgY, w: L.w, h: imgH, fill: { color: DARK, transparency: 100 }, line: { color: PAPER, width: 1 } });
const rx = 0.5 + L.w + 0.28;
s.addImage({ path: R.path, x: rx, y: imgY, w: R.w, h: imgH });
s.addShape("rect", { x: rx, y: imgY, w: R.w, h: imgH, fill: { color: DARK, transparency: 100 }, line: { color: PAPER, width: 1 } });
T(s, "REFERENCE SKY ATLAS", { x: 0.5, y: 5.3, w: L.w, h: 0.3, fontSize: 14.5, bold: true, color: PAPER });
MO(s, "SPHEREx fields over live AllWISE context — zoom out to the real sky.", { x: 0.5, y: 5.62, w: L.w, h: 0.3, fontSize: 12, color: MUTD });
T(s, "GAIA DR3 OVERLAY — MOVER FOUND", { x: rx, y: 5.3, w: R.w, h: 0.3, fontSize: 14.5, bold: true, color: PAPER });
MO(s, "Barnard's Star auto-flagged at 10.4\"/yr, epoch-propagated by Gaia proper motion.", { x: rx, y: 5.62, w: R.w, h: 0.3, fontSize: 12, color: MUTD });
SQ(s, 0.5, 6.35, 0.13);
MO(s, "Screenshots — release v0.5 workbench, live QR3 sessions, Oct–Nov 2026. Nothing staged, nothing simulated.", { x: 0.78, y: 6.28, w: 11.8, h: 0.3, fontSize: 12.5, color: PAPER });
MO(s, "Every frame carries its UTC, detector, wavelength range and flagged-pixel fraction.", { x: 0.78, y: 6.62, w: 11.8, h: 0.3, fontSize: 12, color: MUTD });
s.addNotes("Two real screens: the two-layer atlas, and the Gaia overlay catching Barnard's Star unprompted. Mention the data inspector: UTC, detector, local wavelength, flag fraction.");

/* ---------------- SLIDE 6 — CLOSE (red) ---------------- */
s = p.addSlide();
s.background = { color: RED };
MO(s, "05 — THE INVITATION", { x: MG, y: 0.48, w: 8, h: 0.3, fontSize: 12.5, color: PAPER, charSpacing: 2, bold: true });
MO(s, "06 / 06", { x: 11.55, y: 0.48, w: 1.28, h: 0.3, fontSize: 12, color: "F6D4DA", align: "right" });
T(s, "The next Planet X finder might not be an astronomer.", { x: MG, y: 1.35, w: 12.0, h: 2.0, fontFace: D, fontSize: 46, color: PAPER, lineSpacing: 58 });
T(s, "A student. A teacher. A curious coder blinking two real SPHEREx epochs. QoreX hands the public the comparator — the way WiseView did for WISE.", { x: MG, y: 3.55, w: 11.4, h: 0.8, fontSize: 17, color: PAPER, lineSpacing: 24 });
s.addShape("rect", { x: MG, y: 4.7, w: 12.33, h: 1.2, fill: { color: PAPER } });
MO(s, "CODE + DOCS   github.com/shree-aru/spherex-motion-explorer", { x: 0.9, y: 4.95, w: 11.5, h: 0.32, fontSize: 15, color: INK, bold: true });
MO(s, LIVE ? `LIVE APP      ${LIVE}` : "LIVE APP      public deployment — link in the project submission form", { x: 0.9, y: 5.33, w: 11.5, h: 0.32, fontSize: 15, color: RED, bold: true });
MO(s, "TEAM QOREX — PLANET X AND SPHEREx · NASA SPACE APPS CHALLENGE 2026", { x: MG, y: 6.7, w: 8.5, h: 0.3, fontSize: 12.5, color: PAPER, charSpacing: 1.5 });
MO(s, "SI-ASSISTED BUILD (CODE · TEXT · DESIGN) — DISCLOSURE IN REPO", { x: 8.6, y: 6.7, w: 4.23, h: 0.3, fontSize: 12, color: "F6D4DA", align: "right" });
s.addNotes("Close on the invitation, hand over the two links, state the SI disclosure. Then run the live demo if time allows.");

p.writeFile({ fileName: "docs/QoreX_SpaceApps_Demo.pptx" }).then(() => console.log("deck written"));
