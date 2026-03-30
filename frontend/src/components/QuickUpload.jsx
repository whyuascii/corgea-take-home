import { useState, useRef } from 'react'
import api from '../api/client'

export default function QuickUpload({ slug, onUploadComplete }) {
  const fileInputRef = useRef(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  const handleUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      await api.post(`/projects/${slug}/scans/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      if (onUploadComplete) onUploadComplete()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  return (
    <div className="mb-6">
      <div
        className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${
          uploading
            ? 'border-indigo-500 bg-indigo-500/5'
            : 'border-gray-700 hover:border-indigo-500'
        }`}
      >
        <label className="cursor-pointer">
          <div className="flex flex-col items-center gap-1">
            <svg
              className="w-8 h-8 text-gray-500 mb-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
              />
            </svg>
            {uploading ? (
              <p className="text-indigo-400 text-sm font-medium">Uploading...</p>
            ) : (
              <>
                <p className="text-gray-400 text-sm">
                  Drop a Semgrep JSON report or click to upload
                </p>
                <p className="text-indigo-400 text-sm font-medium">Browse Files</p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>
      </div>
      {error && (
        <p className="text-red-400 text-sm mt-2">{error}</p>
      )}
    </div>
  )
}
