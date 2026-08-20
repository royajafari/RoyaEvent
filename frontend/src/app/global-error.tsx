"use client";

// app/error.tsx فقط خطاهای زیر root layout رو می‌گیره — اگه خودِ layout.tsx
// (یا چیزی که مستقیم توش mount شده، مثل NetworkStatusGate) throw کنه،
// نکست‌جس سراغ global-error.tsx می‌ره. چون این فایل کل root layout رو
// جایگزین می‌کنه، باید خودش <html>/<body> کامل داشته باشه — نمی‌تونه به
// چیزی که از layout.tsx میاد (فونت/هدر/فوتر) تکیه کنه.
export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="fa" dir="rtl">
      <body
        style={{
          display: "flex",
          minHeight: "100vh",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "1rem",
          fontFamily: "sans-serif",
          background: "#161826",
          color: "#fff",
        }}
      >
        <p>مشکلی در بارگذاری سایت پیش آمد.</p>
        <button
          type="button"
          onClick={() => reset()}
          style={{
            padding: "0.5rem 1.5rem",
            borderRadius: "0.5rem",
            background: "#2E9E4F",
            color: "#fff",
            border: "none",
            cursor: "pointer",
          }}
        >
          تلاش دوباره
        </button>
      </body>
    </html>
  );
}
