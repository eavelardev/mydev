const getMermaidValue = (mermaidValue) => {
    const initRegex = /^%%\{init:(.*?)\}%%/s;
    const match = mermaidValue.match(initRegex);
    if (match) {
        const initObject = getInitObj(match[0]);
        return {
            init: initObject,
            content: mermaidValue.slice(match[0].length)
        };
    }
    return {
        init: {},
        content: mermaidValue
    };
}

const getInitObj = (initDirective) => {
    if (!initDirective) return null;
    const objRegex = /%%\{init:\s*({.*})\s*\}%%/s;
    const match = initDirective.match(objRegex);
    if (match) {
        try {
            return JSON.parse(match[1].replace(/'/g, '"'));
        } catch (e) {
            console.error('Failed to parse init directive:', e);
            return {};
        }
    }
    return {};
}

const createMermaidValue = (initObj, content) => {
    const initString = `%%{init:${JSON.stringify(initObj).replace(/"/g, "'")}}%%`;
    return initString + content;
}

const mermaidThemeTransform = {
    name: 'mermaid-theme-transform',
    doc: 'Apply custom theme to Mermaid diagrams',
    stage: 'document',
    plugin: (_, utils) => (node) => {
        const darkTheme = 'dark';
        const lightTheme = 'neutral';

        utils.selectAll('mermaid', node).forEach((mermaidNode) => {
            const { init, content } = getMermaidValue(mermaidNode.value);

            const darkNodeValue = createMermaidValue(init.theme ? init : { ...init, theme: darkTheme }, content);
            const lightNodeValue = createMermaidValue(init.theme ? init : { ...init, theme: lightTheme }, content);

            const divNode = {
                type: 'div',
                children: [
                    {
                        type: 'mermaid',
                        value: darkNodeValue,
                        class: 'hidden dark:block'
                    },
                    {
                        type: 'mermaid',
                        value: lightNodeValue,
                        class: 'dark:hidden'
                    }
                ]
            }

            Object.keys(mermaidNode).forEach(key => {
                delete mermaidNode[key];
            });

            Object.assign(mermaidNode, divNode);
        });
    }
}

const plugin = {
    name: 'Mermaid Theme Plugin',
    transforms: [mermaidThemeTransform],
};

export default plugin;