// see (https://next.jupyterbook.org/plugins/directives-and-roles#create-a-transform)
// using (https://stackoverflow.com/questions/18681788/how-to-get-a-youtube-thumbnail-from-a-youtube-iframe)


const iframeTransform = {
  name: "iframe-to-thumbnail-pdf",
  doc: "Replace iframes in PDF builds with youtube thumbnail.",
  stage: "document",
  plugin: (opts, utils) => async (tree, vfile) => {
    
    // Detect if we are building a PDF by checking for pdf or typst in the command line arguments
    const isPDF = process.argv.some(arg => arg.includes("pdf") || arg.includes("typst"));

    // Get all nodes for each page
    const rootChildren = tree.children[0]?.children || [];

    if (isPDF) {

        for (const [index, node] of rootChildren.entries()) {
            if (node.type === "container" && node.children[0]?.type === "iframe") {

                const url = node.children[0]?.src || "No link found";

                let youtube_video_id = url.match(/youtube\.com.*(\?v=|\/embed\/)(.{11})/).pop();
                let thumbnail = `https://img.youtube.com/vi/${youtube_video_id}/0.jpg`;
                
                // Make a figure out of it
                node.type = "container";
                node.kind = "figure";
                node.children = [
                    {
                        type: "image",
                        url: thumbnail,
                        alt: "Thumbnail",
                        title: " - ",
                        width: "400px",
                        align: "center"
                    },
                    {
                        type: "caption",
                        children: [
                            {
                                type: "paragraph",
                                children: [
                                    { type: "text", value: "Click " },
                                    { type: "link", url: url, children: [{ type: "text", value: "here" }] },
                                    { type: "text", value: " to go to the video." }
                                ]
                            }
                        ]
                    }
                ];
            }
        }
    }
  },
};

const plugin = {
  name: "Iframe PDF Plugin",
  transforms: [iframeTransform],
};

export default plugin;