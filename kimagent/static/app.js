/* Kimagent — interactions de l'interface web (exécution, Ollama, démo) */
(function () {
  "use strict";

  // ── Tableau de bord : état Ollama + données démo ─────────────────────────
  var ollamaEl = document.getElementById("ollama-status");
  if (ollamaEl) loadOllama(ollamaEl);

  document.querySelectorAll("[data-demo]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      btn.disabled = true;
      fetch("/api/demo", { method: "POST" })
        .then(function (r) { return r.json(); })
        .then(function () { location.href = "/"; })
        .catch(function (e) { alert("Échec : " + e); btn.disabled = false; });
    });
  });

  // ── Formulaire d'exécution ────────────────────────────────────────────────
  var form = document.getElementById("run-form");
  if (form) initRunForm(form);

  function personaVisibility(form) {
    var persona = form.querySelector("select[name=persona]").value;
    form.querySelectorAll(".task-group").forEach(function (g) {
      g.style.display = g.dataset.persona === persona ? "" : "none";
    });
    var wrap = document.getElementById("ollama-wrap");
    if (wrap) wrap.style.display = form.dataset.brain === "ollama" ? "" : "none";
  }

  function initRunForm(form) {
    var select = form.querySelector("select[name=persona]");
    select.addEventListener("change", function () { personaVisibility(form); });
    personaVisibility(form);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var persona = select.value;
      var tasks = [];
      form.querySelectorAll(".task-group").forEach(function (g) {
        if (g.dataset.persona !== persona) return;
        g.querySelectorAll("input[type=checkbox]:checked").forEach(function (cb) {
          tasks.push(cb.value);
        });
      });
      var payload = {
        persona: persona,
        tasks: tasks,
        demo: form.querySelector("[name=demo]").checked,
        force: form.querySelector("[name=force]").checked,
        no_brain: form.querySelector("[name=no_brain]").checked,
        ollama_model: (form.querySelector("[name=ollama_model]").value || "").trim() || null
      };

      var btn = form.querySelector("button[type=submit]");
      var section = document.getElementById("run-section");
      var consoleEl = document.getElementById("run-console");
      var resultsEl = document.getElementById("run-results");
      section.style.display = "";
      consoleEl.textContent = "";
      resultsEl.innerHTML = "";
      section.scrollIntoView({ behavior: "smooth" });
      btn.disabled = true;
      btn.textContent = "⏳ En cours…";

      fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
        .then(function (r) {
          if (!r.ok) return r.json().then(function (d) { throw new Error(d.error || r.status); });
          return r.json();
        })
        .then(function (d) {
          appendLog(consoleEl, "step", "Lancement de « " + persona + " » — exécution en arrière-plan…");
          pollRun(d.run_id, consoleEl, resultsEl, 0);
        })
        .catch(function (err) { appendLog(consoleEl, "err", String(err.message || err)); })
        .finally(function () { btn.disabled = false; btn.textContent = "▶ Lancer"; });
    });
  }

  function pollRun(runId, consoleEl, resultsEl, since) {
    fetch("/api/run/" + runId + "?since=" + since)
      .then(function (r) {
        if (!r.ok) throw new Error("Exécution introuvable");
        return r.json();
      })
      .then(function (d) {
        (d.new_logs || []).forEach(function (l) { appendLog(consoleEl, l.kind, l.msg); });
        consoleEl.scrollTop = consoleEl.scrollHeight;
        if (d.status === "running") {
          setTimeout(function () { pollRun(runId, consoleEl, resultsEl, d.total); }, 1200);
        } else {
          finishRun(d, consoleEl, resultsEl);
        }
      })
      .catch(function (e) { appendLog(consoleEl, "warn", "Suivi interrompu : " + e); });
  }

  function finishRun(d, consoleEl, resultsEl) {
    if (d.status === "error") {
      appendLog(consoleEl, "err", d.error || "Erreur inconnue.");
      return;
    }
    appendLog(consoleEl, "ok", "Terminé : " + d.written.length + " livrable(s) généré(s).");
    d.written.forEach(function (w) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = w.url;
      a.textContent = "📄 " + w.name;
      li.appendChild(a);
      resultsEl.appendChild(li);
    });
    var more = document.createElement("li");
    var a2 = document.createElement("a");
    a2.href = "/outputs";
    a2.textContent = "→ Voir tous les livrables";
    more.appendChild(a2);
    resultsEl.appendChild(more);
  }

  function appendLog(pre, kind, msg) {
    var icons = { step: "→", ok: "✔", warn: "⚠", err: "✖", info: "ℹ" };
    var span = document.createElement("span");
    span.className = "log-" + kind;
    span.textContent = (icons[kind] || "·") + " " + msg + "\n";
    pre.appendChild(span);
  }

  function loadOllama(el) {
    fetch("/api/ollama")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.ok) {
          var list = d.models.length
            ? " · modèles : " + d.models.join(", ")
            : " · aucun modèle installé (<code>ollama pull qwen2.5:1.5b</code>)";
          el.innerHTML = '<span class="badge ok">● Ollama accessible</span> sur <code>' +
            d.url + "</code>" + list;
        } else {
          el.innerHTML = '<span class="badge err">● Ollama injoignable</span> sur <code>' +
            d.url + "</code> — lancez <code>ollama serve</code>";
        }
      })
      .catch(function () {
        el.innerHTML = '<span class="badge warn">● état inconnu</span>';
      });
  }
})();
