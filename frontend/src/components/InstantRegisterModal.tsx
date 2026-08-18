"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { CompleteProfilePrompt } from "@/components/CompleteProfilePrompt";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApiError, authApi, isIncompleteProfileError } from "@/lib/api-client";
import { eventsApi } from "@/lib/events-api";
import type { EventListItem } from "@/lib/events-api";
import { toEnglishDigits, toPersianDigits } from "@/lib/digits";
import { ordersApi } from "@/lib/orders-api";
import { ticketsApi } from "@/lib/tickets-api";
import { track } from "@/lib/track";
import { useAuthStore } from "@/store/auth-store";

type Step = "destination" | "otp" | "confirm" | "submitting" | "needsProfile" | "success" | "error";

// نکته‌ی مهم: این کامپوننت خودش state رو موقع باز/بسته‌شدن ریست نمی‌کنه —
// parent باید این کامپوننت رو فقط وقتی مودال واقعاً بازه mount کنه
// (`{open && <InstantRegisterModal .../>}`) تا هر بار باز شدن، mount تازه‌ای
// باشه و state از صفر شروع بشه — نه toggle کردن یک instance همیشه-mounted.
// همچنین عمداً هیچ‌جا register() از دل یک effect صدا زده نمی‌شه (نه حتی
// برای شروع خودکار وقتی از قبل لاگینیم) — همیشه از یک event handler واقعی
// (کلیک دکمه‌ی «تأیید»، یا بعد از تأیید موفق OTP)، تا با قانون
// react-hooks/set-state-in-effect تداخل نداشته باشه. این خودش UX رو هم بهتر
// می‌کنه: کاربر لاگین‌کرده قبل از ثبت‌نام واقعی، یه صفحه‌ی تأیید می‌بینه.
export function InstantRegisterModal({
  event,
  onOpenChange,
}: {
  event: EventListItem;
  onOpenChange: (open: boolean) => void;
}) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setAccessToken = useAuthStore((s) => s.setAccessToken);

  const [step, setStep] = useState<Step>(() => (accessToken ? "confirm" : "destination"));
  const [channel, setChannel] = useState<"sms" | "email">("sms");
  const [destination, setDestination] = useState("");
  const [otp, setOtp] = useState("");
  const [challengeId, setChallengeId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // این کامپوننت فقط وقتی مودال واقعاً باز می‌شه mount می‌شه (نکته‌ی بالا)،
  // پس mount == کاربر روی «ثبت‌نام فوری» کلیک کرده == معادل CLICK_REGISTER
  // قیف. track() از یک ماژول دیگه import شده و هیچ setState صدا نمی‌زنه،
  // پس با react-hooks/set-state-in-effect تداخل نداره.
  useEffect(() => {
    track("funnel_step", { step: "CLICK_REGISTER", event_id: event.id });
  }, [event.id]);

  async function register(token: string) {
    setStep("submitting");
    setLoading(true);
    setError(null);
    try {
      const types = await ticketsApi.listByEvent(event.id);
      const ticket = types.find((t) => !t.is_sold_out) ?? types[0];
      if (!ticket) {
        setError("هنوز بلیطی برای این رویداد تعریف نشده است.");
        setStep("error");
        return;
      }
      const detail = await eventsApi.getBySlug(event.slug);
      const session = detail?.sessions[0];
      if (!session) {
        setError("جلسه‌ای برای این رویداد ثبت نشده است.");
        setStep("error");
        return;
      }
      track("funnel_step", { step: "START_CHECKOUT", event_id: event.id });
      const order = await ordersApi.create(
        { ticket_type_id: ticket.id, session_id: session.id },
        token,
      );
      await ordersApi.complete(order.id, token);
      track("funnel_step", { step: "COMPLETE_ORDER", event_id: event.id });
      setStep("success");
    } catch (err) {
      if (isIncompleteProfileError(err)) {
        setStep("needsProfile");
      } else {
        setError(err instanceof ApiError ? err.message : "خطا در ثبت‌نام؛ دوباره تلاش کنید");
        setStep("error");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleRequestOtp() {
    if (!destination.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.requestOtp(destination.trim(), channel);
      setChallengeId(res.challenge_id);
      setStep("otp");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در ارسال کد؛ دوباره تلاش کنید");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp() {
    if (!challengeId || otp.length < 4) return;
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.verifyOtp(challengeId, otp);
      if (!res.verified || !res.access_token) {
        setError(res.message ?? "کد وارد‌شده نامعتبر است");
        return;
      }
      setAccessToken(res.access_token);
      await register(res.access_token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در تأیید کد");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="text-right">
        <DialogHeader>
          <DialogTitle>ثبت‌نام فوری</DialogTitle>
          <DialogDescription>{event.title}</DialogDescription>
        </DialogHeader>

        {step === "destination" && (
          <div className="flex flex-col gap-4">
            <Tabs value={channel} onValueChange={(v) => setChannel(v as "sms" | "email")}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="sms">پیامک</TabsTrigger>
                <TabsTrigger value="email">ایمیل</TabsTrigger>
              </TabsList>
            </Tabs>
            <div className="flex flex-col gap-2">
              <Label htmlFor="instant-destination">
                {channel === "sms" ? "شماره موبایل" : "ایمیل"}
              </Label>
              <Input
                id="instant-destination"
                dir="ltr"
                placeholder={channel === "sms" ? "09xxxxxxxxx" : "you@example.com"}
                value={channel === "sms" ? toPersianDigits(destination) : destination}
                onChange={(e) =>
                  setDestination(channel === "sms" ? toEnglishDigits(e.target.value) : e.target.value)
                }
              />
            </div>
            {error && <p className="text-destructive text-sm">{error}</p>}
            <Button disabled={loading || !destination.trim()} onClick={handleRequestOtp}>
              ارسال کد تأیید
            </Button>
            <p className="text-muted-foreground text-center text-xs">
              ورود شما به معنای پذیرش{" "}
              <Link href="/terms" target="_blank" className="text-primary hover:underline">
                قوانین و مقررات
              </Link>{" "}
              رویا ایونت است.
            </p>
          </div>
        )}

        {step === "otp" && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="instant-otp">
                کد تأیید ارسال‌شده به {channel === "sms" ? toPersianDigits(destination) : destination}
              </Label>
              <Input
                id="instant-otp"
                dir="ltr"
                inputMode="numeric"
                maxLength={8}
                value={toPersianDigits(otp)}
                onChange={(e) => setOtp(toEnglishDigits(e.target.value))}
              />
            </div>
            {error && <p className="text-destructive text-sm">{error}</p>}
            <Button disabled={loading || otp.length < 4} onClick={handleVerifyOtp}>
              تأیید و ثبت‌نام
            </Button>
          </div>
        )}

        {step === "confirm" && accessToken && (
          <div className="flex flex-col gap-4">
            <p className="text-sm">با یک کلیک، برای این رویداد ثبت‌نام می‌شوید.</p>
            {error && <p className="text-destructive text-sm">{error}</p>}
            <Button disabled={loading} onClick={() => register(accessToken)}>
              تأیید و ثبت‌نام
            </Button>
          </div>
        )}

        {step === "submitting" && (
          <p className="text-muted-foreground text-sm">در حال ثبت‌نام...</p>
        )}

        {step === "needsProfile" && accessToken && (
          <CompleteProfilePrompt onCompleted={() => register(accessToken)} />
        )}

        {step === "error" && error && (
          <div className="flex flex-col gap-3">
            <p className="text-destructive text-sm">{error}</p>
            <Button
              variant="outline"
              onClick={() => setStep(accessToken ? "confirm" : "destination")}
            >
              تلاش دوباره
            </Button>
          </div>
        )}

        {step === "success" && (
          <div className="flex flex-col gap-3">
            <p className="text-sm">ثبت‌نام شما با موفقیت انجام شد 🎉</p>
            <Link
              href="/tickets"
              className={buttonVariants({ className: "w-fit" })}
              onClick={() => onOpenChange(false)}
            >
              مشاهده بلیط‌های من
            </Link>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default InstantRegisterModal;
