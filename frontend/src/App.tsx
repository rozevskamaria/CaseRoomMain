import { gql, useQuery } from "@apollo/client";

const PING = gql`
  query Ping {
    ping
    version
    health
  }
`;

interface PingData {
  ping: string;
  version: string;
  health: string;
}

export default function App() {
  const { data, loading, error } = useQuery<PingData>(PING);

  const containerStyle: React.CSSProperties = {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "column",
    gap: "0.75rem",
    textAlign: "center",
    padding: "2rem",
  };

  let status: React.ReactNode;
  if (loading) {
    status = <p>Connecting to backend…</p>;
  } else if (error || !data) {
    status = (
      <>
        <p>Backend not yet connected.</p>
        <p style={{ fontSize: "0.9rem", opacity: 0.7 }}>
          Start the backend at <code>{import.meta.env.VITE_GRAPHQL_URL}</code> and reload.
        </p>
      </>
    );
  } else {
    status = (
      <p>
        Backend says: {data.ping} · v{data.version}
      </p>
    );
  }

  return (
    <main style={containerStyle}>
      <h1 style={{ fontWeight: 700 }}>CaseRoom</h1>
      {status}
    </main>
  );
}
