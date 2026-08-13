import Link from "next/link";

import { EventCard } from "@/components/EventCard";
import { Badge } from "@/components/ui/badge";
import { NewsletterSignup } from "@/components/NewsletterSignup";
import { eventsServer } from "@/lib/events-server";
import { instructorsServer } from "@/lib/instructors-server";

export default async function Home() {
  const [instructors, popularEvents] = await Promise.all([
    instructorsServer.listPopular(),
    eventsServer.listPublic({ sort: "popular" }),
  ]);

  return (
    <div className="flex flex-1 flex-col items-center gap-16 bg-zinc-50 px-4 py-16 dark:bg-black">
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

      {popularEvents.length > 0 && (
        <section className="flex w-full max-w-4xl flex-col gap-4">
          <h2 className="text-lg font-semibold">وبینارهای محبوب</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
            {popularEvents.slice(0, 6).map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        </section>
      )}

      {instructors.length > 0 && (
        <section className="flex w-full max-w-4xl flex-col gap-4">
          <h2 className="text-lg font-semibold">مدرس‌های محبوب</h2>
          <div className="flex flex-wrap justify-center gap-6">
            {instructors.map((instructor) => (
              <Link
                key={instructor.id}
                href={`/instructors/${instructor.id}`}
                className="flex w-24 flex-col items-center gap-2 text-center"
              >
                <div className="bg-muted flex h-20 w-20 items-center justify-center overflow-hidden rounded-full transition-opacity hover:opacity-80">
                  {instructor.avatar_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={instructor.avatar_url}
                      alt={instructor.name}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <span className="text-muted-foreground text-xl">
                      {instructor.name.charAt(0)}
                    </span>
                  )}
                </div>
                <span className="line-clamp-2 text-sm font-medium">{instructor.name}</span>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
