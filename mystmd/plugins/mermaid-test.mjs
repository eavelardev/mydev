import fs from 'node:fs';
import path from 'node:path';

function findProjectRoot(filePath) {
  let dir = path.dirname(filePath);
  while (dir !== path.dirname(dir)) {
    const mystYml = path.join(dir, 'myst.yml');
    if (fs.existsSync(mystYml)) {
      return dir;
    }
    dir = path.dirname(dir);
  }
  return null;
}

function getMermaidTheme(filePath) {
  const root = findProjectRoot(filePath);
  if (!root) return 'default';
  const mystYml = path.join(root, 'myst.yml');
  try {
    const content = fs.readFileSync(mystYml, 'utf-8');
    // Simple check for mode: dark
    const lines = content.split('\n');
    for (const line of lines) {
      if (line.includes('mode:') && line.includes('dark')) {
        return 'dark';
      }
    }
    return 'default';
  } catch (e) {
    return 'default';
  }
}

const visit = (node) => {
  if (!node || typeof node !== 'object') return;

  if (node.type === 'mermaid') {
    const theme = getMermaidTheme(node.position?.start?.file || '');
    console.log(`Applying Mermaid theme: ${theme}`);
    const initDirective = `%%{init: {'theme': 'dark'}}%%\n`;
    if (!node.value.startsWith('%%{init:')) {
      node.value = initDirective + node.value;
    }
  }

  if (Array.isArray(node.children)) {
    node.children.forEach((child) => visit(child));
  }
};

export default {
  name: 'mermaid-theme-transform',
  transforms: [
    {
      name: 'mermaid-theme-transform',
      stage: 'document',
      plugin: (options, utils) => (tree, vfile) => {
        visit(tree);
        return tree;
      },
    },
  ],
};
