import {
  AlertCircle,
  Bot,
  Check,
  ClipboardPaste,
  ChevronLeft,
  ChevronRight,
  Clipboard,
  Copy,
  ExternalLink,
  Image,
  KeyRound,
  LoaderCircle,
  Maximize2,
  Minus,
  ScanLine,
  Settings,
  Trash2,
  X,
} from 'lucide-react'
import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import type { MouseEvent } from 'react'
import {
  ApiEnvelope,
  AppState,
  bridge,
  onPraqEvent,
  Provider,
} from './bridge'
import { ConfirmDialog } from './components/ConfirmDialog'
import { SelectField } from './components/SelectField'

const INITIAL_STATE: AppState = {
  provider: 'groq',
  models: [],
  selectedModel: '',
  hasGeminiKey: false,
  hasGroqKey: false,
  geminiKeySuffix: '',
  groqKeySuffix: '',
  busy: false,
  status: 'Conectando ao PRAQ…',
  revision: 0,
  history: [],
  historyIndex: -1,
}

type Screen = 'main' | 'settings'
type Notice = { type: 'error' | 'success'; text: string } | null

function App() {
  const [screen, setScreen] = useState<Screen>('main')
  const [state, setState] = useState<AppState>(INITIAL_STATE)
  const [notice, setNotice] = useState<Notice>(null)
  const [copied, setCopied] = useState(false)
  const [initializing, setInitializing] = useState(true)

  const applyState = useCallback((nextState: AppState) => {
    setState((currentState) => (
      nextState.revision >= currentState.revision ? nextState : currentState
    ))
  }, [])

  const consumeEnvelope = useCallback((envelope: ApiEnvelope) => {
    if (envelope.state) applyState(envelope.state)
    if (!envelope.ok) {
      setNotice({
        type: 'error',
        text: envelope.message || 'Não foi possível concluir a ação.',
      })
    }
    return envelope.ok
  }, [applyState])

  const run = useCallback(
    async (action: () => Promise<ApiEnvelope>) => {
      setNotice(null)
      try {
        return consumeEnvelope(await action())
      } catch (error) {
        setNotice({
          type: 'error',
          text: error instanceof Error ? error.message : 'Erro inesperado na integração.',
        })
        return false
      }
    },
    [consumeEnvelope],
  )

  useEffect(() => {
    const unsubscribe = onPraqEvent((detail) => {
      applyState(detail.state)
      if (detail.type === 'result') {
        setNotice(null)
      } else if (detail.type === 'error') {
        setNotice({ type: 'error', text: detail.message || 'Ocorreu um erro.' })
      }
    })

    const initialize = async () => {
      // pywebview pode injetar a API após o carregamento inicial da página.
      if (!window.pywebview?.api) {
        await new Promise<void>((resolve) => {
          const ready = () => resolve()
          window.addEventListener('pywebviewready', ready, { once: true })
          window.setTimeout(resolve, 1500)
        })
      }
      await run(bridge.initialize)
      setInitializing(false)
    }

    void initialize()
    return unsubscribe
  }, [applyState, run])

  const currentHistory = useMemo(() => {
    if (state.historyIndex < 0 || state.historyIndex >= state.history.length) return ''
    return state.history[state.historyIndex]
  }, [state.history, state.historyIndex])

  const answer = currentHistory
  const hasActiveKey =
    state.provider === 'groq' ? state.hasGroqKey : state.hasGeminiKey

  const copyAnswer = async () => {
    if (!answer) return
    try {
      await navigator.clipboard.writeText(answer)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setNotice({ type: 'error', text: 'Não foi possível copiar a resposta.' })
    }
  }

  return (
    <div className="app-shell">
      <Header busy={state.busy} />

      {notice && (
        <div className={`notice notice--${notice.type}`} role="alert">
          {notice.type === 'error' ? <AlertCircle size={16} /> : <Check size={16} />}
          <span>{notice.text}</span>
          <button className="icon-button notice__close" onClick={() => setNotice(null)} aria-label="Fechar aviso">
            <X size={15} />
          </button>
        </div>
      )}

      {screen === 'main' ? (
        <MainScreen
          state={state}
          answer={answer}
          hasActiveKey={hasActiveKey}
          copied={copied}
          initializing={initializing}
          run={run}
          copyAnswer={copyAnswer}
          openSettings={() => setScreen('settings')}
        />
      ) : (
        <SettingsScreen
          state={state}
          run={run}
          goBack={() => setScreen('main')}
          onSaved={() => setNotice({ type: 'success', text: 'Chaves salvas com segurança.' })}
          onCleared={(message) => setNotice({ type: 'success', text: message || 'Chaves removidas.' })}
        />
      )}

      <div className="sr-only" aria-live="polite">
        {state.busy ? state.status || 'Processando' : copied ? 'Resposta copiada' : notice?.text}
      </div>
    </div>
  )
}

interface HeaderProps {
  busy: boolean
}

function Header({ busy }: HeaderProps) {
  const startDrag = (event: MouseEvent<HTMLElement>) => {
    if (event.button !== 0 || (event.target as HTMLElement).closest('button')) return
    void bridge.startWindowDrag().catch(() => undefined)
  }

  const toggleFromDoubleClick = (event: MouseEvent<HTMLElement>) => {
    if (!(event.target as HTMLElement).closest('button')) {
      void bridge.toggleMaximizeWindow().catch(() => undefined)
    }
  }

  const snapAtTop = (event: MouseEvent<HTMLElement>) => {
    if (event.button === 0 && event.screenY <= 1 && !(event.target as HTMLElement).closest('button')) {
      void bridge.toggleMaximizeWindow().catch(() => undefined)
    }
  }

  return (
    <header className="app-header" onMouseDown={startDrag} onDoubleClick={toggleFromDoubleClick} onMouseUp={snapAtTop}>
      <div className="header-content">
      <div className="brand-group">
        <img className="brand-logo" src="./logo-sem-fundo.png" alt="" />
        <div className="brand-copy">
          <h1 className="sr-only">PRAQ</h1>
          <p><span>Pra Responder</span><span>Atividade Quieto</span></p>
        </div>
        {busy && <LoaderCircle className="spinner titlebar-spinner" size={15} aria-label="Processando" />}
      </div>
      <div className="titlebar-controls">
        <button className="window-button" onClick={() => void bridge.minimizeWindow().catch(() => undefined)} aria-label="Minimizar" title="Minimizar"><Minus size={16} /></button>
        <button className="window-button" onClick={() => void bridge.toggleMaximizeWindow().catch(() => undefined)} aria-label="Maximizar ou restaurar" title="Maximizar"><Maximize2 size={14} /></button>
        <button className="window-button window-button--close" onClick={() => void bridge.closeWindow().catch(() => undefined)} aria-label="Fechar" title="Fechar"><X size={16} /></button>
      </div>
      </div>
    </header>
  )
}

interface MainScreenProps {
  state: AppState
  answer: string
  hasActiveKey: boolean
  copied: boolean
  initializing: boolean
  run: (action: () => Promise<ApiEnvelope>) => Promise<boolean>
  copyAnswer: () => Promise<void>
  openSettings: () => void
}

function MainScreen({ state, answer, hasActiveKey, copied, initializing, run, copyAnswer, openSettings }: MainScreenProps) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  const historyCount = state.history.length
  const displayIndex = historyCount > 0 ? Math.max(0, state.historyIndex) + 1 : 0
  const disabled = state.busy || initializing || !hasActiveKey

  const setProvider = (provider: Provider) => {
    if (provider !== state.provider) void run(() => bridge.setProvider(provider))
  }

  const deleteHistory = async () => {
    setConfirmDelete(false)
    await run(bridge.historyDelete)
  }

  return (
    <main className="main-screen">
      <div className="setup-stack">
      <section className="control-strip" aria-label="Seleção de inteligência artificial">
        <div className="field field--provider">
          <span className="field-label" id="provider-label">Provedor</span>
          <div className="segmented" role="group" aria-labelledby="provider-label">
            <button aria-pressed={state.provider === 'groq'} className={state.provider === 'groq' ? 'is-active' : ''} onClick={() => setProvider('groq')} disabled={state.busy}>Groq</button>
            <button aria-pressed={state.provider === 'gemini'} className={state.provider === 'gemini' ? 'is-active' : ''} onClick={() => setProvider('gemini')} disabled={state.busy}>Gemini</button>
            <button className="provider-settings" onClick={openSettings} aria-label="Abrir configurações" title="Configurações"><Settings size={17} /></button>
          </div>
        </div>
        <SelectField id="model" label="Modelo" value={state.selectedModel} options={state.models} onChange={(model) => void run(() => bridge.setModel(model))} disabled={state.busy || state.models.length === 0} />
        <div className={`connection-state ${hasActiveKey ? 'is-ready' : 'is-missing'}`} title={hasActiveKey ? 'Chave configurada' : 'Chave não configurada'}>
          <span className="status-dot" />
          {hasActiveKey ? 'Pronto' : 'Sem chave'}
        </div>
      </section>

      {!hasActiveKey && !initializing && (
        <div className="key-banner">
          <KeyRound size={18} />
          <div><strong>Configure a chave {state.provider === 'groq' ? 'Groq' : 'Gemini'}</strong><span>É necessário conectar o provedor antes de analisar.</span></div>
          <button className="text-button" onClick={openSettings}>Configurar</button>
        </div>
      )}
      </div>

      <section className="answer-workspace" aria-label="Resposta da IA">
        <div className="workspace-heading">
          <div><span className="eyebrow">RESPOSTA</span>{state.busy ? <span className="processing-label"><LoaderCircle className="spinner" size={12} />{state.status}</span> : answer && <span className="answer-meta">{answer.length.toLocaleString('pt-BR')} caracteres</span>}</div>
          <button className="icon-button copy-button" onClick={() => void copyAnswer()} disabled={!answer} title="Copiar resposta" aria-label="Copiar resposta">
            {copied ? <Check size={17} /> : <Copy size={17} />}
          </button>
        </div>
        <div className="answer-scroll" tabIndex={0} aria-busy={state.busy}>
          {!answer && state.busy ? (
            <div className="empty-state busy-state"><LoaderCircle className="spinner" size={25} /><strong>Processando</strong><span>{state.status || 'Aguarde enquanto a IA prepara a resposta…'}</span></div>
          ) : answer ? (
            <div className="answer-text">{answer}</div>
          ) : (
            <div className="empty-state"><Bot size={27} /><strong>Sua resposta aparecerá aqui</strong><span>Selecione um texto ou capture uma questão para começar.</span></div>
          )}
        </div>
        <div className="history-bar">
          <span className="history-label">HISTÓRICO</span>
          <div className="history-controls">
            <button className="icon-button compact" onClick={() => void run(bridge.historyPrev)} disabled={state.busy || historyCount === 0 || state.historyIndex <= 0} aria-label="Resposta anterior" title="Anterior"><ChevronLeft size={16} /></button>
            <span className="history-count" aria-label={`${displayIndex} de ${historyCount}`}>{displayIndex} / {historyCount}</span>
            <button className="icon-button compact" onClick={() => void run(bridge.historyNext)} disabled={state.busy || historyCount === 0 || state.historyIndex >= historyCount - 1} aria-label="Próxima resposta" title="Próxima"><ChevronRight size={16} /></button>
            <span className="divider" />
            <button className="icon-button compact danger" onClick={() => setConfirmDelete(true)} disabled={state.busy || historyCount === 0} aria-label="Excluir resposta atual" title="Excluir"><Trash2 size={15} /></button>
          </div>
        </div>
      </section>

      <section className={`action-area ${state.provider === 'groq' ? 'action-area--groq' : ''}`} aria-label="Ações de captura">
        <button className={`primary-action ${state.provider === 'gemini' ? 'primary-action--secondary' : ''}`} onClick={() => void run(bridge.analyzeSelectedText)} disabled={disabled} title="Analisar texto selecionado">
          <Clipboard size={18} />
          <span>Analisar texto</span>
          <kbd>F2</kbd>
        </button>
        {state.provider === 'gemini' && <button className="secondary-action secondary-action--single" onClick={() => void run(bridge.captureSingle)} disabled={disabled} title="Capturar uma imagem">
          <Image size={17} /><span>Captura única</span><kbd>F8</kbd>
        </button>}
        {state.provider === 'gemini' && <button className="secondary-action secondary-action--scroll" onClick={() => void run(bridge.captureScroll)} disabled={disabled} title="Para questões que exigem rolagem">
           <ScanLine size={17} /><span>Captura dupla</span><kbd>F9</kbd>
        </button>}
      </section>

      <footer className="status-footer">
        <span className={state.busy ? 'pulse-dot' : 'status-dot'} />
        <span>{state.status || (hasActiveKey ? 'Aguardando uma ação' : 'Configuração necessária')}</span>
        <span className="footer-hint">{state.provider === 'gemini' ? 'Use Groq para respostas rápidas' : 'Imagens requerem Gemini'}</span>
      </footer>

      {confirmDelete && (
        <ConfirmDialog title="Excluir esta resposta?" description="Ela será removida do histórico desta sessão." icon={<Trash2 size={20} />} confirmLabel="Excluir" onCancel={() => setConfirmDelete(false)} onConfirm={() => void deleteHistory()} />
      )}
    </main>
  )
}

interface SettingsScreenProps {
  state: AppState
  run: (action: () => Promise<ApiEnvelope>) => Promise<boolean>
  goBack: () => void
  onSaved: () => void
  onCleared: (message?: string) => void
}

function SettingsScreen({ state, run, goBack, onSaved, onCleared }: SettingsScreenProps) {
  const [geminiKey, setGeminiKey] = useState('')
  const [groqKey, setGroqKey] = useState('')
  const [confirmClear, setConfirmClear] = useState(false)
  const [confirmSave, setConfirmSave] = useState(false)
  const [saving, setSaving] = useState(false)
  const [fieldErrors, setFieldErrors] = useState({ gemini: '', groq: '' })

  const validateKeys = () => {
    const errors = {
      gemini: geminiKey && (!geminiKey.startsWith('AIza') || geminiKey.length < 30) ? 'A chave Gemini informada é inválida.' : '',
      groq: groqKey && (!groqKey.startsWith('gsk_') || groqKey.length < 30) ? 'A chave Groq informada é inválida.' : '',
    }
    setFieldErrors(errors)
    return !errors.gemini && !errors.groq
  }

  const saveKeys = async () => {
    setConfirmSave(false)
    setSaving(true)
    const ok = await run(() => bridge.saveKeys(geminiKey.trim(), groqKey.trim()))
    setSaving(false)
    if (ok) {
      setGeminiKey('')
      setGroqKey('')
      onSaved()
    }
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!geminiKey.trim() && !groqKey.trim()) return
    if (!validateKeys()) return
    const replacesConfiguredKey =
      (state.hasGeminiKey && Boolean(geminiKey.trim())) ||
      (state.hasGroqKey && Boolean(groqKey.trim()))
    if (replacesConfiguredKey) {
      setConfirmSave(true)
      return
    }
    void saveKeys()
  }

  const clearKeys = async () => {
    setConfirmClear(false)
    if (await run(bridge.clearKeys)) {
      setGeminiKey('')
      setGroqKey('')
      onCleared('Chave removida.')
    }
  }

  const clearSingleKey = async (provider: Provider) => {
    if (await run(() => bridge.clearKey(provider))) {
      if (provider === 'gemini') setGeminiKey('')
      else setGroqKey('')
      onCleared()
    }
  }

  const openLink = (url: string) => void run(() => bridge.openExternal(url))

  const pasteKey = async (setValue: (value: string) => void) => {
    try {
      const result = await bridge.readClipboard()
      if (result.ok && result.value?.trim()) setValue(result.value.trim())
    } catch {
      // Native clipboard access can be unavailable while another app owns it.
    }
  }

  const maskedKey = (suffix: string) => `${'*'.repeat(24)}${suffix || 'XXXX'}`

  return (
    <main className="settings-screen">
      <div className="settings-page-title"><h1>Configurações</h1></div>
      <div className="settings-intro">
        <div><span className="eyebrow">CREDENCIAIS</span><h2>Chaves de API</h2></div>
      </div>

      <form className="key-form" onSubmit={(event) => void submit(event)}>
         <KeyField
          id="groq-key"
          label="Groq"
           value={groqKey}
           setValue={(value) => { setGroqKey(value); setFieldErrors((current) => ({ ...current, groq: '' })) }}
           configured={state.hasGroqKey}
           maskedValue={maskedKey(state.groqKeySuffix)}
           placeholder="Digite sua chave Groq"
            pasteKey={() => pasteKey((value) => { setGroqKey(value); setFieldErrors((current) => ({ ...current, groq: '' })) })}
            clearKey={state.hasGroqKey ? () => void clearSingleKey('groq') : undefined}
          hint="Análise de texto rápida"
          openDocs={() => openLink('https://console.groq.com/keys')}
          error={fieldErrors.groq}
        />
        <KeyField
          id="gemini-key"
          label="Google Gemini"
           value={geminiKey}
           setValue={(value) => { setGeminiKey(value); setFieldErrors((current) => ({ ...current, gemini: '' })) }}
           configured={state.hasGeminiKey}
           maskedValue={maskedKey(state.geminiKeySuffix)}
           placeholder="Digite sua chave Gemini"
            pasteKey={() => pasteKey((value) => { setGeminiKey(value); setFieldErrors((current) => ({ ...current, gemini: '' })) })}
            clearKey={state.hasGeminiKey ? () => void clearSingleKey('gemini') : undefined}
          hint="Texto e capturas de imagem"
          openDocs={() => openLink('https://aistudio.google.com/app/apikey')}
          error={fieldErrors.gemini}
        />

        <div className="security-note"><KeyRound size={17} /><span><strong>Armazenamento protegido</strong>Suas credenciais ficam criptografadas pelo Windows. Campos vazios não substituem chaves já salvas.</span></div>

        <div className="settings-actions">
          <button type="button" className="button-ghost" onClick={goBack}>Voltar</button>
          <div className="settings-actions__right">
            <button type="button" className="button-ghost danger-text" onClick={() => setConfirmClear(true)} disabled={!state.hasGeminiKey && !state.hasGroqKey}>Limpar chaves</button>
            <button type="submit" className="save-button" disabled={saving || (!geminiKey.trim() && !groqKey.trim())}>{saving ? <LoaderCircle className="spinner" size={17} /> : <Check size={17} />}Salvar alterações</button>
          </div>
        </div>
      </form>

      {confirmClear && (
        <ConfirmDialog title="Remover todas as chaves?" description="As análises ficarão indisponíveis até que novas credenciais sejam configuradas." icon={<KeyRound size={20} />} confirmLabel="Remover chaves" onCancel={() => setConfirmClear(false)} onConfirm={() => void clearKeys()} />
      )}
      {confirmSave && (
        <ConfirmDialog title="Substituir chave configurada?" description="A chave atual será substituída pelo novo valor informado. Esta ação não pode ser desfeita." icon={<KeyRound size={20} />} confirmLabel="Substituir e salvar" onCancel={() => setConfirmSave(false)} onConfirm={() => void saveKeys()} />
      )}
    </main>
  )
}

interface KeyFieldProps {
  id: string
  label: string
  value: string
  setValue: (value: string) => void
  configured: boolean
  maskedValue: string
  placeholder: string
  pasteKey: () => Promise<void>
  clearKey?: () => void
  hint: string
  openDocs: () => void
  error: string
}

function KeyField({ id, label, value, setValue, configured, maskedValue, placeholder, pasteKey, clearKey, hint, openDocs, error }: KeyFieldProps) {
  return (
    <section className="key-row" aria-labelledby={`${id}-label`}>
      <div className="key-row__heading">
        <div><label className={configured ? 'provider-label is-configured' : 'provider-label'} id={`${id}-label`} htmlFor={id}>{label}</label><span>{hint}</span></div>
         <span className={`key-status ${configured ? 'is-configured' : ''}`}><span className="status-dot" />{configured ? 'Configurada' : 'Não configurada'}</span>
      </div>
      <div className="input-row">
         <div className="password-wrap">
            <input id={id} type="password" value={value} onChange={(event) => setValue(event.target.value)} placeholder={configured ? maskedValue : placeholder} autoComplete="off" spellCheck={false} aria-invalid={Boolean(error)} aria-describedby={`${id}-help ${error ? `${id}-error` : ''}`} />
            {clearKey && <button type="button" className="clear-key-button" onClick={clearKey} aria-label="Limpar chave" title="Limpar"><Trash2 size={17} /></button>}
            <button type="button" className="paste-button" onClick={() => void pasteKey()} aria-label="Colar" title="Colar"><ClipboardPaste size={17} /></button>
        </div>
        <button type="button" className="official-link" onClick={openDocs} title={`Abrir página oficial da ${label}`}>Obter chave<ExternalLink size={14} /></button>
      </div>
      {error && <span className="field-error" id={`${id}-error`}>{error}</span>}
      <span id={`${id}-help`} className="sr-only">A chave permanece mascarada e não será armazenada no navegador.</span>
    </section>
  )
}

export default App
