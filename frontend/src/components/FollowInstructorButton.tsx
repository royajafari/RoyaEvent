"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { socialApi } from "@/lib/social-api";
import { useAuthStore } from "@/store/auth-store";

export function FollowInstructorButton({ instructorId }: { instructorId: number }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [following, setFollowing] = useState(false);
  const [followerCount, setFollowerCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    socialApi
      .myFollows(accessToken)
      .then((follows) => setFollowing(follows.instructor_ids.includes(instructorId)))
      .catch(() => setFollowing(false));
  }, [accessToken, instructorId]);

  async function toggle() {
    if (!accessToken || loading) return;
    setLoading(true);
    try {
      const result = following
        ? await socialApi.unfollowInstructor(instructorId, accessToken)
        : await socialApi.followInstructor(instructorId, accessToken);
      setFollowing(result.following);
      setFollowerCount(result.follower_count);
    } finally {
      setLoading(false);
    }
  }

  if (!accessToken) return null;

  return (
    <Button variant={following ? "default" : "outline"} size="sm" onClick={toggle} disabled={loading}>
      {following ? "دنبال می‌کنید" : "دنبال کردن مدرس"}
      {followerCount !== null && ` (${followerCount.toLocaleString("fa-IR")})`}
    </Button>
  );
}

export default FollowInstructorButton;
