import { useState } from 'react'

/* ------------------------------------------------------------------ */
/*  Reusable components                                                */
/* ------------------------------------------------------------------ */

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-gray-300 transition-colors"
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

function CodeBlock({ code }) {
  return (
    <div className="relative my-3">
      <CopyButton text={code} />
      <pre className="bg-gray-950 border border-gray-800 rounded-lg p-4 text-sm text-gray-300 overflow-x-auto font-mono">
        <code>{code}</code>
      </pre>
    </div>
  )
}

function TabBar({ tabs, active, onChange, size = 'md' }) {
  const pad = size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
  return (
    <div className="flex flex-wrap gap-1 mb-6">
      {tabs.map((t) => (
        <button
          key={t}
          onClick={() => onChange(t)}
          className={`${pad} rounded-lg font-medium transition-colors ${
            active === t
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          {t}
        </button>
      ))}
    </div>
  )
}

function Card({ children, className = '' }) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl p-6 ${className}`}>
      {children}
    </div>
  )
}

function SectionTitle({ children }) {
  return <h3 className="text-lg font-semibold text-white mb-3">{children}</h3>
}

function Tip({ variant = 'blue', children }) {
  const styles = {
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-300',
    yellow: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-300',
  }
  return (
    <div className={`border rounded-xl p-4 mt-4 ${styles[variant]}`}>
      <p className="text-sm">{children}</p>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Tab content sections                                               */
/* ------------------------------------------------------------------ */

function GettingStartedTab() {
  return (
    <div className="space-y-8">
      {/* Install Semgrep */}
      <Card>
        <SectionTitle>Install Semgrep</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">
          Semgrep Community Edition is free and open-source. Choose your preferred installation method:
        </p>

        <h4 className="text-sm font-semibold text-gray-300 mt-4 mb-1">pip (Recommended)</h4>
        <CodeBlock code="pip install semgrep" />

        <h4 className="text-sm font-semibold text-gray-300 mt-4 mb-1">Homebrew (macOS)</h4>
        <CodeBlock code="brew install semgrep" />

        <h4 className="text-sm font-semibold text-gray-300 mt-4 mb-1">Docker (no install needed)</h4>
        <CodeBlock code='docker run --rm -v "${PWD}:/src" semgrep/semgrep semgrep --config auto /src' />

        <p className="text-sm text-gray-300 mt-4">Verify your installation:</p>
        <CodeBlock code="semgrep --version" />
      </Card>

      {/* Run First Scan */}
      <Card>
        <SectionTitle>Run Your First Scan</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">
          Navigate to your project directory and run Semgrep with the{' '}
          <code className="bg-gray-800 px-1.5 py-0.5 rounded text-xs">--json</code> flag.
          VulnTracker requires JSON output.
        </p>

        <h4 className="text-sm font-semibold text-gray-300 mt-4 mb-1">Auto-detect rules for your languages</h4>
        <CodeBlock code="semgrep --config auto --json . > semgrep-results.json" />

        <h4 className="text-sm font-semibold text-gray-300 mt-4 mb-1">Security-focused scan</h4>
        <CodeBlock code="semgrep --config p/security-audit --json . > semgrep-results.json" />

        <h4 className="text-sm font-semibold text-gray-300 mt-4 mb-1">OWASP Top 10</h4>
        <CodeBlock code="semgrep --config p/owasp-top-ten --json . > semgrep-results.json" />

        <Tip variant="blue">
          <span className="font-semibold">Tip:</span> Exclude noisy directories with{' '}
          <code className="bg-gray-800 px-1 py-0.5 rounded text-xs">--exclude="node_modules/*"</code> and{' '}
          <code className="bg-gray-800 px-1 py-0.5 rounded text-xs">--exclude="vendor/*"</code>
        </Tip>
      </Card>

      {/* Upload Results */}
      <Card>
        <SectionTitle>Upload Results</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">You can push scan results two ways:</p>

        <h4 className="text-sm font-semibold text-gray-300 mt-2 mb-1">Option A: Upload via the UI</h4>
        <ol className="list-decimal list-inside text-gray-300 text-sm space-y-1 ml-2">
          <li>Go to your project's <strong className="text-white">Scans</strong> page</li>
          <li>Click <strong className="text-white">Upload Scan</strong></li>
          <li>
            Select your <code className="bg-gray-800 px-1 py-0.5 rounded text-xs">semgrep-results.json</code> file
          </li>
        </ol>

        <h4 className="text-sm font-semibold text-gray-300 mt-5 mb-1">Option B: Push via API (for automation)</h4>
        <p className="text-sm text-gray-300 mb-2">
          Find your API key in <strong className="text-white">Project Settings</strong>, then:
        </p>
        <CodeBlock
          code={`curl -X POST https://your-vulntracker-instance/api/projects/YOUR_PROJECT_SLUG/scans/push/ \\
  -H "Authorization: Api-Key YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d @semgrep-results.json`}
        />
      </Card>
    </div>
  )
}

/* ------------------------------------------------------------------ */

const CI_PROVIDERS = ['GitHub Actions', 'CircleCI', 'GitLab CI', 'Shell']

const CI_SNIPPETS = {
  'GitHub Actions': {
    filename: '.github/workflows/semgrep.yml',
    code: `name: Semgrep Security Scan
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Semgrep
        run: pip install semgrep

      - name: Run Semgrep
        run: semgrep --config auto --json . > results.json

      - name: Push to VulnTracker
        run: |
          curl -sf -X POST \${{ secrets.VULNTRACKER_URL }}/api/projects/\${{ secrets.VULNTRACKER_PROJECT_SLUG }}/scans/push/ \\
            -H "Authorization: Api-Key \${{ secrets.VULNTRACKER_API_KEY }}" \\
            -H "Content-Type: application/json" \\
            -d @results.json`,
  },
  CircleCI: {
    filename: '.circleci/config.yml',
    code: `version: 2.1
jobs:
  semgrep-scan:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run: pip install semgrep
      - run: semgrep --config auto --json . > results.json
      - run: |
          curl -sf -X POST \${VULNTRACKER_URL}/api/projects/\${VULNTRACKER_PROJECT_SLUG}/scans/push/ \\
            -H "Authorization: Api-Key \${VULNTRACKER_API_KEY}" \\
            -H "Content-Type: application/json" \\
            -d @results.json
workflows:
  security:
    jobs:
      - semgrep-scan`,
  },
  'GitLab CI': {
    filename: '.gitlab-ci.yml',
    code: `semgrep-scan:
  image: python:3.12-slim
  stage: test
  script:
    - pip install semgrep
    - semgrep --config auto --json . > results.json
    - |
      curl -sf -X POST "\${VULNTRACKER_URL}/api/projects/\${VULNTRACKER_PROJECT_SLUG}/scans/push/" \\
        -H "Authorization: Api-Key \${VULNTRACKER_API_KEY}" \\
        -H "Content-Type: application/json" \\
        -d @results.json
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'`,
  },
  Shell: {
    filename: 'scan.sh',
    code: `#!/bin/bash
set -euo pipefail

# Required environment variables:
#   VULNTRACKER_URL          - Your VulnTracker instance URL
#   VULNTRACKER_PROJECT_SLUG - Project slug from the URL
#   VULNTRACKER_API_KEY      - Project API key from Settings

semgrep --config auto --json . > /tmp/results.json

curl -sf -X POST "\${VULNTRACKER_URL}/api/projects/\${VULNTRACKER_PROJECT_SLUG}/scans/push/" \\
  -H "Authorization: Api-Key \${VULNTRACKER_API_KEY}" \\
  -H "Content-Type: application/json" \\
  -d @/tmp/results.json

echo "Scan results pushed successfully!"`,
  },
}

function CICDIntegrationTab() {
  const [provider, setProvider] = useState('GitHub Actions')
  const snippet = CI_SNIPPETS[provider]

  return (
    <div className="space-y-6">
      {/* Environment variables reference */}
      <Card>
        <SectionTitle>Required Environment Variables</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">
          Configure these secrets or environment variables in your CI provider before using the snippets below.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left text-gray-400 pb-2 pr-4">Variable</th>
                <th className="text-left text-gray-400 pb-2 pr-4">Example</th>
                <th className="text-left text-gray-400 pb-2">Description</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              <tr className="border-b border-gray-800/50">
                <td className="py-2 pr-4 font-mono text-xs text-indigo-400">VULNTRACKER_URL</td>
                <td className="py-2 pr-4 font-mono text-xs text-gray-500">https://vulntracker.example.com</td>
                <td className="py-2">Base URL of your VulnTracker instance</td>
              </tr>
              <tr className="border-b border-gray-800/50">
                <td className="py-2 pr-4 font-mono text-xs text-indigo-400">VULNTRACKER_PROJECT_SLUG</td>
                <td className="py-2 pr-4 font-mono text-xs text-gray-500">YOUR_PROJECT_SLUG</td>
                <td className="py-2">Project slug (visible in the project URL)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-mono text-xs text-indigo-400">VULNTRACKER_API_KEY</td>
                <td className="py-2 pr-4 font-mono text-xs text-gray-500">YOUR_API_KEY</td>
                <td className="py-2">Project API key from Settings page</td>
              </tr>
            </tbody>
          </table>
        </div>
        <Tip variant="yellow">
          <span className="font-semibold">Security:</span> Never hard-code API keys in your CI config files.
          Always use your CI provider's secrets management.
        </Tip>
      </Card>

      {/* Provider-specific snippets */}
      <Card>
        <SectionTitle>Pipeline Configuration</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">
          Select your CI provider below, then copy the config into your repository.
        </p>

        <TabBar tabs={CI_PROVIDERS} active={provider} onChange={setProvider} size="sm" />

        <div className="mb-2 flex items-center gap-2">
          <span className="text-xs text-gray-500">File:</span>
          <code className="bg-gray-800 px-2 py-0.5 rounded text-xs text-indigo-400">{snippet.filename}</code>
        </div>

        <CodeBlock code={snippet.code} />
      </Card>
    </div>
  )
}

/* ------------------------------------------------------------------ */

function APIReferenceTab() {
  return (
    <div className="space-y-8">
      {/* Push endpoint */}
      <Card>
        <SectionTitle>Push Scan Results</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">
          Upload Semgrep JSON output for a project. This creates a new scan and imports all findings.
        </p>

        <div className="flex items-center gap-3 mb-4">
          <span className="bg-green-600/20 text-green-400 text-xs font-bold px-2.5 py-1 rounded">POST</span>
          <code className="text-sm text-gray-300 font-mono">
            /api/projects/<span className="text-indigo-400">{'YOUR_PROJECT_SLUG'}</span>/scans/push/
          </code>
        </div>

        <h4 className="text-sm font-semibold text-gray-300 mb-2">Headers</h4>
        <div className="overflow-x-auto mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left text-gray-400 pb-2 pr-4">Header</th>
                <th className="text-left text-gray-400 pb-2 pr-4">Value</th>
                <th className="text-left text-gray-400 pb-2">Required</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              <tr className="border-b border-gray-800/50">
                <td className="py-2 pr-4 font-mono text-xs text-indigo-400">Authorization</td>
                <td className="py-2 pr-4 font-mono text-xs">Api-Key YOUR_API_KEY</td>
                <td className="py-2 text-green-400">Yes</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-mono text-xs text-indigo-400">Content-Type</td>
                <td className="py-2 pr-4 font-mono text-xs">application/json</td>
                <td className="py-2 text-green-400">Yes</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h4 className="text-sm font-semibold text-gray-300 mb-2">Request Body</h4>
        <p className="text-sm text-gray-300 mb-2">
          The request body must be the raw Semgrep JSON output (the contents of the file produced by{' '}
          <code className="bg-gray-800 px-1 py-0.5 rounded text-xs">semgrep --json</code>).
        </p>

        <h4 className="text-sm font-semibold text-gray-300 mt-4 mb-2">Example</h4>
        <CodeBlock
          code={`curl -X POST https://your-vulntracker-instance/api/projects/YOUR_PROJECT_SLUG/scans/push/ \\
  -H "Authorization: Api-Key YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d @semgrep-results.json`}
        />

        <h4 className="text-sm font-semibold text-gray-300 mt-4 mb-2">Responses</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left text-gray-400 pb-2 pr-4">Status</th>
                <th className="text-left text-gray-400 pb-2">Description</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              <tr className="border-b border-gray-800/50">
                <td className="py-2 pr-4 font-mono text-xs text-green-400">201 Created</td>
                <td className="py-2">Scan created successfully. Response includes scan ID and finding counts.</td>
              </tr>
              <tr className="border-b border-gray-800/50">
                <td className="py-2 pr-4 font-mono text-xs text-yellow-400">400 Bad Request</td>
                <td className="py-2">Invalid JSON payload or missing required Semgrep fields.</td>
              </tr>
              <tr className="border-b border-gray-800/50">
                <td className="py-2 pr-4 font-mono text-xs text-red-400">401 Unauthorized</td>
                <td className="py-2">Missing or invalid API key.</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-mono text-xs text-red-400">404 Not Found</td>
                <td className="py-2">Project slug does not exist.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      {/* Authentication */}
      <Card>
        <SectionTitle>Authentication</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">
          VulnTracker uses project-scoped API keys for machine-to-machine authentication. Every API request
          must include the key in the <code className="bg-gray-800 px-1 py-0.5 rounded text-xs">Authorization</code> header.
        </p>

        <h4 className="text-sm font-semibold text-gray-300 mb-2">Header Format</h4>
        <CodeBlock code="Authorization: Api-Key YOUR_API_KEY" />

        <p className="text-sm text-gray-300 mt-4">
          You can find or regenerate your API key on your project's <strong className="text-white">Settings</strong> page.
          Each project has its own unique key.
        </p>
      </Card>
    </div>
  )
}

/* ------------------------------------------------------------------ */

function ManagingFindingsTab() {
  return (
    <div className="space-y-8">
      {/* False Positives */}
      <Card>
        <SectionTitle>Handling False Positives</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">
          Not every finding is a real vulnerability. VulnTracker lets you triage findings to keep your dashboard clean.
        </p>
        <ol className="list-decimal list-inside text-gray-300 text-sm space-y-2 ml-2">
          <li>
            Open a finding from the <strong className="text-white">Findings</strong> list.
          </li>
          <li>
            Review the code context, rule description, and severity.
          </li>
          <li>
            Change the status to <strong className="text-white">False Positive</strong> if the finding is not applicable.
          </li>
          <li>
            Add a note explaining why it was marked as a false positive for future reference.
          </li>
        </ol>
        <Tip variant="blue">
          <span className="font-semibold">Tip:</span> If a rule consistently produces false positives for your codebase,
          consider disabling it in the <strong className="text-white">Rules</strong> page instead of triaging each finding individually.
        </Tip>
      </Card>

      {/* Bulk Actions */}
      <Card>
        <SectionTitle>Bulk Actions</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">
          The Findings page supports bulk operations to help you triage at scale.
        </p>
        <ol className="list-decimal list-inside text-gray-300 text-sm space-y-2 ml-2">
          <li>
            Use the checkboxes on the <strong className="text-white">Findings</strong> page to select multiple findings.
          </li>
          <li>
            Use the bulk action toolbar that appears to change status or severity for all selected items at once.
          </li>
          <li>
            Filter findings by severity, status, or rule before selecting to target specific groups efficiently.
          </li>
        </ol>
      </Card>

      {/* Rules Management */}
      <Card>
        <SectionTitle>Rules Management</SectionTitle>
        <p className="text-sm text-gray-300 mb-4">
          Rules control which Semgrep patterns are tracked in your project. Use the Rules page to customize behavior.
        </p>
        <ol className="list-decimal list-inside text-gray-300 text-sm space-y-2 ml-2">
          <li>
            Navigate to the <strong className="text-white">Rules</strong> page from the project navigation.
          </li>
          <li>
            Each rule shows its ID, severity, and the number of findings it has generated.
          </li>
          <li>
            <strong className="text-white">Disable</strong> a rule to stop it from creating new findings in future scans.
            Existing findings from a disabled rule remain in your history.
          </li>
          <li>
            <strong className="text-white">Change severity</strong> to override the default severity assigned by Semgrep
            (e.g., downgrade an informational rule or escalate a critical one).
          </li>
        </ol>
        <Tip variant="yellow">
          <span className="font-semibold">Note:</span> Disabling a rule only affects future scans.
          Findings already imported from previous scans will not be removed.
        </Tip>
      </Card>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main HowTo page                                                    */
/* ------------------------------------------------------------------ */

const TABS = ['Getting Started', 'CI/CD Integration', 'API Reference', 'Managing Findings']

export default function HowTo() {
  const [activeTab, setActiveTab] = useState('Getting Started')

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-white mb-2">How To Use VulnTracker</h1>
      <p className="text-gray-400 mb-8">
        Everything you need to set up Semgrep scanning, integrate with your CI/CD pipeline, and manage findings.
      </p>

      <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} />

      {activeTab === 'Getting Started' && <GettingStartedTab />}
      {activeTab === 'CI/CD Integration' && <CICDIntegrationTab />}
      {activeTab === 'API Reference' && <APIReferenceTab />}
      {activeTab === 'Managing Findings' && <ManagingFindingsTab />}
    </div>
  )
}
