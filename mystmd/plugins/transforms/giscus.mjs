// MyST plugin for Giscus comments integration
// Adds Giscus comments to each page using GitHub Discussions
// Allows per-page configuration via frontmatter

const DEFAULTS = {
  repo: "IVIA-AF/livre",
  repoId: "R_kgDOPKBYSA",
  category: "Commentaire",
  categoryId: "DIC_kwDOPKBYSM4CuxXP",
  mapping: "pathname", // Creates separate discussion per page/chapter
  strict: "0",
  reactionsEnabled: "1",
  emitMetadata: "0",
  inputPosition: "top",
  theme: "light",
  lang: "fr",
};

const addGiscusComments = {
  name: "add-giscus-comments",
  doc: "Add Giscus comments section to every document.",
  stage: "document",
  plugin: (_, utils) => (tree, file) => {
    // #region agent log - Simple console output for debugging
    console.log('[GISCUS PLUGIN] Plugin function called for file:', file?.path || 'unknown');
    // #endregion

    // Allow page-level opts via frontmatter: comments: {repo, repoId, category, etc., enabled}
    const fm = file?.data?.frontmatter ?? {};
    const cfg = Object.assign({}, DEFAULTS, fm.comments ?? {});
    
    // #region agent log
    console.log('[GISCUS PLUGIN] Config check - enabled:', cfg.enabled, 'repo:', cfg.repo);
    // #endregion
    
    if (cfg.enabled === false) {
      // #region agent log
      console.log('[GISCUS PLUGIN] Skipping - enabled is false');
      // #endregion
      return;
    }

    // Check if Giscus is already added
    const existing = utils.selectAll('html', tree);
    const hasGiscus = existing.some(node => 
      node.value && node.value.includes('giscus.app')
    );
    
    // #region agent log
    console.log('[GISCUS PLUGIN] Existing check - html blocks:', existing.length, 'hasGiscus:', hasGiscus);
    // #endregion
    
    if (hasGiscus) {
      // #region agent log
      console.log('[GISCUS PLUGIN] Skipping - Giscus already exists');
      // #endregion
      return;
    }

    // Create HTML block with Giscus container and script
    const giscusHTML = `
<div class="giscus-container" id="giscus-container" style="
  max-width: 100%; 
  margin: 3rem 0 2rem 0; 
  padding: 2rem; 
  background: #ffffff; 
  border-radius: 8px; 
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); 
  border: 1px solid #e1e5e9; 
  min-height: 200px;
  clear: both;
  overflow: hidden;
">
  <h3 style="
    margin: 0 0 1.5rem 0; 
    color: #333; 
    font-size: 1.3rem; 
    font-weight: 600;
    text-align: center;
    border-bottom: 2px solid #007cba;
    padding-bottom: 0.5rem;
  ">💬 Commentaires et Discussions</h3>
  
  <div id="giscus-comments"></div>
  
  <script>
    (function() {
      const script = document.createElement('script');
      script.src = 'https://giscus.app/client.js';
      script.setAttribute('data-repo', '${cfg.repo}');
      script.setAttribute('data-repo-id', '${cfg.repoId}');
      script.setAttribute('data-category', '${cfg.category}');
      script.setAttribute('data-category-id', '${cfg.categoryId}');
      script.setAttribute('data-mapping', '${cfg.mapping}');
      script.setAttribute('data-strict', '${cfg.strict}');
      script.setAttribute('data-reactions-enabled', '${cfg.reactionsEnabled}');
      script.setAttribute('data-emit-metadata', '${cfg.emitMetadata}');
      script.setAttribute('data-input-position', '${cfg.inputPosition}');
      script.setAttribute('data-theme', '${cfg.theme}');
      script.setAttribute('data-lang', '${cfg.lang}');
      script.crossOrigin = 'anonymous';
      script.async = true;
      
      const container = document.getElementById('giscus-comments');
      if (container) {
        container.appendChild(script);
      }
    })();
  </script>
</div>`;

    const htmlBlock = {
      type: "html",
      value: giscusHTML,
    };

    // Append to the end of the document
    if (!tree.children) tree.children = [];
    tree.children.push(htmlBlock);
    
    // #region agent log
    console.log('[GISCUS PLUGIN] Added HTML block - tree children:', tree.children.length, 'block type:', htmlBlock.type);
    // #endregion
  },
};

const plugin = {
  name: "myst-giscus",
  transforms: [addGiscusComments],
};

export default plugin;