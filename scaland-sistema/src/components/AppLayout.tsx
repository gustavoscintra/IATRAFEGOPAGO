import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Contagens dos badges da sidebar entram junto com os hooks de dados de
  // cada módulo (Fase 1, passos 2-4). Por enquanto ficam zeradas.
  const counts = { clientes: 0, leads: 0, tarefas: 0 }

  return (
    <div className="app">
      <Sidebar open={sidebarOpen} onNavigate={() => setSidebarOpen(false)} counts={counts} />
      <main className="main">
        <button className="hamb" onClick={() => setSidebarOpen((v) => !v)}>☰ Menu</button>
        <Outlet />
      </main>
    </div>
  )
}
