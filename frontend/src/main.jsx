import React, { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import "./styles.css";

const API = "http://127.0.0.1:8000";

async function apiRequest(path, token, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const raw = await response.text();
  let data = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    data = { detail: raw };
  }
  if (!response.ok) {
    throw new Error(data.detail || `Request failed (${response.status})`);
  }
  return data;
}

const cropOptions = ["Rice", "Wheat", "Maize", "Tomato", "Potato", "Cotton", "Soybean", "Sugarcane"];
const stageOptions = ["seedling", "vegetative", "flowering", "fruiting", "maturity"];
const navItems = [
  { name: "Dashboard", icon: "▦" },
  { name: "My Farms", icon: "⌂" },
  { name: "Crop Health", icon: "♧" },
  { name: "AI Analysis", icon: "✳" },
];

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("farmshield_token") || "");
  const [email, setEmail] = useState("aniket@farmshield.com");
  const [password, setPassword] = useState("");
  const [user, setUser] = useState(null);
  const [farms, setFarms] = useState([]);
  const [crops, setCrops] = useState([]);
  const [selectedFarm, setSelectedFarm] = useState("");
  const [selectedCrop, setSelectedCrop] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [predictionCrop, setPredictionCrop] = useState(null);
  const [predictionFarm, setPredictionFarm] = useState(null);
  const [page, setPage] = useState("Dashboard");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showFarmForm, setShowFarmForm] = useState(false);
  const [showCropForm, setShowCropForm] = useState(false);
  const [farmName, setFarmName] = useState("");
  const [farmLocation, setFarmLocation] = useState("");
  const [farmArea, setFarmArea] = useState("1");
  const [soilMoisture, setSoilMoisture] = useState("25");
  const [soilPh, setSoilPh] = useState("6.5");
  const [cropName, setCropName] = useState("Rice");
  const [cropVariety, setCropVariety] = useState("");
  const [growthStage, setGrowthStage] = useState("vegetative");
  const [plantingDate, setPlantingDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const clearNotice = () => { setError(""); setMessage(""); };

  function logout() {
    localStorage.removeItem("farmshield_token");
    setToken(""); setUser(null); setFarms([]); setCrops([]); setPrediction(null);
    setPredictionCrop(null); setPredictionFarm(null); setPassword("");
    setPage("Dashboard"); setError(""); setMessage("You have been logged out.");
  }

  async function loadUser(currentToken) {
    const result = await apiRequest("/api/v1/auth/me", currentToken);
    setUser(result);
  }

  async function loadFarms(currentToken) {
    const result = await apiRequest("/api/v1/farms", currentToken);
    setFarms(Array.isArray(result) ? result : []);
    if (result?.length) {
      setSelectedFarm((previous) => result.some((farm) => String(farm.id) === String(previous)) ? previous : String(result[0].id));
    } else {
      setSelectedFarm(""); setCrops([]); setSelectedCrop("");
    }
  }

  async function loadCrops(farmId, currentToken = token) {
    if (!farmId) { setCrops([]); setSelectedCrop(""); return; }
    const result = await apiRequest(`/api/v1/farms/${farmId}/crops`, currentToken);
    setCrops(Array.isArray(result) ? result : []);
    if (result?.length) {
      setSelectedCrop((previous) => result.some((crop) => String(crop.id) === String(previous)) ? previous : String(result[0].id));
    } else { setSelectedCrop(""); }
  }

  async function refreshApp(currentToken = token) {
    setLoading(true); clearNotice();
    try {
      await loadUser(currentToken);
      await loadFarms(currentToken);
    } catch (err) {
      if (String(err.message).toLowerCase().includes("token") || String(err.message).includes("401")) {
        localStorage.removeItem("farmshield_token"); setToken(""); setUser(null);
      }
      setError(err.message);
    } finally { setLoading(false); }
  }

  useEffect(() => { if (token) refreshApp(token); }, [token]);
  useEffect(() => {
    if (token && selectedFarm) loadCrops(selectedFarm, token).catch((err) => setError(err.message));
    else { setCrops([]); setSelectedCrop(""); }
  }, [selectedFarm, token]);

  async function login(event) {
    event.preventDefault(); setLoading(true); clearNotice();
    try {
      const result = await apiRequest("/api/v1/auth/login", "", { method: "POST", body: JSON.stringify({ email, password }) });
      localStorage.setItem("farmshield_token", result.access_token);
      setToken(result.access_token); setPassword(""); setMessage("Welcome back. You are signed in.");
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  async function createFarm(event) {
    event.preventDefault(); setLoading(true); clearNotice();
    try {
      const farm = await apiRequest("/api/v1/farms", token, { method: "POST", body: JSON.stringify({
        name: farmName.trim(), location: farmLocation.trim(), area: Number(farmArea), area_unit: "acres",
        soil_moisture: soilMoisture === "" ? null : Number(soilMoisture), soil_ph: soilPh === "" ? null : Number(soilPh),
      }) });
      setFarmName(""); setFarmLocation(""); setShowFarmForm(false);
      await loadFarms(token); setSelectedFarm(String(farm.id)); setMessage("Farm registered successfully.");
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  async function createCrop(event) {
    event.preventDefault();
    if (!selectedFarm) { setError("Select a farm before adding a crop."); return; }
    setLoading(true); clearNotice();
    try {
      await apiRequest(`/api/v1/farms/${selectedFarm}/crops`, token, { method: "POST", body: JSON.stringify({
        crop: cropName,
        variety: cropVariety.trim() || null,
        growth_stage: growthStage,
        planting_date: plantingDate,
      }) });
      setCropVariety("");
      setGrowthStage("vegetative");
      setPlantingDate(new Date().toISOString().slice(0, 10));
      setShowCropForm(false);
      await loadCrops(selectedFarm);
      setMessage("Crop added successfully.");
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  async function analyzeCrop(cropId = selectedCrop) {
    if (!selectedFarm || !cropId) { setError("Select a farm and crop before running an assessment."); return; }
    setLoading(true); clearNotice(); setPrediction(null);
    const farmForPrediction = farms.find((farm) => String(farm.id) === String(selectedFarm)) || null;
    const cropForPrediction = crops.find((crop) => String(crop.id) === String(cropId)) || null;
    try {
      const result = await apiRequest(`/api/v1/farms/${selectedFarm}/crops/${cropId}/risk`, token, { method: "POST" });
      setPrediction(result); setPredictionFarm(farmForPrediction); setPredictionCrop(cropForPrediction);
      setSelectedCrop(String(cropId)); setPage("AI Analysis"); setMessage("Risk assessment completed. This is a development demo result.");
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  const selectedFarmObject = farms.find((farm) => String(farm.id) === String(selectedFarm));
  const selectedCropObject = crops.find((crop) => String(crop.id) === String(selectedCrop));
  const username = user?.email ? user.email.split("@")[0] : "Farmer";
  const riskPercent = useMemo(() => {
    if (prediction?.risk_probability == null) return null;
    const raw = Number(prediction.risk_probability);
    return Math.max(0, Math.min(100, raw <= 1 ? raw * 100 : raw));
  }, [prediction]);
  const riskLevel = String(prediction?.risk_level || "UNASSESSED").toUpperCase();
  const riskClass = riskLevel.includes("HIGH") ? "high" : riskLevel.includes("MED") ? "medium" : riskLevel.includes("LOW") ? "low" : "neutral";

  function navigate(nextPage) { setPage(nextPage); setMobileNavOpen(false); clearNotice(); }

  if (!token) {
    return <div className="auth-shell">
      <div className="auth-visual">
        <div className="auth-brand"><span className="brand-symbol">✳</span><span>FarmShield <b>AI</b></span></div>
        <div className="auth-hero-copy">
          <span className="eyebrow">SMARTER FARMING STARTS HERE</span>
          <h1>See crop stress<br /><em>before it spreads.</em></h1>
          <p>A prototype decision-support workspace for farm records and crop-risk assessments.</p>
          <div className="auth-feature"><span>✓</span> Farm and crop management</div>
          <div className="auth-feature"><span>✓</span> Explainable development-model output</div>
          <div className="auth-feature"><span>✓</span> One place to review risk assessments</div>
        </div>
        <div className="auth-bottom-note">BUILT FOR EARLY-ACTION AGRICULTURE</div>
      </div>
      <main className="auth-main">
        <section className="auth-card">
          <div className="mobile-brand"><span className="brand-symbol">✳</span> FarmShield AI</div>
          <span className="eyebrow green-eyebrow">FARMSAFE WORKSPACE</span>
          <h2>Welcome back</h2>
          <p className="auth-subtitle">Sign in to continue to your farm dashboard.</p>
          {error && <div className="notice error-notice" role="alert"><b>Something went wrong</b><span>{error}</span></div>}
          {message && <div className="notice success-notice" role="status">{message}</div>}
          <form onSubmit={login} className="form-stack">
            <label className="field-label">Email address<input className="field-input" type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="you@example.com" /></label>
            <label className="field-label">Password<input className="field-input" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required placeholder="Enter your password" /></label>
            <button className="button button-primary button-wide" type="submit" disabled={loading}>{loading ? <><span className="spinner" /> Signing in…</> : <>Sign in <span>→</span></>}</button>
          </form>
          <div className="auth-disclaimer"><span>ⓘ</span><p><b>Development environment</b><br />This build uses a development model and placeholder environmental readings. It is not a validated farm advisory service.</p></div>
        </section>
        <footer className="auth-footer">© FarmShield AI · Prototype build</footer>
      </main>
    </div>;
  }

  return <div className="app-shell">
    <aside className={`sidebar ${mobileNavOpen ? "sidebar-open" : ""}`}>
      <button className="brand-lockup" onClick={() => navigate("Dashboard")} aria-label="FarmShield AI home"><span className="brand-symbol">✳</span><span className="brand-name">FarmShield <b>AI</b><small>EARLY WARNING SYSTEM</small></span></button>
      <div className="nav-caption">WORKSPACE</div>
      <nav className="side-nav" aria-label="Main navigation">
        {navItems.map((item) => <button key={item.name} className={`nav-link ${page === item.name ? "active" : ""}`} onClick={() => navigate(item.name)}><span className="nav-icon">{item.icon}</span><span>{item.name}</span>{item.name === "AI Analysis" && prediction && <span className="nav-indicator" />}</button>)}
      </nav>
      <div className="sidebar-spacer" />
      <div className="sidebar-demo"><span className="demo-dot" /><div><b>DEVELOPMENT MODE</b><small>Predictions are for demonstration only.</small></div></div>
      <div className="sidebar-user"><div className="user-avatar">{username.slice(0, 2).toUpperCase()}</div><div className="user-details"><b>{username}</b><span>{user?.email || email}</span></div><button className="logout-icon" onClick={logout} title="Log out" aria-label="Log out">↗</button></div>
    </aside>

    <main className="main-content">
      <header className="topbar">
        <div className="topbar-heading"><button className="mobile-menu" onClick={() => setMobileNavOpen((open) => !open)} aria-label="Toggle navigation">☰</button><div><div className="breadcrumb">WORKSPACE <span>/</span> {page.toUpperCase()}</div><h1>{page === "Dashboard" ? "Farm overview" : page === "My Farms" ? "Your farms" : page === "Crop Health" ? "Crop health" : "AI risk analysis"}</h1><p>{page === "Dashboard" ? "A clear view of your registered farm data." : page === "My Farms" ? "Manage your farm records and growing conditions." : page === "Crop Health" ? "Review crops and start an assessment." : "Review the latest model output and its limitations."}</p></div></div>
        <div className="topbar-right"><span className="environment-pill"><span /> DEVELOPMENT</span><div className="topbar-avatar">{username.slice(0, 1).toUpperCase()}</div></div>
      </header>

      <div className="demo-banner"><div className="banner-icon">!</div><div><b>DEMO DATA — NOT LIVE FARM DATA</b><p>Risk assessments use placeholder environmental inputs and a development model. Do not use them to make real-world farming decisions.</p></div><span className="banner-tag">PROTOTYPE</span></div>

      {error && <div className="notice error-notice" role="alert"><span className="notice-symbol">!</span><div><b>Action couldn't be completed</b><p>{error}</p></div><button onClick={() => setError("")} aria-label="Dismiss error">×</button></div>}
      {message && <div className="notice success-notice" role="status"><span className="notice-symbol">✓</span><span>{message}</span><button onClick={() => setMessage("")} aria-label="Dismiss message">×</button></div>}
      {loading && <div className="loading-strip"><span className="spinner" /> Working with FarmShield API…</div>}

      {page === "Dashboard" && <>
        <section className="welcome-row"><div><span className="eyebrow green-eyebrow">YOUR FIELD COMMAND CENTRE</span><h2>Good to see you, {username} <span>✳</span></h2><p>Keep your farm records organized and review prototype crop-risk assessments.</p></div><button className="button button-primary" onClick={() => { setShowFarmForm(true); navigate("My Farms"); }}>＋ Register a farm</button></section>
        <section className="stats-grid">
          <article className="metric-card"><div className="metric-head"><span>REGISTERED FARMS</span><span className="metric-icon mint">⌂</span></div><div className="metric-value">{farms.length.toString().padStart(2, "0")}</div><div className="metric-foot">Farm records in your account</div></article>
          <article className="metric-card"><div className="metric-head"><span>CROPS IN SELECTED FARM</span><span className="metric-icon blue">♧</span></div><div className="metric-value">{crops.length.toString().padStart(2, "0")}</div><div className="metric-foot">{selectedFarmObject?.name || "Select or add a farm"}</div></article>
          <article className="metric-card"><div className="metric-head"><span>SELECTED FARM</span><span className="metric-icon amber">⌖</span></div><div className="metric-value metric-text">{selectedFarmObject?.name || "No farm selected"}</div><div className="metric-foot">{selectedFarmObject?.location || "Add a farm to get started"}</div></article>
          <article className="metric-card"><div className="metric-head"><span>LATEST ASSESSMENT</span><span className="metric-icon violet">✳</span></div><div className="metric-value metric-text">{prediction ? riskLevel : "Not run"}</div><div className="metric-foot">{prediction ? "Development-model result" : "Run an assessment below"}</div></article>
        </section>

        <section className="dashboard-grid">
          <article className="surface-card assessment-card">
            <div className="section-heading"><div><span className="eyebrow">START HERE</span><h3>Assess crop risk</h3><p>Choose a registered farm and crop to run the model.</p></div><span className="heading-icon">✳</span></div>
            {farms.length === 0 ? <div className="empty-state"><div className="empty-icon">⌂</div><b>No farm records yet</b><p>Register a farm first, then add a crop to begin.</p><button className="button button-primary" onClick={() => { setShowFarmForm(true); navigate("My Farms"); }}>Register your first farm</button></div> : <div className="form-stack assessment-form">
              <label className="field-label">Farm<select className="field-input" value={selectedFarm} onChange={(event) => setSelectedFarm(event.target.value)}><option value="">Select a farm</option>{farms.map((farm) => <option key={farm.id} value={farm.id}>{farm.name} — {farm.location}</option>)}</select></label>
              <label className="field-label">Crop<select className="field-input" value={selectedCrop} onChange={(event) => setSelectedCrop(event.target.value)} disabled={!crops.length}><option value="">{crops.length ? "Select a crop" : "No crops in this farm"}</option>{crops.map((crop) => <option key={crop.id} value={crop.id}>{crop.crop}{crop.variety ? ` · ${crop.variety}` : ""}</option>)}</select></label>
              <button className="button button-primary button-wide" onClick={() => analyzeCrop()} disabled={loading || !selectedFarm || !selectedCrop}>{loading ? "Analyzing…" : <>Run crop-risk assessment <span>→</span></>}</button>
              <p className="microcopy">This creates a new assessment using the current development pipeline.</p>
            </div>}
          </article>
          <article className="surface-card farm-summary-card"><div className="section-heading"><div><span className="eyebrow">FARM RECORD</span><h3>Selected farm</h3><p>Details saved in your local project database.</p></div><span className="heading-icon">⌂</span></div>
            {selectedFarmObject ? <><div className="farm-summary-hero"><div className="farm-illustration">🌱</div><div><h4>{selectedFarmObject.name}</h4><p>⌖ {selectedFarmObject.location || "Location not specified"}</p></div></div><div className="detail-list"><div><span>Registered area</span><b>{selectedFarmObject.area ?? "—"} {selectedFarmObject.area_unit || "acres"}</b></div><div><span>Soil moisture input</span><b>{selectedFarmObject.soil_moisture ?? "—"}{selectedFarmObject.soil_moisture != null ? "%" : ""}</b></div><div><span>Soil pH input</span><b>{selectedFarmObject.soil_ph ?? "—"}</b></div></div><button className="button button-secondary button-wide" onClick={() => navigate("My Farms")}>Manage farm details <span>→</span></button></> : <div className="empty-state compact"><div className="empty-icon">⌂</div><b>No farm selected</b><p>Your registered farm details will appear here.</p></div>}
          </article>
        </section>

        <section className="surface-card crops-overview"><div className="section-heading"><div><span className="eyebrow">REGISTERED CROPS</span><h3>Crop portfolio</h3><p>{selectedFarmObject ? `Crops associated with ${selectedFarmObject.name}.` : "Select a farm to see its crops."}</p></div><button className="button button-secondary" onClick={() => { setShowCropForm(true); navigate("Crop Health"); }} disabled={!selectedFarm}>＋ Add crop</button></div>
          {crops.length ? <div className="crop-card-grid">{crops.map((crop) => <article className="crop-summary" key={crop.id}><div className="crop-emblem">🌾</div><div className="crop-summary-info"><b>{crop.crop}</b><span>{crop.variety || "Variety not specified"}</span><small>Stage: {crop.growth_stage || "Not specified"}</small></div><button className="icon-action" onClick={() => { setSelectedCrop(String(crop.id)); analyzeCrop(String(crop.id)); }} disabled={loading} aria-label={`Analyze ${crop.crop}`}>→</button></article>)}</div> : <div className="empty-inline">No crops found for this farm yet. Add a crop to enable risk assessment.</div>}
        </section>
      </>}

      {page === "My Farms" && <>
        <section className="page-intro-row"><div><span className="eyebrow green-eyebrow">FARM MANAGEMENT</span><h2>Your farms</h2><p>Keep farm locations, area, and soil inputs together.</p></div><button className="button button-primary" onClick={() => setShowFarmForm((open) => !open)}>{showFarmForm ? "× Cancel" : "＋ Add farm"}</button></section>
        {showFarmForm && <section className="surface-card form-card"><div className="section-heading"><div><h3>Register a farm</h3><p>Enter the farm details to save a new record.</p></div><span className="heading-icon">＋</span></div><form onSubmit={createFarm} className="form-grid"><label className="field-label">Farm name<input className="field-input" value={farmName} onChange={(event) => setFarmName(event.target.value)} required placeholder="e.g. North Field" /></label><label className="field-label">Location<input className="field-input" value={farmLocation} onChange={(event) => setFarmLocation(event.target.value)} required placeholder="Village, district or region" /></label><label className="field-label">Area (acres)<input className="field-input" type="number" min="0.01" step="any" value={farmArea} onChange={(event) => setFarmArea(event.target.value)} required /></label><label className="field-label">Soil moisture (%)<input className="field-input" type="number" min="0" max="100" step="any" value={soilMoisture} onChange={(event) => setSoilMoisture(event.target.value)} /></label><label className="field-label">Soil pH<input className="field-input" type="number" min="0" max="14" step="0.1" value={soilPh} onChange={(event) => setSoilPh(event.target.value)} /></label><div className="form-actions"><button className="button button-primary" disabled={loading}>{loading ? "Saving…" : "Save farm"}</button><button className="button button-ghost" type="button" onClick={() => setShowFarmForm(false)}>Cancel</button></div></form></section>}
        {farms.length ? <div className="farm-card-grid">{farms.map((farm) => <article className={`farm-record ${String(farm.id) === String(selectedFarm) ? "selected" : ""}`} key={farm.id}><div className="farm-record-top"><div className="farm-record-icon">⌂</div>{String(farm.id) === String(selectedFarm) && <span className="selected-pill">SELECTED</span>}</div><h3>{farm.name}</h3><p className="farm-location">⌖ {farm.location || "Location not specified"}</p><div className="farm-record-metrics"><div><span>AREA</span><b>{farm.area ?? "—"} {farm.area_unit || "acres"}</b></div><div><span>SOIL MOISTURE</span><b>{farm.soil_moisture ?? "—"}{farm.soil_moisture != null ? "%" : ""}</b></div><div><span>SOIL pH</span><b>{farm.soil_ph ?? "—"}</b></div></div><button className="button button-secondary button-wide" onClick={() => { setSelectedFarm(String(farm.id)); navigate("Crop Health"); }}>View crops <span>→</span></button></article>)}</div> : <div className="surface-card empty-state"><div className="empty-icon">⌂</div><h3>No farms registered</h3><p>Add your first farm to start using the FarmShield workspace.</p><button className="button button-primary" onClick={() => setShowFarmForm(true)}>＋ Register a farm</button></div>}
      </>}

      {page === "Crop Health" && <>
        <section className="page-intro-row"><div><span className="eyebrow green-eyebrow">CROP MANAGEMENT</span><h2>Crop health</h2><p>Select a farm, manage crop records, and request a risk assessment.</p></div><button className="button button-primary" onClick={() => setShowCropForm((open) => !open)} disabled={!selectedFarm}>{showCropForm ? "× Cancel" : "＋ Add crop"}</button></section>
        <section className="surface-card farm-select-bar"><label className="field-label">Viewing farm<select className="field-input" value={selectedFarm} onChange={(event) => setSelectedFarm(event.target.value)}><option value="">Select a farm</option>{farms.map((farm) => <option key={farm.id} value={farm.id}>{farm.name} — {farm.location}</option>)}</select></label><div className="farm-select-note"><span className="demo-dot" /> Crop records are loaded from the backend.</div></section>
        {showCropForm && <section className="surface-card form-card"><div className="section-heading"><div><h3>Add a crop</h3><p>Save a crop record under the selected farm.</p></div><span className="heading-icon">♧</span></div><form onSubmit={createCrop} className="form-grid"><label className="field-label">Crop type<select className="field-input" value={cropName} onChange={(event) => setCropName(event.target.value)}>{cropOptions.map((crop) => <option key={crop} value={crop}>{crop}</option>)}</select></label><label className="field-label">Variety (optional)<input className="field-input" value={cropVariety} onChange={(event) => setCropVariety(event.target.value)} placeholder="e.g. Pusa Basmati 1509" /></label><label className="field-label">Growth stage<select className="field-input" value={growthStage} onChange={(event) => setGrowthStage(event.target.value)}>{stageOptions.map((stage) => <option key={stage} value={stage}>{stage[0].toUpperCase() + stage.slice(1)}</option>)}</select></label><label className="field-label">Planting date<input className="field-input" type="date" value={plantingDate} onChange={(event) => setPlantingDate(event.target.value)} required /></label><div className="form-actions"><button className="button button-primary" disabled={loading || !selectedFarm}>{loading ? "Saving…" : "Save crop"}</button><button className="button button-ghost" type="button" onClick={() => setShowCropForm(false)}>Cancel</button></div></form></section>}
        {crops.length ? <div className="crop-card-grid health-grid">{crops.map((crop) => <article className="crop-health-card" key={crop.id}><div className="crop-health-top"><div className="crop-emblem large">🌾</div><span className="status-chip neutral">NOT ASSESSED</span></div><h3>{crop.crop}</h3><p>{crop.variety || "Variety not specified"}</p><div className="crop-stage-row"><span>Growth stage</span><b>{crop.growth_stage || "Not specified"}</b></div><div className="crop-stage-row"><span>Crop record ID</span><b>#{crop.id}</b></div><button className="button button-primary button-wide" onClick={() => analyzeCrop(String(crop.id))} disabled={loading}>{loading ? "Analyzing…" : "Analyze crop risk →"}</button><p className="card-demo-note">Demo model · placeholder inputs</p></article>)}</div> : <div className="surface-card empty-state"><div className="empty-icon">♧</div><h3>No crops in this farm</h3><p>Choose a farm with crop records or add a crop to this farm.</p><button className="button button-primary" onClick={() => setShowCropForm(true)} disabled={!selectedFarm}>＋ Add a crop</button></div>}
      </>}

      {page === "AI Analysis" && <>
        <section className="page-intro-row"><div><span className="eyebrow green-eyebrow">MODEL OUTPUT</span><h2>AI crop-risk analysis</h2><p>A readable view of the latest assessment returned by your backend.</p></div><button className="button button-secondary" onClick={() => navigate("Dashboard")}>← Back to dashboard</button></section>
        {!prediction ? <div className="surface-card empty-state"><div className="empty-icon">✳</div><h3>No assessment generated yet</h3><p>Select a farm and crop on the dashboard, then run an assessment to see the result here.</p><button className="button button-primary" onClick={() => navigate("Dashboard")}>Start an assessment →</button></div> : <>
          <div className="analysis-context"><div className="context-icon">🌱</div><div><span>ASSESSMENT SUBJECT</span><b>{predictionFarm?.name || "Selected farm"} · {predictionCrop?.crop || "Selected crop"}</b><small>{predictionCrop?.variety || "Variety not specified"} · Stage: {predictionCrop?.growth_stage || "Not specified"}</small></div><span className="status-chip neutral">DEVELOPMENT MODEL</span></div>
          <section className="analysis-result-grid"><article className="surface-card risk-result-card"><div className="section-heading"><div><span className="eyebrow">RISK OUTPUT</span><h3>Predicted crop-stress risk</h3></div><span className={`status-chip ${riskClass}`}>{riskLevel}</span></div><div className={`risk-score ${riskClass}`}><div><strong>{riskPercent == null ? "—" : `${riskPercent.toFixed(1)}%`}</strong><span>MODEL RISK SCORE</span></div><div className="risk-track"><span style={{ width: `${riskPercent ?? 0}%` }} /></div></div><p className="risk-result-caption">This is a model output for demonstration, not a verified probability of crop loss or a real-world diagnosis.</p><div className="analysis-meta"><div><span>Model</span><b>{prediction.model_name || "Development model"}</b></div><div><span>Version</span><b>{prediction.model_version || "Not provided"}</b></div><div><span>Confidence output</span><b>{prediction.confidence == null ? "Not provided" : `${(Number(prediction.confidence) <= 1 ? Number(prediction.confidence) * 100 : Number(prediction.confidence)).toFixed(1)}%`}</b></div></div></article>
            <article className="surface-card factors-card"><div className="section-heading"><div><span className="eyebrow">INTERPRETATION</span><h3>What the model returned</h3><p>These explanations are development output and may need agronomic validation.</p></div><span className="heading-icon">⌁</span></div><div className="factor-primary"><span className="factor-symbol">!</span><div><span>PRIMARY RISK FACTOR</span><b>{prediction.primary_risk || "Not provided"}</b></div></div><div className="factor-list"><h4>Additional factors</h4>{prediction.secondary_risks?.length ? <ul>{prediction.secondary_risks.map((risk, index) => <li key={`${risk}-${index}`}>{risk}</li>)}</ul> : <p>No additional factors returned by the model.</p>}</div></article></section>
          <section className="surface-card explanation-card"><div className="section-heading"><div><span className="eyebrow">MODEL EXPLANATION</span><h3>Assessment notes</h3><p>Items returned by the current development pipeline.</p></div></div>{prediction.explanation?.length ? <ol className="explanation-list">{prediction.explanation.map((item, index) => <li key={`${item}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span><p>{item}</p></li>)}</ol> : <p className="empty-inline">No explanation text was returned by this assessment.</p>}<div className="validation-warning"><span>ⓘ</span><p><b>Important limitation</b><br />This prototype uses placeholder environmental readings and a model trained on synthetic development data. Its scores and confidence output have not been validated for real-world farming. Use local observations and qualified agricultural advice for actual decisions.</p></div><button className="button button-primary" onClick={() => navigate("Dashboard")}>Run another assessment →</button></section>
        </>}
      </>}

      <footer className="app-footer"><span>© FarmShield AI</span><span>Prototype build · Synthetic-model development · Not for operational farm decisions</span></footer>
    </main>
  </div>;
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode><App /></React.StrictMode>
);
