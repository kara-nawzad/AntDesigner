Self-hosted frontend font assets.

- Fraunces variable, Inter, and JetBrains Mono were sourced from the pinned
  Fontsource npm packages (version 5.2.8) during the HTML rebuild.
- Only Latin subsets and the weights used by the UI are included.
- They are served locally so the initial page render does not depend on Google Fonts.
