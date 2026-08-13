"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { socialApi } from "@/lib/social-api";
import { useAuthStore } from "@/store/auth-store";

export function FollowOrganizerButton({ organizerId }: { organizerId: number }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [following, setFollowing] = useState(false);
  const [followerCount, setFollowerCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    socialApi
      .myFollows(accessToken)
      .then((follows) => setFollowing(follows.organizer_ids.includes(organizerId)))
      .catch(() => setFollowing(false));
  }, [accessToken, organizerId]);

  async function toggle() {
    if (!accessToken || loading) return;
    setLoading(true);
    try {
      const result = following
        ? await socialApi.unfollowOrganizer(organizerId, accessToken)
        : await socialApi.followOrganizer(organizerId, accessToken);
      setFollowing(result.following);
      setFollowerCount(result.follower_count);
    } finally {
      setLoading(false);
    }
  }

  if (!accessToken) return null;

  return (
    <Button variant={following ? "default" : "outline"} size="sm" onClick={toggle} disabled={loading}>
      {following ? "دنبال می‌کنید" : "دنبال کردن برگزارکننده"}
      {followerCount !== null && ` (${followerCount.toLocaleString("fa-IR")})`}
    </Button>
  );
}

export default FollowOrganizerButton;
