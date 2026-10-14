import { Check, ChevronDown } from 'lucide-react'
import { KeyboardEvent, useEffect, useRef, useState } from 'react'

interface SelectFieldProps {
  id: string
  label: string
  value: string
  options: string[]
  disabled?: boolean
  onChange: (value: string) => void
}

// Display-only hints keyed by exact model ID. The API always receives
// the pure ID; hints never leave the dropdown UI.
const MODEL_HINTS: Record<string, string> = {
  'allam-2-7b': 'Instantâneo · Barato · Contexto curto',
  'openai/gpt-oss-20b': 'Rápido · Econômico',
  'openai/gpt-oss-120b': 'Inteligente · Lento',
  'qwen/qwen3.8-27b': 'Versátil · Caro',
  'models/gemini-3.1-flash-lite': 'Barato · Rápido',
  'models/gemini-3.5-flash-lite': 'Rápido · Econômico',
  'models/gemini-3.5-flash': 'Inteligente · Rápido',
  'models/gemini-3.8-flash': 'Mais inteligente · Lento',
}

export function SelectField({
  id,
  label,
  value,
  options,
  disabled = false,
  onChange,
}: SelectFieldProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const closeOnOutsideClick = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', closeOnOutsideClick)
    return () => document.removeEventListener('pointerdown', closeOnOutsideClick)
  }, [])

  const select = (nextValue: string) => {
    onChange(nextValue)
    setOpen(false)
    buttonRef.current?.focus()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'Escape') {
      setOpen(false)
      return
    }
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return
    event.preventDefault()
    if (!open) {
      setOpen(true)
      return
    }
    const currentIndex = Math.max(0, options.indexOf(value))
    const direction = event.key === 'ArrowDown' ? 1 : -1
    const nextIndex = (currentIndex + direction + options.length) % options.length
    if (options[nextIndex]) onChange(options[nextIndex])
  }

  return (
    <div className="field field--model select-field" ref={rootRef}>
      <span className="field-label" id={`${id}-label`}>{label}</span>
      <button
        ref={buttonRef}
        id={id}
        type="button"
        className="select-trigger"
        aria-labelledby={`${id}-label ${id}-value`}
        aria-haspopup="listbox"
        aria-expanded={open}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={handleKeyDown}
      >
        <span id={`${id}-value`}>{value || 'Nenhum modelo'}</span>
        <ChevronDown size={15} aria-hidden="true" />
      </button>
      <div className={`select-popup ${open ? 'is-open' : ''}`} role="listbox" aria-labelledby={`${id}-label`} aria-hidden={!open}>
        {options.map((option) => (
          <button
            type="button"
            role="option"
            aria-selected={option === value}
            tabIndex={open ? 0 : -1}
            className={option === value ? 'is-selected' : ''}
            key={option}
            onClick={() => select(option)}
          >
            <span>{option}{MODEL_HINTS[option] && <span className="model-hint"> · {MODEL_HINTS[option]}</span>}</span>
            {option === value && <Check size={14} aria-hidden="true" />}
          </button>
        ))}
      </div>
    </div>
  )
}
