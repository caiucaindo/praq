export type Provider = 'groq' | 'gemini'

export interface AppState {
  provider: Provider
  models: string[]
  selectedModel: string
  hasGeminiKey: boolean
  hasGroqKey: boolean
  geminiKeySuffix: string
  groqKeySuffix: string
  busy: boolean
  status: string
  revision: number
  history: string[]
  historyIndex: number
}

export interface ApiEnvelope {
  ok: boolean
  state?: AppState
  message?: string
}

export type PraqEventDetail =
  | { type: 'state'; state: AppState; message?: string; jobId?: string }
  | { type: 'result'; state: AppState; result: string; jobId: string; provider: Provider; model: string }
  | { type: 'error'; state: AppState; message: string; jobId?: string }

interface PraqApi {
  initialize(): Promise<ApiEnvelope>
  read_clipboard(): Promise<ApiEnvelope & { value?: string }>
  set_provider(provider: Provider): Promise<ApiEnvelope>
  set_model(model: string): Promise<ApiEnvelope>
  analyze_selected_text(): Promise<ApiEnvelope>
  capture_single(): Promise<ApiEnvelope>
  capture_scroll(): Promise<ApiEnvelope>
  save_keys(geminiKey: string, groqKey: string): Promise<ApiEnvelope>
  clear_keys(): Promise<ApiEnvelope>
  clear_key(provider: Provider): Promise<ApiEnvelope>
  history_prev(): Promise<ApiEnvelope>
  history_next(): Promise<ApiEnvelope>
  history_delete(): Promise<ApiEnvelope>
  open_external(url: string): Promise<ApiEnvelope>
  window_minimize(): Promise<ApiEnvelope>
  window_toggle_maximize(): Promise<ApiEnvelope>
  window_close(): Promise<ApiEnvelope>
  window_start_drag(): Promise<ApiEnvelope>
}

declare global {
  interface Window {
    pywebview?: {
      api: PraqApi
    }
  }

  interface WindowEventMap {
    'praq:event': CustomEvent<PraqEventDetail>
  }
}

const getApi = (): PraqApi => {
  const api = window.pywebview?.api
  if (!api) {
    throw new Error('A integração com o aplicativo ainda não está disponível.')
  }
  return api
}

export const bridge = {
  initialize: () => getApi().initialize(),
  readClipboard: () => getApi().read_clipboard(),
  setProvider: (provider: Provider) => getApi().set_provider(provider),
  setModel: (model: string) => getApi().set_model(model),
  analyzeSelectedText: () => getApi().analyze_selected_text(),
  captureSingle: () => getApi().capture_single(),
  captureScroll: () => getApi().capture_scroll(),
  saveKeys: (geminiKey: string, groqKey: string) =>
    getApi().save_keys(geminiKey, groqKey),
  clearKeys: () => getApi().clear_keys(),
  clearKey: (provider: Provider) => getApi().clear_key(provider),
  historyPrev: () => getApi().history_prev(),
  historyNext: () => getApi().history_next(),
  historyDelete: () => getApi().history_delete(),
  openExternal: (url: string) => getApi().open_external(url),
  minimizeWindow: () => getApi().window_minimize(),
  toggleMaximizeWindow: () => getApi().window_toggle_maximize(),
  closeWindow: () => getApi().window_close(),
  startWindowDrag: () => getApi().window_start_drag(),
}

export const onPraqEvent = (
  listener: (detail: PraqEventDetail) => void,
): (() => void) => {
  const handler = (event: CustomEvent<PraqEventDetail>) => listener(event.detail)
  window.addEventListener('praq:event', handler)
  return () => window.removeEventListener('praq:event', handler)
}
