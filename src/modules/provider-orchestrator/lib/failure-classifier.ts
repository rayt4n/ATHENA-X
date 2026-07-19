/**
 * Failure Type Classifier — categorizes every failure into one of 9 types.
 * Only some failure types count against certification.
 *
 * | Category                | Counts Against Certification? |
 * |------------------------|------------------------------|
 * | valid_response          | No (success)                  |
 * | expected_empty          | No (market closed)            |
 * | timeout                 | Yes                           |
 * | http_429                | Yes                           |
 * | http_403                | Yes                           |
 * | malformed_json          | Yes                           |
 * | invalid_ohlc            | Yes                           |
 * | missing_candle          | Yes                           |
 * | duplicate_timestamp     | Yes                           |
 */

export type FailureType =
  | "valid_response"
  | "expected_empty"
  | "timeout"
  | "http_429"
  | "http_403"
  | "http_5xx"
  | "connection_error"
  | "malformed_json"
  | "invalid_ohlc"
  | "missing_candle"
  | "duplicate_timestamp";

export interface FailureClassification {
  type: FailureType;
  countsAgainstCert: boolean;
  description: string;
}

const FAILURE_META: Record<FailureType, { counts: boolean; desc: string }> = {
  valid_response:     { counts: false, desc: "Valid response with data" },
  expected_empty:     { counts: false, desc: "Empty payload — market closed (expected)" },
  timeout:            { counts: true,  desc: "Request timed out" },
  http_429:           { counts: true,  desc: "Rate limited (HTTP 429)" },
  http_403:           { counts: true,  desc: "Forbidden / IP blocked (HTTP 403)" },
  http_5xx:           { counts: true,  desc: "Server error (HTTP 5xx)" },
  connection_error:   { counts: true,  desc: "Connection reset or network error" },
  malformed_json:     { counts: true,  desc: "Response is not valid JSON" },
  invalid_ohlc:       { counts: true,  desc: "OHLC values fail sanity checks" },
  missing_candle:     { counts: true,  desc: "Gap in candle sequence" },
  duplicate_timestamp:{ counts: true,  desc: "Duplicate timestamp in data" },
};

export function classifyFailure(
  httpStatus: number | null,
  errorMessage: string | null,
  emptyPayload: boolean,
  marketOpen: boolean
): FailureClassification {
  // If HTTP status is known
  if (httpStatus === 429) return { type: "http_429", countsAgainstCert: true, description: FAILURE_META.http_429.desc };
  if (httpStatus === 403) return { type: "http_403", countsAgainstCert: true, description: FAILURE_META.http_403.desc };
  if (httpStatus && httpStatus >= 500) return { type: "http_5xx", countsAgainstCert: true, description: FAILURE_META.http_5xx.desc };

  // If error message indicates timeout
  if (errorMessage && /timeout|timed out|deadline/i.test(errorMessage)) {
    return { type: "timeout", countsAgainstCert: true, description: FAILURE_META.timeout.desc };
  }

  // If error message indicates connection issue
  if (errorMessage && /connection|reset|econnrefused|socket/i.test(errorMessage)) {
    return { type: "connection_error", countsAgainstCert: true, description: FAILURE_META.connection_error.desc };
  }

  // If error message indicates JSON parse issue
  if (errorMessage && /json|parse|unexpected token/i.test(errorMessage)) {
    return { type: "malformed_json", countsAgainstCert: true, description: FAILURE_META.malformed_json.desc };
  }

  // Empty payload
  if (emptyPayload) {
    if (!marketOpen) {
      return { type: "expected_empty", countsAgainstCert: false, description: FAILURE_META.expected_empty.desc };
    }
    // Empty when market is open — counts as a failure
    return { type: "missing_candle", countsAgainstCert: true, description: "Empty payload during market hours" };
  }

  // Default to connection error
  return { type: "connection_error", countsAgainstCert: true, description: errorMessage ?? "Unknown error" };
}

export function getFailureMeta(type: FailureType): { counts: boolean; desc: string } {
  return FAILURE_META[type] ?? FAILURE_META.connection_error;
}

export interface FailureTypeCounts {
  valid_response: number;
  expected_empty: number;
  timeout: number;
  http_429: number;
  http_403: number;
  http_5xx: number;
  connection_error: number;
  malformed_json: number;
  invalid_ohlc: number;
  missing_candle: number;
  duplicate_timestamp: number;
}

export function createEmptyFailureCounts(): FailureTypeCounts {
  return {
    valid_response: 0,
    expected_empty: 0,
    timeout: 0,
    http_429: 0,
    http_403: 0,
    http_5xx: 0,
    connection_error: 0,
    malformed_json: 0,
    invalid_ohlc: 0,
    missing_candle: 0,
    duplicate_timestamp: 0,
  };
}

export function getCertRelevantFailures(counts: FailureTypeCounts): number {
  return counts.timeout + counts.http_429 + counts.http_403 + counts.http_5xx +
    counts.connection_error + counts.malformed_json + counts.invalid_ohlc +
    counts.missing_candle + counts.duplicate_timestamp;
}
