// Deterministic mock OHLC data generator used by the chart components
// until a live data backend is wired in.
export function generateMockOHLC({ days = 120, startPrice = 100, seed = 42 } = {}) {
  let s = seed;
  const rand = () => {
    // Linear congruential generator for deterministic pseudo-random data.
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };

  const data = [];
  let price = startPrice;
  const start = new Date();
  start.setDate(start.getDate() - days);

  for (let i = 0; i < days; i += 1) {
    const date = new Date(start);
    date.setDate(start.getDate() + i);
    const time = date.toISOString().slice(0, 10);

    const open = price;
    const drift = (rand() - 0.48) * startPrice * 0.03;
    const close = Math.max(1, open + drift);
    const high = Math.max(open, close) + rand() * startPrice * 0.01;
    const low = Math.min(open, close) - rand() * startPrice * 0.01;

    data.push({
      time,
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      value: Number(close.toFixed(2)),
    });
    price = close;
  }
  return data;
}

export function toLineData(ohlc) {
  return (ohlc || []).map((d) => ({ time: d.time, value: d.close }));
}
