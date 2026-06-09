export type ProfileRecord = {
  id?: number;
  profile_name: string;
  name: string;
  linkedin_url: string;
  last_connections_number: number | null;
  last_checked_at: string;
  active: boolean;
  created_at?: string;
};
