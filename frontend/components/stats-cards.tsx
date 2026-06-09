type StatsCardsProps = {
  totalProfiles: number;
  activeCount: number;
  averageConnections: number;
  highestConnections: number;
};

const cards: Array<{
  key: keyof StatsCardsProps;
  label: string;
}> = [
  { key: "totalProfiles", label: "Total Profiles" },
  { key: "activeCount", label: "Active Profiles" },
  { key: "averageConnections", label: "Avg Connections" },
  { key: "highestConnections", label: "Highest Connections" }
];

export function StatsCards(props: StatsCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.key}
          className="rounded-3xl border border-border bg-panel p-5 shadow-panel"
        >
          <p className="text-sm font-medium text-muted">{card.label}</p>
          <p className="mt-3 text-3xl font-semibold text-ink">
            {props[card.key].toLocaleString()}
          </p>
        </div>
      ))}
    </div>
  );
}
