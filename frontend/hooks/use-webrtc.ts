"use client"

import { useCallback, useRef, useState } from "react"
import { BACKEND_URL } from "@/lib/config"

export function useWebRTC() {
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  const waitForIceGathering = useCallback((pc: RTCPeerConnection): Promise<void> => {
    return new Promise((resolve) => {
      if (pc.iceGatheringState === "complete") {
        resolve()
        return
      }

      const checkState = () => {
        if (pc.iceGatheringState === "complete") {
          pc.removeEventListener("icegatheringstatechange", checkState)
          resolve()
        }
      }

      pc.addEventListener("icegatheringstatechange", checkState)
    })
  }, [])

  const setupWebRTC = useCallback(async (stream: MediaStream) => {
    try {
      console.log("[WebRTC] Setting up peer connection")
      const pc = new RTCPeerConnection()
      pcRef.current = pc

      stream.getTracks().forEach((track) => {
        console.log("[WebRTC] Adding track:", track.kind)
        pc.addTrack(track, stream)
      })

      pc.onconnectionstatechange = () => {
        console.log("[WebRTC] Connection state:", pc.connectionState)
        setIsConnected(pc.connectionState === "connected")
      }

      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)
      console.log("[WebRTC] Created offer, waiting for ICE gathering...")

      await waitForIceGathering(pc)
      console.log("[WebRTC] ICE gathering complete, sending offer to backend")

      const response = await fetch(`${BACKEND_URL}/offer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sdp: pc.localDescription!.sdp,
          type: pc.localDescription!.type,
        }),
      })

      if (!response.ok) {
        throw new Error(`Backend responded with ${response.status}`)
      }

      const answer = await response.json()
      console.log("[WebRTC] Received answer from backend")
      await pc.setRemoteDescription(answer)
      console.log("[WebRTC] Connection established!")
    } catch (err) {
      console.error("[WebRTC] Setup error:", err)
      setIsConnected(false)
    }
  }, [waitForIceGathering])

  const closeConnection = useCallback(() => {
    if (pcRef.current) {
      pcRef.current.close()
      pcRef.current = null
    }
    setIsConnected(false)
  }, [])

  return {
    pcRef,
    isConnected,
    setupWebRTC,
    closeConnection,
  }
}
