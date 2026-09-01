import { NavLink } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'

interface SidebarProps {
  open: boolean
  onNavigate: () => void
  counts: { clientes: number; leads: number; tarefas: number }
}

export function Sidebar({ open, onNavigate, counts }: SidebarProps) {
  const { theme, setTheme } = useTheme()
  const { usuario, user, signOut } = useAuth()

  const nome = usuario?.nome || user?.email?.split('@')[0] || 'Você'
  const inicial = nome.charAt(0).toUpperCase()

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="logo"><span className="dot" /> Scaland</div>

      <NavLink to="/clientes" onClick={onNavigate} className={({ isActive }) => `nav-item ${isActive ? 'on' : ''}`}>
        <span className="ic">◈</span> Clientes <span className="badge">{counts.clientes}</span>
      </NavLink>
      <NavLink to="/prospeccao" onClick={onNavigate} className={({ isActive }) => `nav-item ${isActive ? 'on' : ''}`}>
        <span className="ic">◎</span> Prospecção <span className="badge">{counts.leads}</span>
      </NavLink>
      <NavLink to="/tarefas" onClick={onNavigate} className={({ isActive }) => `nav-item ${isActive ? 'on' : ''}`}>
        <span className="ic">✓</span> Tarefas <span className="badge">{counts.tarefas}</span>
      </NavLink>

      <div className="nav-phase">Fase 2 · em breve</div>
      <button className="nav-item locked"><span className="ic">$</span> Financeiro <span className="locktag">breve</span></button>
      <button className="nav-item locked"><span className="ic">▲</span> Indicadores <span className="locktag">breve</span></button>

      <div className="sidebar-foot">
        <div className="userchip">
          <div className="avatar">{inicial}</div>
          <div>
            {nome}
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{usuario?.papel || '—'}</div>
          </div>
        </div>
        <div className="theme-mini">
          <button className={theme === 'light' ? 'on' : ''} onClick={() => setTheme('light')}>☀️ Claro</button>
          <button className={theme === 'dark' ? 'on' : ''} onClick={() => setTheme('dark')}>🌙 Escuro</button>
        </div>
        <button
          className="btn-ghost btn-sm"
          style={{ width: '100%', marginTop: 10 }}
          onClick={signOut}
        >
          Sair
        </button>
      </div>
    </aside>
  )
}
