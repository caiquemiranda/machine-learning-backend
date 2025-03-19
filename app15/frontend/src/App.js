import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

// Componentes de layout
import PrivateRoute from './components/layout/PrivateRoute';
import PublicRoute from './components/layout/PublicRoute';

// Páginas públicas
import Login from './components/auth/Login';
import Register from './components/auth/Register';

// Páginas privadas
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import NewPrediction from './pages/predictions/NewPrediction';
import PredictionHistory from './pages/predictions/PredictionHistory';

function App() {
    return (
        <Router>
            <AuthProvider>
                <Routes>
                    {/* Rota raiz */}
                    <Route path="/" element={<Navigate to="/dashboard" />} />

                    {/* Rotas públicas */}
                    <Route element={<PublicRoute restricted={true} />}>
                        <Route path="/login" element={<Login />} />
                        <Route path="/register" element={<Register />} />
                    </Route>

                    {/* Rotas privadas */}
                    <Route element={<PrivateRoute />}>
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/profile" element={<Profile />} />
                        <Route path="/predictions/new" element={<NewPrediction />} />
                        <Route path="/predictions/history" element={<PredictionHistory />} />
                    </Route>

                    {/* Rota para admin */}
                    <Route element={<PrivateRoute requireAdmin={true} />}>
                        <Route path="/admin" element={<div>Painel de Administração</div>} />
                    </Route>

                    {/* Rota para 404 */}
                    <Route path="*" element={<Navigate to="/dashboard" />} />
                </Routes>
            </AuthProvider>
        </Router>
    );
}

export default App; 