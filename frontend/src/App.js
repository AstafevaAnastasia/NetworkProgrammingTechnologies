import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Auth from './pages/Auth';
import Profile from './pages/Profile';
import './styles/main.css';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const userData = localStorage.getItem('user');

        if (token && userData) {
          setUser(JSON.parse(userData));
        }
      } catch (e) {
        localStorage.clear();
      }
    };

    checkAuth();
  }, []);

  return (
    <Router>
      <div className="app">
        <Navbar user={user} setUser={setUser} />
        <Routes>
          <Route path="/" element={<Home user={user} />} />
          <Route path="/auth" element={<Auth setUser={setUser} />} />
          <Route
            path="/profile"
            element={<Profile user={user} setUser={setUser} />}
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;