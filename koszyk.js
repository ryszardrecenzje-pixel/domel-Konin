/**
 * Domel Konin – koszyk wyceny (localStorage)
 * Dodawanie produktów → panel koszyka → „Proszę o wycenę” → formularz na index.html
 */
(function () {
  "use strict";

  var STORAGE_KEY = "domel_koszyk_wyceny";
  var FORM_PAGE = "index.html#repair";

  function loadCart() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function saveCart(items) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    updateUI();
  }

  function productKey(p) {
    return (p.id || p.tytul || "").toLowerCase().trim();
  }

  function addToCart(product) {
    var items = loadCart();
    var key = productKey(product);
    if (!key) return;
    var exists = items.some(function (x) {
      return productKey(x) === key;
    });
    if (exists) {
      showToast("Ten produkt jest już na liście wyceny");
      openPanel();
      return;
    }
    items.push({
      id: product.id || key,
      tytul: product.tytul || "Produkt",
      status: product.status || "",
      cena: product.cena || "",
      src: product.src || window.location.pathname.split("/").pop() || ""
    });
    saveCart(items);
    showToast("Dodano do wyceny: " + (product.tytul || ""));
  }

  function removeFromCart(id) {
    var key = (id || "").toLowerCase().trim();
    var items = loadCart().filter(function (x) {
      return productKey(x) !== key;
    });
    saveCart(items);
  }

  function clearCart() {
    saveCart([]);
  }

  function buildQuoteMessage(items) {
    if (!items.length) return "";
    var lines = [
      "Dzień dobry,",
      "",
      "Proszę o wycenę następujących produktów:",
      ""
    ];
    items.forEach(function (p, i) {
      var line = i + 1 + ". " + p.tytul;
      if (p.status) line += " (" + p.status + ")";
      if (p.cena) line += " – " + p.cena;
      lines.push(line);
    });
    lines.push("");
    lines.push("Proszę o kontakt z propozycją ceny / dostępności.");
    lines.push("Pozdrawiam");
    return lines.join("\n");
  }

  function goToQuote() {
    var items = loadCart();
    if (!items.length) {
      showToast("Dodaj najpierw produkty do wyceny");
      return;
    }
    // zapisz też gotową treść – formularz ją wczyta
    localStorage.setItem(STORAGE_KEY + "_msg", buildQuoteMessage(items));
    var base = FORM_PAGE;
    // jeśli już jesteśmy na index.html
    if (/index\.html$/i.test(window.location.pathname) || window.location.pathname.endsWith("/")) {
      fillFormIfPresent();
      var el = document.getElementById("repair");
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        closePanel();
        return;
      }
    }
    window.location.href = base;
  }

  function fillFormIfPresent() {
    var ta = document.getElementById("message");
    if (!ta) return;
    var items = loadCart();
    var msg = localStorage.getItem(STORAGE_KEY + "_msg") || buildQuoteMessage(items);
    if (msg && items.length) {
      ta.value = msg;
      // ukryte pole dla Formspree
      var hidden = document.getElementById("koszyk_produkty");
      if (!hidden) {
        hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = "produkty_do_wyceny";
        hidden.id = "koszyk_produkty";
        var form = ta.closest("form");
        if (form) form.appendChild(hidden);
      }
      hidden.value = items.map(function (p) {
        return p.tytul;
      }).join("; ");

      var title = document.querySelector("#repair h2");
      if (title && items.length) {
        title.textContent = "Prośba o wycenę (" + items.length + " prod.)";
      }
      var desc = document.querySelector("#repair .section-desc");
      if (desc && items.length) {
        desc.textContent =
          "Lista wybranych produktów została wpisana w treść wiadomości. Uzupełnij dane kontaktowe i wyślij zgłoszenie.";
      }
    }
  }

  /* ---------- UI ---------- */

  function ensureStyles() {
    if (document.getElementById("domel-koszyk-css")) return;
    var css = document.createElement("style");
    css.id = "domel-koszyk-css";
    css.textContent = [
      ".btn-add-quote{margin-top:10px;width:100%;padding:10px 12px;background:#1a4b84;color:#fff;border:none;border-radius:6px;font-weight:600;cursor:pointer;font-size:0.9rem;transition:background .2s}",
      ".btn-add-quote:hover{background:#0b3d6d}",
      ".btn-add-quote.in-cart{background:#28a745}",
      "#domel-cart-fab{position:fixed;right:20px;bottom:24px;z-index:10000;width:58px;height:58px;border-radius:50%;background:#ff6600;color:#fff;border:none;box-shadow:0 4px 16px rgba(0,0,0,.25);cursor:pointer;font-size:1.4rem;display:flex;align-items:center;justify-content:center}",
      "#domel-cart-fab:hover{background:#e55c00}",
      "#domel-cart-count{position:absolute;top:-4px;right:-4px;background:#1a4b84;color:#fff;font-size:12px;font-weight:700;min-width:22px;height:22px;border-radius:11px;display:none;align-items:center;justify-content:center;padding:0 5px}",
      "#domel-cart-count.show{display:flex}",
      "#domel-cart-overlay{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10001;opacity:0;pointer-events:none;transition:opacity .2s}",
      "#domel-cart-overlay.open{opacity:1;pointer-events:auto}",
      "#domel-cart-panel{position:fixed;top:0;right:0;width:min(380px,100%);height:100%;background:#fff;z-index:10002;box-shadow:-4px 0 24px rgba(0,0,0,.15);transform:translateX(100%);transition:transform .25s ease;display:flex;flex-direction:column}",
      "#domel-cart-panel.open{transform:translateX(0)}",
      ".domel-cart-header{padding:16px 18px;background:#1a4b84;color:#fff;display:flex;justify-content:space-between;align-items:center}",
      ".domel-cart-header h3{margin:0;font-size:1.1rem}",
      ".domel-cart-close{background:transparent;border:none;color:#fff;font-size:1.6rem;cursor:pointer;line-height:1}",
      ".domel-cart-body{flex:1;overflow-y:auto;padding:12px 16px}",
      ".domel-cart-empty{color:#888;text-align:center;padding:2rem 1rem}",
      ".domel-cart-item{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;padding:12px 0;border-bottom:1px solid #eee}",
      ".domel-cart-item-info{flex:1}",
      ".domel-cart-item-info strong{display:block;color:#1a4b84;font-size:0.95rem}",
      ".domel-cart-item-info span{font-size:0.8rem;color:#666}",
      ".domel-cart-remove{background:transparent;border:none;color:#c0392b;cursor:pointer;font-size:1.1rem;padding:4px}",
      ".domel-cart-footer{padding:14px 16px;border-top:1px solid #eee;display:flex;flex-direction:column;gap:8px}",
      ".domel-cart-footer .btn-quote{background:#ff6600;color:#fff;border:none;padding:12px;border-radius:6px;font-weight:700;cursor:pointer;font-size:1rem}",
      ".domel-cart-footer .btn-quote:hover{background:#e55c00}",
      ".domel-cart-footer .btn-clear{background:#f0f0f0;color:#333;border:none;padding:8px;border-radius:6px;cursor:pointer;font-size:0.85rem}",
      "#domel-toast{position:fixed;bottom:90px;right:20px;z-index:10003;background:#1a4b84;color:#fff;padding:10px 16px;border-radius:8px;font-size:0.9rem;opacity:0;transform:translateY(10px);transition:opacity .2s,transform .2s;pointer-events:none;max-width:280px}",
      "#domel-toast.show{opacity:1;transform:translateY(0)}"
    ].join("");
    document.head.appendChild(css);
  }

  function ensureUI() {
    if (document.getElementById("domel-cart-fab")) return;
    ensureStyles();

    var fab = document.createElement("button");
    fab.id = "domel-cart-fab";
    fab.type = "button";
    fab.setAttribute("aria-label", "Lista wyceny");
    fab.innerHTML =
      '<i class="fa-solid fa-clipboard-list"></i><span id="domel-cart-count">0</span>';
    fab.addEventListener("click", openPanel);
    document.body.appendChild(fab);

    var overlay = document.createElement("div");
    overlay.id = "domel-cart-overlay";
    overlay.addEventListener("click", closePanel);
    document.body.appendChild(overlay);

    var panel = document.createElement("div");
    panel.id = "domel-cart-panel";
    panel.innerHTML =
      '<div class="domel-cart-header"><h3>Lista do wyceny</h3><button type="button" class="domel-cart-close" aria-label="Zamknij">&times;</button></div>' +
      '<div class="domel-cart-body" id="domel-cart-body"></div>' +
      '<div class="domel-cart-footer">' +
      '<button type="button" class="btn-quote" id="domel-btn-quote">Proszę o wycenę</button>' +
      '<button type="button" class="btn-clear" id="domel-btn-clear">Wyczyść listę</button>' +
      "</div>";
    document.body.appendChild(panel);
    panel.querySelector(".domel-cart-close").addEventListener("click", closePanel);
    document.getElementById("domel-btn-quote").addEventListener("click", goToQuote);
    document.getElementById("domel-btn-clear").addEventListener("click", function () {
      if (loadCart().length && confirm("Wyczyścić listę wyceny?")) clearCart();
    });

    var toast = document.createElement("div");
    toast.id = "domel-toast";
    document.body.appendChild(toast);
  }

  function openPanel() {
    ensureUI();
    renderPanel();
    document.getElementById("domel-cart-overlay").classList.add("open");
    document.getElementById("domel-cart-panel").classList.add("open");
  }

  function closePanel() {
    var o = document.getElementById("domel-cart-overlay");
    var p = document.getElementById("domel-cart-panel");
    if (o) o.classList.remove("open");
    if (p) p.classList.remove("open");
  }

  function renderPanel() {
    var body = document.getElementById("domel-cart-body");
    if (!body) return;
    var items = loadCart();
    if (!items.length) {
      body.innerHTML = '<p class="domel-cart-empty">Lista jest pusta.<br>Dodaj produkty przyciskiem „Dodaj do wyceny”.</p>';
      return;
    }
    body.innerHTML = items
      .map(function (p) {
        var meta = [p.status, p.cena].filter(Boolean).join(" · ");
        return (
          '<div class="domel-cart-item">' +
          '<div class="domel-cart-item-info"><strong>' +
          escapeHtml(p.tytul) +
          "</strong>" +
          (meta ? "<span>" + escapeHtml(meta) + "</span>" : "") +
          '</div><button type="button" class="domel-cart-remove" data-id="' +
          escapeAttr(productKey(p)) +
          '" title="Usuń">&times;</button></div>'
        );
      })
      .join("");
    body.querySelectorAll(".domel-cart-remove").forEach(function (btn) {
      btn.addEventListener("click", function () {
        removeFromCart(btn.getAttribute("data-id"));
      });
    });
  }

  function updateUI() {
    ensureUI();
    var items = loadCart();
    var badge = document.getElementById("domel-cart-count");
    if (badge) {
      badge.textContent = String(items.length);
      if (items.length) badge.classList.add("show");
      else badge.classList.remove("show");
    }
    // oznacz przyciski na stronie
    var keys = {};
    items.forEach(function (p) {
      keys[productKey(p)] = true;
    });
    document.querySelectorAll(".btn-add-quote").forEach(function (btn) {
      var id = (btn.getAttribute("data-id") || btn.getAttribute("data-title") || "").toLowerCase();
      if (keys[id]) {
        btn.classList.add("in-cart");
        btn.textContent = "Na liście wyceny ✓";
      } else {
        btn.classList.remove("in-cart");
        btn.textContent = "Dodaj do wyceny";
      }
    });
    if (document.getElementById("domel-cart-panel") && document.getElementById("domel-cart-panel").classList.contains("open")) {
      renderPanel();
    }
  }

  function showToast(text) {
    ensureUI();
    var t = document.getElementById("domel-toast");
    if (!t) return;
    t.textContent = text;
    t.classList.add("show");
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(function () {
      t.classList.remove("show");
    }, 2200);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function escapeAttr(s) {
    return escapeHtml(s).replace(/'/g, "&#39;");
  }

  function slugify(s) {
    return String(s || "")
      .toLowerCase()
      .trim()
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9ąćęłńóśźż\-]/gi, "");
  }

  /** Dokleja przyciski do istniejących kart .product-card */
  function enhanceCards() {
    document.querySelectorAll(".product-card").forEach(function (card) {
      if (card.querySelector(".btn-add-quote")) return;
      var h3 = card.querySelector("h3");
      if (!h3) return;
      var title = h3.textContent.trim();
      var id = card.getAttribute("data-id") || slugify(title);
      var statusEl = card.querySelector(".availability");
      var status = statusEl ? statusEl.textContent.trim() : "";
      var cenaEl = card.querySelector(".cena");
      var cena = cenaEl ? cenaEl.textContent.trim() : "";

      card.setAttribute("data-id", id);
      if (!card.getAttribute("data-title")) card.setAttribute("data-title", title.toLowerCase());

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn-add-quote";
      btn.setAttribute("data-id", id);
      btn.setAttribute("data-title", title);
      btn.setAttribute("data-status", status);
      btn.setAttribute("data-cena", cena);
      btn.textContent = "Dodaj do wyceny";
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        addToCart({
          id: id,
          tytul: title,
          status: status,
          cena: cena,
          src: window.location.pathname.split("/").pop() || ""
        });
      });
      card.appendChild(btn);
    });
  }

  function bindExistingButtons() {
    document.querySelectorAll(".btn-add-quote").forEach(function (btn) {
      if (btn._domelBound) return;
      btn._domelBound = true;
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        addToCart({
          id: btn.getAttribute("data-id") || btn.getAttribute("data-title"),
          tytul: btn.getAttribute("data-title") || btn.getAttribute("data-id"),
          status: btn.getAttribute("data-status") || "",
          cena: btn.getAttribute("data-cena") || "",
          src: window.location.pathname.split("/").pop() || ""
        });
      });
    });
  }

  function init() {
    ensureUI();
    enhanceCards();
    bindExistingButtons();
    updateUI();
    fillFormIfPresent();

    // jeśli hash #repair – przewiń
    if (window.location.hash === "#repair") {
      setTimeout(function () {
        var el = document.getElementById("repair");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 100);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // public API (opcjonalnie)
  window.DomelKoszyk = {
    add: addToCart,
    remove: removeFromCart,
    clear: clearCart,
    items: loadCart,
    open: openPanel,
    quote: goToQuote
  };
})();
