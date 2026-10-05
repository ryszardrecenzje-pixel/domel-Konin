/**
 * Domel Konin – prosty koszyk (localStorage)
 * Działa na promocjach i innych podstronach po dołączeniu tego pliku.
 */
(function () {
  const KEY = "domel_koszyk_v1";

  function read() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "[]");
    } catch (e) {
      return [];
    }
  }

  function write(items) {
    localStorage.setItem(KEY, JSON.stringify(items));
    updateBadge();
    document.dispatchEvent(new CustomEvent("domel-cart-changed", { detail: items }));
  }

  function parsePrice(str) {
    if (typeof str === "number") return str;
    const d = String(str || "").replace(/[^\d]/g, "");
    return d ? parseInt(d, 10) : 0;
  }

  function addItem(item) {
    const items = read();
    const id = item.id || item.tytul;
    const existing = items.find((x) => x.id === id);
    if (existing) {
      existing.qty = (existing.qty || 1) + (item.qty || 1);
    } else {
      items.push({
        id: id,
        tytul: item.tytul || "Produkt",
        cena: item.cena || "",
        cenaNum: parsePrice(item.cena),
        zdjecie: item.zdjecie || "images/logo.png",
        qty: item.qty || 1,
      });
    }
    write(items);
    return items;
  }

  function removeItem(id) {
    write(read().filter((x) => x.id !== id));
  }

  function setQty(id, qty) {
    const items = read();
    const it = items.find((x) => x.id === id);
    if (!it) return;
    it.qty = Math.max(1, parseInt(qty, 10) || 1);
    write(items);
  }

  function clear() {
    write([]);
  }

  function count() {
    return read().reduce((s, x) => s + (x.qty || 1), 0);
  }

  function total() {
    return read().reduce((s, x) => s + (x.cenaNum || parsePrice(x.cena)) * (x.qty || 1), 0);
  }

  function updateBadge() {
    const n = count();
    document.querySelectorAll("[data-cart-count]").forEach((el) => {
      el.textContent = String(n);
      el.style.display = n > 0 ? "" : "none";
    });
    document.querySelectorAll("[data-cart-total]").forEach((el) => {
      el.textContent = total().toLocaleString("pl-PL") + " zł";
    });
  }

  function toast(msg) {
    let t = document.getElementById("domel-cart-toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "domel-cart-toast";
      t.style.cssText =
        "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#0f172a;color:#fff;padding:12px 20px;border-radius:8px;z-index:10000;font-size:0.95rem;box-shadow:0 8px 24px rgba(0,0,0,.25);opacity:0;transition:opacity .2s";
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.opacity = "1";
    clearTimeout(t._timer);
    t._timer = setTimeout(() => {
      t.style.opacity = "0";
    }, 2200);
  }

  // Global API
  window.DomelCart = {
    read,
    addItem,
    removeItem,
    setQty,
    clear,
    count,
    total,
    updateBadge,
    toast,
  };

  document.addEventListener("DOMContentLoaded", function () {
    updateBadge();

    document.body.addEventListener("click", function (e) {
      const btn = e.target.closest("[data-add-to-cart]");
      if (!btn) return;
      e.preventDefault();
      const card = btn.closest(".product-card") || btn;
      const tytul =
        btn.getAttribute("data-title") ||
        (card.querySelector("h3") && card.querySelector("h3").textContent) ||
        "Produkt";
      const cena =
        btn.getAttribute("data-price") ||
        (card.querySelector(".cena") && card.querySelector(".cena").textContent) ||
        "";
      const imgEl = card.querySelector(".product-card-image img");
      const zdjecie =
        btn.getAttribute("data-image") || (imgEl && imgEl.getAttribute("src")) || "images/logo.png";
      addItem({ id: tytul, tytul, cena, zdjecie });
      toast("Dodano do koszyka: " + tytul.slice(0, 48) + (tytul.length > 48 ? "…" : ""));
      btn.classList.add("added");
      setTimeout(() => btn.classList.remove("added"), 600);
    });
  });
})();
