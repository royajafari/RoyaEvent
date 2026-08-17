"use client";

import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Html5Qrcode } from "html5-qrcode";

import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api-client";
import type { EventDetail } from "@/lib/events-api";
import { eventsApi } from "@/lib/events-api";
import { organizerApi } from "@/lib/organizer-api";
import { useAuthStore } from "@/store/auth-store";

const READER_ELEMENT_ID = "checkin-qr-reader";

type ScanResult = { kind: "success" | "error"; message: string };

export default function CheckInPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ code?: string }>;
}) {
  const { id } = use(params);
  const { code: codeFromQr } = use(searchParams);
  const eventId = Number(id);
  const accessToken = useAuthStore((s) => s.accessToken);

  const [event, setEvent] = useState<EventDetail | null>(null);
  // اگه از لینک QR بلیط اومده باشیم (نه ورود دستی)، کد از پیش پر می‌شه —
  // ولی چک‌این واقعی هنوز نیاز به یک تپ صریح روی دکمه داره (نه خودکار از
  // دل effect)، هم به‌خاطر قانون react-hooks/set-state-in-effect این پروژه
  // هم برای جلوگیری از چک‌این تصادفی با باز شدن دوباره‌ی همون لینک قدیمی.
  const [manualCode, setManualCode] = useState(codeFromQr ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const scannerRef = useRef<Html5Qrcode | null>(null);
  const busyRef = useRef(false);

  useEffect(() => {
    if (!accessToken) return;
    eventsApi.getById(eventId, accessToken).then(setEvent).catch(() => {});
  }, [accessToken, eventId]);

  async function submitCode(code: string) {
    const trimmed = code.trim();
    if (!trimmed || !accessToken || busyRef.current) return;
    busyRef.current = true;
    setSubmitting(true);
    try {
      const attendee = await organizerApi.checkIn(eventId, trimmed, accessToken);
      setResult({
        kind: "success",
        message: `چک‌این موفق: ${attendee.user_full_name ?? "بدون نام"}`,
      });
    } catch (err) {
      setResult({
        kind: "error",
        message: err instanceof ApiError ? err.message : "خطا در چک‌این",
      });
    } finally {
      setSubmitting(false);
      busyRef.current = false;
    }
  }

  useEffect(() => {
    if (!accessToken) return;
    const scanner = new Html5Qrcode(READER_ELEMENT_ID);
    scannerRef.current = scanner;
    scanner
      .start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        (decodedText) => {
          scanner.pause(true);
          submitCode(decodedText);
        },
        () => {
          // فریم بدون QR — این callback مدام صدا زده می‌شه، عمداً بی‌اثر.
        },
      )
      .catch(() => {
        setCameraError("دسترسی به دوربین ممکن نشد؛ کد بلیط را دستی وارد کنید.");
      });

    return () => {
      scanner
        .stop()
        .catch(() => {})
        .finally(() => {
          scanner.clear();
        });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- submitCode با useRef busy کنترل می‌شه، نیازی به دوباره‌ساخت اسکنر با هر رندر نیست
  }, [accessToken, eventId]);

  function handleResumeScanning() {
    setResult(null);
    scannerRef.current?.resume();
  }

  function handleManualSubmit(e: React.FormEvent) {
    e.preventDefault();
    submitCode(manualCode);
    setManualCode("");
  }

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای دیدن این صفحه باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-6 px-4 py-10">
      <Breadcrumbs
        items={[
          { label: "شرکت‌کنندگان", href: `/organizer/events/${eventId}/attendees` },
          { label: "چک‌این حضوری" },
        ]}
      />
      <h1 className="text-2xl font-bold">چک‌این حضوری {event ? `— ${event.title}` : ""}</h1>
      <p className="text-muted-foreground text-sm">
        QR بلیط شرکت‌کننده را با دوربین اسکن کنید، یا کد بلیط را دستی وارد کنید.
      </p>

      <div className="overflow-hidden rounded-lg ring-1 ring-foreground/10">
        <div id={READER_ELEMENT_ID} className="w-full" />
      </div>
      {cameraError && <p className="text-destructive text-sm">{cameraError}</p>}

      {result && (
        <div
          className={
            result.kind === "success"
              ? "rounded-lg bg-primary/10 p-4 text-sm text-primary ring-1 ring-primary/30"
              : "bg-destructive/10 text-destructive ring-destructive/30 rounded-lg p-4 text-sm ring-1"
          }
        >
          <p>{result.message}</p>
          <Button size="sm" variant="outline" className="mt-3" onClick={handleResumeScanning}>
            ادامه‌ی اسکن
          </Button>
        </div>
      )}

      <form onSubmit={handleManualSubmit} className="flex flex-col gap-2">
        <Label htmlFor="manual-ticket-code">
          {codeFromQr ? "کد بلیط از لینک QR پر شد — برای تأیید بزنید" : "ورود دستی کد بلیط"}
        </Label>
        <div className="flex flex-wrap gap-2">
          <Input
            id="manual-ticket-code"
            dir="ltr"
            value={manualCode}
            onChange={(e) => setManualCode(e.target.value)}
            placeholder="مثال: AB12CD34EF"
            className="max-w-xs"
          />
          <Button type="submit" disabled={submitting || !manualCode.trim()}>
            چک‌این
          </Button>
        </div>
      </form>

      <Link
        href={`/organizer/events/${eventId}/attendees`}
        className={buttonVariants({ variant: "outline", className: "w-fit" })}
      >
        بازگشت به لیست شرکت‌کنندگان
      </Link>
    </div>
  );
}
