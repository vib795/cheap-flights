import { Itinerary } from '../api/types';
import { ItineraryCard } from './ItineraryCard';

interface ResultsListProps {
  results: Itinerary[];
  isLoading: boolean;
  error: string | null;
}

export function ResultsList({ results, isLoading, error }: ResultsListProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-12 text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Searching for flights...</p>
        <p className="text-sm text-gray-500 mt-2">
          Fetching offers, analyzing transit risks, and ranking by safety + price
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold text-lg mb-2">Error</h3>
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  if (results.length === 0) {
    return null;
  }

  return (
    <div>
      <div className="mb-4 flex justify-between items-center">
        <h3 className="text-xl font-bold text-gray-800">
          Top {results.length} Results (Ranked by Price + Safety)
        </h3>
        <div className="text-sm text-gray-600">
          Showing best-ranked itineraries
        </div>
      </div>

      <div className="space-y-4">
        {results.map((itinerary, idx) => (
          <div key={itinerary.id} className="relative">
            <div className="absolute -left-8 top-6 text-gray-400 font-bold text-lg">
              #{idx + 1}
            </div>
            <ItineraryCard itinerary={itinerary} />
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-gray-100 rounded-lg">
        <h4 className="font-semibold text-gray-800 mb-2">Important Disclaimers:</h4>
        <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
          <li>
            <strong>Transit/visa guidance is heuristic-based and NOT authoritative.</strong> Always
            verify with official sources (embassy, consulate, airline) before booking.
          </li>
          <li>
            "Safe transit" ranking is a product feature for Indian travelers, not a legal
            guarantee.
          </li>
          <li>
            Preferred transit countries are based on general patterns; individual circumstances
            vary.
          </li>
          <li>Even with relevant visas/permits, always confirm airside vs landside rules.</li>
          <li>This is a search tool only - no booking functionality.</li>
        </ul>
      </div>
    </div>
  );
}
