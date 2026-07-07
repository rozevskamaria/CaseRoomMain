import { useState } from "react";
import { LoginView } from "./LoginView";
import { RegisterView } from "./RegisterView";
import { VerifyView } from "./VerifyView";

type AuthRoute = "login" | "register" | "verify";

export interface AuthScreensProps {
  initialRoute?: AuthRoute;
  verifyToken?: string | null;
  onAuthed: () => void;
}

function clearVerifyUrl() {
  if (window.location.pathname === "/auth/verify") {
    window.history.replaceState({}, "", "/");
  }
}

export function AuthScreens({
  initialRoute = "login",
  verifyToken = null,
  onAuthed,
}: AuthScreensProps) {
  const [route, setRoute] = useState<AuthRoute>(initialRoute);

  if (route === "verify") {
    return (
      <VerifyView
        token={verifyToken}
        onConfirmed={onAuthed}
        onBackToLogin={() => {
          clearVerifyUrl();
          setRoute("login");
        }}
      />
    );
  }

  if (route === "register") {
    return <RegisterView onGoToLogin={() => setRoute("login")} />;
  }

  return (
    <LoginView onGoToRegister={() => setRoute("register")} onAuthed={onAuthed} />
  );
}
