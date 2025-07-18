declare module "monaco-vim" {
  export interface CMAdapter {
    /** Dispose the vim mode and clean up event listeners */
    dispose(): void;
    
    /** Get the current vim mode (normal, insert, visual, etc.) */
    mode: string;
    
    /** Set vim option */
    setOption(name: string, value: any): void;
    
    /** Get vim option */
    getOption(name: string): any;
    
    /** Execute a vim command */
    executeCommand(command: string): void;
    
    /** Get the status bar element */
    statusBar: HTMLElement | null;
    
    /** Access to the underlying CodeMirror vim instance */
    cm: any;
    
    /** Event handlers */
    on(event: string, callback: Function): void;
    off(event: string, callback: Function): void;
    
    /** Vim-specific methods */
    handleKey(key: string): boolean;
    findNext(): void;
    findPrev(): void;
    
    /** State management */
    state: {
      vim: any;
      keyMap: string;
      insertMode: boolean;
      visualMode: boolean;
    };
  }

  export function initVimMode(editor: any, statusBar: HTMLElement | null): CMAdapter;
}
