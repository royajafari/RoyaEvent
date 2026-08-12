"use client";

import { useEffect, useState } from "react";
import styles from "./RoyaEventLoader.module.css";

// همون چرخه‌ی رنگ سبز/سفید/قرمز لوگوی اصلی (RoyaEventLogo.tsx) — حروف
// R,o,y,a,E,v,e,n,t به ترتیب.
const LETTER_COLOR: Record<string, string> = {
  R: "#2E9E4F",
  o: "#FFFFFF",
  y: "#DA1A32",
  a: "#2E9E4F",
  E: "#FFFFFF",
  v: "#DA1A32",
  e: "#2E9E4F",
  n: "#FFFFFF",
  t: "#DA1A32",
};

// Precomputed centered x-offsets (px) for each letter at 72px/800-weight system sans.
// Re-derive with canvas.measureText if you change FONT_SIZE or the font.
const REL_X: Record<string, number> = {
  o: -115.5,
  y: -73.05,
  a: -31.9,
  v: 53.65,
  e: 94.7,
  n: 137.9,
  t: 173.9,
};

const OYA_DELAY = 1.15; // seconds after mount, once R/E have stuck together
const VENT_DELAY = 1.55;
const STAGGER = 0.09;

/**
 * Full-screen RoyaEvent intro. Mount it while the page's real content is
 * loading; pass `ready` once that content has resolved and it fades itself
 * out. Designed for Next.js `loading.tsx` (Suspense swaps this out
 * automatically) or a manual splash controlled by `ready`.
 */
export function RoyaEventLoader({ ready = false }: { ready?: boolean }) {
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    if (ready) {
      const t = setTimeout(() => setHidden(true), 50);
      return () => clearTimeout(t);
    }
  }, [ready]);

  return (
    <div className={`${styles.stage} ${hidden ? styles.hidden : ""}`}>
      <div className={styles.word} style={{ fontSize: 72 }}>
        <span className={`${styles.letter} ${styles.letterR}`} style={{ color: LETTER_COLOR.R }}>
          R
        </span>
        {["o", "y", "a"].map((ch, i) => (
          <span
            key={ch}
            className={`${styles.letter} ${styles.fadeLetter}`}
            style={{
              left: `calc(50% + ${REL_X[ch]}px)`,
              animationDelay: `${OYA_DELAY + i * STAGGER}s`,
              color: LETTER_COLOR[ch],
            }}
          >
            {ch}
          </span>
        ))}
        <span className={`${styles.letter} ${styles.letterE}`} style={{ color: LETTER_COLOR.E }}>
          E
        </span>
        {["v", "e", "n", "t"].map((ch, i) => (
          <span
            key={ch}
            className={`${styles.letter} ${styles.fadeLetter}`}
            style={{
              left: `calc(50% + ${REL_X[ch]}px)`,
              animationDelay: `${VENT_DELAY + i * STAGGER}s`,
              color: LETTER_COLOR[ch],
            }}
          >
            {ch}
          </span>
        ))}
      </div>
    </div>
  );
}

export default RoyaEventLoader;
