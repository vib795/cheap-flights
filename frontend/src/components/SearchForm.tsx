import { useState } from 'react';
import { SearchRequest, CabinClass, SafetyMode } from '../api/types';

interface SearchFormProps {
  onSearch: (request: SearchRequest) => void;
  isLoading: boolean;
}

const COMMON_VISAS = ['US', 'UK', 'SCHENGEN', 'CA', 'AU', 'JP', 'KR', 'AE', 'SG'];
const COMMON_RESIDENCIES = ['US_GC', 'CA_PR', 'UK_BRP', 'EU_PR'];

export function SearchForm({ onSearch, isLoading }: SearchFormProps) {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [date, setDate] = useState('');
  const [adults, setAdults] = useState(1);
  const [cabin, setCabin] = useState<CabinClass>('ECONOMY');
  const [maxStops, setMaxStops] = useState(2);
  const [passportNationality, setPassportNationality] = useState('IN');
  const [safetyMode, setSafetyMode] = useState<SafetyMode>('balanced');

  // Travel docs (optional)
  const [showTravelDocs, setShowTravelDocs] = useState(false);
  const [selectedVisas, setSelectedVisas] = useState<string[]>([]);
  const [selectedResidencies, setSelectedResidencies] = useState<string[]>([]);
  const [travelNotes, setTravelNotes] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const request: SearchRequest = {
      origin: origin.toUpperCase(),
      destination: destination.toUpperCase(),
      date,
      adults,
      cabin,
      max_stops: maxStops,
      passport_nationality: passportNationality,
      safety_mode: safetyMode,
      flex_days: 0,
    };

    // Add travel docs if any are selected
    if (selectedVisas.length > 0 || selectedResidencies.length > 0 || travelNotes) {
      request.travel_docs = {
        visas: selectedVisas,
        residencies: selectedResidencies,
        notes: travelNotes,
      };
    }

    onSearch(request);
  };

  const toggleVisa = (visa: string) => {
    setSelectedVisas((prev) =>
      prev.includes(visa) ? prev.filter((v) => v !== visa) : [...prev, visa]
    );
  };

  const toggleResidency = (residency: string) => {
    setSelectedResidencies((prev) =>
      prev.includes(residency) ? prev.filter((r) => r !== residency) : [...prev, residency]
    );
  };

  // Get minimum date (today)
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">
        GeoFlight Scout <span className="text-sm font-normal text-gray-500">(IN-first)</span>
      </h2>
      <p className="text-sm text-gray-600 mb-6">
        Find cheap flights with smart transit safety ranking for Indian travelers.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Origin and Destination */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Origin (IATA Code) *
            </label>
            <input
              type="text"
              required
              maxLength={3}
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="e.g. DEL"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Destination (IATA Code) *
            </label>
            <input
              type="text"
              required
              maxLength={3}
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. SFO"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Date and Passengers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Departure Date *
            </label>
            <input
              type="date"
              required
              min={today}
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Adults</label>
            <select
              value={adults}
              onChange={(e) => setAdults(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Cabin and Max Stops */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cabin Class</label>
            <select
              value={cabin}
              onChange={(e) => setCabin(e.target.value as CabinClass)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ECONOMY">Economy</option>
              <option value="PREMIUM_ECONOMY">Premium Economy</option>
              <option value="BUSINESS">Business</option>
              <option value="FIRST">First</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Stops</label>
            <select
              value={maxStops}
              onChange={(e) => setMaxStops(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>Non-stop only</option>
              <option value={1}>1 stop max</option>
              <option value={2}>2 stops max</option>
            </select>
          </div>
        </div>

        {/* Passport Nationality */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Passport Nationality *
          </label>
          <input
            type="text"
            required
            maxLength={2}
            value={passportNationality}
            onChange={(e) => setPassportNationality(e.target.value.toUpperCase())}
            placeholder="e.g. IN"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">ISO 2-letter country code (default: IN)</p>
        </div>

        {/* Safety Mode */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Safety Mode (Ranking Strategy)
          </label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="price_first"
                checked={safetyMode === 'price_first'}
                onChange={(e) => setSafetyMode(e.target.value as SafetyMode)}
                className="mr-2"
              />
              <span className="text-sm">Price First</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="balanced"
                checked={safetyMode === 'balanced'}
                onChange={(e) => setSafetyMode(e.target.value as SafetyMode)}
                className="mr-2"
              />
              <span className="text-sm font-semibold">Balanced</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="safety_first"
                checked={safetyMode === 'safety_first'}
                onChange={(e) => setSafetyMode(e.target.value as SafetyMode)}
                className="mr-2"
              />
              <span className="text-sm">Safety First</span>
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            How to rank results: price-focused vs safety-focused
          </p>
        </div>

        {/* Travel Docs (Optional Collapsible) */}
        <div className="border-t pt-4">
          <button
            type="button"
            onClick={() => setShowTravelDocs(!showTravelDocs)}
            className="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center"
          >
            {showTravelDocs ? '▼' : '▶'} Additional Travel Documents (Optional)
          </button>
          <p className="text-xs text-gray-500 mt-1">
            Help improve risk assessment by indicating visas/residencies you hold
          </p>

          {showTravelDocs && (
            <div className="mt-4 space-y-4">
              {/* Visas */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Visas You Hold:
                </label>
                <div className="flex flex-wrap gap-2">
                  {COMMON_VISAS.map((visa) => (
                    <button
                      key={visa}
                      type="button"
                      onClick={() => toggleVisa(visa)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        selectedVisas.includes(visa)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {visa}
                    </button>
                  ))}
                </div>
              </div>

              {/* Residencies */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Residency Permits:
                </label>
                <div className="flex flex-wrap gap-2">
                  {COMMON_RESIDENCIES.map((residency) => (
                    <button
                      key={residency}
                      type="button"
                      onClick={() => toggleResidency(residency)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        selectedResidencies.includes(residency)
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {residency}
                    </button>
                  ))}
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Notes:
                </label>
                <textarea
                  value={travelNotes}
                  onChange={(e) => setTravelNotes(e.target.value)}
                  placeholder="e.g., Valid US B1/B2 until 2028"
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 text-white font-semibold py-3 px-6 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Searching...' : 'Search Flights'}
        </button>
      </form>
    </div>
  );
}
