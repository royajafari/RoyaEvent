// لوگوی متنی سایت — برای هدر/ناوبری.
// Usage: <RoyaEventLogo size={26} />
const LETTERS = ["R", "o", "y", "a", "E", "v", "e", "n", "t"] as const;
const CYCLE_COLORS = ["#2E9E4F", "#FFFFFF", "#DA1A32"];
const COLORS = LETTERS.map((_, i) => CYCLE_COLORS[i % 3]);

export function RoyaEventLogo({ size = 26 }: { size?: number }) {
  return (
    <span
      style={{
        display: "inline-flex",
        fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
        fontWeight: 800,
        fontSize: size,
        lineHeight: 1,
        letterSpacing: "-0.01em",
        direction: "ltr",
      }}
      aria-label="RoyaEvent"
    >
      {LETTERS.map((ch, i) => (
        <span key={i} style={{ color: COLORS[i] }}>
          {ch}
        </span>
      ))}
    </span>
  );
}

export default RoyaEventLogo;
