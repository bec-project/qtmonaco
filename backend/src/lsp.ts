import * as monaco from "monaco-editor";
import { listen } from "vscode-ws-jsonrpc";
import type { MessageConnection } from "vscode-jsonrpc";

export type LspCompletionItem = {
  label: string;
  insertText?: string;
  documentation?: string | { value: string };
};

export type CompletionResult = { items: LspCompletionItem[] } | LspCompletionItem[];

class LspClient {
  private currentConnection: MessageConnection | null = null;
  private reconnectAttempts = 0;
  private readonly baseReconnectDelay = 1000; // Start with 1 second delay
  private readonly maxReconnectDelay = 10000; // Cap at 10 seconds
  private providersRegistered = false;
  private pylspUrl: string = "localhost:1234"; // Default host and port
  private providerDisposables: monaco.IDisposable[] = [];
  private reconnectTimeoutId: number | null = null;
  private isDestroyed = false;
  private healthCheckInterval: number | null = null;
  private webSocket: WebSocket | null = null;
  public prependedData: string | null = null; // Data to prepend to the model content
  public onSignatureHelp: ((data: monaco.languages.SignatureHelp) => void) | null = null; // Callback for signature help

  constructor(pylspUrl: string = "localhost:1234") {
    this.pylspUrl = pylspUrl;
    this.connect();
  }

  private connect() {
    // Don't reconnect if the client has been destroyed
    if (this.isDestroyed) {
      console.log("LSP client has been destroyed, skipping connection attempt");
      return;
    }

    this.webSocket = new WebSocket("ws://" + this.pylspUrl);
    const webSocket = this.webSocket;
    webSocket.onopen = () => {
      console.log("WebSocket connected");
      this.reconnectAttempts = 0; // Reset on successful connection
    };

    webSocket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    webSocket.onclose = (event) => {
      console.log("WebSocket disconnected:", event.code, event.reason);
      this.currentConnection = null;
      this.stopHealthCheck(); // Stop health check when connection is lost

      // Don't reconnect if the client has been destroyed
      if (this.isDestroyed) {
        console.log("LSP client has been destroyed, skipping reconnection");
        return;
      }

      // Cancel any existing reconnect attempt
      if (this.reconnectTimeoutId !== null) {
        clearTimeout(this.reconnectTimeoutId);
        this.reconnectTimeoutId = null;
      }

      // Always attempt to reconnect with exponential backoff
      const delay = Math.min(
        this.baseReconnectDelay * Math.min(Math.pow(1.5, this.reconnectAttempts), 10),
        this.maxReconnectDelay
      );
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

      this.reconnectTimeoutId = window.setTimeout(() => {
        this.reconnectTimeoutId = null;
        this.connect();
      }, delay);
    };

    listen({
      webSocket,
      onConnection: (connection: MessageConnection) => {
        this.currentConnection = connection;
        connection.listen();

        const initializeRequest = {
          processId: null,
          rootUri: null,
          capabilities: {},
        };

        connection
          .sendRequest("initialize", initializeRequest)
          .then(() => {
            connection.sendNotification("initialized", {});
            console.log("LSP connection initialized successfully");
            // Start health check for this connection
            this.startHealthCheck();
          })
          .catch((error) => {
            console.error("Failed to initialize LSP:", error);
            // Close the connection to trigger a reconnect
            if (this.currentConnection === connection) {
              this.currentConnection = null;
              connection.dispose();
              webSocket.close();
            }
          });

        // Register Monaco providers, disposing old ones first if needed
        this.registerMonacoProviders();
      },
    });
  }

  private prependModelData(model: monaco.editor.ITextModel) {
    return this.prependedData ? this.prependedData + model.getValue() : model.getValue();
  }

  private registerMonacoProviders() {
    // Dispose existing providers first
    if (this.providersRegistered) {
      console.log("Disposing existing Monaco providers before re-registering");
      this.providerDisposables.forEach((disposable) => disposable.dispose());
      this.providerDisposables = [];
      this.providersRegistered = false;
    }

    // Monaco Completion Provider
    const completionProvider = monaco.languages.registerCompletionItemProvider("python", {
      triggerCharacters: ["."],
      provideCompletionItems: async (model: monaco.editor.ITextModel, position: monaco.Position) => {
        // Always use the current connection, not a captured reference
        const connection = this.currentConnection;
        if (!this.isConnectionValid(connection)) {
          console.warn("No valid LSP connection available for completion");
          return { suggestions: [] };
        }

        // At this point, connection is guaranteed to be valid and non-null
        const validConnection = connection!;

        const uri = model.uri.toString();
        let line = position.lineNumber - 1;
        const character = position.column - 1;

        // add the length of the prepended data to the line
        if (this.prependedData) {
          const prependedLines = this.prependedData.split("\n").length - 1;
          line += prependedLines; // Adjust line number based on prepended data
        }

        validConnection.sendNotification("textDocument/didOpen", {
          textDocument: {
            uri,
            languageId: "python",
            version: 1,
            text: this.prependModelData(model),
          },
        });

        try {
          const result: CompletionResult = await validConnection.sendRequest("textDocument/completion", {
            textDocument: { uri },
            position: { line, character },
            context: { triggerKind: 1 }, // 1 for Invoked
          });

          const items = Array.isArray(result) ? result : result.items;

          const suggestions = items.map((item: any) => ({
            ...item,
          }));
          return { suggestions };
        } catch (e) {
          console.error("LSP completion failed:", e);

          // Check if the error indicates a disposed connection
          if (e instanceof Error && (e.message.includes("disposed") || e.message.includes("closed"))) {
            console.warn("Connection was disposed during completion request, forcing reconnection");
            this.currentConnection = null;
            this.forceReconnect();
          }

          return { suggestions: [] };
        }
      },
    });

    // Monaco Signature Help Provider
    const signatureProvider = monaco.languages.registerSignatureHelpProvider("python", {
      signatureHelpTriggerCharacters: ["(", ",", "="],
      provideSignatureHelp: async (model, position, _token, context): Promise<monaco.languages.SignatureHelpResult> => {
        // Always use the current connection, not a captured reference
        const connection = this.currentConnection;
        if (!this.isConnectionValid(connection)) {
          console.warn("No valid LSP connection available for signature help");
          return { value: { signatures: [], activeSignature: 0, activeParameter: 0 }, dispose: () => {} };
        }

        // At this point, connection is guaranteed to be valid and non-null
        const validConnection = connection!;

        const uri = model.uri.toString();
        let line = position.lineNumber - 1;
        const character = position.column - 1;

        // add the length of the prepended data to the line
        if (this.prependedData) {
          const prependedLines = this.prependedData.split("\n").length - 1;
          line += prependedLines; // Adjust line number based on prepended data
        }

        validConnection.sendNotification("textDocument/didOpen", {
          textDocument: {
            uri,
            languageId: "python",
            version: 1,
            text: this.prependModelData(model),
          },
        });

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
          if (this.onSignatureHelp) {
            this.onSignatureHelp(signatureHelp);
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
            this.currentConnection = null;
            this.forceReconnect();
          }

          return {
            value: { signatures: [], activeSignature: 0, activeParameter: 0 },
            dispose: () => {},
          };
        }
      },
    });

    // Monaco Hover Provider
    const hoverProvider = monaco.languages.registerHoverProvider("python", {
      provideHover: async (model: monaco.editor.ITextModel, position: monaco.Position) => {
        // Always use the current connection, not a captured reference
        const connection = this.currentConnection;
        if (!this.isConnectionValid(connection)) {
          console.warn("No valid LSP connection available for hover");
          return null;
        }

        // At this point, connection is guaranteed to be valid and non-null
        const validConnection = connection!;

        const uri = model.uri.toString();
        let line = position.lineNumber - 1;
        const character = position.column - 1;

        // add the length of the prepended data to the line
        if (this.prependedData) {
          const prependedLines = this.prependedData.split("\n").length - 1;
          line += prependedLines; // Adjust line number based on prepended data
        }

        validConnection.sendNotification("textDocument/didOpen", {
          textDocument: {
            uri,
            languageId: "python",
            version: 1,
            text: this.prependModelData(model),
          },
        });

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
            this.currentConnection = null;
            this.forceReconnect();
          }
        }

        return null;
      },
    });

    // Store disposables for cleanup
    this.providerDisposables.push(completionProvider, signatureProvider, hoverProvider);
    this.providersRegistered = true;
    console.log("Monaco language providers registered successfully");
  }

  private isConnectionValid(connection: MessageConnection | null): boolean {
    if (!connection) return false;

    try {
      // First check if connection has obvious disposal indicators
      if ((connection as any)._disposed || (connection as any).isDisposed?.()) {
        console.warn("Detected disposed connection via disposal flags");
        if (this.currentConnection === connection) {
          this.currentConnection = null;
          this.forceReconnect();
        }
        return false;
      }

      // Check if connection has a state property that indicates it's closed
      const state = (connection as any).state || (connection as any)._state;
      if (state === "closed" || state === "disposed" || state === 3) {
        // 3 = closed state
        console.warn("Detected closed connection via state check");
        if (this.currentConnection === connection) {
          this.currentConnection = null;
          this.forceReconnect();
        }
        return false;
      }

      return true;
    } catch (e) {
      console.warn("Error checking connection validity, treating as invalid:", e);
      if (this.currentConnection === connection) {
        this.currentConnection = null;
        this.forceReconnect();
      }
      return false;
    }
  }

  private forceReconnect() {
    if (this.isDestroyed) return;

    console.log("Forcing reconnection due to disposed connection");

    // Cancel any existing reconnect attempt
    if (this.reconnectTimeoutId !== null) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    // Start reconnecting immediately
    this.reconnectTimeoutId = window.setTimeout(() => {
      this.reconnectTimeoutId = null;
      this.connect();
    }, 100); // Very short delay to avoid blocking
  }

  private startHealthCheck() {
    // Clear any existing health check
    this.stopHealthCheck();

    // Check connection health every 5 seconds
    this.healthCheckInterval = window.setInterval(async () => {
      if (this.isDestroyed) {
        this.stopHealthCheck();
        return;
      }

      console.log("Status of the current connection: ", this.isConnected() ? "Connected" : "Disconnected");

      // First do the basic validity check
      if (this.currentConnection && !this.isConnectionValid(this.currentConnection)) {
        console.log("Health check detected invalid connection via basic checks");
        return; // forceReconnect() is already called by isConnectionValid()
      }
      if (this.webSocket?.readyState !== WebSocket.OPEN) {
        console.log("Health check detected invalid connection via WebSocket state");
        this.forceReconnect();
        return; // forceReconnect() will handle the reconnection
      }
    }, 5000);
  }

  private stopHealthCheck() {
    if (this.healthCheckInterval !== null) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
  }

  public isConnected(): boolean {
    return this.isConnectionValid(this.currentConnection);
  }

  public getConnection(): MessageConnection | null {
    return this.currentConnection;
  }

  public setLspUrl(newUrl: string) {
    if (this.isDestroyed) {
      console.warn("Cannot change URL: LSP client has been destroyed");
      return;
    }

    console.log(`Changing LSP URL from ${this.pylspUrl} to ${newUrl}`);
    this.pylspUrl = newUrl;

    // Cancel any pending reconnect attempt
    if (this.reconnectTimeoutId !== null) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    // Close current connection to trigger reconnect with new URL
    if (this.currentConnection) {
      this.currentConnection.dispose();
      this.currentConnection = null;
    }

    // Reset reconnect attempts for new URL
    this.reconnectAttempts = 0;

    // Start connecting to the new URL
    this.connect();
  }

  destroy() {
    // Mark as destroyed to prevent further connections
    this.isDestroyed = true;

    // Stop health check
    this.stopHealthCheck();

    // Cancel any pending reconnect attempts
    if (this.reconnectTimeoutId !== null) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    // Dispose of Monaco providers first
    this.providerDisposables.forEach((disposable) => disposable.dispose());
    this.providerDisposables = [];
    this.providersRegistered = false;

    // Then dispose of the LSP connection
    if (this.currentConnection) {
      this.currentConnection.dispose();
      this.currentConnection = null;
    }

    console.log("LSP client destroyed");
  }
}

export default LspClient;
