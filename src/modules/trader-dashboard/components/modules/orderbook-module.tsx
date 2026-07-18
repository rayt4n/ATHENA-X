"use client";

import { useEffect, useState } from "react";

interface Props {
  selectedSymbol: string;
}

interface Level {
  price: number;
  size: number;
  total: number;
}

export function OrderBookModule({ selectedSymbol }: Props) {
  const [bids, setBids] = useState<Level[]>([]);
  const [asks, setAsks] = useState<Level[]>([]);
  const [midPrice, setMidPrice] = useState(585.42);

  useEffect(() => {
    const generate = () => {
      const base = 585 + (selectedSymbol.charCodeAt(0) % 10);
      const newBids: Level[] = [];
      const newAsks: Level[] = [];
      let bidTotal = 0, askTotal = 0;
      for (let i = 0; i < 12; i++) {
        const bidPrice = base - i * 0.05 - Math.random() * 0.02;
        const askPrice = base + i * 0.05 + Math.random() * 0.02;
        const bidSize = Math.floor(100 + Math.random() * 5000);
        const askSize = Math.floor(100 + Math.random() * 5000);
        bidTotal += bidSize;
        askTotal += askSize;
        newBids.push({ price: bidPrice, size: bidSize, total: bidTotal });
        newAsks.push({ price: askPrice, size: askSize, total: askTotal });
      }
      setBids(newBids);
      setAsks(newAsks);
      setMidPrice(base);
    };
    generate();
    const interval = setInterval(generate, 1500);
    return () => clearInterval(interval);
  }, [selectedSymbol]);

  const maxSize = Math.max(...bids.map((b) => b.size), ...asks.map((a) => a.size), 1);

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-1.5 border-b border-border/40 bg-background/30 flex items-center justify-between">
        <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground/70">Order Book · {selectedSymbol}</span>
        <span className="text-[11px] font-mono font-bold text-primary">{midPrice.toFixed(2)}</span>
      </div>
      <div className="grid grid-cols-2 text-[9px] font-mono uppercase tracking-wider text-muted-foreground/60 px-2 py-1 border-b border-border/20">
        <div className="flex justify-between"><span>Bid Size</span><span>Bid Price</span></div>
        <div className="flex justify-between"><span>Ask Price</span><span>Ask Size</span></div>
      </div>
      <div className="flex-1 grid grid-cols-2 overflow-hidden">
        {/* Bids */}
        <div className="overflow-y-auto scroll-thin border-r border-border/20">
          {bids.map((b, i) => (
            <div key={i} className="relative px-2 py-0.5 text-[10px] font-mono flex justify-between border-b border-border/10">
              <div className="absolute inset-y-0 right-0" style={{ width: `${(b.size / maxSize) * 100}%`, backgroundColor: "rgba(52, 211, 153, 0.08)" }} />
              <span className="relative text-muted-foreground">{b.size.toLocaleString()}</span>
              <span className="relative" style={{ color: "#34d399" }}>{b.price.toFixed(2)}</span>
            </div>
          ))}
        </div>
        {/* Asks */}
        <div className="overflow-y-auto scroll-thin">
          {asks.map((a, i) => (
            <div key={i} className="relative px-2 py-0.5 text-[10px] font-mono flex justify-between border-b border-border/10">
              <div className="absolute inset-y-0 left-0" style={{ width: `${(a.size / maxSize) * 100}%`, backgroundColor: "rgba(248, 113, 113, 0.08)" }} />
              <span className="relative" style={{ color: "#f87171" }}>{a.price.toFixed(2)}</span>
              <span className="relative text-muted-foreground">{a.size.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="px-3 py-1 border-t border-border/40 bg-background/30 text-[9px] font-mono text-muted-foreground/70 flex justify-between">
        <span>imbalance: <span style={{ color: "#34d399" }}>+12.4%</span></span>
        <span>spread: 0.05</span>
      </div>
    </div>
  );
}
