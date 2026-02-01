// style for experiment directive in pdf format
const experimentStyle = {
  border : `rgb(255, 0, 0)`,
  header : `rgb(251,183,183)`,
  body : `rgb(255,255,255)`
}

//Helper function to get text from a node
let getText = (node) => {
  if(node.type === "text") return node.value;
  if(node.children) return node.children.map(getText).join("");
  return "";
}

const experiment = {
  name: "experiment",
  doc: "An experiment admonition that uses a specific color.",
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
      "class": "admonition-experiment",  //Add class (custom.css)
      "icon": false,
      "children": [
        
        {
          "type": "admonitionTitle",
          "class": "admonition-title-experiment",
          "children": ctx.parseMyst(`${title}`)["children"][0]["children"]
        },
        
        {
          "type": "paragraph",
          "class": "admonition-body-experiment", //add 'fake' class, for later use and for selecting in transform
          "children": ctx.parseMyst(body)["children"] 
        }
      ]
    }

    return [admonition];
  }
};

const experimentTransform = {
  name: "conditional-experiment",
  doc: "Replace custom experiment admonitions in PDF builds.",
  stage: "document",
  plugin: (opts, utils) => (tree) => {
    
    // Detect if we are building a PDF using typst, using latex the directive only is enough
    const isPDF = process.argv.some(arg => arg.includes("typst"));

    //Exit if not
    if(!isPDF) return;

    // As we defined the node ourselves, we can search for it
    const experiments = utils.selectAll('admonition[class~="admonition-experiment"]', tree);

    experiments.forEach((node) => {

      // Get title and body
      const titleNode = utils.select('admonitionTitle[class~="admonition-title-experiment"]', node);
      const bodyNode = utils.select('paragraph[class~="admonition-body-experiment"]', node); 

      const title = getText(titleNode);
      const body = getText(bodyNode);

      // Replace the *contents* of the node in place, somehow foreach does not work... some copy problem
      Object.assign(node, {
        type: 'raw',
        lang: 'typst',
        typst: `
          // template_admonition.typ

          #block(
            fill: ${experimentStyle.header},
            stroke: (left: 1pt + ${experimentStyle.border}),
            width: 100%,
            inset: (x: 0.8em, y: 0.4em),
            above: 0.5em,
            below: 0em,
            strong("${title}"),
          )

          #block(
            fill: ${experimentStyle.body},
            stroke: (left: 1pt + ${experimentStyle.border}),
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
  name: "experiment",
  directives: [experiment],
  transforms: [experimentTransform],
};

export default plugin;

