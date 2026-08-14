import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { EventCard } from "@/components/EventCard";
import { FollowOrganizerButton } from "@/components/FollowOrganizerButton";
import { Separator } from "@/components/ui/separator";
import { organizersServer } from "@/lib/organizers-server";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const organizer = await organizersServer.getById(Number(id));
  if (!organizer) return { title: "برگزارکننده یافت نشد" };
  return { title: `${organizer.name ?? "برگزارکننده"} | رویا ایونت` };
}

export default async function OrganizerDetailPage({ params }: Props) {
  const { id } = await params;
  const organizer = await organizersServer.getById(Number(id));
  if (!organizer) notFound();

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-wrap items-center gap-4">
        <div className="bg-muted flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full">
          {organizer.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={organizer.avatar_url}
              alt={organizer.name ?? "برگزارکننده"}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-muted-foreground text-2xl">
              {(organizer.name ?? "؟").charAt(0)}
            </span>
          )}
        </div>
        <div className="flex min-w-0 flex-col gap-1">
          <h1 className="text-2xl font-bold sm:text-3xl">{organizer.name ?? "بدون نام"}</h1>
          <span className="text-muted-foreground text-sm">
            {organizer.follower_count.toLocaleString("fa-IR")} دنبال‌کننده
          </span>
        </div>
        <div className="sm:mr-auto">
          <FollowOrganizerButton organizerId={organizer.id} />
        </div>
      </div>

      <Separator />

      <section className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold">رویدادهای این برگزارکننده</h2>
        {organizer.events.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            فعلاً رویداد منتشرشده‌ای از این برگزارکننده نیست.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
            {organizer.events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
