import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ApolloProvider } from "@apollo/client";
import { I18nextProvider } from "react-i18next";
import { client } from "./apollo";
import i18n from "./i18n";
import { AuthGate } from "./screens/auth";
import "./index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <I18nextProvider i18n={i18n}>
      <ApolloProvider client={client}>
        <AuthGate />
      </ApolloProvider>
    </I18nextProvider>
  </StrictMode>,
);
