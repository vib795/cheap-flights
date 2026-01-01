export type CabinClass = 'ECONOMY' | 'PREMIUM_ECONOMY' | 'BUSINESS' | 'FIRST';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type SafetyMode = 'price_first' | 'balanced' | 'safety_first';

export interface TravelDocs {
  visas: string[];
  residencies: string[];
  notes: string;
}

export interface SearchRequest {
  origin: string;
  destination: string;
  date: string;
  adults: number;
  cabin: CabinClass;
  max_stops: number;
  passport_nationality: string;
  safety_mode: SafetyMode;
  travel_docs?: TravelDocs;
  flex_days: number;
}

export interface FlightSegment {
  carrier: string;
  flight_number: string;
  from: string;
  to: string;
  depart_at: string;
  arrive_at: string;
  duration_minutes: number;
}

export interface Layover {
  airport: string;
  minutes: number;
  country?: string;
}

export interface RiskAssessment {
  level: RiskLevel;
  reasons: string[];
  verify_steps: string[];
  transit_countries: string[];
  layover_airports: string[];
}

export interface VisaBaseline {
  destination_entry_summary: string;
  source: string;
  disclaimer: string;
}

export interface Price {
  total: number;
  currency: string;
}

export interface Itinerary {
  id: string;
  provider: string;
  price: Price;
  total_duration_minutes: number;
  stops: number;
  segments: FlightSegment[];
  layovers: Layover[];
  transit_countries: string[];
  risk: RiskAssessment;
  visa_baseline?: VisaBaseline;
  score: number;
  raw_provider_payload_ref?: string;
}

export interface SearchMeta {
  provider: string;
  cached: boolean;
  generated_at: string;
}

export interface SearchResponse {
  search_id: string;
  query: SearchRequest;
  results: Itinerary[];
  meta: SearchMeta;
}
