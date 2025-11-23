import React, { useMemo } from "react";

export const GlobalKeyframes = () => (
  <>
    <svg style={{ position: 'absolute', width: 0, height: 0 }}>
      <defs>
        <filter id="glass-distortion">
          <feTurbulence type="fractalNoise" baseFrequency="0.008 0.002" numOctaves="4" result="warp" seed="5">
            <animate attributeName="baseFrequency" values="0.008 0.002;0.01 0.003;0.008 0.002" dur="8s" repeatCount="indefinite" />
          </feTurbulence>
          <feDisplacementMap xChannelSelector="R" yChannelSelector="G" scale="50" in="SourceGraphic" in2="warp" />
        </filter>
      </defs>
    </svg>
  </>
);

export const BackgroundFX: React.FC = () => {
  const blobs = useMemo(() => Array.from({ length: 3 }).map((_, i) => ({
    id: i,
    size: 240 + (i % 3) * 110,
    top: `${(i * 13) % 85 + 5}%`,
    left: `${(i * 19) % 85 + 5}%`,
    duration: 120 + (i % 5) * 40,
    delay: i * 1.2,
    even: i % 2 === 0,
  })), []);

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div data-anim className="absolute inset-0" style={{
        background:
          "radial-gradient(1200px 600px at 0% 0%, rgba(59,130,246,0.28), transparent)," +
          "radial-gradient(1000px 600px at 100% 0%, rgba(96,165,250,0.28), transparent)," +
          "radial-gradient(900px 500px at -10% 80%, rgba(191,219,254,0.45), transparent)," +
          "linear-gradient(to bottom right, #ffffff, #eaf2ff)",
        filter: "saturate(1.15) contrast(1.03)",
        animation: "colorShift 180s linear infinite",
      }} />

      <div data-anim className="absolute -inset-[20%] opacity-[0.06]" style={{
        background:
          "conic-gradient(from 0deg at 50% 50%, rgba(255,255,255,0.0) 0deg, rgba(255,255,255,0.5) 35deg, rgba(255,255,255,0.0) 70deg)",
        transformOrigin: "50% 50%",
        animation: "shineSweep 240s linear infinite",
      }} />

      <div className="absolute inset-0 opacity-[0.14]" style={{ maskImage: "radial-gradient(60% 60% at 50% 50%, black, transparent)" }}>
        <div data-anim className="w-full h-full" style={{
          backgroundImage:
            "linear-gradient(to right, rgba(30,64,175,0.08) 1px, transparent 1px)," +
            "linear-gradient(to bottom, rgba(30,64,175,0.08) 1px, transparent 1px)",
          backgroundSize: "36px 36px",
          animation: "slowPan 600s linear infinite",
        }} />
      </div>

      {blobs.map((b, idx) => (
        <div key={b.id} data-anim className={`absolute rounded-full ${b.even ? "blur-xl opacity-[0.12]" : "blur-lg opacity-[0.8]"}`} style={{
          top: b.top,
          left: b.left,
          width: b.size,
          height: b.size,
          background:
            idx % 2 === 0
              ? "radial-gradient(circle at 30% 30%, rgba(96,165,250,0.45), rgba(59,130,246,0.25), transparent 60%)"
              : "radial-gradient(circle at 70% 60%, rgba(147,197,253,0.4), rgba(191,219,254,0.25), transparent 60%)",
          animation: `floatXY ${b.duration}s ease-in-out ${b.delay}s infinite`,
        }} />
      ))}
    </div>
  );
};
