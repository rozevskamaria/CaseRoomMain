import type { CodegenConfig } from "@graphql-codegen/cli";

const schema = process.env.VITE_GRAPHQL_URL || "http://localhost:8000/graphql";

const config: CodegenConfig = {
  overwrite: true,
  schema,
  documents: "src/**/*.{ts,tsx}",
  generates: {
    "./src/gql/": {
      preset: "client",
      presetConfig: {
        fragmentMasking: false,
      },
    },
  },
};

export default config;
