"use client";

import { useEffect, useState } from "react";
import { Heart } from "lucide-react";

import { Button } from "@/components/ui/button";
import { socialApi } from "@/lib/social-api";
import { useAuthStore } from "@/store/auth-store";

export function FavoriteButton({ eventId }: { eventId: number }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [favorited, setFavorited] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    socialApi
      .myFavorites(accessToken)
      .then((events) => setFavorited(events.some((e) => e.id === eventId)))
      .catch(() => setFavorited(false));
  }, [accessToken, eventId]);

  if (!accessToken) return null;

  async function toggle() {
    if (!accessToken || loading) return;
    setLoading(true);
    try {
      const result = favorited
        ? await socialApi.removeFavorite(eventId, accessToken)
        : await socialApi.addFavorite(eventId, accessToken);
      setFavorited(result.favorited);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button variant={favorited ? "default" : "outline"} size="sm" onClick={toggle} disabled={loading}>
      <Heart className={favorited ? "fill-current" : ""} />
      {favorited ? "علاقه‌مندی‌ها" : "افزودن به علاقه‌مندی‌ها"}
    </Button>
  );
}

export default FavoriteButton;
