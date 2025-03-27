import React, { useState } from 'react';
import Home from './pages/Home';
import Auth from './pages/Auth';
import Profile from './pages/Profile';
import Navbar from './components/Navbar';

function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState('home');

  return (
    <div className="app">
      <Navbar user={user} setPage={setPage} />

      {page === 'home' && <Home />}
      {page === 'auth' && <Auth setUser={setUser} setPage={setPage} />}
      {page === 'profile' && <Profile user={user} />}
    </div>
  );
}

export default App;