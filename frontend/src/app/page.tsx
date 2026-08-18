import Link from "next/link";

import { CategoryCarousel } from "@/components/CategoryCarousel";
import { EventCarousel } from "@/components/EventCarousel";
import { Badge } from "@/components/ui/badge";
import { NewsletterSignup } from "@/components/NewsletterSignup";
import { eventsServer } from "@/lib/events-server";
import { homeServer } from "@/lib/home-server";

export default async function Home() {
  const [sections, allCategories] = await Promise.all([
    homeServer.getSections(),
    eventsServer.listCategories(),
  ]);
  const parentCategories = allCategories.filter((c) => c.parent_id === null);

  return (
    <div className="flex flex-1 flex-col items-center gap-16 bg-zinc-50 py-16 dark:bg-black">
      <div className="flex w-full max-w-2xl flex-col items-center gap-6 px-4 text-center">
        <Badge variant="secondary">نسخه‌ی در حال توسعه</Badge>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">رویا ایونت</h1>
        <p className="text-muted-foreground max-w-md text-lg">
          پلتفرم مدیریت و تجربه‌ی رویداد و وبینار — به‌زودی می‌تونید رویدادها
          رو کشف کنید، بلیط بگیرید و رویداد خودتون رو برگزار کنید.
        </p>

        <NewsletterSignup />
      </div>

      <CategoryCarousel categories={parentCategories} />

      {sections.upcoming_events.length > 0 && (
        <EventCarousel
          id="tour-upcoming"
          title="وبینارهای پیش‌رو"
          events={sections.upcoming_events}
          viewAllHref="/events"
          highlight
          pulseIcon="dot"
        />
      )}

      {sections.top_rated_events.length > 0 && (
        <EventCarousel
          title="برترین وبینارها"
          events={sections.top_rated_events}
          viewAllHref="/events?sort=top_rated"
        />
      )}

      <EventCarousel
        title="وبینارهای محبوب"
        events={sections.popular_events}
        viewAllHref="/events?sort=popular"
        pulseIcon="heart"
      />

      <EventCarousel
        title="آخرین وبینارها"
        events={sections.latest_events}
        viewAllHref="/events"
      />

      <EventCarousel
        id="tour-featured"
        title="وبینارهای ویژه"
        events={sections.featured_events}
        viewAllHref="/events?featured=true"
        pulseIcon="star"
      />

      {sections.popular_instructors.length > 0 && (
        <section className="flex w-full max-w-4xl flex-col gap-4 px-4">
          <h2 className="text-lg font-semibold">مدرس‌های محبوب</h2>
          <div className="flex flex-wrap justify-center gap-6">
            {sections.popular_instructors.map((instructor) => (
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

      {sections.popular_organizers.length > 0 && (
        <section className="flex w-full max-w-4xl flex-col gap-4 px-4">
          <h2 className="text-lg font-semibold">برگزارکننده‌های محبوب</h2>
          <div className="flex flex-wrap justify-center gap-6">
            {sections.popular_organizers.map((organizer) => (
              <Link
                key={organizer.id}
                href={`/organizers/${organizer.id}`}
                className="flex w-24 flex-col items-center gap-2 text-center"
              >
                <div className="bg-muted flex h-20 w-20 items-center justify-center overflow-hidden rounded-full transition-opacity hover:opacity-80">
                  {organizer.avatar_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={organizer.avatar_url}
                      alt={organizer.name}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <span className="text-muted-foreground text-xl">
                      {organizer.name.charAt(0)}
                    </span>
                  )}
                </div>
                <span className="line-clamp-2 text-sm font-medium">{organizer.name}</span>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
