import type { Metadata } from "next";

import { EventCard } from "@/components/EventCard";
import { EventsFilter } from "@/components/EventsFilter";
import { eventsServer } from "@/lib/events-server";

export const metadata: Metadata = {
  title: "رویدادها | رویا ایونت",
  description: "لیست وبینارها و رویدادهای رویا ایونت",
};

type Props = {
  searchParams: Promise<{ category?: string; format?: string; sort?: string; featured?: string }>;
};

export default async function EventsListPage({ searchParams }: Props) {
  const { category, format, sort, featured } = await searchParams;
  const categoryId = category ? Number(category) : undefined;
  const featuredOnly = featured === "true";

  const [events, categories] = await Promise.all([
    eventsServer.listPublic({ categoryId, format, sort, featured: featuredOnly || undefined }),
    eventsServer.listCategories(),
  ]);

  const heading = sort === "popular" ? "وبینارهای محبوب" : featuredOnly ? "وبینارهای ویژه" : "رویدادها";

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{heading}</h1>
        <EventsFilter categories={categories} />
      </div>

      {events.length === 0 ? (
        <p className="text-muted-foreground">رویدادی با این فیلتر پیدا نشد.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
          {events.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      )}
    </div>
  );
}
