"use client";

import { useMemo, useState } from "react";

import { normalizeProfileInput, normalizeProfileRecord } from "@/lib/profile-utils";
import { getSupabaseBrowserClient } from "@/lib/supabase";
import { ProfileRecord } from "@/lib/types";

type FormState = {
  profile_name: string;
  name: string;
  linkedin_url: string;
};

const initialState: FormState = {
  profile_name: "",
  name: "",
  linkedin_url: ""
};

export function CreateProfileForm({
  existingProfiles,
  onCreated
}: {
  existingProfiles: ProfileRecord[];
  onCreated: (created: ProfileRecord) => void;
}) {
  const [form, setForm] = useState<FormState>(initialState);
  const [touched, setTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const duplicateProfileName = useMemo(() => {
    const normalized = normalizeProfileInput(form.profile_name);
    return existingProfiles.some(
      (profile) => normalizeProfileInput(profile.profile_name) === normalized
    );
  }, [existingProfiles, form.profile_name]);

  const duplicateLinkedinUrl = useMemo(() => {
    const normalized = normalizeProfileInput(form.linkedin_url);
    return existingProfiles.some(
      (profile) => normalizeProfileInput(profile.linkedin_url) === normalized
    );
  }, [existingProfiles, form.linkedin_url]);

  const isValid =
    form.profile_name.trim() &&
    form.name.trim() &&
    form.linkedin_url.trim() &&
    !duplicateProfileName &&
    !duplicateLinkedinUrl;

  function updateField(key: keyof FormState, value: string) {
    setTouched(true);
    setErrorMessage("");
    setSuccessMessage("");
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setTouched(true);
    if (!isValid) return;
    setSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const supabase = getSupabaseBrowserClient();
      const payload = {
        profile_name: form.profile_name.trim(),
        name: form.name.trim(),
        linkedin_url: form.linkedin_url.trim(),
        active: true
      };

      const { data, error } = await supabase
        .from("profiles")
        .insert(payload)
        .select("id,profile_name,name,linkedin_url,last_connections_number,last_checked_at,active,created_at")
        .single();

      if (error) {
        throw error;
      }

      const createdRecord = normalizeProfileRecord(data as ProfileRecord);
      onCreated(createdRecord);
      setForm(initialState);
      setTouched(false);
      setSuccessMessage("Profile created successfully in Supabase.");
    } catch (caughtError) {
      setErrorMessage(caughtError instanceof Error ? caughtError.message : "Failed to create profile.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div className="rounded-3xl border border-border bg-panel p-6 shadow-panel">
        <div className="mb-5">
          <h2 className="text-xl font-semibold text-ink">Create Profile</h2>
          <p className="mt-1 text-sm text-muted">
            This form writes directly to Supabase after validating duplicates in the current dataset.
          </p>
        </div>

        {errorMessage ? (
          <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </div>
        ) : null}

        {successMessage ? (
          <div className="mb-4 rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
            {successMessage}
          </div>
        ) : null}

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label className="mb-2 block text-sm font-medium text-ink">Profile Name</label>
            <input
              value={form.profile_name}
              onChange={(event) => updateField("profile_name", event.target.value)}
              className="w-full rounded-2xl border border-border px-4 py-3 text-sm outline-none transition focus:border-brand"
              placeholder="USUT13A"
            />
            {touched && !form.profile_name.trim() ? (
              <p className="mt-2 text-sm text-red-600">`profile_name` is required.</p>
            ) : null}
            {touched && duplicateProfileName ? (
              <p className="mt-2 text-sm text-red-600">This `profile_name` already exists in the local dataset.</p>
            ) : null}
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-ink">Name</label>
            <input
              value={form.name}
              onChange={(event) => updateField("name", event.target.value)}
              className="w-full rounded-2xl border border-border px-4 py-3 text-sm outline-none transition focus:border-brand"
              placeholder="Hazel Carter"
            />
            {touched && !form.name.trim() ? (
              <p className="mt-2 text-sm text-red-600">`name` is required.</p>
            ) : null}
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-ink">LinkedIn URL</label>
            <input
              value={form.linkedin_url}
              onChange={(event) => updateField("linkedin_url", event.target.value)}
              className="w-full rounded-2xl border border-border px-4 py-3 text-sm outline-none transition focus:border-brand"
              placeholder="https://www.linkedin.com/in/example-profile"
            />
            {touched && !form.linkedin_url.trim() ? (
              <p className="mt-2 text-sm text-red-600">`linkedin_url` is required.</p>
            ) : null}
            {touched && duplicateLinkedinUrl ? (
              <p className="mt-2 text-sm text-red-600">This `linkedin_url` already exists in the local dataset.</p>
            ) : null}
          </div>

          <button
            type="submit"
            disabled={!isValid || submitting}
            className="rounded-2xl bg-brand px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {submitting ? "Saving..." : "Save Profile"}
          </button>
        </form>
      </div>

      <div className="rounded-3xl border border-border bg-panel p-6 shadow-panel">
        <h3 className="text-lg font-semibold text-ink">Validation Rules</h3>
        <p className="mt-1 text-sm text-muted">
          These checks run before the insert request goes to Supabase.
        </p>

        <div className="mt-5 space-y-3">
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="font-medium text-ink">`profile_name` must be unique</p>
            <p className="mt-1 text-sm text-muted">The form blocks inserts when an existing profile uses the same `profile_name`.</p>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="font-medium text-ink">`linkedin_url` must be unique</p>
            <p className="mt-1 text-sm text-muted">The form also blocks duplicates when the LinkedIn URL already exists in Supabase.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
