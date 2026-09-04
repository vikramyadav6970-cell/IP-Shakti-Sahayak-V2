import React, { useEffect, useRef } from "react";

interface SacredTreeBackgroundProps {
  growthDuration?: number; // default 4000ms (4.0s)
  scale?: number;          // default 1.22
  treeOpacity?: number;    // default 0.18 (very transparent thin background layer)
  onComplete?: () => void;
}

interface PixelData {
  x: number;
  y: number;
  r: number;
  g: number;
  b: number;
  a: number;
  appearT: number;
}

export const SacredTreeBackground: React.FC<SacredTreeBackgroundProps> = ({
  growthDuration = 4000,
  scale = 1.22,
  treeOpacity = 0.35,
  onComplete,
}) => {
  const treeCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const sporesCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const masterPixelsRef = useRef<PixelData[]>([]);
  const isDataReadyRef = useRef(false);
  const animFrameIdRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);

  // Initialize and parse image data
  useEffect(() => {
    const sourceImg = new Image();
    sourceImg.src = "/tree-cutout.png";

    sourceImg.onload = () => {
      const w = sourceImg.width;
      const h = sourceImg.height;

      const offCanvas = document.createElement("canvas");
      offCanvas.width = w;
      offCanvas.height = h;
      const offCtx = offCanvas.getContext("2d", { willReadFrequently: true });
      if (!offCtx) return;

      offCtx.imageSmoothingEnabled = true;
      offCtx.imageSmoothingQuality = "high";
      offCtx.drawImage(sourceImg, 0, 0);

      const imgData = offCtx.getImageData(0, 0, w, h);
      const data = imgData.data;

      const centerX = w / 2;
      const rootBaseY = 250;
      const trunkForkY = 208;
      const maxRootDist = 180;
      const maxCanopyDist = 175;

      const pixels: PixelData[] = [];

      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const idx = (y * w + x) * 4;
          const alpha = data[idx + 3];

          if (alpha > 18) {
            const r = data[idx];
            const g = data[idx + 1];
            const b = data[idx + 2];

            let appearT = 0;

            if (y >= rootBaseY) {
              const rootDist = Math.hypot(x - centerX, y - rootBaseY);
              const angle = Math.atan2(x - centerX, y - rootBaseY);
              const wave = Math.sin(angle * 6.5) * 0.04;
              appearT = 0.01 + (rootDist / maxRootDist) * 0.32 + wave;
            } else if (y >= 228 && y < rootBaseY) {
              const trunkDist = (rootBaseY - y) / (rootBaseY - 228);
              appearT = 0.28 + trunkDist * 0.14;
            } else if (y >= trunkForkY && y < 228) {
              const forkDist = (228 - y) / (228 - trunkForkY);
              appearT = 0.40 + forkDist * 0.15;
            } else {
              const dist = Math.hypot(x - centerX, y - trunkForkY);
              const angle = Math.atan2(x - centerX, trunkForkY - y);
              const branchTier = dist / maxCanopyDist;
              const angularWave = Math.sin(angle * 5) * 0.06;
              const isOuterLeaf = dist > 78 && g > 150 && g > r + 30;

              if (isOuterLeaf) {
                const leafHash = Math.abs(Math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1;
                appearT = 0.70 + branchTier * 0.18 + leafHash * 0.12;
              } else {
                appearT = 0.52 + branchTier * 0.24 + angularWave;
              }
            }

            appearT = Math.max(0.01, Math.min(appearT, 0.99));

            pixels.push({
              x,
              y,
              r,
              g,
              b,
              a: alpha,
              appearT,
            });
          }
        }
      }

      masterPixelsRef.current = pixels;
      isDataReadyRef.current = true;

      if (treeCanvasRef.current) {
        treeCanvasRef.current.width = w;
        treeCanvasRef.current.height = h;
      }

      triggerGrowth();
    };

    return () => {
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
    };
  }, [growthDuration]);

  // Growth loop
  const triggerGrowth = () => {
    startTimeRef.current = performance.now();

    const renderLoop = (now: number) => {
      if (!isDataReadyRef.current || !treeCanvasRef.current) {
        animFrameIdRef.current = requestAnimationFrame(renderLoop);
        return;
      }

      const canvas = treeCanvasRef.current;
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      if (!ctx) return;

      const elapsed = now - startTimeRef.current;
      const progress = Math.min(elapsed / growthDuration, 1);
      const frameBuffer = ctx.createImageData(canvas.width, canvas.height);
      const fData = frameBuffer.data;
      const pixels = masterPixelsRef.current;
      const w = canvas.width;

      for (let i = 0; i < pixels.length; i++) {
        const p = pixels[i];

        if (progress >= p.appearT) {
          const pixelIdx = (p.y * w + p.x) * 4;
          const timeSinceEmergence = progress - p.appearT;
          let r = p.r;
          let g = p.g;
          let b = p.b;
          const a = p.a;

          if (timeSinceEmergence < 0.035) {
            const boost = 1 - timeSinceEmergence / 0.035;
            r = Math.min(255, r + 90 * boost);
            g = 255;
            b = Math.min(255, b + 120 * boost);
          }

          fData[pixelIdx] = r;
          fData[pixelIdx + 1] = g;
          fData[pixelIdx + 2] = b;
          fData[pixelIdx + 3] = a;
        }
      }

      ctx.putImageData(frameBuffer, 0, 0);

      if (progress < 1) {
        animFrameIdRef.current = requestAnimationFrame(renderLoop);
      } else {
        if (onComplete) onComplete();
      }
    };

    animFrameIdRef.current = requestAnimationFrame(renderLoop);
  };

  // Bioluminescent floating spores loop
  useEffect(() => {
    const canvas = sporesCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let cw = (canvas.width = window.innerWidth);
    let ch = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      cw = canvas.width = window.innerWidth;
      ch = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    const spores = Array.from({ length: 70 }, () => ({
      x: Math.random() * cw,
      y: Math.random() * ch,
      size: Math.random() * 2.0 + 0.6,
      speedY: Math.random() * 0.4 + 0.15,
      speedX: (Math.random() - 0.5) * 0.25,
      pulse: Math.random() * Math.PI * 2,
      baseAlpha: Math.random() * 0.4 + 0.2,
    }));

    let sporeFrameId: number;

    const renderSpores = () => {
      ctx.clearRect(0, 0, cw, ch);
      spores.forEach((s) => {
        s.y -= s.speedY;
        s.x += s.speedX;
        s.pulse += 0.025;

        if (s.y < -15) {
          s.y = ch + 15;
          s.x = Math.random() * cw;
        }

        const a = (Math.sin(s.pulse) * 0.3 + 0.7) * s.baseAlpha;
        ctx.beginPath();
        ctx.fillStyle = `rgba(167, 243, 208, ${a})`;
        ctx.shadowBlur = 8;
        ctx.shadowColor = "#34d399";
        ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
        ctx.fill();
      });
      sporeFrameId = requestAnimationFrame(renderSpores);
    };

    renderSpores();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(sporeFrameId);
    };
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none">
      {/* 1. Deep Midnight Obsidian Aura (Matches NyayAI aesthetic) */}
      <div className="absolute inset-0 bg-[#030712]/95" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,rgba(16,185,129,0.16)_0%,rgba(4,18,12,0.6)_55%,transparent_85%)]" />

      {/* 2. Floating Spores Canvas */}
      <canvas ref={sporesCanvasRef} className="absolute inset-0 w-full h-full pointer-events-none opacity-80" />

      {/* 3. Dead-Center Sacred Tree Container */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-none"
        style={{
          width: "min(1580px, 98vw)",
          height: "min(1400px, 98vh)",
        }}
      >
        {/* Living Breeze Sway Wrapper */}
        <div
          className="w-full h-full flex items-center justify-center transition-opacity duration-500"
          style={{
            opacity: treeOpacity,
            transform: `scale(${scale})`,
            transformOrigin: "center center",
            animation: "sacredTreeBreeze 9s ease-in-out infinite alternate",
          }}
        >
          <canvas
            ref={treeCanvasRef}
            className="w-full h-full object-contain pointer-events-none drop-shadow-[0_0_32px_rgba(52,211,153,0.65)] drop-shadow-[0_0_10px_rgba(110,231,183,0.8)]"
            style={{
              imageRendering: "auto",
            }}
          />
        </div>
      </div>

      <style>{`
        @keyframes sacredTreeBreeze {
          0% {
            transform: scale(${scale}) rotate(-0.5deg);
          }
          50% {
            transform: scale(${scale * 1.012}) rotate(0.4deg);
          }
          100% {
            transform: scale(${scale}) rotate(0.6deg);
          }
        }
      `}</style>
    </div>
  );
};
