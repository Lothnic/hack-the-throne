"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Mic, MicOff, Video, VideoOff, Circle, Square, Loader2 } from "lucide-react"
import { FaceNotification } from "@/components/face-notification"
import { useFaceDetection } from "@/hooks/use-face-detection"
import { useWebRTC } from "@/hooks/use-webrtc"
import { useRecording } from "@/hooks/use-recording"
import { useInferenceSSE } from "@/hooks/use-inference-sse"
import { cn } from "@/lib/utils"
import {
  calculateVideoTransform,
  mapBoundingBoxToOverlay,
  calculateNotificationPosition,
} from "@/lib/coordinate-mapper"
import PersonContextCard from "./PersonContextCard"

interface PersonData {
  name: string
  description: string
  relationship: string
  person_id?: string
}

type FacePersonMap = Map<string, PersonData>

export default function WebcamStream() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const overlayRef = useRef<HTMLDivElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isVideoReady, setIsVideoReady] = useState(false)
  const [facePersonData, setFacePersonData] = useState<FacePersonMap>(new Map())
  const [isMuted, setIsMuted] = useState(false)

  const { isConnected, setupWebRTC, closeConnection } = useWebRTC()
  const { isRecording, isProcessing, transcription, setTranscription, startRecording, stopRecording } = useRecording(streamRef)
  const { latestPersonData, activeSpeaker, setActiveSpeaker, setLatestPersonData, connectSSE, disconnectSSE } = useInferenceSSE()

  const { detectedFaces, isLoading: isFaceDetectionLoading, error: faceDetectionError } = useFaceDetection(
    videoRef.current,
    {
      enabled: isStreaming && isVideoReady,
      minDetectionConfidence: 0.5,
      targetFps: 20,
      useWorker: true,
    }
  )

  useEffect(() => {
    if (!latestPersonData || detectedFaces.length === 0) {
      return
    }

    const mostProminentFace = detectedFaces.reduce((prev, current) => {
      const prevScore = (prev.boundingBox.width * prev.boundingBox.height) * prev.confidence
      const currentScore = (current.boundingBox.width * current.boundingBox.height) * current.confidence
      return currentScore > prevScore ? current : prev
    })

    setFacePersonData((prev) => {
      const newMap = new Map(prev)
      newMap.set(mostProminentFace.id, latestPersonData)
      return newMap
    })

    console.log(`[FaceDetection] Associated "${latestPersonData.name}" with face ${mostProminentFace.id}`)
    setLatestPersonData(null)
  }, [latestPersonData, detectedFaces, setLatestPersonData])

  useEffect(() => {
    const currentFaceIds = new Set(detectedFaces.map((f) => f.id))
    setFacePersonData((prev) => {
      const newMap = new Map(prev)
      for (const faceId of newMap.keys()) {
        if (!currentFaceIds.has(faceId)) {
          newMap.delete(faceId)
        }
      }
      return newMap
    })
  }, [detectedFaces])

  useEffect(() => {
    startWebcam()
    connectSSE()

    return () => {
      stopWebcam()
      disconnectSSE()
    }
  }, [connectSSE, disconnectSSE])

  const startWebcam = async () => {
    try {
      console.log("[Webcam] Requesting media access...")
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: true,
      })

      if (videoRef.current) {
        const video = videoRef.current

        const handleMetadataLoaded = () => {
          console.log("[Webcam] Video metadata loaded:", {
            width: video.videoWidth,
            height: video.videoHeight,
          })
          setIsVideoReady(true)
        }

        video.addEventListener("loadedmetadata", handleMetadataLoaded)

        if (video.videoWidth > 0 && video.videoHeight > 0) {
          handleMetadataLoaded()
        }

        video.srcObject = stream
        streamRef.current = stream
        stream.getAudioTracks().forEach((track) => {
          track.enabled = !isMuted
        })
        setIsStreaming(true)
        console.log("[Webcam] Stream started")

        setTimeout(() => setupWebRTC(stream), 1000)
      }
    } catch (err) {
      console.error("[Webcam] Error accessing webcam:", err)
    }
  }

  const stopWebcam = () => {
    console.log("[Webcam] Stopping stream")

    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream
      stream.getTracks().forEach((track) => track.stop())
      videoRef.current.srcObject = null
    }

    closeConnection()

    streamRef.current = null
    setIsStreaming(false)
    setIsVideoReady(false)
    setIsMuted(false)
    setActiveSpeaker(null)
  }

  const toggleMute = useCallback(() => {
    const stream = streamRef.current
    if (!stream) {
      return
    }
    setIsMuted((prev) => {
      const next = !prev
      stream.getAudioTracks().forEach((track) => {
        track.enabled = !next
      })
      return next
    })
  }, [])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        e.preventDefault()
        if (isRecording) {
          stopRecording()
        } else if (!isProcessing && isStreaming) {
          startRecording()
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isRecording, isProcessing, isStreaming, startRecording, stopRecording])

  const faceNotifications = detectedFaces
    .map((face) => {
      const video = videoRef.current
      const overlay = overlayRef.current

      if (!video || !overlay) return null

      const videoWidth = video.videoWidth
      const videoHeight = video.videoHeight
      const overlayWidth = overlay.clientWidth
      const overlayHeight = overlay.clientHeight

      if (videoWidth === 0 || videoHeight === 0) return null

      const transform = calculateVideoTransform(videoWidth, videoHeight, overlayWidth, overlayHeight)

      const overlayBox = mapBoundingBoxToOverlay(face.boundingBox, transform, overlayWidth, true)

      const position = calculateNotificationPosition(overlayBox, overlayWidth, overlayHeight)

      return {
        face,
        position,
      }
    })
    .filter((n) => n !== null)

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={cn("absolute inset-0 h-full w-full object-cover transition-all duration-300", "scale-100")}
        style={{ transform: "scaleX(-1)" }}
      />

      <PersonContextCard
        speakerId={activeSpeaker?.person_id || null}
        speakerName={activeSpeaker?.name || null}
      />

      <div ref={overlayRef} className="absolute inset-0 pointer-events-none">
        {faceNotifications.map((notification) => {
          const person = facePersonData.get(notification!.face.id)
          return (
            <FaceNotification
              key={notification!.face.id}
              faceId={notification!.face.id}
              left={notification!.position.left}
              top={notification!.position.top}
              confidence={notification!.face.confidence}
              name={person?.name}
              description={person?.description}
              relationship={person?.relationship}
            />
          )
        })}
      </div>

      <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-2 bg-black/60 backdrop-blur-sm rounded-full">
        <div
          className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"} ${isConnected ? "animate-pulse" : ""}`}
        />
        <span className="text-xs text-white/80">{isConnected ? "Connected (WebRTC)" : "Disconnected"}</span>
      </div>

      {isFaceDetectionLoading && (
        <div className="absolute top-4 left-4 px-3 py-2 bg-black/60 backdrop-blur-sm rounded-full">
          <span className="text-xs text-white/80">Loading face detection...</span>
        </div>
      )}
      {faceDetectionError && (
        <div className="absolute top-4 left-4 px-3 py-2 bg-red-500/60 backdrop-blur-sm rounded-full">
          <span className="text-xs text-white/80">Face detection error</span>
        </div>
      )}

      <div className="absolute bottom-0 left-0 right-0 flex flex-col items-center px-6 py-4 bg-gradient-to-t from-black/80 to-transparent">
        {(transcription || isProcessing) && (
          <div className="mb-4 px-4 py-3 bg-black/70 backdrop-blur-sm rounded-lg max-w-lg w-full">
            {isProcessing ? (
              <div className="flex items-center gap-2 text-white/80">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Processing audio...</span>
              </div>
            ) : (
              <p className="text-sm text-white">{transcription}</p>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <Button
            size="icon"
            variant={isRecording ? "destructive" : "default"}
            onClick={isRecording ? stopRecording : startRecording}
            className={cn(
              "h-14 w-14 rounded-full transition-all",
              isRecording && "animate-pulse ring-2 ring-red-500 ring-offset-2 ring-offset-black"
            )}
            disabled={!isStreaming || isProcessing}
          >
            {isRecording ? <Square className="h-5 w-5 fill-current" /> : <Circle className="h-6 w-6 fill-red-500 text-red-500" />}
          </Button>
          <span className="text-sm text-white/80 min-w-[80px]">
            {isRecording ? "Stop" : isProcessing ? "Processing..." : "Record"}
          </span>

          <Button
            size="icon"
            variant={isMuted ? "default" : "secondary"}
            onClick={toggleMute}
            className="h-12 w-12 rounded-full"
            disabled={!isStreaming}
            aria-pressed={isMuted}
          >
            {isMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </Button>
          <span className="text-sm text-white/80">{isMuted ? "Unmute" : "Mute"}</span>

          <Button
            size="icon"
            variant={isStreaming ? "default" : "secondary"}
            onClick={isStreaming ? stopWebcam : startWebcam}
            className="h-12 w-12 rounded-full"
          >
            {isStreaming ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
          </Button>
          <span className="text-sm text-white/80">{isStreaming ? "Stop Video" : "Start Video"}</span>
        </div>
      </div>
    </div>
  )
}
