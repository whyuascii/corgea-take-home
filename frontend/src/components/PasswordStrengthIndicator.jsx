import { useMemo } from 'react'

const checks = [
  { label: '10+ characters', test: (pw) => pw.length >= 10 },
  { label: 'Contains uppercase letter', test: (pw) => /[A-Z]/.test(pw) },
  { label: 'Contains lowercase letter', test: (pw) => /[a-z]/.test(pw) },
  { label: 'Contains number', test: (pw) => /[0-9]/.test(pw) },
  { label: 'Contains special character', test: (pw) => /[^A-Za-z0-9]/.test(pw) },
]

function getBarColor(score) {
  if (score <= 1) return 'bg-red-500'
  if (score === 2) return 'bg-orange-500'
  if (score === 3) return 'bg-yellow-500'
  return 'bg-green-500'
}

function getStrengthLabel(score) {
  if (score <= 1) return 'Weak'
  if (score === 2) return 'Fair'
  if (score === 3) return 'Good'
  if (score === 4) return 'Strong'
  return 'Very Strong'
}

export default function PasswordStrengthIndicator({ password }) {
  const results = useMemo(() => {
    if (!password) return { score: 0, items: checks.map((c) => ({ ...c, passed: false })) }
    const items = checks.map((c) => ({ ...c, passed: c.test(password) }))
    const score = items.filter((i) => i.passed).length
    return { score, items }
  }, [password])

  if (!password) return null

  const { score, items } = results
  const widthPercent = (score / 5) * 100
  const barColor = getBarColor(score)
  const label = getStrengthLabel(score)

  return (
    <div className="mt-2 space-y-2">
      {/* Progress bar */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${barColor}`}
            style={{ width: `${widthPercent}%` }}
          />
        </div>
        <span className="text-xs text-gray-400 w-20 text-right">{label}</span>
      </div>

      {/* Checklist */}
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item.label} className="flex items-center gap-2 text-xs">
            {item.passed ? (
              <svg className="w-3.5 h-3.5 text-green-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5 text-gray-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <span className={item.passed ? 'text-gray-300' : 'text-gray-500'}>
              {item.label}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
