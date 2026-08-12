import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { EventCard } from "@/components/EventCard";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { formatJalaliDateTime } from "@/lib/date";
import { eventsServer } from "@/lib/events-server";

const FORMAT_LABELS = { online: "آنلاین", in_person: "حضوری", hybrid: "ترکیبی" } as const;

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const event = await eventsServer.getBySlug(slug);
  if (!event) return { title: "رویداد یافت نشد" };
  return {
    title: `${event.title} | رویا ایونت`,
    description: event.description.slice(0, 150),
  };
}

export default async function EventDetailPage({ params }: Props) {
  const { slug } = await params;
  const event = await eventsServer.getBySlug(slug);
  if (!event) notFound();

  const related = await eventsServer.getRelated(event.id);
  const isMultiSession = event.sessions.length > 1;
  const firstSession = event.sessions[0];
  const totalDuration = event.sessions.reduce((sum, s) => sum + s.duration_minutes, 0);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Event",
    name: event.title,
    description: event.description,
    startDate: firstSession?.starts_at,
    eventAttendanceMode:
      event.format === "online"
        ? "https://schema.org/OnlineEventAttendanceMode"
        : "https://schema.org/OfflineEventAttendanceMode",
    eventStatus: "https://schema.org/EventScheduled",
    location:
      event.format === "online"
        ? { "@type": "VirtualLocation", url: event.online_platform_name ?? "" }
        : { "@type": "Place", name: event.venue_address ?? "" },
    image: event.banner_url ?? undefined,
  };

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {event.banner_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={event.banner_url}
          alt={event.title}
          className="aspect-video w-full rounded-lg object-cover"
        />
      ) : (
        <div className="bg-muted aspect-video w-full rounded-lg" />
      )}

      <div className="flex flex-wrap items-center gap-2">
        {event.category && <Badge variant="secondary">{event.category.name}</Badge>}
        <Badge variant="outline">{FORMAT_LABELS[event.format]}</Badge>
        {event.tags.map((tag) => (
          <Badge key={tag.id} variant="outline">
            #{tag.name}
          </Badge>
        ))}
      </div>

      <h1 className="text-2xl font-bold sm:text-3xl">{event.title}</h1>

      <div className="text-muted-foreground flex flex-wrap gap-x-6 gap-y-2 text-sm">
        <span>کد رویداد: {event.event_code}</span>
        {firstSession && <span>شروع: {formatJalaliDateTime(firstSession.starts_at)}</span>}
        <span>مدت کل: {totalDuration} دقیقه</span>
        <span>{isMultiSession ? `${event.sessions.length} جلسه` : "تک‌جلسه‌ای"}</span>
      </div>

      <Separator />

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold">توضیحات</h2>
        <div className="whitespace-pre-wrap leading-relaxed">{event.description}</div>
      </section>

      <Separator />

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold">محل برگزاری</h2>
        {event.format === "online" ? (
          <p>آنلاین — {event.online_platform_name ?? "پلتفرم اعلام نشده"}</p>
        ) : (
          <p>{event.venue_address}</p>
        )}
      </section>

      <Separator />

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">
          {isMultiSession ? "جلسه‌ها" : "جلسه"}
        </h2>
        <ul className="flex flex-col gap-2">
          {event.sessions.map((session, index) => (
            <li key={session.id} className="rounded-md border p-3 text-sm">
              <div className="font-medium">
                {isMultiSession ? `جلسه ${index + 1}` : "زمان برگزاری"}
              </div>
              <div className="text-muted-foreground">
                {formatJalaliDateTime(session.starts_at)} — {session.duration_minutes} دقیقه
              </div>
            </li>
          ))}
        </ul>
      </section>

      {event.refund_policy && (
        <>
          <Separator />
          <section className="flex flex-col gap-2">
            <h2 className="text-lg font-semibold">قوانین بازگشت وجه</h2>
            <p className="text-muted-foreground text-sm">{event.refund_policy}</p>
          </section>
        </>
      )}

      {related.length > 0 && (
        <>
          <Separator />
          <section className="flex flex-col gap-4">
            <h2 className="text-lg font-semibold">وبینارهای پیشنهادی</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
              {related.map((e) => (
                <EventCard key={e.id} event={e} />
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
