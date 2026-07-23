import { Routes, Route } from 'react-router-dom';
import PropertyList from './pages/PropertyList';
import PropertyDetail from './pages/PropertyDetail';

function App() {
  return (
    <Routes>
      <Route path="/" element={<PropertyList />} />
      <Route path="/properties/:id" element={<PropertyDetail />} />
    </Routes>
  );
}

export default App;
