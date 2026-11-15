// Accessibility toolbar: font size + high contrast (remembered per browser).
(function () {
  const root = document.documentElement;
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
  };
  let fs = parseInt(store.get("fs") || "16", 10);
  const apply = () => {
    root.style.setProperty("--fs", fs + "px");
    document.body.classList.toggle("hc", store.get("hc") === "1");
  };
  apply();
  document.querySelectorAll("[data-a11y]").forEach((b) =>
    b.addEventListener("click", () => {
      const a = b.dataset.a11y;
      if (a === "font-up") fs = Math.min(fs + 2, 24);
      if (a === "font-down") fs = Math.max(fs - 2, 14);
      if (a === "contrast") store.set("hc", store.get("hc") === "1" ? "0" : "1");
      store.set("fs", String(fs));
      apply();
    })
  );
})();
