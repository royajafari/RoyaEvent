import { Badge } from "@/components/ui/badge";
import { NewsletterSignup } from "@/components/NewsletterSignup";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center bg-zinc-50 px-4 py-16 dark:bg-black">
      <div className="flex w-full max-w-2xl flex-col items-center gap-6 text-center">
        <Badge variant="secondary">نسخه‌ی در حال توسعه</Badge>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          رویا ایونت
        </h1>
        <p className="text-muted-foreground max-w-md text-lg">
          پلتفرم مدیریت و تجربه‌ی رویداد و وبینار — به‌زودی می‌تونید رویدادها
          رو کشف کنید، بلیط بگیرید و رویداد خودتون رو برگزار کنید.
        </p>

        <NewsletterSignup />
      </div>
    </div>
  );
}
