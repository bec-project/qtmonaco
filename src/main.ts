import * as monaco from "monaco-editor";
import LspClient from "./lsp";

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

// Build qt bridge
let bridge: any = null;

let lspClient: LspClient | null = null;

// Define init function
function init() {
  // Add any initialization code here if needed
  console.log("Editor initialized");
  sendToPython("bridge_initialized", true);
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
  switch (name) {
    case "set_text":
      const model = editor.getModel();
      if (model) {
        model.setValue(data);
      }
      break;
    case "read":
      // Readout the current value from the editor
      const currentValue = editor.getValue();
      sendToPython("_current_text", currentValue); // Send back the current value
      break;
    case "set_cursor": {
      // Set the cursor position in the editor
      const position = data; // Assuming data is an object with line and column properties
      const model = editor.getModel();
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
      }
      break;
  }
}
