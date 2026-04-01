import { useState, useEffect, useRef, useCallback } from 'react'

const WARNING_TIME = 25 * 60 * 1000  // 25 minutes
const LOGOUT_TIME = 30 * 60 * 1000   // 30 minutes

/**
 * Hook that tracks user activity and triggers a warning before auto-logout.
 *
 * After 25 minutes of inactivity, `showWarning` becomes true.
 * After 30 minutes of inactivity, `onLogout` is called.
 *
 * @param {Function} onLogout - Called when the session expires
 * @returns {{ showWarning: boolean, resetTimer: Function, timeRemaining: number }}
 */
export default function useSessionTimeout(onLogout) {
  const [showWarning, setShowWarning] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(5 * 60)

  const warningTimerRef = useRef(null)
  const logoutTimerRef = useRef(null)
  const countdownRef = useRef(null)
  const lastActivityRef = useRef(Date.now())
  const showWarningRef = useRef(false)
  const onLogoutRef = useRef(onLogout)

  // Keep refs in sync
  useEffect(() => { showWarningRef.current = showWarning }, [showWarning])
  useEffect(() => { onLogoutRef.current = onLogout }, [onLogout])

  const clearAllTimers = useCallback(() => {
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current)
      warningTimerRef.current = null
    }
    if (logoutTimerRef.current) {
      clearTimeout(logoutTimerRef.current)
      logoutTimerRef.current = null
    }
    if (countdownRef.current) {
      clearInterval(countdownRef.current)
      countdownRef.current = null
    }
  }, [])

  const startCountdown = useCallback(() => {
    const elapsed = Date.now() - lastActivityRef.current
    const remaining = Math.max(0, Math.ceil((LOGOUT_TIME - elapsed) / 1000))
    setTimeRemaining(remaining)

    countdownRef.current = setInterval(() => {
      const now = Date.now()
      const elapsedNow = now - lastActivityRef.current
      const secs = Math.max(0, Math.ceil((LOGOUT_TIME - elapsedNow) / 1000))
      setTimeRemaining(secs)

      if (secs <= 0) {
        clearInterval(countdownRef.current)
        countdownRef.current = null
      }
    }, 1000)
  }, [])

  const startTimers = useCallback(() => {
    clearAllTimers()
    lastActivityRef.current = Date.now()

    warningTimerRef.current = setTimeout(() => {
      setShowWarning(true)
      startCountdown()
    }, WARNING_TIME)

    logoutTimerRef.current = setTimeout(() => {
      clearAllTimers()
      setShowWarning(false)
      onLogoutRef.current?.()
    }, LOGOUT_TIME)
  }, [clearAllTimers, startCountdown])

  const resetTimer = useCallback(() => {
    setShowWarning(false)
    setTimeRemaining(5 * 60)
    startTimers()
  }, [startTimers])

  useEffect(() => {
    const activityEvents = ['mousemove', 'keydown', 'click']

    let activityDebounce = null
    const debouncedHandler = () => {
      if (activityDebounce) return
      activityDebounce = setTimeout(() => {
        activityDebounce = null
      }, 1000)
      // Use ref to avoid stale closure
      if (!showWarningRef.current) {
        lastActivityRef.current = Date.now()
        clearAllTimers()
        startTimers()
      }
    }

    activityEvents.forEach((event) => {
      window.addEventListener(event, debouncedHandler)
    })

    startTimers()

    return () => {
      activityEvents.forEach((event) => {
        window.removeEventListener(event, debouncedHandler)
      })
      clearAllTimers()
      if (activityDebounce) clearTimeout(activityDebounce)
    }
  }, [clearAllTimers, startTimers])

  return { showWarning, resetTimer, timeRemaining }
}
