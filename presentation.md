# ForgetMeNot - Hackathon Presentation

## 🎯 Project Summary
**ForgetMeNot** is an AI-powered memory companion for dementia patients that recognizes faces, remembers relationships, and provides real-time context about visitors.

---

## Speaker 1: The Problem & Vision (2 min)

### Opening Hook
> "Imagine not recognizing your own son when he walks through the door."

### The Problem
- **55 million** people worldwide live with dementia
- Patients forget faces, names, and relationships of loved ones
- This causes distress for both patients and caregivers
- Current solutions: photo albums, whiteboards — **outdated and passive**

### Our Vision
- An **always-on AI companion** that:
  - Recognizes who walks in the room
  - Whispers context: "This is David, your son. He visited last Tuesday."
  - Learns and remembers relationships automatically
  - Provides caregivers with insights

### Key Differentiator
> "We don't just remind — we **understand and adapt**."

---

## Speaker 2: Technical Architecture (2 min)

### System Overview
```
Camera → Face Recognition → Voice → LLM → Memory Database → UI
```

### Core Technologies
| Component | Technology |
|-----------|------------|
| Face Detection | MediaPipe Vision (real-time, browser-based) |
| Voice Transcription | Whisper Large V3 (Groq API) |
| Relationship Extraction | LLaMA 3 70B (Groq API) |
| Speaker Embedding | PyAnnote Audio (voice fingerprinting) |
| Database | Convex (real-time sync) |
| Frontend | Next.js 15 + TailwindCSS |
| Backend | FastAPI + WebRTC |

### How It Works (Live Demo Flow)
1. **Face detected** → Matched against stored embeddings
2. **Voice captured** → Transcribed in real-time
3. **LLM extracts** → Names, relationships from conversation
4. **Database updated** → "David" linked to face + relationship "Your Son"
5. **Next visit** → System recognizes David instantly

### Technical Highlights
- **Real-time WebRTC streaming** for low latency
- **Persistent memory** across sessions
- **Event-driven architecture** for scalability

---

## Speaker 3: Live Demo & User Experience (2 min)

### Demo Script
1. **Start on home screen** — Show camera feed with face detection boxes
2. **New person enters** — "Unknown person detected"
3. **Speak to device** — "Hi Mom, it's me, your son David!"
4. **Show LLM processing** — Name extracted, relationship saved
5. **Close and reopen** — David is now recognized instantly
6. **Show dashboard** — Caregiver sees all visitors, relationships, activity

### UI/UX Highlights
- **Dementia-friendly design**: Large text, high contrast, calming colors
- **Minimal cognitive load**: Only essential information shown
- **Caregiver Dashboard**: Overview of all visitors and interactions
- **Real-time notifications**: "David (Your Son) just arrived"

### Accessibility Features
- Large photos for easy recognition
- Simple relationship labels
- Color-coded activity feed
- Works passively (no interaction required from patient)

---

## Speaker 4: Impact & Future Roadmap (2 min)

### Immediate Impact
- **Reduces anxiety** for dementia patients
- **Empowers caregivers** with conversation history
- **Preserves dignity** by enabling meaningful interactions
- **Works 24/7** without human intervention

### Real-World Scenarios
| Scenario | How ForgetMeNot Helps |
|----------|----------------------|
| Visitor arrives | "Sarah, your nurse, is here for your checkup" |
| Phone call | "This is your daughter calling" |
| Daily caregiver | Tracks conversation topics to avoid repetition |

### Future Roadmap
1. **Phase 1** — AR glasses integration (discrete, always-on)
2. **Phase 2** — Voice assistant ("Who was here yesterday?")
3. **Phase 3** — Emotion detection (detect distress, alert caregivers)
4. **Phase 4** — Multi-patient support for care facilities

### Business Model
- **B2C**: Monthly subscription for families ($29/mo)
- **B2B**: Licensing to assisted living facilities
- **Healthcare partnerships**: Integration with patient records

### Closing Statement
> "ForgetMeNot doesn't cure dementia — but it gives back the one thing patients lose first: **connection with the people who love them**."

---

## Q&A Preparation

### Likely Questions

**Q: How do you handle privacy?**
> All data stays local or in encrypted cloud storage. HIPAA compliance on roadmap.

**Q: What if the patient has multiple visitors at once?**
> We use speaker diarization to track multiple voices and faces simultaneously.

**Q: How accurate is face recognition?**
> MediaPipe achieves 95%+ accuracy. We also use voice embedding as backup.

**Q: What happens if internet goes down?**
> Core face recognition works offline. Sync happens when reconnected.

**Q: How is this different from a smart display with photos?**
> Photos are passive. We actively recognize, remember, and provide context in real-time.

---

## 🏆 Judging Criteria Alignment

| Criteria | How We Score |
|----------|--------------|
| **Innovation** | First AI memory companion combining face + voice + LLM |
| **Technical Complexity** | WebRTC, real-time ML, event-driven architecture |
| **Social Impact** | Directly helps 55M dementia patients worldwide |
| **Completeness** | Working demo with persistence, dashboard, real-time UI |
| **Presentation** | Clear problem → solution → demo → impact flow |

---

*Built with ❤️ at the Hackathon*
