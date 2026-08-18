"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { ApiError, authApi } from "@/lib/api-client";
import { toEnglishDigits, toPersianDigits } from "@/lib/digits";
import { useAuthStore } from "@/store/auth-store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

type Step = "destination" | "otp";

export default function LoginPage() {
  const router = useRouter();
  const setAccessToken = useAuthStore((s) => s.setAccessToken);

  const [channel, setChannel] = useState<"sms" | "email">("sms");
  const [destination, setDestination] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<Step>("destination");
  const [challengeId, setChallengeId] = useState<number | null>(null);
  const [cooldown, setCooldown] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  function startCooldown(seconds: number) {
    setCooldown(seconds);
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1 && timerRef.current) {
          clearInterval(timerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }

  async function handleRequestOtp() {
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.requestOtp(destination, channel);
      setChallengeId(res.challenge_id);
      setStep("otp");
      startCooldown(res.retry_after);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در ارسال کد؛ دوباره تلاش کنید");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    if (!challengeId || cooldown > 0) return;
    setError(null);
    try {
      const res = await authApi.resendOtp(challengeId);
      setChallengeId(res.challenge_id);
      startCooldown(res.retry_after);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در ارسال مجدد کد");
    }
  }

  async function handleVerify() {
    if (!challengeId) return;
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.verifyOtp(challengeId, otp);
      if (!res.verified || !res.access_token) {
        setError(res.message ?? "کد وارد‌شده نامعتبر است");
        return;
      }
      setAccessToken(res.access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطا در تأیید کد");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center px-4 py-16">
      <Card className="w-full max-w-sm text-right">
        <CardHeader>
          <CardTitle>ورود به رویا ایونت</CardTitle>
          <CardDescription>
            {step === "destination"
              ? "شماره موبایل یا ایمیل خود را وارد کنید تا کد تأیید ارسال شود."
              : `کد ارسال‌شده به ${channel === "sms" ? toPersianDigits(destination) : destination} را وارد کنید.`}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {step === "destination" && (
            <>
              <Tabs value={channel} onValueChange={(v) => setChannel(v as "sms" | "email")}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="sms">پیامک</TabsTrigger>
                  <TabsTrigger value="email">ایمیل</TabsTrigger>
                </TabsList>
              </Tabs>
              <div className="flex flex-col gap-2">
                <Label htmlFor="destination">
                  {channel === "sms" ? "شماره موبایل" : "ایمیل"}
                </Label>
                <Input
                  id="destination"
                  dir="ltr"
                  placeholder={channel === "sms" ? "۰۹xxxxxxxxx" : "you@example.com"}
                  value={channel === "sms" ? toPersianDigits(destination) : destination}
                  onChange={(e) =>
                    setDestination(channel === "sms" ? toEnglishDigits(e.target.value) : e.target.value)
                  }
                />
              </div>
              {error && <p className="text-destructive text-sm">{error}</p>}
              <Button disabled={loading || !destination} onClick={handleRequestOtp}>
                ارسال کد تأیید
              </Button>
            </>
          )}

          {step === "otp" && (
            <>
              <div className="flex flex-col gap-2">
                <Label htmlFor="otp">کد تأیید</Label>
                <Input
                  id="otp"
                  dir="ltr"
                  inputMode="numeric"
                  maxLength={8}
                  value={toPersianDigits(otp)}
                  onChange={(e) => setOtp(toEnglishDigits(e.target.value))}
                />
              </div>
              {error && <p className="text-destructive text-sm">{error}</p>}
              <Button disabled={loading || otp.length < 4} onClick={handleVerify}>
                تأیید و ورود
              </Button>
              <Button variant="ghost" disabled={cooldown > 0} onClick={handleResend}>
                {cooldown > 0 ? `ارسال مجدد کد (${toPersianDigits(cooldown)} ثانیه)` : "ارسال مجدد کد"}
              </Button>
            </>
          )}

          <p className="text-muted-foreground text-center text-xs">
            ورود شما به معنای پذیرش{" "}
            <Link href="/terms" target="_blank" className="text-primary hover:underline">
              قوانین و مقررات
            </Link>{" "}
            رویا ایونت است.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
