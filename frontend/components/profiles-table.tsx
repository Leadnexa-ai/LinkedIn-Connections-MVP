"use client";

import { useMemo, useState } from "react";

import { formatConnections, formatDateTime } from "@/lib/profile-utils";
import { ProfileRecord } from "@/lib/types";

type SortKey = "profile_name" | "name" | "last_connections_number";

export function ProfilesTable({ records }: { records: ProfileRecord[] }) {
  const [query, setQuery] = useState("");
  const [activeOnly, setActiveOnly] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>("last_connections_number");

  const filteredRows = useMemo(() => {
    const loweredQuery = query.trim().toLowerCase();
    const rows = records.filter((record) => {
      if (activeOnly && !record.active) return false;
      if (!loweredQuery) return true;
      return (
        record.profile_name.toLowerCase().includes(loweredQuery) ||
        record.name.toLowerCase().includes(loweredQuery)
      );
    });

    return rows.sort((left, right) => {
      if (sortKey === "last_connections_number") {
        return (right.last_connections_number ?? -1) - (left.last_connections_number ?? -1);
      }
      return left[sortKey].localeCompare(right[sortKey]);
    });
  }, [activeOnly, query, records, sortKey]);

  return (
    <div className="rounded-3xl border border-border bg-panel p-5 shadow-panel">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-lg font-semibold text-ink">Profiles</h3>
          <p className="text-sm text-muted">Search, sort, and review the latest connection counts.</p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search profile name or person name"
            className="rounded-2xl border border-border bg-white px-4 py-2 text-sm outline-none ring-0 transition focus:border-brand"
          />
          <select
            value={sortKey}
            onChange={(event) => setSortKey(event.target.value as SortKey)}
            className="rounded-2xl border border-border bg-white px-4 py-2 text-sm outline-none transition focus:border-brand"
          >
            <option value="last_connections_number">Sort by connections</option>
            <option value="profile_name">Sort by profile_name</option>
            <option value="name">Sort by name</option>
          </select>
          <label className="flex items-center gap-2 rounded-2xl border border-border px-4 py-2 text-sm text-ink">
            <input
              checked={activeOnly}
              onChange={(event) => setActiveOnly(event.target.checked)}
              type="checkbox"
              className="h-4 w-4 rounded border-border"
            />
            Active only
          </label>
        </div>
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-y-2">
          <thead>
            <tr className="text-left text-xs font-semibold uppercase tracking-wide text-muted">
              <th className="px-4 py-2">Profile Name</th>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">LinkedIn URL</th>
              <th className="px-4 py-2">Connections</th>
              <th className="px-4 py-2">Last Checked</th>
              <th className="px-4 py-2">Active</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((record) => (
              <tr key={record.linkedin_url} className="rounded-2xl bg-slate-50 text-sm text-ink">
                <td className="rounded-l-2xl px-4 py-3 font-medium">{record.profile_name}</td>
                <td className="px-4 py-3">{record.name}</td>
                <td className="max-w-xs px-4 py-3">
                  <a href={record.linkedin_url} target="_blank" rel="noreferrer" className="line-clamp-1">
                    {record.linkedin_url}
                  </a>
                </td>
                <td className="px-4 py-3">{formatConnections(record.last_connections_number)}</td>
                <td className="px-4 py-3">{formatDateTime(record.last_checked_at)}</td>
                <td className="rounded-r-2xl px-4 py-3">
                  <span
                    className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                      record.active ? "bg-green-100 text-green-700" : "bg-slate-200 text-slate-600"
                    }`}
                  >
                    {record.active ? "Active" : "Inactive"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
