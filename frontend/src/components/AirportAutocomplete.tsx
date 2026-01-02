import { useState, useEffect, useRef } from 'react';
import airportsData from '../data/airports.json';

interface Airport {
  iata: string;
  name: string;
  city: string;
  country: string;
  country_code: string;
  label: string;
  search: string;
}

interface AirportAutocompleteProps {
  value: string;
  onChange: (iata: string) => void;
  placeholder?: string;
  label: string;
  required?: boolean;
}

export default function AirportAutocomplete({
  value,
  onChange,
  placeholder = 'e.g. New York, JFK',
  label,
  required = false
}: AirportAutocompleteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredAirports, setFilteredAirports] = useState<Airport[]>([]);
  const [selectedAirport, setSelectedAirport] = useState<Airport | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const airports: Airport[] = airportsData as Airport[];

  // Initialize selected airport from value prop
  useEffect(() => {
    if (value && !selectedAirport) {
      const airport = airports.find(a => a.iata === value.toUpperCase());
      if (airport) {
        setSelectedAirport(airport);
        setSearchTerm(airport.label);
      }
    }
  }, [value, selectedAirport, airports]);

  // Filter airports based on search term
  useEffect(() => {
    if (!searchTerm) {
      setFilteredAirports([]);
      return;
    }

    const term = searchTerm.toLowerCase();
    const results = airports.filter(airport =>
      airport.search.includes(term) ||
      airport.iata.toLowerCase().includes(term)
    ).slice(0, 50); // Limit to 50 results

    setFilteredAirports(results);
  }, [searchTerm, airports]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    setIsOpen(true);

    // If user clears the input
    if (!value) {
      setSelectedAirport(null);
      onChange('');
    }
  };

  const handleSelect = (airport: Airport) => {
    setSelectedAirport(airport);
    setSearchTerm(airport.label);
    onChange(airport.iata);
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
    // Select all text on focus for easy replacement
    if (searchTerm) {
      setTimeout(() => {
        const input = wrapperRef.current?.querySelector('input');
        input?.select();
      }, 0);
    }
  };

  return (
    <div ref={wrapperRef} className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>

      <input
        type="text"
        value={searchTerm}
        onChange={handleInputChange}
        onFocus={handleInputFocus}
        placeholder={placeholder}
        required={required}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        autoComplete="off"
      />

      {/* Dropdown */}
      {isOpen && filteredAirports.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-80 overflow-y-auto">
          {filteredAirports.map((airport) => (
            <div
              key={airport.iata}
              onClick={() => handleSelect(airport)}
              className="px-3 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">
                    {airport.city} ({airport.iata})
                  </div>
                  <div className="text-sm text-gray-600 truncate">
                    {airport.name}
                  </div>
                </div>
                <div className="ml-2 text-sm text-gray-500">
                  {airport.country}
                </div>
              </div>
            </div>
          ))}

          {filteredAirports.length === 50 && (
            <div className="px-3 py-2 text-sm text-gray-500 text-center border-t">
              Showing first 50 results. Type more to refine search.
            </div>
          )}
        </div>
      )}

      {/* No results message */}
      {isOpen && searchTerm && filteredAirports.length === 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-3 text-sm text-gray-500 text-center">
          No airports found. Try searching by city name or IATA code.
        </div>
      )}

      {/* Helper text */}
      <p className="mt-1 text-xs text-gray-500">
        Search by city name, airport name, or IATA code
      </p>
    </div>
  );
}
