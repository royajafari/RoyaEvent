import type { Metadata } from "next";

import { EventCard } from "@/components/EventCard";
import { eventsServer } from "@/lib/events-server";

export const metadata: Metadata = {
  title: "رویدادها | رویا ایونت",
  description: "لیست وبینارها و رویدادهای رویا ایونت",
};

export default async function EventsListPage() {
  const events = await eventsServer.listPublic();

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <h1 className="text-2xl font-bold">رویدادها</h1>

      {events.length === 0 ? (
        <p className="text-muted-foreground">فعلاً رویدادی منتشر نشده است.</p>
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
