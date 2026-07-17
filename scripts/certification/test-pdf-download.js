// Test script: trigger PDF download via the API and save to /home/z/my-project/download/
// Run with: node scripts/certification/test-pdf-download.js

async function main() {
  const payload = {
    version: "1.0",
    generatedAt: Date.now(),
    buildHash: "athx-14.5.0-audit",
    environment: "internal-validation",
    modules: [
      {
        id: "data", index: 1, name: "Data Certification", status: "fail", score: 0.711, checks: [
          { id: "d1", label: "Provider Freshness", status: "fail", score: 0.7, value: "14/20", target: "≥ 90%", unit: "providers", evidence: "6 providers down" },
          { id: "d2", label: "Validation Accuracy", status: "pass", score: 0.93, value: "13/14", target: "≥ 85%", unit: "checks" },
          { id: "d3", label: "Standardization Accuracy", status: "pass", score: 0.9, value: "9/10", target: "≥ 85%", unit: "checks" },
          { id: "d4", label: "Missing Data", status: "fail", score: 0.4, value: "9 stale", target: "0 stale", unit: "symbols" },
          { id: "d5", label: "Replay Accuracy", status: "pass", score: 0.989, value: "98.9%", target: "≥ 98%", unit: "match" },
          { id: "d6", label: "Synchronization", status: "pass", score: 0.85, value: "2.1s", target: "≤ 2s", unit: "lag" },
        ],
      },
      {
        id: "intelligence", index: 2, name: "Intelligence Certification", status: "pass", score: 0.882, checks: [
          { id: "i1", label: "Technical DNA", status: "pass", score: 0.82, value: "82.0%", target: "conf ≥ 65%" },
          { id: "i2", label: "Options DNA", status: "pass", score: 0.78, value: "78.0%", target: "conf ≥ 65%" },
          { id: "i3", label: "Market DNA", status: "pass", score: 0.91, value: "91.0%", target: "conf ≥ 65%" },
          { id: "i4", label: "Narrative DNA", status: "warn", score: 0.62, value: "62.0%", target: "conf ≥ 65%" },
          { id: "i5", label: "Forecast DNA", status: "pass", score: 0.85, value: "85.0%", target: "conf ≥ 65%" },
          { id: "i6", label: "Trade DNA", status: "pass", score: 0.74, value: "74.0%", target: "conf ≥ 65%" },
          { id: "i7", label: "Operations DNA", status: "pass", score: 0.88, value: "88.0%", target: "conf ≥ 65%" },
        ],
      },
      {
        id: "forecast", index: 3, name: "Forecast Certification", status: "pass", score: 0.867, checks: [
          { id: "f1", label: "MAE", status: "pass", score: 0.9, value: "1.823", target: "≤ 2.0", unit: "pts" },
          { id: "f2", label: "RMSE", status: "pass", score: 0.88, value: "2.412", target: "≤ 3.0", unit: "pts" },
          { id: "f3", label: "Directional Accuracy", status: "pass", score: 0.683, value: "68.3%", target: "≥ 60%" },
          { id: "f4", label: "Calibration", status: "pass", score: 0.94, value: "0.971", target: "0.85 – 1.15" },
          { id: "f5", label: "Bull/Base/Bear", status: "pass", score: 0.7, value: "72% / 68% / 65%", target: "≥ 65% each" },
        ],
      },
      { id: "decision", index: 4, name: "Decision Certification", status: "warn", score: 0.816, checks: [] },
      { id: "stress", index: 5, name: "Stress Testing", status: "warn", score: 0.85, checks: [] },
      { id: "replay", index: 6, name: "Replay Certification", status: "warn", score: 0.976, checks: [] },
      {
        id: "performance", index: 7, name: "Performance Certification", status: "fail", score: 0.88, checks: [
          { id: "p1", label: "Event Bus Latency", status: "pass", score: 0.92, value: "34.2ms", target: "≤ 50ms p95" },
          { id: "p2", label: "DB Write Latency", status: "fail", score: 0.4, value: "42.1ms", target: "≤ 30ms p95" },
          { id: "p3", label: "Forecast Latency", status: "pass", score: 0.85, value: "312ms", target: "≤ 500ms" },
          { id: "p4", label: "Dashboard Latency", status: "pass", score: 0.9, value: "142ms", target: "≤ 200ms" },
          { id: "p5", label: "Memory", status: "pass", score: 0.88, value: "3.6GB", target: "≤ 4GB" },
          { id: "p6", label: "CPU", status: "pass", score: 0.92, value: "38.5%", target: "≤ 70%" },
          { id: "p7", label: "GPU", status: "pass", score: 0.95, value: "52.3%", target: "≤ 80%" },
          { id: "p8", label: "Queue Depth", status: "pass", score: 0.95, value: "97", target: "≤ 1000" },
        ],
      },
    ],
    overallScore: 0.855,
    status: "not_certified",
    criticalFailures: 0,
    warnings: 4,
    exitCriteria: [
      { id: "ec.regression", label: "Full regression suite passes", passed: true, detail: "985 tests across 14 stages" },
      { id: "ec.session", label: "Live data stable for ≥ 1 trading session", passed: true, detail: "6.5h RTH session completed" },
      { id: "ec.dna", label: "All 7 DNA objects meet confidence thresholds", passed: true, detail: "All 7 DNA ≥ 65% confidence" },
      { id: "ec.forecast", label: "Forecast accuracy meets targets", passed: true, detail: "Directional accuracy 68.3% (target 60%)" },
      { id: "ec.replay", label: "Replay results deterministic", passed: true, detail: "97.6% match across 5 scenarios" },
      { id: "ec.stress", label: "Stress tests pass without critical failures", passed: true, detail: "8 scenarios, all recovered" },
      { id: "ec.failover", label: "Provider failover works automatically", passed: false, detail: "Failover > 4s on Yahoo outage" },
      { id: "ec.eventbus", label: "Event bus stable under peak load", passed: true, detail: "p95 < 50ms at 10× throughput" },
      { id: "ec.database", label: "Database integrity & recovery verified", passed: false, detail: "DB p95 42ms exceeds 30ms target" },
      { id: "ec.report", label: "Production Certification Report archived", passed: true, detail: "This document" },
    ],
    signedBy: "ATHENA-X Certification Engine",
    validUntil: Date.now() + 86400000,
  };

  console.log("POSTing to /api/certification-pdf…");
  const t0 = Date.now();
  const res = await fetch("http://localhost:3000/api/certification-pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const elapsed = Date.now() - t0;

  console.log(`HTTP ${res.status} in ${elapsed}ms`);
  console.log(`Content-Type: ${res.headers.get("content-type")}`);
  console.log(`Content-Disposition: ${res.headers.get("content-disposition")}`);

  if (!res.ok) {
    console.error("Failed:", await res.text());
    process.exit(1);
  }

  const buf = Buffer.from(await res.arrayBuffer());
  const outPath = "/home/z/my-project/download/athena-x-certification-audit.pdf";
  const fs = await import("fs/promises");
  await fs.writeFile(outPath, buf);
  console.log(`✓ Saved ${buf.length} bytes to ${outPath}`);
}

main().catch((err) => { console.error(err); process.exit(1); });
