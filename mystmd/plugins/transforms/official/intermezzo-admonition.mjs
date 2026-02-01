/* Custom intermezzo admonition, based on documentation (see https://next.jupyterbook.org/plugins/directives-and-roles#create-a-custom-admonition). 
*   css file (custom.css) included in style folder. 
*/

const intermezzoStyle = {
  border : `rgb(162, 0, 255)`, 
  header : `rgb(218,154,255)`,
  body : `rgb(255,255,255)`
}

let getText = (node) => {
  if(node.type === "text") return node.value;
  if(node.children) return node.children.map(getText).join("");
  return "";
}

const intermezzo = {
  name: "intermezzo",
  doc: "A custom admonition that uses a specific color.",
  arg: { type: String, doc: "The title of the admonition." },
  options: {
    collapsed: { type: Boolean, doc: "Whether to collapse the admonition." },
  },
  body: { type: String, doc: "The body of the directive." },
  run(data, vfile, ctx) {
    
    let title = data.arg.trim();
    let body = data.body.trim();

    const admonition = {
      "type": "admonition",
      "kind": "note",
      "class": "admonition-intermezzo",  //Add class (custom.css)
      "icon": false,
      "children": [
        
        {
          "type": "admonitionTitle",
          "class": "admonition-title-intermezzo",
          "children": ctx.parseMyst(`${title}`)["children"][0]["children"]
        },
        
        {
          "type": "paragraph",
          "class": "admonition-body-intermezzo", //add 'fake' class, for later use and for selecting in transform
          "children": ctx.parseMyst(body)["children"] 
        }
      ]
    }

    return [admonition];
  }
};

const intermezzoTransform = {
  name: "conditional-intermezzo",
  doc: "Replace custom intermezzo admonitions in PDF builds.",
  stage: "document",
  plugin: (opts, utils) => (tree) => {
    
    // Detect if we are building a PDF using typst, using latex the directive only is enough
    const isPDF = process.argv.some(arg => arg.includes("typst"));

    //Exit if not
    if(!isPDF) return;

    // As we defined the node ourselves, we can search for it
    const intermezzos = utils.selectAll('admonition[class~="admonition-intermezzo"]', tree);

    intermezzos.forEach((node) => {

      // Get title and body
      const titleNode = utils.select('admonitionTitle[class~="admonition-title-intermezzo"]', node);
      const bodyNode = utils.select('paragraph[class~="admonition-body-intermezzo"]', node); 

      const title = getText(titleNode);
      const body = getText(bodyNode);

      // Replace the *contents* of the node in place, somehow foreach does not work... some copy problem
      Object.assign(node, {
        type: 'raw',
        lang: 'typst',
        typst: `
          // template_admonition.typ

          #block(
            fill: ${intermezzoStyle.header},
            stroke: (left: 1pt + ${intermezzoStyle.border}),
            width: 100%,
            inset: (x: 0.8em, y: 0.4em),
            above: 0.5em,
            below: 0em,
            strong("${title}"),
          )

          #block(
            fill: ${intermezzoStyle.body},
            stroke: (left: 1pt + ${intermezzoStyle.border}),
            width: 100%,
            inset: (x: 0.8em, y: 0.6em),
            above: 0em,
            below: 0.5em,
            "${body}"
          )
        `
      });
    });    
    
  }
};

const plugin = {
  name: "intermezzo",
  directives: [intermezzo],
  transforms: [intermezzoTransform],
};

export default plugin;

