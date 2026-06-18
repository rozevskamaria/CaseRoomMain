import { ApolloClient, InMemoryCache } from "@apollo/client";

const uri = import.meta.env.VITE_GRAPHQL_URL || "http://localhost:8000/graphql";

export const client = new ApolloClient({
  uri,
  cache: new InMemoryCache(),
});
