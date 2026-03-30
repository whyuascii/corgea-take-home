function RiskBadge({ label, value }) {
  if (!value) return null
  const colorClass =
    value === 'HIGH' ? 'bg-red-500/20 text-red-400' :
    value === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
    'bg-green-500/20 text-green-400'
  return (
    <div>
      <span className="text-gray-500 text-xs">{label}</span>
      <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>{value}</span>
    </div>
  )
}

export default function SecurityDetails({ metadata }) {
  if (!metadata || Object.keys(metadata).length === 0) return null

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6">
      <h2 className="text-sm font-medium text-gray-400 mb-3">Security Details</h2>

      {/* Risk Assessment */}
      {(metadata.likelihood || metadata.impact || metadata.confidence) && (
        <div className="flex gap-4">
          <RiskBadge label="Likelihood" value={metadata.likelihood} />
          <RiskBadge label="Impact" value={metadata.impact} />
          <RiskBadge label="Confidence" value={metadata.confidence} />
        </div>
      )}

      {/* CWE badges */}
      {metadata.cwe?.length > 0 && (
        <div className="mt-3">
          <span className="text-gray-500 text-xs block mb-1">CWE</span>
          <div className="flex flex-wrap gap-1">
            {metadata.cwe.map((c) => (
              <span key={c} className="px-2 py-0.5 bg-orange-500/10 text-orange-400 rounded text-xs">{c}</span>
            ))}
          </div>
        </div>
      )}

      {/* OWASP badges */}
      {metadata.owasp?.length > 0 && (
        <div className="mt-3">
          <span className="text-gray-500 text-xs block mb-1">OWASP</span>
          <div className="flex flex-wrap gap-1">
            {metadata.owasp.map((o) => (
              <span key={o} className="px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded text-xs">{o}</span>
            ))}
          </div>
        </div>
      )}

      {/* References */}
      {metadata.references?.length > 0 && (
        <div className="mt-3">
          <span className="text-gray-500 text-xs block mb-1">References</span>
          {metadata.references.map((ref) => (
            <a key={ref} href={ref} target="_blank" rel="noreferrer"
              className="text-indigo-400 text-xs hover:underline block truncate">{ref}</a>
          ))}
        </div>
      )}

      {/* Suggested Fix */}
      {metadata.fix && (
        <div className="mt-4">
          <span className="text-gray-500 text-xs block mb-1">Suggested Fix</span>
          <pre className="bg-green-500/5 border border-green-500/20 rounded-lg p-3 text-sm text-green-300 font-mono overflow-x-auto">{metadata.fix}</pre>
        </div>
      )}

      {/* Technology tags and Vulnerability class */}
      {(metadata.technology?.length > 0 || metadata.vulnerability_class?.length > 0) && (
        <div className="flex flex-wrap gap-2 mt-3">
          {metadata.technology?.map((t) => (
            <span key={t} className="px-2 py-0.5 bg-gray-800 text-gray-400 rounded text-xs">{t}</span>
          ))}
          {metadata.vulnerability_class?.map((v) => (
            <span key={v} className="px-2 py-0.5 bg-gray-800 text-gray-400 rounded text-xs">{v}</span>
          ))}
        </div>
      )}

      {/* Source link */}
      {metadata.source && (
        <a href={metadata.source} target="_blank" rel="noreferrer"
          className="text-indigo-400 text-xs hover:underline mt-2 inline-block">
          View rule documentation &rarr;
        </a>
      )}
    </div>
  )
}
