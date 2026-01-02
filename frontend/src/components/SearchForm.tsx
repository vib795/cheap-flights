import { useState } from 'react';
import { SearchRequest, CabinClass, SafetyMode } from '../api/types';
import AirportAutocomplete from './AirportAutocomplete';

interface SearchFormProps {
  onSearch: (request: SearchRequest) => void;
  isLoading: boolean;
}

const COMMON_VISAS = ['US', 'UK', 'SCHENGEN', 'CA', 'AU', 'JP', 'KR', 'AE', 'SG'];
const COMMON_RESIDENCIES = ['US_GC', 'CA_PR', 'UK_BRP', 'EU_PR'];

// Comprehensive list of countries with ISO 2-letter codes
const COUNTRIES = [
  { code: 'AF', name: 'Afghanistan' },
  { code: 'AL', name: 'Albania' },
  { code: 'DZ', name: 'Algeria' },
  { code: 'AD', name: 'Andorra' },
  { code: 'AO', name: 'Angola' },
  { code: 'AG', name: 'Antigua and Barbuda' },
  { code: 'AR', name: 'Argentina' },
  { code: 'AM', name: 'Armenia' },
  { code: 'AU', name: 'Australia' },
  { code: 'AT', name: 'Austria' },
  { code: 'AZ', name: 'Azerbaijan' },
  { code: 'BS', name: 'Bahamas' },
  { code: 'BH', name: 'Bahrain' },
  { code: 'BD', name: 'Bangladesh' },
  { code: 'BB', name: 'Barbados' },
  { code: 'BY', name: 'Belarus' },
  { code: 'BE', name: 'Belgium' },
  { code: 'BZ', name: 'Belize' },
  { code: 'BJ', name: 'Benin' },
  { code: 'BT', name: 'Bhutan' },
  { code: 'BO', name: 'Bolivia' },
  { code: 'BA', name: 'Bosnia and Herzegovina' },
  { code: 'BW', name: 'Botswana' },
  { code: 'BR', name: 'Brazil' },
  { code: 'BN', name: 'Brunei' },
  { code: 'BG', name: 'Bulgaria' },
  { code: 'BF', name: 'Burkina Faso' },
  { code: 'BI', name: 'Burundi' },
  { code: 'KH', name: 'Cambodia' },
  { code: 'CM', name: 'Cameroon' },
  { code: 'CA', name: 'Canada' },
  { code: 'CV', name: 'Cape Verde' },
  { code: 'CF', name: 'Central African Republic' },
  { code: 'TD', name: 'Chad' },
  { code: 'CL', name: 'Chile' },
  { code: 'CN', name: 'China' },
  { code: 'CO', name: 'Colombia' },
  { code: 'KM', name: 'Comoros' },
  { code: 'CG', name: 'Congo' },
  { code: 'CR', name: 'Costa Rica' },
  { code: 'HR', name: 'Croatia' },
  { code: 'CU', name: 'Cuba' },
  { code: 'CY', name: 'Cyprus' },
  { code: 'CZ', name: 'Czech Republic' },
  { code: 'DK', name: 'Denmark' },
  { code: 'DJ', name: 'Djibouti' },
  { code: 'DM', name: 'Dominica' },
  { code: 'DO', name: 'Dominican Republic' },
  { code: 'EC', name: 'Ecuador' },
  { code: 'EG', name: 'Egypt' },
  { code: 'SV', name: 'El Salvador' },
  { code: 'GQ', name: 'Equatorial Guinea' },
  { code: 'ER', name: 'Eritrea' },
  { code: 'EE', name: 'Estonia' },
  { code: 'ET', name: 'Ethiopia' },
  { code: 'FJ', name: 'Fiji' },
  { code: 'FI', name: 'Finland' },
  { code: 'FR', name: 'France' },
  { code: 'GA', name: 'Gabon' },
  { code: 'GM', name: 'Gambia' },
  { code: 'GE', name: 'Georgia' },
  { code: 'DE', name: 'Germany' },
  { code: 'GH', name: 'Ghana' },
  { code: 'GR', name: 'Greece' },
  { code: 'GD', name: 'Grenada' },
  { code: 'GT', name: 'Guatemala' },
  { code: 'GN', name: 'Guinea' },
  { code: 'GW', name: 'Guinea-Bissau' },
  { code: 'GY', name: 'Guyana' },
  { code: 'HT', name: 'Haiti' },
  { code: 'HN', name: 'Honduras' },
  { code: 'HU', name: 'Hungary' },
  { code: 'IS', name: 'Iceland' },
  { code: 'IN', name: 'India' },
  { code: 'ID', name: 'Indonesia' },
  { code: 'IR', name: 'Iran' },
  { code: 'IQ', name: 'Iraq' },
  { code: 'IE', name: 'Ireland' },
  { code: 'IL', name: 'Israel' },
  { code: 'IT', name: 'Italy' },
  { code: 'JM', name: 'Jamaica' },
  { code: 'JP', name: 'Japan' },
  { code: 'JO', name: 'Jordan' },
  { code: 'KZ', name: 'Kazakhstan' },
  { code: 'KE', name: 'Kenya' },
  { code: 'KI', name: 'Kiribati' },
  { code: 'KP', name: 'North Korea' },
  { code: 'KR', name: 'South Korea' },
  { code: 'KW', name: 'Kuwait' },
  { code: 'KG', name: 'Kyrgyzstan' },
  { code: 'LA', name: 'Laos' },
  { code: 'LV', name: 'Latvia' },
  { code: 'LB', name: 'Lebanon' },
  { code: 'LS', name: 'Lesotho' },
  { code: 'LR', name: 'Liberia' },
  { code: 'LY', name: 'Libya' },
  { code: 'LI', name: 'Liechtenstein' },
  { code: 'LT', name: 'Lithuania' },
  { code: 'LU', name: 'Luxembourg' },
  { code: 'MK', name: 'North Macedonia' },
  { code: 'MG', name: 'Madagascar' },
  { code: 'MW', name: 'Malawi' },
  { code: 'MY', name: 'Malaysia' },
  { code: 'MV', name: 'Maldives' },
  { code: 'ML', name: 'Mali' },
  { code: 'MT', name: 'Malta' },
  { code: 'MH', name: 'Marshall Islands' },
  { code: 'MR', name: 'Mauritania' },
  { code: 'MU', name: 'Mauritius' },
  { code: 'MX', name: 'Mexico' },
  { code: 'FM', name: 'Micronesia' },
  { code: 'MD', name: 'Moldova' },
  { code: 'MC', name: 'Monaco' },
  { code: 'MN', name: 'Mongolia' },
  { code: 'ME', name: 'Montenegro' },
  { code: 'MA', name: 'Morocco' },
  { code: 'MZ', name: 'Mozambique' },
  { code: 'MM', name: 'Myanmar' },
  { code: 'NA', name: 'Namibia' },
  { code: 'NR', name: 'Nauru' },
  { code: 'NP', name: 'Nepal' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'NZ', name: 'New Zealand' },
  { code: 'NI', name: 'Nicaragua' },
  { code: 'NE', name: 'Niger' },
  { code: 'NG', name: 'Nigeria' },
  { code: 'NO', name: 'Norway' },
  { code: 'OM', name: 'Oman' },
  { code: 'PK', name: 'Pakistan' },
  { code: 'PW', name: 'Palau' },
  { code: 'PS', name: 'Palestine' },
  { code: 'PA', name: 'Panama' },
  { code: 'PG', name: 'Papua New Guinea' },
  { code: 'PY', name: 'Paraguay' },
  { code: 'PE', name: 'Peru' },
  { code: 'PH', name: 'Philippines' },
  { code: 'PL', name: 'Poland' },
  { code: 'PT', name: 'Portugal' },
  { code: 'QA', name: 'Qatar' },
  { code: 'RO', name: 'Romania' },
  { code: 'RU', name: 'Russia' },
  { code: 'RW', name: 'Rwanda' },
  { code: 'KN', name: 'Saint Kitts and Nevis' },
  { code: 'LC', name: 'Saint Lucia' },
  { code: 'VC', name: 'Saint Vincent and the Grenadines' },
  { code: 'WS', name: 'Samoa' },
  { code: 'SM', name: 'San Marino' },
  { code: 'ST', name: 'Sao Tome and Principe' },
  { code: 'SA', name: 'Saudi Arabia' },
  { code: 'SN', name: 'Senegal' },
  { code: 'RS', name: 'Serbia' },
  { code: 'SC', name: 'Seychelles' },
  { code: 'SL', name: 'Sierra Leone' },
  { code: 'SG', name: 'Singapore' },
  { code: 'SK', name: 'Slovakia' },
  { code: 'SI', name: 'Slovenia' },
  { code: 'SB', name: 'Solomon Islands' },
  { code: 'SO', name: 'Somalia' },
  { code: 'ZA', name: 'South Africa' },
  { code: 'SS', name: 'South Sudan' },
  { code: 'ES', name: 'Spain' },
  { code: 'LK', name: 'Sri Lanka' },
  { code: 'SD', name: 'Sudan' },
  { code: 'SR', name: 'Suriname' },
  { code: 'SZ', name: 'Eswatini' },
  { code: 'SE', name: 'Sweden' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'SY', name: 'Syria' },
  { code: 'TW', name: 'Taiwan' },
  { code: 'TJ', name: 'Tajikistan' },
  { code: 'TZ', name: 'Tanzania' },
  { code: 'TH', name: 'Thailand' },
  { code: 'TL', name: 'Timor-Leste' },
  { code: 'TG', name: 'Togo' },
  { code: 'TO', name: 'Tonga' },
  { code: 'TT', name: 'Trinidad and Tobago' },
  { code: 'TN', name: 'Tunisia' },
  { code: 'TR', name: 'Turkey' },
  { code: 'TM', name: 'Turkmenistan' },
  { code: 'TV', name: 'Tuvalu' },
  { code: 'UG', name: 'Uganda' },
  { code: 'UA', name: 'Ukraine' },
  { code: 'AE', name: 'United Arab Emirates' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'US', name: 'United States' },
  { code: 'UY', name: 'Uruguay' },
  { code: 'UZ', name: 'Uzbekistan' },
  { code: 'VU', name: 'Vanuatu' },
  { code: 'VA', name: 'Vatican City' },
  { code: 'VE', name: 'Venezuela' },
  { code: 'VN', name: 'Vietnam' },
  { code: 'YE', name: 'Yemen' },
  { code: 'ZM', name: 'Zambia' },
  { code: 'ZW', name: 'Zimbabwe' },
];

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
          <AirportAutocomplete
            value={origin}
            onChange={setOrigin}
            label="Origin"
            placeholder="e.g. New Delhi, DEL"
            required
          />
          <AirportAutocomplete
            value={destination}
            onChange={setDestination}
            label="Destination"
            placeholder="e.g. San Francisco, SFO"
            required
          />
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
          <select
            required
            value={passportNationality}
            onChange={(e) => setPassportNationality(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {COUNTRIES.map((country) => (
              <option key={country.code} value={country.code}>
                {country.name} ({country.code})
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Select your passport country (risk assessment is optimized for Indian travelers)
          </p>
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
