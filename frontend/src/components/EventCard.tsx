import Link from "next/link";

import { InstantRegisterButton } from "@/components/InstantRegisterButton";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { formatJalaliShort } from "@/lib/date";
import type { EventListItem } from "@/lib/events-api";

const FORMAT_LABELS: Record<EventListItem["format"], string> = {
  online: "آنلاین",
  in_person: "حضوری",
  hybrid: "ترکیبی",
};

export function EventCard({ event }: { event: EventListItem }) {
  // مقایسه با «اکنون» ذاتاً وابسته به زمان رندر است (نه یک باگ خالص‌بودن
  // واقعی)؛ این کامپوننت همیشه به‌صورت Server Component و تازه در هر
  // درخواست رندر می‌شود، پس ریسک ناهماهنگی hydration بین سرور/کلاینت وجود ندارد.
  // eslint-disable-next-line react-hooks/purity -- مقایسه با «اکنون» است، نه باگ
  const isPast = event.next_session_at ? new Date(event.next_session_at).getTime() < Date.now() : false;

  return (
    <Link href={`/events/${event.slug}`} className="block h-full">
      <Card
        className={`h-full overflow-hidden pt-0 transition-shadow hover:shadow-md ${
          isPast ? "opacity-60" : ""
        }`}
      >
        <div className="bg-muted relative aspect-video w-full overflow-hidden">
          {event.banner_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={event.banner_url}
              alt={event.title}
              className={`h-full w-full object-cover ${isPast ? "blur-[2px]" : ""}`}
            />
          ) : (
            <div className="text-muted-foreground flex h-full w-full items-center justify-center text-sm">
              بدون بنر
            </div>
          )}
          {isPast && (
            <Badge variant="secondary" className="absolute bottom-2 right-2">
              این وبینار برگزار شده است
            </Badge>
          )}
          {event.is_featured && (
            <Badge className="absolute top-2 right-2">ویژه</Badge>
          )}
          {event.is_instant_registration && (
            <Badge variant="destructive" className="absolute top-2 left-2">
              فوری
            </Badge>
          )}
        </div>
        <CardHeader>
          <CardTitle className="line-clamp-2 text-base">{event.title}</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground flex flex-col gap-1 text-sm">
          {event.category && <span>{event.category.name}</span>}
          {event.next_session_at && <span>{formatJalaliShort(event.next_session_at)}</span>}
        </CardContent>
        <CardFooter className="flex items-center justify-between gap-2">
          <Badge variant="outline">{FORMAT_LABELS[event.format]}</Badge>
          {event.rating_count > 0 && (
            <span className="text-sm">
              ⭐ {event.rating_avg.toFixed(1)} ({event.rating_count})
            </span>
          )}
          {event.is_instant_registration && !isPast && event.status === "published" && (
            <InstantRegisterButton event={event} />
          )}
        </CardFooter>
      </Card>
    </Link>
  );
}
