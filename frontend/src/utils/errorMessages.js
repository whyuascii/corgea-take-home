/**
 * Extract a human-readable error message from a DRF error response.
 *
 * Handles the following shapes returned by Django REST Framework:
 *   - { error: "string" }
 *   - { detail: "string" }
 *   - { field1: ["err", ...], field2: ["err", ...] }  (field errors object)
 *   - ["err1", "err2"]  (array of strings)
 *
 * @param {Error} error  - Axios error (or any error with response.data)
 * @param {string} fallback - Fallback message when nothing useful can be extracted
 * @returns {string}
 */
export function getErrorMessage(error, fallback = 'An unexpected error occurred') {
  if (!error?.response?.data) {
    return fallback
  }

  const data = error.response.data

  // { error: "..." }
  if (typeof data.error === 'string') {
    return data.error
  }

  // { detail: "..." }
  if (typeof data.detail === 'string') {
    return data.detail
  }

  // Array of strings: ["err1", "err2"]
  if (Array.isArray(data)) {
    const messages = data.filter((item) => typeof item === 'string')
    if (messages.length > 0) {
      return messages.join(' ')
    }
    return fallback
  }

  // Object with field errors: { field: ["err", ...], ... }
  if (typeof data === 'object' && data !== null) {
    const fieldMessages = []
    for (const key of Object.keys(data)) {
      const value = data[key]
      if (Array.isArray(value) && value.length > 0) {
        fieldMessages.push(String(value[0]))
      } else if (typeof value === 'string') {
        fieldMessages.push(value)
      }
    }
    if (fieldMessages.length > 0) {
      return fieldMessages.join(' ')
    }
  }

  return fallback
}

/**
 * Extract field-level errors from a DRF error response.
 *
 * @param {Error} error - Axios error
 * @returns {Object} Mapping of field names to arrays of error strings, e.g.
 *   { email: ["This field is required."], password: ["Too short."] }
 */
export function getFieldErrors(error) {
  if (!error?.response?.data) {
    return {}
  }

  const data = error.response.data

  if (typeof data !== 'object' || data === null || Array.isArray(data)) {
    return {}
  }

  const fields = {}
  for (const [key, value] of Object.entries(data)) {
    // Skip non-field keys like "detail" or "error"
    if (key === 'detail' || key === 'error') continue

    if (Array.isArray(value)) {
      fields[key] = value.map(String)
    } else if (typeof value === 'string') {
      fields[key] = [value]
    }
  }

  return fields
}
