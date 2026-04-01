import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function getInitials(user) {
  if (!user) return '?'
  // If user has first_name and last_name, use those initials
  if (user.first_name && user.last_name) {
    return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
  }
  // If user has a full name field
  if (user.name) {
    const parts = user.name.trim().split(/\s+/)
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
    }
    return parts[0][0].toUpperCase()
  }
  // Fall back to first letter of username
  if (user.username) {
    return user.username[0].toUpperCase()
  }
  return '?'
}

export default function UserDropdown() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const initials = getInitials(user)

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-500 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900"
        aria-label="User menu"
      >
        {initials}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50 overflow-hidden">
          {/* User info section */}
          <div className="px-4 py-3 border-b border-gray-800">
            <p className="text-sm font-medium text-white truncate">
              {user?.first_name && user?.last_name
                ? `${user.first_name} ${user.last_name}`
                : user?.username}
            </p>
            {user?.email && (
              <p className="text-xs text-gray-400 truncate mt-0.5">{user.email}</p>
            )}
          </div>

          {/* Menu items */}
          <div className="py-1">
            <Link
              to="/settings/account"
              onClick={() => setOpen(false)}
              className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
            >
              Account Settings
            </Link>
            <Link
              to="/settings/account#password"
              onClick={() => setOpen(false)}
              className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
            >
              Change Password
            </Link>
          </div>

          {/* Divider + Logout */}
          <div className="border-t border-gray-800 py-1">
            <button
              onClick={() => {
                setOpen(false)
                logout()
              }}
              className="block w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
