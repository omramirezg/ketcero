import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

// Sitio estático: cada página sale como carpeta/index.html, igual que el sitio que arma construir.py.
export default defineConfig({
  site: "https://ketcero.com",
  integrations: [mdx()],
  build: { format: "directory", inlineStylesheets: "never" },
  compressHTML: false,
  devToolbar: { enabled: false },
});
