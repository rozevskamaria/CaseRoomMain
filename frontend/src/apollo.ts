import { ApolloClient, InMemoryCache } from "@apollo/client";

const uri = import.meta.env.VITE_GRAPHQL_URL || "/graphql";

export const client = new ApolloClient({
  uri,
  credentials: "include",
  cache: new InMemoryCache(),
});
