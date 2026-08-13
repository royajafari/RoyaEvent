import { RoyaEventLogo } from "@/components/RoyaEventLogo";

export function SiteFooter() {
  // سال شمسی برای هماهنگی با کل سایت (نمایش جلالی، ذخیره‌ی میلادی طبق قرارداد lib/date.ts)
  const jalaliYear = new Intl.DateTimeFormat("fa-IR-u-ca-persian", { year: "numeric" }).format(
    new Date(),
  );

  return (
    <footer className="border-border mt-auto flex flex-col items-center gap-2 border-t px-4 py-6 text-center">
      <RoyaEventLogo size={18} />
      <p className="text-muted-foreground text-sm">
        © {jalaliYear} تمامی حقوق برای رویا ایونت محفوظ است.
      </p>
    </footer>
  );
}

export default SiteFooter;
