import { useState } from 'react';
import { SearchForm } from './components/SearchForm';
import { ResultsList } from './components/ResultsList';
import { searchFlights } from './api/client';
import { SearchRequest, Itinerary } from './api/types';

function App() {
  const [results, setResults] = useState<Itinerary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (request: SearchRequest) => {
    setIsLoading(true);
    setError(null);
    setResults([]);

    try {
      const response = await searchFlights(request);
      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            GeoFlight Scout
          </h1>
          <p className="text-gray-600">
            Smart flight search with transit safety ranking for Indian travelers
          </p>
        </header>

        <SearchForm onSearch={handleSearch} isLoading={isLoading} />

        <ResultsList results={results} isLoading={isLoading} error={error} />
      </div>

      <footer className="max-w-5xl mx-auto px-4 py-8 mt-12 text-center text-sm text-gray-500">
        <p>GeoFlight Scout MVP - For educational and research purposes</p>
        <p className="mt-1">
          Transit safety heuristics are based on common patterns for Indian passport holders.
          Always verify official requirements.
        </p>
      </footer>
    </div>
  );
}

export default App;
