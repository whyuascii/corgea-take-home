/**
 * Extract results from API response, handling both paginated and flat formats.
 * Paginated: { count, next, previous, results: [...] }
 * Flat: [...]
 */
export function extractResults(data) {
  if (Array.isArray(data)) return { results: data, count: data.length, next: null, previous: null }
  if (data && typeof data === 'object' && 'results' in data) return data
  return { results: [], count: 0, next: null, previous: null }
}

export function getTotalPages(count, pageSize = 25) {
  return Math.max(1, Math.ceil(count / pageSize))
}
