import * as monaco from "monaco-editor";

// Collection of Python code snippets
export const pythonSnippets = [
  {
    label: "for loop",
    kind: monaco.languages.CompletionItemKind.Snippet,
    insertText: ["for ${1:var} in ${2:iterable}:", "\t${0:pass}"].join("\n"),
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    documentation: "Python for loop snippet",
  },
];

/**
 * Get Python snippets that match the given word
 * @param word The current word being typed by the user
 * @returns Filtered list of snippets that match the word
 */
export function getPythonSnippets(word: string = ""): monaco.languages.CompletionItem[] {
  const lowerWord = word.toLowerCase();

  // Filter snippets that match the current word
  const filteredSnippets = !word
    ? pythonSnippets
    : pythonSnippets.filter((snippet) => {
        return snippet.label.toLowerCase().startsWith(lowerWord) || snippet.label.toLowerCase().includes(lowerWord);
      });

  // Convert our snippet format to proper Monaco CompletionItem format
  return filteredSnippets.map((snippet) => ({
    label: snippet.label,
    kind: snippet.kind,
    insertText: snippet.insertText,
    insertTextRules: snippet.insertTextRules,
    documentation:
      typeof snippet.documentation === "string"
        ? { value: snippet.documentation, isTrusted: false }
        : snippet.documentation,
    // These properties are required to make it a valid CompletionItem
    sortText: snippet.label,
    filterText: snippet.label,
    // Adding a dummy range to satisfy Monaco's requirements
    range: {
      startLineNumber: 0,
      startColumn: 0,
      endLineNumber: 0,
      endColumn: 0,
    },
  }));
}
