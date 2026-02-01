import { visit, SKIP, EXIT } from "unist-util-visit";

/**
 * Locate `redacted` nodes, and redact their text children (recursively)
 *
 * @param node - tree to transform
 */
function redactTransform(node) {
  const test = (child, index, parent) => {
    return (
      child.class &&
      child.class.split(/\s/).some((class_) => class_ === "redacted")
    );
  };
  visit(node, test, (child, index, parent) => {
    // Wrap any child text nodes
    visit(child, "text", (textChild, textIndex, textParent) => {
      (textParent ?? parent).children[textParent ? textIndex : index] = {
        type: "delete",
        children: [textChild],
      };
      return SKIP;
    });
    return SKIP;
  });
}

const plugin = {
  name: "Redact text",
  transforms: [
    {
      name: "transform-typography",
      doc: "An example transform that rewrites text with a 'redacted' class to become children of delete",
      stage: "document",
      plugin: (_, utils) => (node) => {
        redactTransform(node);
      },
    },
  ],
};

export default plugin;
