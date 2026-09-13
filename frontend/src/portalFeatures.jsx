import React, { useEffect, useState } from 'react'
import { Activity, ArrowUpRight, ClipboardList, FileWarning, Home, MapPin, Package, Search, Users } from 'lucide-react'

const API = '/api'
function api(path, options = {}) {
  const token = localStorage.token
  return fetch(API + path, { headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, ...options }).then(async response => {
    const result = await response.json()
    if (!response.ok) throw Error(result.detail || 'Something went wrong')
    return result
  })
}
function Page({ eyebrow, title, sub, children }) { return <main className="page"><div className="page-head"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="page-sub">{sub}</p></div></div>{children}</main> }
function Empty({ icon: Icon = ClipboardList, title, body }) { return <div className="empty-state"><span className="empty-icon"><Icon size={22} /></span><h3>{title}</h3><p>{body}</p></div> }
function Badge({ children }) { return <span className={`badge ${String(children).toLowerCase().replaceAll('_', '-')}`}>{String(children).replaceAll('_', ' ')}</span> }
const statusOptions = ['OPEN', 'CLAIMED', 'RESOLVED', 'REPORTED', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED']

export function RoomPage() {
  const [room, setRoom] = useState(null)
  useEffect(() => { api('/my-room').then(setRoom) }, [])
  if (!room) return <Page eyebrow="STUDENT / ROOM" title="My room" sub="Loading your room record..."><div className="feature-panel loading-stack"><div className="skeleton-line" /><div className="skeleton-line" /></div></Page>
  return <Page eyebrow="STUDENT / ROOM" title={`Room ${room.room}`} sub="Your room assignment, directly from the student register."><section className="room-overview"><div className="room-identity"><span className="hero-icon"><Home /></span><div><p className="eyebrow">CURRENT ASSIGNMENT</p><h2>{room.hostel}</h2><p>Block {room.block} · Floor {room.floor} · Room {room.room}</p></div></div><div className="room-facts"><span><small>Occupancy</small><strong>{room.occupancy} / 4</strong></span><span><small>Room type</small><strong>Standard</strong></span></div></section><section className="feature-panel"><div className="section-heading"><div><p className="eyebrow">RESIDENTS</p><h2>Roommates</h2></div><span className="section-count">{room.roommates.length} roommates</span></div>{room.roommates.length ? <div className="roommate-list">{room.roommates.map(item => <div className="roommate-row" key={item.id}><span className="avatar">{item.name[0]}</span><div><strong>{item.name}</strong><small>{item.email}</small></div><span className="roommate-id">Student ID #{item.id}</span></div>)}</div> : <Empty icon={Users} title="No roommates assigned" body="Your room currently has no other registered residents." />}</section></Page>
}

export function StudentsPage() {
  const [students, setStudents] = useState([])
  useEffect(() => { api('/students').then(setStudents) }, [])
  return <Page eyebrow="WARDEN / STUDENTS" title="Students" sub="The current student register, grouped by the assigned room."><section className="feature-panel"><div className="section-heading"><div><p className="eyebrow">LIVE REGISTER</p><h2>Residents</h2></div><span className="section-count">{students.length} students</span></div>{students.length ? <div className="record-list">{students.map(student => <article className="record-row" key={student.id}><span className="record-icon"><Users size={17} /></span><div className="record-main"><div className="row-between"><strong>{student.name}</strong><Badge>{student.role}</Badge></div><small>Student ID #{student.id} · {student.email}</small><p>{student.hostel} · Block {student.block} · Room {student.room}</p></div><ArrowUpRight className="record-arrow" size={17} /></article>)}</div> : <Empty icon={Users} title="No students registered" body="Students will appear here after they are added to the master register." />}</section></Page>
}

export function LostFoundPage({ user }) {
  const [items, setItems] = useState([]); const [kind, setKind] = useState('LOST'); const [message, setMessage] = useState(''); const [loading, setLoading] = useState(true)
  const load = () => { setLoading(true); api('/lost-found').then(setItems).finally(() => setLoading(false)) }
  useEffect(load, [])
  async function submit(event) { event.preventDefault(); const form = new FormData(event.target); try { await api('/lost-found', { method: 'POST', body: JSON.stringify({ kind, title: form.get('title'), description: form.get('description'), location: form.get('location') }) }); setMessage('Item report saved.'); event.target.reset(); load() } catch (error) { setMessage(error.message) } }
  async function update(id, status) { await api(`/lost-found/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }); load() }
  const canManage = user.role === 'WARDEN' || user.role === 'ADMIN'
  return <Page eyebrow={`${user.role.replace('_', ' ')} / LOST & FOUND`} title="Lost & Found" sub="A shared record for items reported inside the hostel.">{user.role === 'STUDENT' && <form className="feature-panel form-grid" onSubmit={submit}><div className="form-intro"><p className="eyebrow">REPORT AN ITEM</p><h2>Keep the record useful</h2><p>Describe only an item you have actually lost or found.</p></div><div className="segmented"><button type="button" className={kind === 'LOST' ? 'selected' : ''} onClick={() => setKind('LOST')}>I lost something</button><button type="button" className={kind === 'FOUND' ? 'selected' : ''} onClick={() => setKind('FOUND')}>I found something</button></div><label>Item title<input name="title" required placeholder="e.g. Black water bottle" /></label><label>Location<input name="location" required placeholder="e.g. Common room" /></label><label className="full-width">Description<textarea name="description" required /></label><button className="primary" type="submit">Report {kind.toLowerCase()} item <ArrowUpRight size={16} /></button>{message && <p className="success full-width">{message}</p>}</form>}<section className="feature-panel"><div className="section-heading"><div><p className="eyebrow">LIVE REGISTER</p><h2>Reported items</h2></div><span className="section-count">{items.length} records</span></div>{loading ? <div className="loading-stack"><div className="skeleton-line" /><div className="skeleton-line" /></div> : items.length ? <div className="record-list">{items.map(item => <article className="record-row" key={item.id}><span className="record-icon"><Package size={17} /></span><div className="record-main"><div className="row-between"><strong>{item.title}</strong><Badge>{item.status}</Badge></div><small>{item.kind} · {item.location} · {item.user.name}</small><p>{item.description}</p><time>{new Date(item.created_at).toLocaleString()}</time></div>{canManage && <select className="status-select" value={item.status} onChange={event => update(item.id, event.target.value)}>{statusOptions.slice(0, 3).map(status => <option key={status}>{status}</option>)}</select>}</article>)}</div> : <Empty icon={Search} title="No lost or found items" body="Reports will appear here after a student submits one." />}</section></Page>
}

export function ComplaintOpsPage({ user, maintenance = false }) {
  const [items, setItems] = useState([]); const [workers, setWorkers] = useState([]); const [loading, setLoading] = useState(true); const canAssign = user.role === 'WARDEN' || user.role === 'ADMIN'; const manager = user.role === 'STAFF_MANAGER'
  const load = () => { setLoading(true); Promise.all([api('/complaints'), canAssign ? api('/workers') : Promise.resolve([])]).then(([complaints, staff]) => { setItems(manager ? complaints.filter(item => item.assigned_to) : complaints); setWorkers(staff) }).finally(() => setLoading(false)) }
  useEffect(load, [])
  async function update(id, values) { await api(`/complaints/${id}`, { method: 'PATCH', body: JSON.stringify(values) }); load() }
  return <Page eyebrow={`${user.role.replace('_', ' ')} / ${maintenance ? 'MAINTENANCE' : 'COMPLAINTS'}`} title={maintenance ? 'Maintenance queue' : 'Complaint management'} sub={manager ? 'Assigned work from the shared complaint register.' : 'Review, assign, and move real complaints through their lifecycle.'}><section className="feature-panel"><div className="section-heading"><div><p className="eyebrow">{manager ? 'ASSIGNED WORK' : 'ISSUE TRACKING'}</p><h2>{manager ? 'My active work' : 'Complaint queue'}</h2></div><span className="section-count">{items.length} records</span></div>{loading ? <div className="loading-stack"><div className="skeleton-line" /><div className="skeleton-line" /></div> : items.length ? <div className="record-list">{items.map(item => <article className="record-row complaint-row" key={item.id}><span className="record-icon"><FileWarning size={17} /></span><div className="record-main"><div className="row-between"><strong>{item.ticket} · {item.title}</strong><Badge>{item.status}</Badge></div><small>{item.category} · {item.priority} · {item.student} · {item.location}</small><p>{item.assigned_to ? `Assigned to ${item.assigned_to}` : 'Unassigned complaint awaiting review.'}</p><time>{new Date(item.created_at).toLocaleString()}</time></div><div className="record-controls">{canAssign && <select className="status-select" value={item.assigned_to || ''} onChange={event => update(item.id, { assigned_to: event.target.value })}><option value="">Assign worker...</option>{workers.map(worker => <option key={worker.id}>{worker.name}</option>)}</select>}<select className="status-select" value={item.status} onChange={event => update(item.id, { status: event.target.value })}><option>REPORTED</option><option>ASSIGNED</option><option>IN_PROGRESS</option><option>RESOLVED</option><option>COMPLETED</option></select></div></article>)}</div> : <Empty icon={manager ? Activity : FileWarning} title={manager ? 'No active work assigned' : 'No complaints reported'} body={manager ? 'Assigned maintenance work will appear here.' : 'Student complaints will appear here after they are submitted.'} />}</section></Page>
}

function Bars({ title, rows }) { return <div className="analytics-group"><div className="section-heading"><h3>{title}</h3><span>{rows.length} groups</span></div>{rows.length ? rows.map(row => <div className="bar-row" key={row.label}><span>{row.label}</span><b>{row.value}</b><i style={{ width: `${Math.min(100, row.value * 12 + 4)}%` }} /></div>) : <p className="muted">No records yet.</p>}</div> }
export function AnalyticsPage({ report = false }) {
  const [data, setData] = useState(null); useEffect(() => { api('/analytics').then(setData) }, [])
  if (!data) return <Page eyebrow="ADMIN / ANALYTICS" title="Analytics" sub="Loading live database measures..."><div className="feature-panel loading-stack"><div className="skeleton-line" /><div className="skeleton-line" /></div></Page>
  return <Page eyebrow={`${report ? 'OPERATIONS / REPORTS' : 'ADMIN / ANALYTICS'}`} title={report ? 'Operational reports' : 'Analytics'} sub="Every measure below is calculated from current operational records."><section className="stat-strip analytics-stats">{[['Students', data.students], ['Present today', data.attendance.present], ['Not checked in', data.attendance.not_checked_in], ['Requests', data.requests.hospital + data.requests.leave + data.requests.outpass + data.requests.cleaning], ['Complaints', data.complaints.by_status.reduce((sum, row) => sum + row.value, 0)], ['Meal ratings', data.meal_ratings.count]].map(([label, value]) => <div className="metric" key={label}><span className="metric-icon"><Activity size={16} /></span><small>{label}</small><strong>{value}</strong><span className="metric-context">Current database value</span></div>)}</section><section className="analytics-grid"><section className="feature-panel"><Bars title="Complaints by category" rows={data.complaints.by_category} /><Bars title="Complaint status" rows={data.complaints.by_status} /></section><section className="feature-panel"><Bars title="Requests by type" rows={data.requests.by_type} /><div className="analytics-group"><div className="section-heading"><h3>Meal satisfaction</h3></div><strong className="big-value">{data.meal_ratings.count ? `${data.meal_ratings.average} / 5` : 'No ratings yet'}</strong><p className="muted">Only submitted student ratings are included.</p></div></section></section></Page>
}

// ─────────────────────────────────────────────────────────────
// HOSTEL ATTENDANCE VERIFICATION — Student Portal Page
// ─────────────────────────────────────────────────────────────
export function StudentAttendancePage({ user }) {
  const [config, setConfig] = useState(null)
  const [status, setStatus] = useState(null)
  const [gpsState, setGpsState] = useState({ verified: false, checking: false, message: 'Click to verify GPS location', lat: null, lon: null })
  const [networkState, setNetworkState] = useState({ verified: false, checking: false, message: 'Click to verify hostel network' })
  const [currentTime, setCurrentTime] = useState(new Date())
  const [marking, setMarking] = useState(false)
  const [successData, setSuccessData] = useState(null)
  const [error, setError] = useState('')

  // Live clock
  useEffect(() => {
    const t = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  // Load config and student status on mount
  useEffect(() => {
    api('/hostel-attendance/config').then(setConfig).catch(() => {})
    api('/hostel-attendance/status').then(setStatus).catch(() => {})
  }, [])

  // Compute session state from local time (matches server IST logic)
  function localSessionState() {
    const h = currentTime.getHours()
    if (h < 16) return 'before'
    if (h < 18) return 'open'
    return 'closed'
  }

  const sessionState = localSessionState()
  const alreadyMarked = status?.already_marked

  // ── GPS Verification ──────────────────────────────────────
  function verifyGPS() {
    if (!navigator.geolocation) { setGpsState(s => ({ ...s, verified: false, message: 'Geolocation is not supported by your browser.' })); return }
    setGpsState(s => ({ ...s, checking: true, message: 'Requesting location…' }))
    navigator.geolocation.getCurrentPosition(
      pos => {
        const { latitude, longitude } = pos.coords
        if (!config) { setGpsState(s => ({ ...s, checking: false, verified: false, message: 'Config not loaded yet, please wait.', lat: latitude, lon: longitude })); return }
        const R = 6371000
        const dLat = (config.hostel_lat - latitude) * Math.PI / 180
        const dLon = (config.hostel_lon - longitude) * Math.PI / 180
        const a = Math.sin(dLat/2)**2 + Math.cos(latitude*Math.PI/180) * Math.cos(config.hostel_lat*Math.PI/180) * Math.sin(dLon/2)**2
        const dist = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
        const inside = config.demo_mode || dist <= config.geofence_meters
        setGpsState({
          checking: false, verified: inside, lat: latitude, lon: longitude,
          message: config.demo_mode
            ? `Demo mode — GPS check bypassed. (Detected: ${latitude.toFixed(5)}, ${longitude.toFixed(5)})`
            : inside
              ? `Location verified — ${dist.toFixed(0)}m from hostel (within ${config.geofence_meters}m)`
              : `You are outside the permitted hostel location. (${dist.toFixed(0)}m away, limit ${config.geofence_meters}m)`
        })
      },
      err => setGpsState(s => ({ ...s, checking: false, verified: false, message: `Location error: ${err.message}` })),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  }

  // ── Network Verification ──────────────────────────────────
  async function verifyNetwork() {
    setNetworkState(s => ({ ...s, checking: true, message: 'Checking hostel network…' }))
    try {
      const res = await api('/hostel-attendance/verify-network', { method: 'POST' })
      setNetworkState({ checking: false, verified: res.network_verified, message: res.message })
    } catch (e) {
      setNetworkState({ checking: false, verified: false, message: e.message || 'Network check failed.' })
    }
  }

  // ── Mark Present ─────────────────────────────────────────
  async function markPresent() {
    setError(''); setMarking(true)
    try {
      const res = await api('/hostel-attendance/mark-present', {
        method: 'POST',
        body: JSON.stringify({ latitude: gpsState.lat ?? 0, longitude: gpsState.lon ?? 0, gps_verified: gpsState.verified, network_verified: networkState.verified })
      })
      setSuccessData(res)
      setStatus(s => ({ ...s, already_marked: true, status: 'PRESENT', marked_time: res.time }))
    } catch (e) { setError(e.message) } finally { setMarking(false) }
  }

  const canMark = sessionState === 'open' && gpsState.verified && networkState.verified && !alreadyMarked
  const fmtTime = t => t.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })

  // ── Session banner ────────────────────────────────────────
  function SessionBanner() {
    if (sessionState === 'before') return (
      <div className="attend-banner attend-banner-wait">
        <span className="attend-banner-icon">🕓</span>
        <div><strong>Attendance Not Started</strong><p>The attendance session opens at 4:00 PM. Please return between 4:00 PM and 6:00 PM.</p></div>
      </div>
    )
    if (sessionState === 'closed') return (
      <div className="attend-banner attend-banner-closed">
        <span className="attend-banner-icon">🔒</span>
        <div><strong>Attendance Session Closed</strong><p>The session has ended. {alreadyMarked ? 'Your attendance was recorded as PRESENT.' : 'You were marked ABSENT.'}</p></div>
      </div>
    )
    return (
      <div className="attend-banner attend-banner-open">
        <span className="attend-banner-icon">🟢</span>
        <div><strong>Session Open</strong><p>Attendance window: 4:00 PM – 6:00 PM. Complete both verifications and click MARK PRESENT.</p></div>
      </div>
    )
  }

  // ── Success card ──────────────────────────────────────────
  if (successData || (alreadyMarked && status?.marked_time)) {
    const sd = successData || { time: status.marked_time, gps_verified: true, network_verified: true }
    return (
      <Page eyebrow="STUDENT / ATTENDANCE" title="Hostel Attendance" sub="GPS + Hostel Wi-Fi dual-verification.">
        <div className="attend-success">
          <div className="attend-success-icon">✅</div>
          <h2>Attendance Marked</h2>
          <div className="attend-success-badge">PRESENT</div>
          <div className="attend-success-details">
            <div className="attend-success-row"><span>Time</span><strong>{sd.time}</strong></div>
            <div className="attend-success-row"><span>GPS</span><strong className="attend-check">✓ Verified</strong></div>
            <div className="attend-success-row"><span>Hostel Wi-Fi</span><strong className="attend-check">✓ Verified</strong></div>
            <div className="attend-success-row"><span>Date</span><strong>{new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</strong></div>
          </div>
          <p className="muted" style={{marginTop:14,fontSize:12}}>Your attendance record has been saved to the hostel database.</p>
        </div>
      </Page>
    )
  }

  return (
    <Page eyebrow="STUDENT / ATTENDANCE" title="Hostel Attendance" sub="GPS + Hostel Wi-Fi dual-verification required to mark attendance.">
      {/* Time info bar */}
      <div className="attend-time-bar">
        <div className="attend-time-item"><span className="eyebrow">ATTENDANCE TIME</span><strong>4:00 PM – 6:00 PM</strong></div>
        <div className="attend-time-item"><span className="eyebrow">CURRENT TIME</span><strong>{fmtTime(currentTime)}</strong></div>
        <div className="attend-time-item"><span className="eyebrow">STATUS</span>
          <span className={`attend-session-badge attend-session-${sessionState}`}>
            {sessionState === 'before' ? 'Not Started' : sessionState === 'open' ? 'Open' : 'Closed'}
          </span>
        </div>
        {alreadyMarked && <div className="attend-time-item"><span className="eyebrow">YOUR STATUS</span><strong style={{color:'var(--accent)'}}>✓ PRESENT</strong></div>}
      </div>

      <SessionBanner />

      {/* Verification cards */}
      <div className="attend-verify-grid">
        {/* GPS Card */}
        <div className={`attend-verify-card ${gpsState.verified ? 'verified' : gpsState.checking ? 'checking' : ''}`}>
          <div className="attend-verify-header">
            <span className="attend-verify-dot">{gpsState.verified ? '🟢' : gpsState.checking ? '🔄' : '🔴'}</span>
            <div>
              <p className="eyebrow">GPS LOCATION</p>
              <strong>{gpsState.verified ? 'Verified' : gpsState.checking ? 'Checking…' : 'Not Verified'}</strong>
            </div>
          </div>
          <p className="attend-verify-msg">{gpsState.message}</p>
          {!alreadyMarked && (
            <button className="outline" onClick={verifyGPS} disabled={gpsState.checking || sessionState === 'closed'}>
              {gpsState.checking ? 'Locating…' : gpsState.verified ? 'Re-verify GPS' : 'Verify GPS Location'}
            </button>
          )}
        </div>

        {/* Wi-Fi Card */}
        <div className={`attend-verify-card ${networkState.verified ? 'verified' : networkState.checking ? 'checking' : ''}`}>
          <div className="attend-verify-header">
            <span className="attend-verify-dot">{networkState.verified ? '🟢' : networkState.checking ? '🔄' : '🔴'}</span>
            <div>
              <p className="eyebrow">HOSTEL WI-FI</p>
              <strong>{networkState.verified ? 'Verified' : networkState.checking ? 'Checking…' : 'Not Verified'}</strong>
            </div>
          </div>
          <p className="attend-verify-msg">{networkState.message}</p>
          {!alreadyMarked && (
            <button className="outline" onClick={verifyNetwork} disabled={networkState.checking || sessionState === 'closed'}>
              {networkState.checking ? 'Checking…' : networkState.verified ? 'Re-verify Network' : 'Verify Hostel Network'}
            </button>
          )}
        </div>
      </div>

      {/* Overall verification status */}
      <div className={`attend-overall ${canMark ? 'ready' : ''}`}>
        <span className="attend-verify-dot" style={{fontSize:18}}>{canMark ? '🟢' : '🔴'}</span>
        <div>
          <p className="eyebrow">VERIFICATION STATUS</p>
          <strong>{canMark ? 'Both Conditions Verified — Ready to Mark' : 'Verification Incomplete'}</strong>
          {!canMark && (
            <p style={{margin:'6px 0 0',fontSize:12,color:'var(--muted)'}}>
              {sessionState !== 'open' ? 'Attendance session is not open.' :
                !gpsState.verified && !networkState.verified ? 'GPS and Hostel Wi-Fi verification required.' :
                !gpsState.verified ? 'GPS location verification required.' :
                'Hostel Wi-Fi verification required.'}
            </p>
          )}
        </div>
      </div>

      {/* Mark Present button */}
      {!alreadyMarked && (
        <div style={{marginTop:20}}>
          {error && <p className="error" style={{marginBottom:10}}>⚠ {error}</p>}
          <button
            id="btn-mark-present"
            className={`primary wide attend-mark-btn ${canMark && !marking ? 'active' : ''}`}
            onClick={markPresent}
            disabled={!canMark || marking}
          >
            {marking ? 'Submitting…' : '✓ MARK PRESENT'}
          </button>
          {!canMark && <p style={{marginTop:8,fontSize:11,color:'var(--muted)',textAlign:'center'}}>Complete both verifications above during 4:00 PM – 6:00 PM to enable this button.</p>}
        </div>
      )}
    </Page>
  )
}

// ─────────────────────────────────────────────────────────────
// HOSTEL ATTENDANCE VERIFICATION — Warden Dashboard Page
// ─────────────────────────────────────────────────────────────
export function WardenAttendancePage({ user }) {
  const [data, setData] = useState(null)
  const [notifyMsg, setNotifyMsg] = useState('')
  const [closingSession, setClosingSession] = useState(false)
  const [activeTab, setActiveTab] = useState('present')

  function load() {
    api('/hostel-attendance/summary').then(setData).catch(() => {})
  }

  useEffect(() => {
    load()
    // Poll every 15 seconds for real-time updates
    const interval = setInterval(load, 15000)
    return () => clearInterval(interval)
  }, [])

  async function sendNotify(studentId, studentName) {
    try {
      await api('/hostel-attendance/notify-absent', { method: 'POST', body: JSON.stringify({ student_id: studentId }) })
      setNotifyMsg(`Notification sent to ${studentName}`)
      setTimeout(() => setNotifyMsg(''), 3000)
    } catch (e) { setNotifyMsg(e.message) }
  }

  async function closeSession() {
    if (!window.confirm('Close the attendance session? All pending students will be marked ABSENT.')) return
    setClosingSession(true)
    try {
      const res = await api('/hostel-attendance/session-close', { method: 'POST' })
      setNotifyMsg(`Session closed — Present: ${res.present}, Absent: ${res.absent}`)
      load()
    } catch (e) { setNotifyMsg(e.message) } finally { setClosingSession(false) }
  }

  const sessionLabel = data ? (data.session_state === 'before' ? 'Not Started' : data.session_state === 'open' ? 'Open' : 'Closed') : '…'

  return (
    <Page eyebrow="WARDEN / ATTENDANCE" title="Attendance Register" sub="Live GPS + Wi-Fi verified hostel attendance — auto-refreshes every 15 seconds.">

      {/* Session state banner */}
      <div className={`attend-banner attend-banner-${data?.session_state || 'before'}`} style={{marginBottom:18}}>
        <span className="attend-banner-icon">{data?.session_state === 'open' ? '🟢' : data?.session_state === 'closed' ? '🔒' : '🕓'}</span>
        <div style={{flex:1}}>
          <strong>Session: {sessionLabel} · 4:00 PM – 6:00 PM</strong>
          <p style={{margin:0,fontSize:12,color:'var(--muted)'}}>
            {data?.session_state === 'open' ? 'Attendance window is currently open. Dashboard updates every 15 seconds.' :
             data?.session_state === 'closed' ? 'Session closed. All pending records have been or can be finalised.' :
             'Session has not started yet. It opens at 4:00 PM.'}
          </p>
        </div>
        {data?.session_state === 'open' && (
          <button className="outline" onClick={closeSession} disabled={closingSession} style={{flexShrink:0}}>
            {closingSession ? 'Closing…' : 'Close Session'}
          </button>
        )}
        <span className="live-label" style={{flexShrink:0}}><i />Live</span>
      </div>

      {/* Summary stat strip */}
      {data ? (
        <div className="attend-summary-strip">
          {[
            { label: 'TOTAL STUDENTS', value: data.total, color: '' },
            { label: 'PRESENT', value: data.present_count, color: 'var(--accent)' },
            { label: 'PENDING', value: data.pending_count, color: 'var(--warning)' },
            { label: 'ABSENT', value: data.absent_count, color: 'var(--danger)' },
          ].map(({ label, value, color }) => (
            <div className="attend-stat-card" key={label}>
              <span className="eyebrow">{label}</span>
              <strong style={color ? { color } : {}}>{value}</strong>
              <span className="metric-context">Live database count</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="loading-stack"><div className="skeleton-line" /><div className="skeleton-line" /></div>
      )}

      {notifyMsg && <p className="success" style={{marginBottom:12}}>✓ {notifyMsg}</p>}

      {data && (
        <>
          {/* Tab navigation */}
          <div className="segmented" style={{marginBottom:16}}>
            <button className={activeTab === 'present' ? 'selected' : ''} onClick={() => setActiveTab('present')}>
              ✓ Present ({data.present_count})
            </button>
            <button className={activeTab === 'pending' ? 'selected' : ''} onClick={() => setActiveTab('pending')}>
              ⏳ Pending ({data.pending_count})
            </button>
            <button className={activeTab === 'absent' ? 'selected' : ''} onClick={() => setActiveTab('absent')}>
              🚨 Absent ({data.absent_count})
            </button>
          </div>

          {/* PRESENT students */}
          {activeTab === 'present' && (
            <section className="feature-panel">
              <div className="section-heading">
                <div><p className="eyebrow">VERIFIED PRESENT</p><h2>Present students</h2></div>
                <span className="section-count">{data.present_count} students</span>
              </div>
              {data.present.length ? (
                <div className="attend-table">
                  <div className="attend-table-head">
                    <span>Room</span><span>Name</span><span>Email</span><span>Time</span><span>GPS</span><span>Wi-Fi</span>
                  </div>
                  {data.present.map(s => (
                    <div className="attend-table-row" key={s.id}>
                      <span className="attend-room">{s.room || '—'}</span>
                      <span><strong>{s.name}</strong></span>
                      <span className="attend-muted">{s.email}</span>
                      <span className="attend-time">{s.marked_time}</span>
                      <span className={s.gps_verified ? 'attend-check' : 'attend-fail'}>{s.gps_verified ? '✓ GPS' : '✗ GPS'}</span>
                      <span className={s.network_verified ? 'attend-check' : 'attend-fail'}>{s.network_verified ? '✓ Wi-Fi' : '✗ Wi-Fi'}</span>
                    </div>
                  ))}
                </div>
              ) : <Empty icon={Users} title="No students marked present yet" body="Students who successfully verify GPS and hostel Wi-Fi will appear here." />}
            </section>
          )}

          {/* PENDING students */}
          {activeTab === 'pending' && (
            <section className="feature-panel">
              <div className="section-heading">
                <div><p className="eyebrow">NOT YET MARKED</p><h2>Pending students</h2></div>
                <span className="section-count">{data.pending_count} students</span>
              </div>
              {data.pending.length ? (
                <div className="attend-table">
                  <div className="attend-table-head">
                    <span>Room</span><span>Name</span><span>Email</span><span>Status</span><span style={{gridColumn:'span 2'}}>Action</span>
                  </div>
                  {data.pending.map(s => (
                    <div className="attend-table-row" key={s.id}>
                      <span className="attend-room">{s.room || '—'}</span>
                      <span><strong>{s.name}</strong></span>
                      <span className="attend-muted">{s.email}</span>
                      <span><span className="badge pending">PENDING</span></span>
                      <span style={{gridColumn:'span 2'}}>
                        <button className="outline" style={{fontSize:11,minHeight:28,padding:'0 10px'}} onClick={() => sendNotify(s.id, s.name)}>Remind</button>
                      </span>
                    </div>
                  ))}
                </div>
              ) : <Empty icon={Users} title="No pending students" body="All students have either marked attendance or been finalised." />}
            </section>
          )}

          {/* ABSENT students */}
          {activeTab === 'absent' && (
            <section className="feature-panel" style={{borderTop:'3px solid var(--danger)'}}>
              <div className="section-heading">
                <div><p className="eyebrow" style={{color:'var(--danger)'}}>🚨 ABSENT STUDENTS</p><h2>Absent students</h2></div>
                <span className="section-count">{data.absent_count} students</span>
              </div>
              {data.absent.length ? (
                <div className="attend-table">
                  <div className="attend-table-head">
                    <span>Room</span><span>Name</span><span>Email</span><span>Status</span><span>Reason</span><span>Action</span>
                  </div>
                  {data.absent.map(s => (
                    <div className="attend-table-row absent-row" key={s.id}>
                      <span className="attend-room">{s.room || '—'}</span>
                      <span><strong>{s.name}</strong></span>
                      <span className="attend-muted">{s.email}</span>
                      <span><span className="badge absent">ABSENT</span></span>
                      <span className="attend-muted" style={{fontSize:11}}>{s.reason}</span>
                      <span>
                        <button className="outline" style={{fontSize:11,minHeight:28,padding:'0 10px',borderColor:'var(--danger)',color:'var(--danger)'}} onClick={() => sendNotify(s.id, s.name)}>Notify</button>
                      </span>
                    </div>
                  ))}
                </div>
              ) : <Empty icon={Users} title={data.session_state === 'closed' ? 'No absent students' : 'No absent students yet'} body={data.session_state === 'closed' ? 'All students marked attendance successfully.' : 'Absent list is finalised after 6:00 PM.'} />}
            </section>
          )}
        </>
      )}
    </Page>
  )
}
