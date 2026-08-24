import { defineConfig, markdown } from "sourcey";

export default defineConfig({
  name: "meshy-content-generator",
  siteUrl: "https://jonbogaty.com",
  baseUrl: "/meshy-content-generator",
  repo: "https://github.com/jbcom/meshy-content-generator",
  editBranch: "main",
  prettyUrls: "slash",
  theme: {
    preset: "default",
    colors: {
      primary: "#0f766e",
      light: "#14b8a6",
      dark: "#115e59",
    },
    fonts: {
      sans: "Inter, ui-sans-serif, system-ui, sans-serif",
      mono: "JetBrains Mono, ui-monospace, monospace",
    },
  },
  logo: "./logo.svg",
  favicon: "./favicon.svg",
  navigation: {
    tabs: [
      {
        tab: "Guides",
        slug: "",
        source: markdown({
          groups: [
            { group: "Get started", pages: ["introduction", "quickstart"] },
            { group: "Reference", pages: ["pipeline-schema", "cli", "api-reference"] },
            { group: "Project", pages: ["architecture", "contributing", "security", "releases"] },
          ],
        }),
      },
    ],
  },
  navbar: {
    links: [{ type: "github", href: "https://github.com/jbcom/meshy-content-generator" }],
  },
  footer: {
    links: [{ type: "github", href: "https://github.com/jbcom/meshy-content-generator" }],
  },
});
