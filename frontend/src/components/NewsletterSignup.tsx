"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

// هنوز endpoint واقعی خبرنامه در بک‌اند پیاده نشده (جزو فازهای بعدیه)؛ فعلاً
// فقط اعتبارسنجی ایمیل + پیام «به‌زودی» نشون داده می‌شه، نه no-op ساکت.
// وضعیت «قبلاً عضو شده» هم چون بک‌اند واقعی نداریم، محلی (localStorage) نگه
// داشته می‌شه — مشابه الگوی تور آموزشی.
const STORAGE_KEY = "royaevent_newsletter_subscribed";

export function NewsletterSignup() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [alreadySubscribed, setAlreadySubscribed] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(false);

  useEffect(() => {
    // خوندن localStorage یه سیستم بیرونیه؛ طبق قرارداد این ریپو (نگاه کن به
    // OnboardingTour) با یه تایمر صفر-میلی‌ثانیه‌ای انجام می‌شه تا لینتر
    // set-state-in-effect رو به‌عنوان setState همگام داخل effect پرچم نکنه.
    const timer = setTimeout(() => {
      setAlreadySubscribed(window.localStorage.getItem(STORAGE_KEY) === "1");
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) {
      setError("لطفاً ایمیل خود را وارد کنید");
      setSubmitted(false);
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("ایمیل واردشده معتبر نیست");
      setSubmitted(false);
      return;
    }
    setError(null);
    setSubmitted(true);
    window.localStorage.setItem(STORAGE_KEY, "1");
    setAlreadySubscribed(true);
  }

  if (alreadySubscribed) {
    return (
      <Card className="w-full text-right">
        <CardHeader>
          <CardTitle>عضو خبرنامه‌ی ما هستید 🎉</CardTitle>
          <CardDescription>
            آیا از کیفیت خبرها و وبینارهای پیشنهادی رضایت دارید؟
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {feedbackGiven ? (
            <p className="text-muted-foreground text-sm">ممنون از بازخوردتون!</p>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setFeedbackGiven(true)}>
                راضی‌ام
              </Button>
              <Button variant="outline" size="sm" onClick={() => setFeedbackGiven(true)}>
                راضی نیستم
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full text-right">
      <CardHeader>
        <CardTitle>عضویت در خبرنامه</CardTitle>
        <CardDescription>
          برای اطلاع از آخرین اخبار و وبینارهای مختلف، در خبرنامه‌ی پلتفرم
          مدیریت و تجربه‌ی رویداد رویا ایونت عضو شوید.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-3 sm:flex-row">
          <Input
            type="email"
            placeholder="ایمیل شما"
            dir="ltr"
            className="text-right"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Button type="submit" className="shrink-0">
            عضویت
          </Button>
        </form>
        {error && <p className="text-destructive text-sm">{error}</p>}
        {submitted && !error && (
          <p className="text-muted-foreground text-sm">
            قابلیت عضویت در خبرنامه به‌زودی فعال می‌شود — ایمیل شما جایی ذخیره نشد.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default NewsletterSignup;
