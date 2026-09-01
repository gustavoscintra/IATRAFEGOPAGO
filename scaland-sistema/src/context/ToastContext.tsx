import { createContext, useContext, useRef, useState, type ReactNode } from 'react'

const ToastContext = createContext<(message: string) => void>(() => {})

export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState('')
  const [show, setShow] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  function toast(m: string) {
    setMessage(m)
    setShow(true)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setShow(false), 1600)
  }

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div id="toast" className={show ? 'show' : ''}>{message}</div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}
