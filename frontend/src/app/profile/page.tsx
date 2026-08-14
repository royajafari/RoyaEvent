"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, authApi } from "@/lib/api-client";
import type { UserOut } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth-store";

export default function ProfilePage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setGlobalUser = useAuthStore((s) => s.setUser);
  const [user, setUser] = useState<UserOut | null>(null);
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingName, setSavingName] = useState(false);
  const [nameSaved, setNameSaved] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [avatarProgress, setAvatarProgress] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    authApi
      .me(accessToken)
      .then((u) => {
        setUser(u);
        setFullName(u.full_name ?? "");
      })
      .finally(() => setLoading(false));
  }, [accessToken]);

  async function handleSaveName(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !fullName.trim()) return;
    setNameError(null);
    setNameSaved(false);
    setSavingName(true);
    try {
      const updated = await authApi.updateProfile(fullName.trim(), accessToken);
      setUser(updated);
      setGlobalUser(updated);
      setNameSaved(true);
    } catch (err) {
      setNameError(err instanceof ApiError ? err.message : "خطا در ذخیره‌ی نام");
    } finally {
      setSavingName(false);
    }
  }

  async function handleAvatarUpload(file: File) {
    if (!accessToken) return;
    setAvatarError(null);
    setAvatarProgress(0);
    try {
      const updated = await authApi.uploadAvatar(file, accessToken, setAvatarProgress);
      setUser(updated);
      setGlobalUser(updated);
    } catch (err) {
      setAvatarError(err instanceof ApiError ? err.message : "خطا در آپلود عکس پروفایل");
    } finally {
      setAvatarProgress(null);
    }
  }

  if (!accessToken) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p>برای دیدن پروفایل خودتان باید وارد شوید.</p>
        <Link href="/login" className={buttonVariants({ className: "mt-4" })}>
          ورود
        </Link>
      </div>
    );
  }

  if (loading) {
    return <p className="text-muted-foreground px-4 py-10 text-center">در حال بارگذاری...</p>;
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-10">
      <h1 className="text-2xl font-bold">پروفایل من</h1>

      <div className="flex flex-col gap-6 md:flex-row md:items-start">
        <Card className="text-right md:w-72 md:shrink-0">
          <CardHeader>
            <CardTitle>عکس پروفایل</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4">
            <div className="bg-muted flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full">
              {user?.avatar_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={user.avatar_url} alt="عکس پروفایل" className="h-full w-full object-cover" />
              ) : (
                <span className="text-muted-foreground text-2xl">
                  {(user?.full_name || user?.phone || "?").charAt(0)}
                </span>
              )}
            </div>
            <div className="flex flex-col items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept="image/png,image/jpeg,image/webp"
                onChange={(e) => e.target.files?.[0] && handleAvatarUpload(e.target.files[0])}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-fit"
                onClick={() => fileInputRef.current?.click()}
                disabled={avatarProgress !== null}
              >
                {avatarProgress !== null ? `در حال آپلود... ${avatarProgress}%` : "تغییر عکس پروفایل"}
              </Button>
              {avatarError && <p className="text-destructive text-sm">{avatarError}</p>}
            </div>
          </CardContent>
        </Card>

        <Card className="text-right flex-1">
          <CardHeader>
            <CardTitle>اطلاعات حساب</CardTitle>
            <CardDescription>
              {user?.phone ? `شماره موبایل: ${user.phone}` : user?.email ? `ایمیل: ${user.email}` : null}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveName} className="flex flex-col gap-3">
              <div className="flex flex-col gap-2">
                <Label htmlFor="full-name">نام و نام خانوادگی</Label>
                <Input
                  id="full-name"
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    setNameSaved(false);
                  }}
                  required
                />
              </div>
              {nameError && <p className="text-destructive text-sm">{nameError}</p>}
              {nameSaved && !nameError && (
                <p className="text-sm text-green-600 dark:text-green-500">تغییرات شما ذخیره شد ✓</p>
              )}
              <Button type="submit" className="w-fit" disabled={savingName || !fullName.trim()}>
                {savingName ? "در حال ذخیره..." : "ذخیره"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
