import * as monaco from "monaco-editor";
import { listen } from "vscode-ws-jsonrpc";
import type { MessageConnection } from "vscode-jsonrpc";
import { createCompletionProvider, createSignatureHelpProvider, createHoverProvider } from "./providers";

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
  public settings: object | null = null; // Store workspace settings

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
      this.onConnectionOpened();
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
            this.onConnectionOpened();
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

  private onConnectionOpened() {
    console.log("LSP connection opened");
    // If there are stored settings, update the workspace configuration
    if (this.settings) {
      this.updateWorkspaceConfiguration(this.settings).catch((error) => {
        console.error("Failed to update workspace configuration on connection open:", error);
      });
    }
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

    // Create providers using factory functions
    const completionProvider = createCompletionProvider(
      () => this.currentConnection,
      this.isConnectionValid.bind(this),
      this.prependModelData.bind(this),
      this.prependedData,
      this.forceReconnect.bind(this)
    );

    const signatureProvider = createSignatureHelpProvider(
      () => this.currentConnection,
      this.isConnectionValid.bind(this),
      this.prependModelData.bind(this),
      this.prependedData,
      this.forceReconnect.bind(this),
      this.onSignatureHelp
    );

    const hoverProvider = createHoverProvider(
      () => this.currentConnection,
      this.isConnectionValid.bind(this),
      this.prependModelData.bind(this),
      this.prependedData,
      this.forceReconnect.bind(this)
    );

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

  /**
   * Updates the workspace configuration settings for the LSP server.
   * @param settings Configuration object with workspace settings
   * @returns Promise that resolves when the configuration is updated
   */
  private async updateWorkspaceConfiguration(settings: Record<string, any>): Promise<void> {
    if (!this.isConnectionValid(this.currentConnection)) {
      console.warn("Cannot update workspace configuration: No valid LSP connection");
      throw new Error("No valid LSP connection available");
    }

    try {
      console.log("Updating workspace configuration:", settings);

      // Send workspace/didChangeConfiguration notification
      await this.currentConnection!.sendNotification("workspace/didChangeConfiguration", {
        settings: settings,
      });

      console.log("Workspace configuration updated successfully");
    } catch (error) {
      console.error("Failed to update workspace configuration:", error);
      throw error;
    }
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
