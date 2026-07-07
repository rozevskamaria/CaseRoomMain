import { useCallback } from "react";
import { useApolloClient, useQuery } from "@apollo/client";
import App from "../../App";
import { MeQuery } from "../../graphql/authOperations";
import { EducatorDashboard } from "../dashboard";
import { AuthScreens } from "./AuthScreens";
import { AuthSpinner } from "./AuthShell";

function readVerifyToken(): string | null {
  if (window.location.pathname !== "/auth/verify") return null;
  return new URLSearchParams(window.location.search).get("token");
}

export function AuthGate() {
  const client = useApolloClient();
  const { data, loading, refetch } = useQuery(MeQuery, {
    fetchPolicy: "cache-and-network",
  });

  const onAuthed = useCallback(() => {
    if (window.location.pathname === "/auth/verify") {
      window.history.replaceState({}, "", "/");
    }
    void refetch();
  }, [refetch]);

  const onLogout = useCallback(() => {
    void client.resetStore();
  }, [client]);

  if (loading && data === undefined) {
    return <AuthSpinner />;
  }

  if (!data?.me) {
    const isVerify = window.location.pathname === "/auth/verify";
    return (
      <AuthScreens
        initialRoute={isVerify ? "verify" : "login"}
        verifyToken={readVerifyToken()}
        onAuthed={onAuthed}
      />
    );
  }

  const role = data.me.role;
  if (role === "staff" || role === "admin") {
    return <EducatorDashboard me={data.me} onLogout={onLogout} />;
  }

  return <App onLogout={onLogout} />;
}
