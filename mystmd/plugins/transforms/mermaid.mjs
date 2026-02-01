//
// const merDirective = {
//     name: 'mermaid-p',
//     doc: 'An example directive for showing a nice random image at a custom size.',
//     body: {
//         type: String,
//         required: true,
//     },
//     run(data) {
//          const graph = btoa(unescape(encodeURIComponent( data.body)))
//          const url = `https://mermaid.ink/img/${graph}?width=800`;
//          const img = { type: 'image', url };
//          return [img];
//         //return [];
//     },
// };
//
// const plugin = { name: 'Custom Mermaid', directives: [merDirective] };
//
// export default plugin;
/**
 * MyST Plugin to convert Mermaid diagrams to images
 * This plugin processes Mermaid nodes in a document and generates images using mermaid-cli.
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import crypto from 'crypto';

function _generateHash(content) {
  return crypto.createHash('md5').update(content).digest('hex').substring(0, 8);
}

const mermaidTransform = {
  name: 'mermaid-to-image',
  doc: 'Transform mermaid nodes to images',
  stage: 'document',
  plugin: (_, utils) => (node) => {
    
    const mermaidNodes = utils.selectAll('mermaid', node);
    console.log(`Found ${mermaidNodes.length} Mermaid nodes`);
    
    if (mermaidNodes.length === 0) return; 

    const tempDir = path.join(process.cwd(), '_build', 'temp');
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }

    mermaidNodes.forEach((mermaidNode, index) => {
      try {
        console.log(`Processing Mermaid diagram ${index + 1}`);
        const mermaidContent = mermaidNode.value;
        
        // Gera um hash único para o conteúdo
        const hash = _generateHash(mermaidContent);
        
        const mermaidFilePath = path.join(tempDir, `mermaid-${hash}.mmd`);
        const imagePath = path.join(tempDir, `mermaid-${hash}.png`);
        const  = path.relative(process.cwd(), imagePath);
        relativeImagePath
        // Salva o conteúdo em um arquivo temporário
        fs.writeFileSync(mermaidFilePath, mermaidContent);
        
        // Gera a imagem usando mermaid-cli
        const cmd = `mmdc -i "${mermaidFilePath}" -o "${imagePath}" -b transparent --scale 4`;
        console.log(`Executing command: ${cmd}`);
        execSync(cmd);
        
        if (fs.existsSync(imagePath)) {
          console.log(`Image generated successfully: ${imagePath} ${relativeImagePath}`);

          const imageNode = {
            type: 'image',
            url: `../../${relativeImagePath}`,
            alt: `Mermaid Diagram ${index + 1}`,
          };
          
          Object.keys(mermaidNode).forEach(key => {
            delete mermaidNode[key];
          });
          
          Object.assign(mermaidNode, imageNode);
        } else {
          throw new Error(`Image generation failed for diagram ${index + 1}`);
        }
      } catch (error) {
        console.error(`Error generating image for diagram ${index + 1}:`, error);
      }
    });
  }
};


const plugin = {
  name: 'Mermaid to Image',
  transforms: [mermaidTransform]
};

export default plugin;