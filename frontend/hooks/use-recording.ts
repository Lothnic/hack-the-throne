"use client"

import { useCallback, useRef, useState } from "react"
import { BACKEND_URL } from "@/lib/config"

interface TranscriptionResult {
  text: string
  segments: number
  speaker_id: string | null
  name: string
  relationship: string
}

export function useRecording(streamRef: React.RefObject<MediaStream | null>) {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcription, setTranscription] = useState<string | null>(null)

  const startRecording = useCallback(() => {
    const stream = streamRef.current
    if (!stream) return

    audioChunksRef.current = []
    const audioStream = new MediaStream(stream.getAudioTracks())
    const mediaRecorder = new MediaRecorder(audioStream, { mimeType: "audio/webm" })

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data)
      }
    }

    mediaRecorder.onstop = async () => {
      setIsProcessing(true)
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })

      try {
        const formData = new FormData()
        formData.append("audio", audioBlob, "recording.webm")

        const response = await fetch(`${BACKEND_URL}/transcribe`, {
          method: "POST",
          body: formData,
        })

        if (response.ok) {
          const result: TranscriptionResult = await response.json()
          const displayName = result.name || "Unknown"
          const displayText = result.text || "No speech detected"

          setTranscription(`${displayName}: ${displayText}`)
          console.log("[Recording] Extracted name:", result.name, "| Relationship:", result.relationship)

          return result
        } else {
          setTranscription("Transcription failed")
        }
      } catch (err) {
        console.error("[Recording] Upload error:", err)
        setTranscription("Error processing audio")
      } finally {
        setIsProcessing(false)
      }
    }

    mediaRecorder.start()
    mediaRecorderRef.current = mediaRecorder
    setIsRecording(true)
    setTranscription(null)
    console.log("[Recording] Started")
  }, [streamRef])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current = null
      setIsRecording(false)
      console.log("[Recording] Stopped")
    }
  }, [isRecording])

  return {
    isRecording,
    isProcessing,
    transcription,
    setTranscription,
    startRecording,
    stopRecording,
  }
}
