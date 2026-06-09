import { ProfileRecord } from "@/lib/types";

export function normalizeProfileRecord(record: Partial<ProfileRecord>): ProfileRecord {
  const rawConnections = record.last_connections_number as number | string | null | undefined;
  const normalizedConnections =
    rawConnections === null ||
    rawConnections === undefined ||
    rawConnections === "" ||
    Number.isNaN(Number(rawConnections))
      ? null
      : Number(rawConnections);

  return {
    id: typeof record.id === "number" ? record.id : record.id ? Number(record.id) : undefined,
    profile_name: String(record.profile_name ?? "").trim(),
    name: String(record.name ?? "").trim(),
    linkedin_url: String(record.linkedin_url ?? "").trim(),
    last_connections_number: normalizedConnections,
    last_checked_at: String(record.last_checked_at ?? "").trim(),
    active: record.active === true || String(record.active).toLowerCase() === "true",
    created_at: String(record.created_at ?? "").trim()
  };
}

export function formatDateTime(value: string): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function formatConnections(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";
  return value.toLocaleString();
}

export function calculateSummary(records: ProfileRecord[]) {
  const activeCount = records.filter((record) => record.active).length;
  const withConnections = records.filter(
    (record) => typeof record.last_connections_number === "number"
  );
  const totalConnections = withConnections.reduce(
    (sum, record) => sum + (record.last_connections_number ?? 0),
    0
  );
  const averageConnections = withConnections.length
    ? Math.round(totalConnections / withConnections.length)
    : 0;
  const highestConnections = withConnections.reduce(
    (highest, record) =>
      Math.max(highest, record.last_connections_number ?? 0),
    0
  );

  return {
    totalProfiles: records.length,
    activeCount,
    averageConnections,
    highestConnections
  };
}

export function normalizeProfileInput(value: string): string {
  return value.trim().toLowerCase();
}
