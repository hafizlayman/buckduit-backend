// =========================================
// frontend/src/components/AdaptiveThresholdCard.jsx
// Stage 13.84 — Adaptive Threshold Card
// =========================================
import React, { useEffect, useState } from "react";

export default function AdaptiveThresholdCard() {
  const [threshold, setThreshold] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchThreshold = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://127.0.0.1:5000/api/predictive/tune-thresholds");
      const data = await res.json();
      setThreshold(data.data || null);
    } catch (err) {
      console.error("Threshold Fetch Error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThreshold();
  }, []);

  return (
    <div className="bg-white rounded-2xl shadow-md p-4 border mt-8">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">
        Adaptive Threshold Auto-Tuner
      </h3>
      {loading && <p className="text-gray-500">Recalculating thresholds…</p>}
      {threshold ? (
        <ul className="text-gray-700">
          <li>Avg Confidence: {threshold.avg_confidence}</li>
          <li>Avg Drift: {threshold.avg_drift}</li>
          <li>Confidence Range: {threshold.lower_threshold} - {threshold.upper_threshold}</li>
          <li>Drift Alert Threshold: {threshold.drift_alert_threshold}</li>
        </ul>
      ) : (
        <p className="text-gray-500">No recent threshold data yet.</p>
      )}
      <button
        onClick={fetchThreshold}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        🔁 Re-Tune
      </button>
    </div>
  );
}
