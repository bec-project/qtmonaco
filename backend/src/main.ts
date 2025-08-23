import * as monaco from "monaco-editor";
import LspClient from "./lsp";
import { initVimMode, type CMAdapter } from "monaco-vim";

const container = document.getElementById("container");
if (!container) {
  throw new Error("Container element not found");
}

const editor = monaco.editor.create(container, {
  value: "",
  language: "python",
  automaticLayout: true,
  theme: "vs-dark",
});

(window as any).qtmonaco = {
  editor: editor,
  monaco: monaco,
  vimMode: null as CMAdapter | null,
  initialized: false,
};

let qtmonaco = (window as any).qtmonaco;

// Build qt bridge
let bridge: any = null;

let lspClient: LspClient | null = null;
let lspHeader: string | null = null;

let decorationsCollection: monaco.editor.IEditorDecorationsCollection | null = null;

// Define init function
function init() {
  // Add any initialization code here if needed
  console.log("Editor initialized");
  sendToPython("bridge_initialized", true);
  qtmonaco.initialized = true;
}

// Declare QWebChannel for TypeScript
declare global {
  interface Window {
    qt: {
      webChannelTransport: any;
    };
  }
  class QWebChannel {
    constructor(transport: any, callback: (channel: any) => void);
  }
}

window.onload = function () {
  console.log("Window loaded, initializing QWebChannel");
  new QWebChannel(window.qt.webChannelTransport, function (channel) {
    bridge = channel.objects.connector;

    // Check if bridge has the expected methods
    if (bridge) {
      bridge.javascript_data_sent.connect(updateFromPython);
      console.log("Successfully connected to javascript_data signal");
    } else {
      console.warn("Bridge javascript_data_sent.connect not available");
    }

    editor.onDidChangeModelContent((_event) => {
      const model = editor.getModel();
      if (model) {
        const value = model.getValue();
        sendToPython("_current_text", value);
      }
    });

    init();
  });
};

function sendToPython(name: string, value: any) {
  if (bridge) {
    bridge._receive(name, JSON.stringify(value));
  }
}

function updateFromPython(name: string, value: string) {
  const data = JSON.parse(value);
  console.log(`Received update from Python: ${name} =`, data);
  const model = editor.getModel();
  switch (name) {
    case "set_text":
      // If the model exists and the user specified a new language or uri
      // dispose the old model
      if (model && (data.language || data.uri)) {
        model.dispose();
        let language = data.language ?? undefined;
        let uri = data.uri ? monaco.Uri.parse(data.uri) : undefined;

        const new_model = monaco.editor.createModel(data.data, language, uri);
      editor.setModel(new_model);
      sendToPython("_current_uri", new_model.uri.toString());
      } else {
        // If no new language or uri is specified, just update the text
        editor.setValue(data.data);
      }
      break;

    case "read":
      // Readout the current value from the editor
      const currentValue = editor.getValue();
      sendToPython("_current_text", currentValue); // Send back the current value
      break;
    case "minimap":
      // Set the minimap visibility
      const isMinimapEnabled = data === true; // Assuming data is a boolean
      console.log(`Setting minimap enabled: ${isMinimapEnabled}`);
      editor.updateOptions({
        minimap: {
          enabled: isMinimapEnabled,
        },
      });
      break;
    case "set_cursor": {
      // Set the cursor position in the editor
      const position = data; // Assuming data is an object with line and column properties
      if (model) {
        const lineNumber = position.line || 1; // Default to line 1 if not provided
        const column = position.column || 1; // Default to column 1 if not provided
        const moveToPosition = position.moveToPosition || ""; // Optional moveToPosition flag
        const newPosition = new monaco.Position(lineNumber, column);
        const newSelection = new monaco.Selection(lineNumber, column, lineNumber, column);
        editor.setPosition(newPosition);
        editor.setSelection(newSelection);
        if (typeof moveToPosition === "string" && moveToPosition) {
          // If moveToPosition is provided, we move the cursor to that location
          if (moveToPosition === "center") {
            editor.revealPositionInCenter(newPosition);
          } else if (moveToPosition === "top") {
            editor.revealPositionNearTop(newPosition, monaco.editor.ScrollType.Smooth);
          } else {
            editor.revealPosition(newPosition); // Ensure the cursor is visible
          }
        }
        sendToPython("_current_cursor", { line: lineNumber, column: column }); // Send back the new cursor position
      }
      break;
    }
    case "highlight_lines":
      // Highlight a range of lines in the editor
      const highlight = data; // Expecting data with start and end line numbers
      const highlightRange = new monaco.Range(highlight.start, 1, highlight.end, 1);
      if (decorationsCollection) {
        decorationsCollection.clear(); // Clear previous decorations if any
      } else {
        decorationsCollection = editor.createDecorationsCollection(); // Create a new collection if it doesn't exist
      }
      const highlightDecoration = {
        range: highlightRange,
        options: {
          isWholeLine: true,
          linesDecorationsClassName: "highlighted-line",
        },
      };
      decorationsCollection.set([highlightDecoration]);
      break;
    case "remove_highlight":
      // Remove the highlight from the editor
      if (decorationsCollection) {
        decorationsCollection.clear(); // Clear all decorations
      }
      break;
    case "delete_line":
      // Delete a specific line in the editor
      if (!model) break;
      let lineToDelete: number | null = null;
      if (typeof data === "number") {
        lineToDelete = data; // If data is a number, use it directly
      } else if (data === "current") {
        const position = editor.getPosition();
        if (position) {
          lineToDelete = position.lineNumber; // Use the current line number
        }
      } else {
        console.warn("Invalid data for delete_line, expected a line number or 'current'");
        break;
      }
      if (lineToDelete !== null) {
        const lineRange = model.getLineContent(lineToDelete);
        const range = new monaco.Range(lineToDelete, 1, lineToDelete, lineRange.length + 1);
        const editOperation = { range: range, text: "" }; // Replace with empty string to delete
        model.pushEditOperations([], [editOperation], () => null); // Apply the edit operation
      }
      break;
    case "insert":
      // Insert text at the specified position
      if (!model) break;
      let position = null;
      if (data.line !== null) {
        position = new monaco.Position(data.line, data.column || 1);
      } else {
        position = editor.getPosition(); // Use current cursor position if no line is specified
      }

      if (position) {
        const insertText = data.text || ""; // Default to empty string if no text provided
        const editOperation = {
          range: new monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column),
          text: insertText,
        };
        model.pushEditOperations([], [editOperation], () => null); // Apply the edit operation
      }
      break;
    case "readonly":
      // Set the editor to read-only mode
      const isReadOnly = data === true;
      editor.updateOptions({ readOnly: isReadOnly });
      break;
    case "language": {
      const model = editor.getModel();
      if (model) {
        monaco.editor.setModelLanguage(model, data);
      }
      break;
    }
    case "theme":
      // Set the theme - Monaco will use a fallback if the theme doesn't exist
      try {
        monaco.editor.setTheme(data);
        console.log(`Applied theme: ${data}`);
        sendToPython("_theme", data); // Send back the theme name
      } catch (error) {
        console.warn(`Failed to apply theme "${data}":`, error);
        // Fallback to default theme
        monaco.editor.setTheme("vs-dark");
        sendToPython("_theme", "vs-dark");
      }
      break;
    case "lsp_url":
      // Destroy existing LSP client if it exists
      if (lspClient) {
        lspClient.destroy();
        lspClient = null;
      }
      // Update LSP client with new URL
      if (data && typeof data === "string") {
        const pylspUrl = data;
        console.log(`Setting up LSP client with URL: ${pylspUrl}`);
        lspClient = new LspClient(pylspUrl);
        lspClient.prependedData = lspHeader || ""; // Set the LSP header if available
      }
      break;
    case "set_lsp_header":
      // Set the LSP header for the client
      lspHeader = data; // Store the header for later use
      if (lspClient) {
        lspClient.prependedData = data;
      }
      break;
    case "get_lsp_header":
      // Get the current LSP header
      const headerData = lspClient ? lspClient.prependedData : "";
      sendToPython("_lsp_header", headerData);
      break;
    case "vim_mode":
      // Enable or disable Vim mode
      if (data === true) {
        if (!qtmonaco.vimMode) {
          var statusNode = document.getElementById("status");
          qtmonaco.vimMode = initVimMode(editor, statusNode);
          console.log("Vim mode enabled");
        }
      } else {
        if (qtmonaco.vimMode) {
          qtmonaco.vimMode.dispose(); // Dispose Vim mode if it exists
          qtmonaco.vimMode = null;
          console.log("Vim mode disabled");
        }
      }
      break;
  }
}
