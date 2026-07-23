// Diktat für kennora.
// Aufnahme über ein WÄHLBARES Mikrofon (getUserMedia) – nur dieses Mikrofon,
// nie System-/Meetingaudio. Segmente (12 s) gehen Base64-in-JSON an /diktat
// (Text-Body -> proxy-verträglich). Der erkannte Text landet im Feld; die Person
// liest gegen und legt selbst ab. Mehrsprachig: die Sprache wird serverseitig
// automatisch erkannt.
(function () {
  var btn = document.getElementById('diktat-btn');
  var textarea = document.getElementById('answer-text');
  var micSel = document.getElementById('mic-select');
  var statusEl = document.getElementById('voice-status');
  if (!btn || !textarea || btn.dataset.stt !== '1') return;

  var statusEl0 = document.getElementById('voice-status');
  var canRecord = navigator.mediaDevices && navigator.mediaDevices.getUserMedia &&
                  typeof MediaRecorder !== 'undefined';
  if (!canRecord) {
    // Häufigster Grund: unsicherer Kontext (http). Browser geben das Mikrofon
    // nur über HTTPS (oder localhost) frei. Nicht stumm verstecken – erklären.
    btn.disabled = true;
    btn.style.opacity = '0.55';
    btn.style.cursor = 'not-allowed';
    if (statusEl0) {
      statusEl0.textContent = (typeof window.isSecureContext !== 'undefined' && !window.isSecureContext)
        ? 'Diktat braucht eine sichere Verbindung – öffne die Seite über https://'
        : 'Dieser Browser unterstützt keine Aufnahme.';
    }
    return;
  }

  var endpoint = btn.dataset.endpoint || '/diktat';
  var SEG_MS = 12000;
  var stream = null, recorder = null, timer = null, running = false;
  var sendQueue = [], sending = false;

  function setStatus(t) { if (statusEl) statusEl.textContent = t || ''; }
  function setUi(on) { btn.textContent = on ? '⏹ Stoppen' : '🎤 Sprechen'; btn.classList.toggle('rec', on); }
  function append(text) {
    if (!text) return;
    textarea.value = (textarea.value ? textarea.value.trim() + ' ' : '') + text;
  }

  function savedMic() { try { return localStorage.getItem('kennora-mic') || ''; } catch (e) { return ''; } }

  function refreshDevices() {
    if (!micSel) return;
    navigator.mediaDevices.enumerateDevices().then(function (devs) {
      var saved = savedMic();
      micSel.innerHTML = '';
      var def = document.createElement('option');
      def.value = ''; def.textContent = 'Standard-Mikrofon';
      micSel.appendChild(def);
      var i = 0;
      devs.forEach(function (d) {
        if (d.kind !== 'audioinput' || !d.deviceId || d.deviceId === 'default') return;
        i += 1;
        var o = document.createElement('option');
        o.value = d.deviceId; o.textContent = d.label || ('Mikrofon ' + i);
        micSel.appendChild(o);
      });
      micSel.value = saved;
      if (micSel.selectedIndex < 0) micSel.value = '';
    }).catch(function () {});
  }

  if (micSel) {
    micSel.style.display = '';
    refreshDevices();
    if (navigator.mediaDevices.addEventListener) {
      navigator.mediaDevices.addEventListener('devicechange', refreshDevices);
    }
    micSel.addEventListener('change', function () {
      try { localStorage.setItem('kennora-mic', micSel.value); } catch (e) {}
      if (running) { stop(); start(); }
    });
  }

  function toB64(blob) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(String(fr.result).split(',')[1] || ''); };
      fr.onerror = reject;
      fr.readAsDataURL(blob);
    });
  }

  function enqueue(blob) { sendQueue.push(blob); while (sendQueue.length > 3) sendQueue.shift(); pump(); }

  function pump() {
    if (sending || !sendQueue.length) {
      if (!sending && !sendQueue.length && !running) setStatus('Fertig – der Text steht im Feld, du kannst ihn anpassen.');
      return;
    }
    sending = true;
    var blob = sendQueue.shift();
    toB64(blob).then(function (b64) {
      return fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio: b64, mime: blob.type || 'audio/webm' })
      });
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d.text) append(d.text);
      if (d.error) setStatus('Diktat: ' + d.error);
      else if (running) setStatus('Aufnahme läuft – nur das gewählte Mikrofon wird erfasst …');
    }).catch(function () { setStatus('Diktat gerade verzögert – läuft weiter …'); })
      .then(function () { sending = false; pump(); });
  }

  function recordSegment() {
    if (!running || !stream) return;
    var chunks = [];
    try { recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' }); }
    catch (e) { recorder = new MediaRecorder(stream); }
    recorder.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
    recorder.onstop = function () {
      if (chunks.length) enqueue(new Blob(chunks, { type: recorder.mimeType || 'audio/webm' }));
      if (running) recordSegment();
    };
    recorder.start();
    timer = setTimeout(function () {
      if (recorder && recorder.state !== 'inactive') recorder.stop();
    }, SEG_MS);
  }

  function start() {
    var id = micSel ? micSel.value : '';
    var constraints = { audio: id ? { deviceId: { exact: id } } : true };
    navigator.mediaDevices.getUserMedia(constraints).then(function (s) {
      stream = s; running = true; setUi(true);
      setStatus('Aufnahme läuft – nur das gewählte Mikrofon wird erfasst …');
      if (micSel) refreshDevices();   // Labels sind erst nach Zugriff sichtbar
      recordSegment();
    }).catch(function () { setStatus('Kein Zugriff aufs Mikrofon.'); });
  }

  function stop() {
    running = false; setUi(false);
    if (timer) { clearTimeout(timer); timer = null; }
    if (recorder && recorder.state !== 'inactive') recorder.stop();
    if (stream) { stream.getTracks().forEach(function (t) { t.stop(); }); stream = null; }
    setStatus('Transkribiere …');
  }

  btn.addEventListener('click', function () { running ? stop() : start(); });
})();
