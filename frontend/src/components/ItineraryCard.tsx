import { Itinerary } from '../api/types';
import { RiskBadge } from './RiskBadge';

interface ItineraryCardProps {
  itinerary: Itinerary;
}

export function ItineraryCard({ itinerary }: ItineraryCardProps) {
  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const copyItinerary = () => {
    navigator.clipboard.writeText(JSON.stringify(itinerary, null, 2));
    alert('Itinerary JSON copied to clipboard!');
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4 hover:shadow-lg transition-shadow">
      {/* Header: Price and Duration */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="text-3xl font-bold text-blue-600">
            {itinerary.price.currency} {itinerary.price.total.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600 mt-1">
            Total: {formatDuration(itinerary.total_duration_minutes)} • {itinerary.stops}{' '}
            {itinerary.stops === 1 ? 'stop' : 'stops'}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <RiskBadge level={itinerary.risk.level} />
          <button
            onClick={copyItinerary}
            className="text-xs text-blue-600 hover:text-blue-800 underline"
          >
            Copy JSON
          </button>
        </div>
      </div>

      {/* Flight Segments */}
      <div className="mb-4 space-y-3">
        {itinerary.segments.map((segment, idx) => (
          <div key={idx} className="flex items-center gap-4 text-sm">
            <div className="font-mono font-semibold text-gray-700">
              {segment.flight_number}
            </div>
            <div className="flex-1 flex items-center gap-2">
              <span className="font-semibold">{segment.from}</span>
              <span className="text-gray-500">{formatDateTime(segment.depart_at)}</span>
              <span className="text-gray-400">→</span>
              <span className="font-semibold">{segment.to}</span>
              <span className="text-gray-500">{formatDateTime(segment.arrive_at)}</span>
              <span className="text-gray-400 ml-auto">
                ({formatDuration(segment.duration_minutes)})
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Layovers */}
      {itinerary.layovers.length > 0 && (
        <div className="mb-4 p-3 bg-gray-50 rounded">
          <div className="text-xs font-semibold text-gray-600 mb-2">LAYOVERS:</div>
          <div className="space-y-1">
            {itinerary.layovers.map((layover, idx) => (
              <div key={idx} className="text-sm text-gray-700">
                {layover.airport} ({layover.country || 'Unknown'}) -{' '}
                {formatDuration(layover.minutes)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transit Countries */}
      {itinerary.transit_countries.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-semibold text-gray-600 mb-1">TRANSIT COUNTRIES:</div>
          <div className="flex flex-wrap gap-2">
            {itinerary.transit_countries.map((country) => (
              <span
                key={country}
                className="inline-block px-2 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded"
              >
                {country}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Risk Assessment */}
      <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
        <div className="text-sm font-semibold text-yellow-900 mb-2">
          Transit Safety & Visa Risk Assessment:
        </div>

        {itinerary.risk.reasons.length > 0 && (
          <div className="mb-3">
            <div className="text-xs font-semibold text-gray-700 mb-1">Risk Factors:</div>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
              {itinerary.risk.reasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        )}

        {itinerary.risk.verify_steps.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-gray-700 mb-1">
              Verification Steps (DO BEFORE BOOKING):
            </div>
            <ul className="list-decimal list-inside text-sm text-gray-700 space-y-1">
              {itinerary.risk.verify_steps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-3 text-xs text-gray-600 italic">
          ⚠️ Transit/visa guidance is best-effort and not authoritative. Verify with official
          sources and airline before booking.
        </div>
      </div>

      {/* Visa Baseline */}
      {itinerary.visa_baseline && (
        <div
          className={`p-3 border rounded ${
            itinerary.visa_baseline.source === 'ai-research'
              ? 'bg-purple-50 border-purple-300'
              : 'bg-blue-50 border-blue-200'
          }`}
        >
          <div
            className={`text-xs font-semibold mb-1 ${
              itinerary.visa_baseline.source === 'ai-research'
                ? 'text-purple-900'
                : 'text-blue-900'
            }`}
          >
            {itinerary.visa_baseline.source === 'ai-research' ? '🤖 ' : ''}
            Destination Entry Info ({itinerary.visa_baseline.source}):
          </div>
          <div className="text-sm text-gray-700 mb-2 whitespace-pre-line">
            {itinerary.visa_baseline.destination_entry_summary}
          </div>
          <div
            className={`text-xs italic ${
              itinerary.visa_baseline.source === 'ai-research'
                ? 'text-purple-700 font-semibold'
                : 'text-gray-600'
            }`}
          >
            {itinerary.visa_baseline.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
}
