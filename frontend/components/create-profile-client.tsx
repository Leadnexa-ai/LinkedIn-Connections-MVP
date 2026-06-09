"use client";

import { useEffect, useState } from "react";

import { CreateProfileForm } from "@/components/create-profile-form";
import { normalizeProfileRecord } from "@/lib/profile-utils";
import { getSupabaseBrowserClient } from "@/lib/supabase";
import { ProfileRecord } from "@/lib/types";

export function CreateProfileClient() {
  const [profiles, setProfiles] = useState<ProfileRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadProfiles() {
      try {
        const supabase = getSupabaseBrowserClient();
        const { data, error } = await supabase
          .from("profiles")
          .select(
            "id,profile_name,name,linkedin_url,last_connections_number,last_checked_at,active,created_at"
          )
          .order("profile_name", { ascending: true });

        if (error) throw error;
        if (!active) return;
        setProfiles(((data ?? []) as ProfileRecord[]).map(normalizeProfileRecord));
      } catch (caughtError) {
        if (!active) return;
        setError(caughtError instanceof Error ? caughtError.message : "Failed to load profiles.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadProfiles();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-border bg-panel p-6 shadow-panel">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">Create Profile</p>
        <h2 className="mt-3 text-3xl font-semibold text-ink">Account creator intake form</h2>
        <p className="mt-2 max-w-3xl text-sm text-muted">
          This page writes directly to the real Supabase `profiles` table and blocks duplicate `profile_name` and
          duplicate `linkedin_url`.
        </p>
      </section>

      {error ? (
        <div className="rounded-3xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</div>
      ) : null}

      {loading ? (
        <div className="rounded-3xl border border-border bg-panel p-8 text-sm text-muted shadow-panel">
          Loading profiles from Supabase...
        </div>
      ) : (
        <CreateProfileForm
          existingProfiles={profiles}
          onCreated={(created) => setProfiles((current) => [created, ...current])}
        />
      )}
    </div>
  );
}
