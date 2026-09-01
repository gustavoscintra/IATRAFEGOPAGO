import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { ProtectedRoute } from './components/ProtectedRoute'
import Login from './pages/Login'
import ClientesPage from './pages/clientes/ClientesPage'
import ProspeccaoPage from './pages/prospeccao/ProspeccaoPage'
import TarefasPage from './pages/tarefas/TarefasPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/clientes" element={<ClientesPage />} />
        <Route path="/prospeccao" element={<ProspeccaoPage />} />
        <Route path="/tarefas" element={<TarefasPage />} />
        <Route index element={<Navigate to="/clientes" replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/clientes" replace />} />
    </Routes>
  )
}
