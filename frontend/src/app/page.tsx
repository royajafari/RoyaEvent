import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center bg-zinc-50 px-4 py-16 dark:bg-black">
      <div className="flex w-full max-w-2xl flex-col items-center gap-6 text-center">
        <div className="flex w-full justify-end">
          <Link href="/login" className={buttonVariants({ variant: "outline", size: "sm" })}>
            ورود
          </Link>
        </div>
        <Badge variant="secondary">نسخه‌ی در حال توسعه</Badge>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          رویا ایونت
        </h1>
        <p className="text-muted-foreground max-w-md text-lg">
          پلتفرم مدیریت و تجربه‌ی رویداد و وبینار — به‌زودی می‌تونید رویدادها
          رو کشف کنید، بلیط بگیرید و رویداد خودتون رو برگزار کنید.
        </p>

        <Card className="w-full text-right">
          <CardHeader>
            <CardTitle>عضویت در خبرنامه</CardTitle>
            <CardDescription>
              برای اطلاع از آخرین اخبار و وبینارهای مختلف، در خبرنامه‌ی
              پلتفرم مدیریت و تجربه‌ی رویداد رویا ایونت عضو شوید.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 sm:flex-row">
            <input
              type="email"
              placeholder="ایمیل شما"
              dir="ltr"
              className="border-input flex h-9 w-full rounded-md border bg-transparent px-3 py-1 text-right text-sm shadow-xs outline-none"
            />
            <Button className="shrink-0">عضویت</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
