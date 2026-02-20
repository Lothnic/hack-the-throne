"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { BACKEND_URL } from "@/lib/config"

interface PersonData {
  name: string
  description: string
  relationship: string
  person_id?: string
}

interface SSEMessage {
  name: string
  description: string
  relationship: string
  person_id?: string
}

export function useInferenceSSE() {
  const eventSourceRef = useRef<EventSource | null>(null)
  const [latestPersonData, setLatestPersonData] = useState<PersonData | null>(null)
  const [activeSpeaker, setActiveSpeaker] = useState<PersonData | null>(null)

  const connectSSE = useCallback(() => {
    try {
      const es = new EventSource(`${BACKEND_URL}/stream/inference`)

      console.log("[SSE] Connecting to:", `${BACKEND_URL}/stream/inference`)

      es.onopen = () => {
        console.log("[SSE] Connected")
      }

      es.addEventListener("inference", (event) => {
        try {
          const message: SSEMessage = JSON.parse(event.data)
          console.log("[SSE] Received inference event:", message)

          if (message.name && message.description && message.relationship) {
            const personData: PersonData = {
              name: message.name,
              description: message.description,
              relationship: message.relationship,
              person_id: message.person_id,
            }
            setLatestPersonData(personData)
            setActiveSpeaker(personData)
          }
        } catch (err) {
          console.error("[SSE] Error parsing message:", err)
        }
      })

      es.onerror = (error) => {
        console.error("[SSE] Error:", error)
      }

      eventSourceRef.current = es
    } catch (err) {
      console.error("[SSE] Connection error:", err)
    }
  }, [])

  const disconnectSSE = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      disconnectSSE()
    }
  }, [disconnectSSE])

  return {
    latestPersonData,
    activeSpeaker,
    setActiveSpeaker,
    setLatestPersonData,
    connectSSE,
    disconnectSSE,
  }
}
