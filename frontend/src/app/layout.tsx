import type { Metadata } from "next";
import { OnboardingTour } from "@/components/OnboardingTour";
import { SessionBootstrap } from "@/components/SessionBootstrap";
import { SiteHeader } from "@/components/SiteHeader";
import { kalameh } from "@/fonts/kalameh";
import "./globals.css";

export const metadata: Metadata = {
  title: "رویا ایونت | مدیریت و برگزاری رویداد و وبینار",
  description:
    "رویا ایونت؛ پلتفرم مدیریت و تجربه‌ی رویداد و وبینار — کشف، ثبت‌نام و برگزاری رویدادهای آنلاین و حضوری.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="fa"
      dir="rtl"
      className={`dark ${kalameh.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        <SessionBootstrap />
        <SiteHeader />
        {children}
        <OnboardingTour />
      </body>
    </html>
  );
}
