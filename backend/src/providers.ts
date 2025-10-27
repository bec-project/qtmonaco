import * as monaco from "monaco-editor";
import type { MessageConnection } from "vscode-jsonrpc";
import { getPythonSnippets } from "./snippets";
import type { CompletionResult } from "./lsp";

/**
 * Helper to check if model position needs adjustment for prepended data
 */
export function adjustLineForPrependedData(position: monaco.Position, prependedData: string | null): number {
  let line = position.lineNumber - 1;

  if (prependedData) {
    const prependedLines = prependedData.split("\n").length - 1;
    line += prependedLines; // Adjust line number based on prepended data
  }

  return line;
}

/**
 * Helper to prepare document for LSP requests
 */
export function prepareDocument(
  connection: MessageConnection,
  model: monaco.editor.ITextModel,
  prependModelData: (model: monaco.editor.ITextModel) => string
) {
  const uri = model.uri.toString();

  connection.sendNotification("textDocument/didOpen", {
    textDocument: {
      uri,
      languageId: "python",
      version: 1,
      text: prependModelData(model),
    },
  });

  return uri;
}

/**
 * Create and register the completion provider
 */
export function createCompletionProvider(
  getCurrentConnection: () => MessageConnection | null,
  isConnectionValid: (connection: MessageConnection | null) => boolean,
  prependModelData: (model: monaco.editor.ITextModel) => string,
  prependedData: string | null,
  forceReconnect: () => void
): monaco.IDisposable {
  return monaco.languages.registerCompletionItemProvider("python", {
    triggerCharacters: ["."],
    provideCompletionItems: async (model: monaco.editor.ITextModel, position: monaco.Position) => {
      // Always use the current connection, not a captured reference
      const connection = getCurrentConnection();
      if (!isConnectionValid(connection)) {
        console.warn("No valid LSP connection available for completion");
        return { suggestions: [] };
      }

      // At this point, connection is guaranteed to be valid and non-null
      const validConnection = connection!;

      // Extract the current word being typed
      const wordAtPosition = model.getWordUntilPosition(position);
      const currentWord = wordAtPosition ? wordAtPosition.word : "";
      console.log("Current word for snippet filtering:", currentWord);

      // Adjust line for prepended data
      const line = adjustLineForPrependedData(position, prependedData);
      const character = position.column - 1;

      // Prepare document
      const uri = prepareDocument(validConnection, model, prependModelData);

      try {
        const result: CompletionResult = await validConnection.sendRequest("textDocument/completion", {
          textDocument: { uri },
          position: { line, character },
          context: { triggerKind: 1 }, // 1 for Invoked
        });

        const items = Array.isArray(result) ? result : result.items;

        let suggestions = items.map((item: any) => ({
          ...item,
        }));

        // Make the suggestions unique
        suggestions = Array.from(
          new Map(
            suggestions.map((item) => [`${item.label}|${item.insertText ?? ""}|${item.kind ?? ""}`, item])
          ).values()
        );

        // Get filtered snippets with properly formatted CompletionItems
        const snippets = getPythonSnippets(currentWord).map((snippet) => {
          // Update the dummy range with the actual position information
          if (snippet.range) {
            snippet.range = {
              startLineNumber: position.lineNumber,
              startColumn: wordAtPosition.startColumn,
              endLineNumber: position.lineNumber,
              endColumn: wordAtPosition.endColumn,
            };
          }
          return snippet;
        });

        return { suggestions: [...suggestions, ...snippets] };
      } catch (e) {
        console.error("LSP completion failed:", e);

        // Check if the error indicates a disposed connection
        if (e instanceof Error && (e.message.includes("disposed") || e.message.includes("closed"))) {
          console.warn("Connection was disposed during completion request, forcing reconnection");
          forceReconnect();
        }

        return { suggestions: [] };
      }
    },
  });
}

/**
 * Create and register the signature help provider
 */
export function createSignatureHelpProvider(
  getCurrentConnection: () => MessageConnection | null,
  isConnectionValid: (connection: MessageConnection | null) => boolean,
  prependModelData: (model: monaco.editor.ITextModel) => string,
  prependedData: string | null,
  forceReconnect: () => void,
  onSignatureHelp: ((data: monaco.languages.SignatureHelp) => void) | null
): monaco.IDisposable {
  return monaco.languages.registerSignatureHelpProvider("python", {
    signatureHelpTriggerCharacters: ["(", ",", "="],
    provideSignatureHelp: async (model, position, _token, context): Promise<monaco.languages.SignatureHelpResult> => {
      // Always use the current connection, not a captured reference
      const connection = getCurrentConnection();
      if (!isConnectionValid(connection)) {
        console.warn("No valid LSP connection available for signature help");
        return { value: { signatures: [], activeSignature: 0, activeParameter: 0 }, dispose: () => {} };
      }

      // At this point, connection is guaranteed to be valid and non-null
      const validConnection = connection!;

      // Adjust line for prepended data
      const line = adjustLineForPrependedData(position, prependedData);
      const character = position.column - 1;

      // Prepare document
      const uri = prepareDocument(validConnection, model, prependModelData);

      try {
        const result: any = await validConnection.sendRequest("textDocument/signatureHelp", {
          textDocument: { uri },
          position: { line, character },
          context: {
            triggerKind: context.triggerKind,
            triggerCharacter: context.triggerCharacter,
          },
        });

        if (!result || !result.signatures?.length) {
          return { value: { signatures: [], activeSignature: 0, activeParameter: 0 }, dispose: () => {} };
        }

        // Adapt LSP SignatureHelp to Monaco's SignatureHelp format with IMarkdownString support
        const signatureHelp: monaco.languages.SignatureHelp = {
          signatures: result.signatures.map((sig: any) => ({
            label: sig.label,
            documentation: sig.documentation
              ? typeof sig.documentation === "string"
                ? { value: sig.documentation }
                : sig.documentation
              : undefined,
            parameters:
              sig.parameters?.map((param: any) => ({
                label: typeof param.label === "string" ? param.label : param.label[0] + "-" + param.label[1],
                documentation: param.documentation
                  ? typeof param.documentation === "string"
                    ? { value: param.documentation }
                    : param.documentation
                  : undefined,
              })) || [],
          })),
          activeSignature: result.activeSignature ?? 0,
          activeParameter: result.activeParameter ?? 0,
        };

        // Call the signature help callback if it exists
        if (onSignatureHelp) {
          onSignatureHelp(signatureHelp);
        }

        return {
          value: signatureHelp,
          dispose: () => {},
        };
      } catch (e) {
        console.error("LSP signature help failed:", e);

        // Check if the error indicates a disposed connection
        if (e instanceof Error && (e.message.includes("disposed") || e.message.includes("closed"))) {
          console.warn("Connection was disposed during signature help request, forcing reconnection");
          forceReconnect();
        }

        return {
          value: { signatures: [], activeSignature: 0, activeParameter: 0 },
          dispose: () => {},
        };
      }
    },
  });
}

/**
 * Create and register the hover provider
 */
export function createHoverProvider(
  getCurrentConnection: () => MessageConnection | null,
  isConnectionValid: (connection: MessageConnection | null) => boolean,
  prependModelData: (model: monaco.editor.ITextModel) => string,
  prependedData: string | null,
  forceReconnect: () => void
): monaco.IDisposable {
  return monaco.languages.registerHoverProvider("python", {
    provideHover: async (model: monaco.editor.ITextModel, position: monaco.Position) => {
      // Always use the current connection, not a captured reference
      const connection = getCurrentConnection();
      if (!isConnectionValid(connection)) {
        console.warn("No valid LSP connection available for hover");
        return null;
      }

      // At this point, connection is guaranteed to be valid and non-null
      const validConnection = connection!;

      // Adjust line for prepended data
      const line = adjustLineForPrependedData(position, prependedData);
      const character = position.column - 1;

      // Prepare document
      const uri = prepareDocument(validConnection, model, prependModelData);

      try {
        const result: any = await validConnection.sendRequest("textDocument/hover", {
          textDocument: { uri },
          position: { line, character },
        });

        if (result?.contents) {
          return {
            contents: Array.isArray(result.contents)
              ? result.contents.map((content: any) => ({ value: content.value || content }))
              : [{ value: result.contents.value || result.contents }],
            range: result.range,
          };
        }
      } catch (e) {
        console.error("LSP hover failed:", e);

        // Check if the error indicates a disposed connection
        if (e instanceof Error && (e.message.includes("disposed") || e.message.includes("closed"))) {
          console.warn("Connection was disposed during hover request, forcing reconnection");
          forceReconnect();
        }
      }

      return null;
    },
  });
}
