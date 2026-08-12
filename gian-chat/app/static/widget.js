/**
 * Bé Giản — widget chat cho web Anh Quang đơn giản.
 *
 * Nhúng 1 dòng:
 *   <script src="https://chat.<domain>/widget.js" defer></script>
 *
 * Tuỳ biến qua data-*:
 *   data-api          URL backend (mặc định suy ra từ src của chính script này)
 *   data-bot-name     Tên bot hiện trên header        (mặc định "Bé Giản")
 *   data-accent       Màu chủ đạo                     (mặc định #2E7D5B)
 *   data-avatar       URL ảnh đại diện
 *   data-greet        Ghi đè câu chào notification
 *   data-zalo         Link Zalo (để trống = ẩn nút)
 *   data-position     bottom-right | bottom-left
 *   data-footer       HTML dòng chân. Để "" là ẩn.
 *
 * ⚠️ MINIFY file này trước khi lên thật. MONA ship bản không minify và lộ
 *    sạch spec nội bộ lẫn số liệu kinh doanh.
 */
(function () {
  "use strict";

  // ── Chống mount đôi (plugin cache của WordPress hay chạy lại script) ──
  if (window.__GIAN_WIDGET_MOUNTED__) return;
  window.__GIAN_WIDGET_MOUNTED__ = true;

  // ─── Cấu hình ────────────────────────────────────────────────────────
  const script = document.currentScript ||
    document.querySelector('script[src*="widget.js"]');

  function deriveApi() {
    if (script && script.dataset.api) return script.dataset.api.replace(/\/$/, "");
    try { return new URL(script.src).origin; } catch (_) { return ""; }
  }

  const API       = deriveApi();
  const BOT_NAME  = (script && script.dataset.botName) || "Bé Giản";
  const ACCENT    = (script && script.dataset.accent) || "#2E7D5B";
  const ACCENT_2  = (script && script.dataset.accentSecondary) || "#7BAE8F";
  const AVATAR    = (script && script.dataset.avatar) || "";
  const POSITION  = (script && script.dataset.position) || "bottom-right";
  const ZALO_URL  = (script && script.dataset.zalo) || "";
  const GREET_OVERRIDE = (script && script.dataset.greet) || null;
  const SUBTITLE  = (script && script.dataset.botSubtitle) ||
                    "Trợ lý của anh Quang — đang online";
  const FOOTER    = (script && script.dataset.footer != null)
    ? script.dataset.footer
    : "Trợ lý AI của <b>Anh Quang đơn giản</b>";

  // ─── Bộ nhớ trình duyệt ──────────────────────────────────────────────
  const K_VISITOR   = "gian_visitor_id";
  const K_SESSION   = "gian_session_id";
  const K_SESS_TTL  = "gian_session_ttl";
  const K_CLICKS    = "gian_clickstream";
  const K_UTM       = "gian_utm";
  const K_CAMPAIGN  = "gian_campaign";
  const K_NOTIF_OFF = "gian_notif_dismissed_at";
  const K_LAST_MSG  = "gian_last_user_msg";
  const K_SEEN      = "gian_chat_seen";
  const K_NUDGE     = "gian_nudge_at";
  const K_PRICE_HIT = "gian_price_views";

  const SESSION_TTL_MS  = 7 * 24 * 3600 * 1000;   // khách quay lại trong 7 ngày → nối tiếp
  const NOTIF_COOLDOWN  = 24 * 3600 * 1000;
  const NOTIF_DELAY_1   = 3000;
  const NOTIF_DELAY_2   = 10000;
  const NUDGE_MS        = 10 * 60 * 1000;         // 10 phút (MONA để 5 — mình chậm hơn)
  const NUDGE_COOLDOWN  = 60 * 60 * 1000;
  const CLICKS_MAX      = 20;
  const CLICKS_TTL_H    = 24;
  const AGENT_POLL_MS   = 3000;

  function ls(k, v) {
    try {
      if (v === undefined) return localStorage.getItem(k);
      localStorage.setItem(k, v);
    } catch (_) {}
    return null;
  }
  // ID phải KHÔNG ĐOÁN ĐƯỢC: /history nhận visitor_id trần, ai biết id là đọc
  // được hội thoại của người đó. Math.random() cho ~40 bit — đoán được.
  // crypto cho 122 bit — không.
  function uid(p) {
    try {
      if (crypto.randomUUID) return p + "_" + crypto.randomUUID().replace(/-/g, "");
      const a = new Uint8Array(16);
      crypto.getRandomValues(a);
      return p + "_" + Array.from(a, function (b) {
        return b.toString(16).padStart(2, "0");
      }).join("");
    } catch (_) {
      return p + "_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
    }
  }

  let visitorId = ls(K_VISITOR);
  if (!visitorId) { visitorId = uid("v"); ls(K_VISITOR, visitorId); }

  let sessionId = null;
  (function restoreSession() {
    const ttl = parseInt(ls(K_SESS_TTL) || "0", 10);
    if (ttl && Date.now() < ttl) sessionId = ls(K_SESSION);
  })();
  function persistSession(id) {
    sessionId = id;
    ls(K_SESSION, id);
    ls(K_SESS_TTL, String(Date.now() + SESSION_TTL_MS));
  }

  // ─── Nguồn khách (first-touch, giữ nguyên cả phiên) ──────────────────
  const CLICK_IDS = ["fbclid", "gclid", "wbraid", "gbraid", "msclkid", "ttclid"];

  function captureUTM() {
    let saved = {};
    try { saved = JSON.parse(ls(K_UTM) || "{}"); } catch (_) {}
    if (saved.first_touch_ts) return saved;   // đã bắt rồi thì thôi

    const q = new URLSearchParams(location.search);
    const out = { first_touch_ts: Date.now(), landing_url: location.href,
                  referrer: document.referrer || "" };
    ["source", "medium", "campaign", "term", "content"].forEach(function (k) {
      const v = q.get("utm_" + k);
      if (v) out[k] = v;
    });
    CLICK_IDS.forEach(function (k) { const v = q.get(k); if (v) out[k] = v; });
    ls(K_UTM, JSON.stringify(out));
    return out;
  }
  function getUTM() {
    try { return JSON.parse(ls(K_UTM) || "{}"); } catch (_) { return {}; }
  }
  captureUTM();

  // ─── Hành trình xem trang ────────────────────────────────────────────
  function loadClicks() {
    try {
      const arr = JSON.parse(ls(K_CLICKS) || "[]");
      const cut = Date.now() - CLICKS_TTL_H * 3600 * 1000;
      return arr.filter(function (e) { return e.ts > cut; }).slice(-CLICKS_MAX);
    } catch (_) { return []; }
  }
  function saveClicks(arr) {
    try { ls(K_CLICKS, JSON.stringify(arr.slice(-CLICKS_MAX))); } catch (_) {}
  }
  (function trackEnter() {
    const arr = loadClicks();
    const last = arr[arr.length - 1];
    if (last && last.url === location.href) return;      // F5 thì không ghi thêm
    arr.push({ url: location.href, host: location.host,
               title: document.title.slice(0, 120), ts: Date.now(), duration_s: 0 });
    saveClicks(arr);
  })();
  window.addEventListener("pagehide", function () {
    const arr = loadClicks();
    if (arr.length) {
      arr[arr.length - 1].duration_s =
        Math.round((Date.now() - arr[arr.length - 1].ts) / 1000);
      saveClicks(arr);
    }
  });

  function getCampaign() { return ls(K_CAMPAIGN) || ""; }
  function setCampaign(k) { if (k) ls(K_CAMPAIGN, String(k)); }

  function captureContext() {
    const arr = loadClicks();
    if (arr.length) {
      arr[arr.length - 1].duration_s =
        Math.round((Date.now() - arr[arr.length - 1].ts) / 1000);
    }
    return {
      current_url: location.href,
      current_title: document.title,
      referrer: document.referrer || "direct",
      lang: document.documentElement.lang || "vi",
      device: /Mobi|Android|iPhone/i.test(navigator.userAgent) ? "mobile" : "desktop",
      clickstream: arr,
      utm: getUTM(),
      campaign: getCampaign()
    };
  }

  // ─── Câu chào đổi theo trang khách đang đứng ─────────────────────────
  // Hardcode ở client: không tốn 1 token LLM nào, mà trúng ngay từ giây đầu.
  function greetingFor() {
    if (GREET_OVERRIDE) return { intro: GREET_OVERRIDE, follow: "" };

    const isReturning = ls(K_SEEN) === "1";
    const lastMsg = ls(K_LAST_MSG);
    if (isReturning) {
      const intro = "Mừng anh/chị quay lại 🌿 Em là <b>" + BOT_NAME + "</b> đây ạ";
      let follow = "Mình tiếp tục chỗ dở hôm trước nha anh/chị 🙏";
      if (lastMsg) {
        const safe = String(lastMsg).slice(0, 90).replace(/[<>]/g, "");
        follow = "Lần trước anh/chị có nhắn em <i>“" + safe +
                 "”</i> — em vẫn nhớ nha, mình tiếp từ đó luôn ạ 🙏";
      }
      return { intro: intro, follow: follow };
    }

    const p = (location.pathname || "/").toLowerCase();
    if (p.includes("hoc-phi") || p.includes("gia") || p.includes("dang-ky")) {
      return {
        intro: "<b>" + BOT_NAME + "</b> đây ạ — em gửi đúng thông tin chương trình cho anh/chị 🌿",
        follow: "Anh/chị cho em hỏi doanh nghiệp mình quy mô sao ạ, để em tư vấn đúng chương trình 🙏"
      };
    }
    if (p.includes("ccsc") || p.includes("dong-tien") || p.includes("tai-chinh")) {
      return {
        intro: "<b>" + BOT_NAME + "</b> đây ạ — anh/chị đang vướng chỗ dòng tiền phải không ạ? 🌿",
        follow: "Anh/chị kể em nghe tháng rồi doanh nghiệp mình gãy ở đâu, em xem giúp ạ 🙏"
      };
    }
    if (p.includes("kien-tao") || p.includes("ceo") || p.includes("quan-tri")) {
      return {
        intro: "<b>" + BOT_NAME + "</b> đây ạ — em hỗ trợ anh/chị tìm hiểu về CEO Kiến Tạo 🌿",
        follow: "Anh/chị đang mắc ở cơ cấu, nhân sự hay dòng tiền ạ? Em gỡ cùng 🙏"
      };
    }
    return {
      intro: "<b>" + BOT_NAME + "</b> — trợ lý của anh Quang đây ạ 🌿",
      follow: "Anh/chị đang vướng chuyện gì trong doanh nghiệp, kể em nghe với ạ 🙏"
    };
  }

  function shouldShowNotif() {
    const at = parseInt(ls(K_NOTIF_OFF) || "0", 10);
    return !(at && Date.now() - at < NOTIF_COOLDOWN);
  }

  // ─── Giao diện ───────────────────────────────────────────────────────
  const CSS = `
:host{--a:${ACCENT};--a2:${ACCENT_2};--bg:#fff;--fg:#2b3230;--muted:#6b7671;
  --bd:#e6e9e7;--bot:#f4f6f5;--radius:16px;
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:14px;line-height:1.55}
*{box-sizing:border-box}
.bubble{position:fixed;${POSITION.includes("left") ? "left:20px" : "right:20px"};
  bottom:20px;width:60px;height:60px;border-radius:50%;border:none;padding:0;
  background:linear-gradient(135deg,var(--a2),var(--a));color:#fff;cursor:pointer;
  box-shadow:0 8px 28px rgba(0,0,0,.22);display:flex;align-items:center;
  justify-content:center;overflow:hidden;z-index:2147483000;
  transition:transform .2s cubic-bezier(.34,1.56,.64,1)}
.bubble:hover{transform:scale(1.08)}
.bubble img{width:100%;height:100%;object-fit:cover}
.bubble svg{width:28px;height:28px}
.notif-stack{position:fixed;${POSITION.includes("left") ? "left:20px" : "right:20px"};
  bottom:92px;z-index:2147483000;display:flex;flex-direction:column;gap:8px;
  max-width:min(320px,calc(100vw - 40px))}
.notif{display:flex;gap:10px;background:rgba(255,255,255,.97);border:1px solid var(--bd);
  border-radius:14px;padding:10px 12px;box-shadow:0 10px 30px rgba(0,0,0,.16);
  cursor:pointer;animation:pop .28s ease;backdrop-filter:blur(8px)}
@keyframes pop{from{opacity:0;transform:translateY(8px) scale(.97)}to{opacity:1;transform:none}}
.notif .ic{width:34px;height:34px;border-radius:50%;flex:0 0 34px;overflow:hidden;
  background:linear-gradient(135deg,var(--a2),var(--a));display:flex;align-items:center;
  justify-content:center;color:#fff;font-weight:700}
.notif .ic img{width:100%;height:100%;object-fit:cover}
.notif .tx{flex:1;font-size:13px;color:var(--fg)}
.notif .x{color:var(--muted);font-size:16px;line-height:1;padding:2px 4px;cursor:pointer}
.panel{position:fixed;${POSITION.includes("left") ? "left:20px" : "right:20px"};
  bottom:92px;width:min(390px,calc(100vw - 32px));height:min(600px,calc(100vh - 130px));
  background:var(--bg);border-radius:var(--radius);box-shadow:0 18px 60px rgba(0,0,0,.26);
  display:none;flex-direction:column;overflow:hidden;z-index:2147483001;
  border:1px solid var(--bd)}
.panel.open{display:flex}
.panel.expanded{width:min(820px,calc(100vw - 40px));height:min(84vh,900px);
  left:50%;right:auto;top:50%;bottom:auto;transform:translate(-50%,-50%)}
.backdrop{position:fixed;inset:0;background:rgba(20,26,24,.55);display:none;
  z-index:2147483000}
.backdrop.show{display:block}
.hd{display:flex;align-items:center;gap:10px;padding:12px 14px;
  background:linear-gradient(135deg,var(--a2),var(--a));color:#fff}
.hd .av{width:38px;height:38px;border-radius:50%;overflow:hidden;background:rgba(255,255,255,.25);
  display:flex;align-items:center;justify-content:center;font-weight:700;flex:0 0 38px}
.hd .av img{width:100%;height:100%;object-fit:cover}
.hd .nm{font-weight:700;font-size:15px}
.hd .st{font-size:11.5px;opacity:.9}
.hd .sp{flex:1}
.hd button{background:transparent;border:none;color:#fff;cursor:pointer;padding:4px;
  border-radius:8px;display:flex}
.hd button:hover{background:rgba(255,255,255,.18)}
.msgs{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:9px;
  background:#fbfcfb}
.msg{max-width:82%;padding:9px 13px;border-radius:14px;word-wrap:break-word;
  white-space:normal;animation:pop .2s ease}
.msg.bot{background:var(--bot);color:var(--fg);align-self:flex-start;border-bottom-left-radius:5px}
.msg.user{background:var(--a);color:#fff;align-self:flex-end;border-bottom-right-radius:5px}
.msg.error{background:#fdecec;color:#a33;align-self:flex-start;font-size:13px}
.msg a{color:inherit;text-decoration:underline}
.typing{align-self:flex-start;background:var(--bot);padding:11px 14px;border-radius:14px;
  border-bottom-left-radius:5px;display:flex;gap:4px}
.typing span{width:7px;height:7px;border-radius:50%;background:var(--muted);
  animation:blink 1.3s infinite}
.typing span:nth-child(2){animation-delay:.18s}
.typing span:nth-child(3){animation-delay:.36s}
@keyframes blink{0%,60%,100%{opacity:.28}30%{opacity:1}}
.zalo-line{padding:6px 14px;font-size:12px;color:var(--muted);border-top:1px solid var(--bd);
  background:#fff}
.zalo-line a{color:var(--a);font-weight:600}
.cmp{display:flex;gap:8px;padding:10px;border-top:1px solid var(--bd);background:#fff;
  align-items:flex-end}
.cmp textarea{flex:1;resize:none;border:1px solid var(--bd);border-radius:12px;
  padding:9px 12px;font:inherit;max-height:100px;outline:none;color:var(--fg);background:#fff}
.cmp textarea:focus{border-color:var(--a)}
.cmp button{background:var(--a);color:#fff;border:none;border-radius:12px;
  padding:9px 16px;font-weight:600;cursor:pointer;font-family:inherit}
.cmp button:disabled{opacity:.5;cursor:default}
.ft{padding:6px 12px;font-size:11px;color:var(--muted);text-align:center;
  border-top:1px solid var(--bd);background:#fff}
@media(max-width:520px){
  .panel{width:100vw;height:100dvh;bottom:0;right:0;left:0;border-radius:0;border:none}
  .panel.expanded{width:100vw;height:100dvh;transform:none;top:0;left:0}
  .bubble{width:54px;height:54px;bottom:16px}
  .notif-stack{bottom:80px}
}`;

  const avatarHtml = AVATAR
    ? '<img src="' + AVATAR + '" alt="' + BOT_NAME + '">'
    : BOT_NAME.trim().charAt(0);

  const HTML = `
<div class="backdrop" data-role="backdrop"></div>
<button class="bubble" aria-label="Mở khung chat với ${BOT_NAME}">
  ${AVATAR ? '<img src="' + AVATAR + '" alt="">' :
    '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/></svg>'}
</button>
<div class="notif-stack" data-role="notif"></div>
<div class="panel">
  <div class="hd">
    <div class="av">${avatarHtml}</div>
    <div>
      <div class="nm">${BOT_NAME}</div>
      <div class="st">${SUBTITLE}</div>
    </div>
    <div class="sp"></div>
    <button data-action="expand" title="Phóng lớn" aria-label="Phóng lớn">
      <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
    </button>
    <button data-action="close" title="Đóng" aria-label="Đóng">
      <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
    </button>
  </div>
  <div class="msgs"></div>
  ${ZALO_URL ? '<div class="zalo-line">Nhắn <a data-channel="zalo" href="' + ZALO_URL +
    '" target="_blank" rel="noopener nofollow">Zalo</a> cũng là em trực ạ 🌿</div>' : ""}
  <div class="cmp">
    <textarea rows="1" maxlength="2000" placeholder="Anh/chị đang vướng gì ạ?"></textarea>
    <button data-action="send">Gửi</button>
  </div>
  ${FOOTER ? '<div class="ft">' + FOOTER + "</div>" : ""}
</div>`;

  // ─── Web Component ───────────────────────────────────────────────────
  class GianWidget extends HTMLElement {
    constructor() {
      super();
      const sh = this.attachShadow({ mode: "open" });
      const st = document.createElement("style");
      st.textContent = CSS;
      sh.appendChild(st);
      const wrap = document.createElement("div");
      wrap.innerHTML = HTML;
      sh.appendChild(wrap);
      this.sh = sh;

      this.bubble   = sh.querySelector(".bubble");
      this.panel    = sh.querySelector(".panel");
      this.backdrop = sh.querySelector('[data-role="backdrop"]');
      this.msgs     = sh.querySelector(".msgs");
      this.ta       = sh.querySelector("textarea");
      this.sendBtn  = sh.querySelector('[data-action="send"]');
      this.notifBox = sh.querySelector('[data-role="notif"]');

      this.busy = false;
      this.typingEl = null;
      this.notif2Shown = false;
      this.nudgeDone = false;
      this.agentSeen = 0;

      this.bubble.addEventListener("click", () => this.toggle());
      this.sendBtn.addEventListener("click", () => this.send());
      this.ta.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); this.send(); }
      });
      this.ta.addEventListener("input", () => {
        this.ta.style.height = "auto";
        this.ta.style.height = Math.min(this.ta.scrollHeight, 100) + "px";
        this.armNudge();
      });

      sh.querySelector('[data-action="close"]').addEventListener("click", () => {
        if (this.panel.classList.contains("expanded")) this.setExpand(false);
        else if (this.panel.classList.contains("open")) this.toggle();
      });
      sh.querySelector('[data-action="expand"]')
        .addEventListener("click", () => this.setExpand());
      this.backdrop.addEventListener("click", () => this.setExpand(false));
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && this.panel.classList.contains("expanded")) {
          this.setExpand(false);
        }
      });

      const zaloLink = sh.querySelector('.zalo-line a[data-channel="zalo"]');
      if (zaloLink) {
        // Tab Zalo tự mở; đồng thời bắn tin ẩn để bot xin số nối kênh.
        zaloLink.addEventListener("click", () => this.send("/_channel_zalo_"));
      }

      if (shouldShowNotif()) setTimeout(() => this.showNotif1(), NOTIF_DELAY_1);
      this.startAgentPull();
      this.checkPricePageRevisit();
    }

    // ── Notification kiểu iOS ──────────────────────────────────────────
    buildNotif(html) {
      const d = document.createElement("div");
      d.className = "notif";
      d.innerHTML =
        '<div class="ic">' + avatarHtml + '</div>' +
        '<div class="tx">' + html + "</div>" +
        '<div class="x" data-x>✕</div>';
      d.addEventListener("click", (e) => {
        if (e.target.hasAttribute("data-x")) {
          e.stopPropagation();
          ls(K_NOTIF_OFF, String(Date.now()));
          this.clearNotifs();
          return;
        }
        this.clearNotifs();
        if (!this.panel.classList.contains("open")) this.toggle();
      });
      this.notifBox.appendChild(d);
      return d;
    }
    showNotif1() {
      if (this.panel.classList.contains("open")) return;
      const g = greetingFor();
      this.buildNotif(g.intro);
      if (g.follow) setTimeout(() => this.showNotif2(g.follow), NOTIF_DELAY_2);
    }
    showNotif2(text) {
      if (this.notif2Shown || this.panel.classList.contains("open")) return;
      this.notif2Shown = true;
      this.buildNotif(text);
    }
    clearNotifs() { this.notifBox.innerHTML = ""; }

    // ── Mở / đóng ──────────────────────────────────────────────────────
    async toggle() {
      const open = this.panel.classList.toggle("open");
      if (open) {
        this.clearNotifs();
        if (this.msgs.children.length === 0) {
          const restored = await this.restoreHistory();
          if (!restored) {
            this.addMsg("Dạ em là " + BOT_NAME + ", trợ lý của anh Quang 🌿 " +
                        "Anh/chị đang vướng chuyện gì trong doanh nghiệp ạ?", "bot");
          }
        }
        this.ta.focus();
        this.armNudge();
      } else {
        this.panel.classList.remove("expanded");
        this.backdrop.classList.remove("show");
        document.body.style.overflow = "";
      }
    }

    setExpand(force) {
      const on = force === undefined
        ? !this.panel.classList.contains("expanded") : !!force;
      this.panel.classList.toggle("expanded", on);
      this.backdrop.classList.toggle("show", on);
      document.body.style.overflow = on ? "hidden" : "";
      if (on) setTimeout(() => this.ta.focus(), 100);
    }

    async openWidget(message) {
      if (!this.panel.classList.contains("open")) await this.toggle();
      const m = (message == null ? "" : String(message)).trim();
      if (m) setTimeout(() => this.send(m), 200);
    }

    // ── Hiển thị ───────────────────────────────────────────────────────
    esc(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
    md(t) {
      let h = this.esc(String(t || "").replace(/<br\s*\/?>/gi, "\n"));
      h = h.replace(/\*\*([^*\n]+?)\*\*/g, "<strong>$1</strong>");
      h = h.replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, "$1<em>$2</em>");
      h = h.replace(/(https?:\/\/[^\s<]+)/g,
        '<a href="$1" target="_blank" rel="noopener">$1</a>');
      return h.replace(/\n{2,}/g, "<br><br>").replace(/\n/g, "<br>");
    }
    addMsg(text, who) {
      const d = document.createElement("div");
      d.className = "msg " + (who || "bot");
      if (who === "user") d.textContent = text; else d.innerHTML = this.md(text);
      this.msgs.appendChild(d);
      this.msgs.scrollTop = this.msgs.scrollHeight;
      return d;
    }
    addTyping() {
      this.removeTyping();
      const d = document.createElement("div");
      d.className = "typing";
      d.innerHTML = "<span></span><span></span><span></span>";
      this.msgs.appendChild(d);
      this.msgs.scrollTop = this.msgs.scrollHeight;
      this.typingEl = d;
    }
    removeTyping() {
      if (this.typingEl) { this.typingEl.remove(); this.typingEl = null; }
    }

    async restoreHistory() {
      try {
        const r = await fetch(API + "/history?visitor_id=" +
                              encodeURIComponent(visitorId) + "&limit=40");
        if (!r.ok) return false;
        const j = await r.json();
        const list = (j.messages || []).filter((m) => m.content);
        if (!list.length) return false;
        list.forEach((m) => this.addMsg(m.content, m.role === "user" ? "user" : "bot"));
        return true;
      } catch (_) { return false; }
    }

    // ── Người thật tiếp quản: poll 3s ──────────────────────────────────
    startAgentPull() {
      setInterval(async () => {
        if (!sessionId || !this.panel.classList.contains("open")) return;
        try {
          const r = await fetch(API + "/chat/agent-pull?session_id=" +
            encodeURIComponent(sessionId) + "&after_id=" + this.agentSeen);
          if (!r.ok) return;
          const j = await r.json();
          (j.messages || []).forEach((m) => {
            if (m.id > this.agentSeen) {
              this.agentSeen = m.id;
              this.removeTyping();
              this.addMsg(m.text, "bot");   // cùng avatar — khách không thấy đứt mạch
            }
          });
        } catch (_) {}
      }, AGENT_POLL_MS);
    }

    // ── Khách im lâu → chủ động nối mạch ───────────────────────────────
    armNudge() {
      clearTimeout(this.nudgeT);
      if (this.nudgeDone) return;
      const last = parseInt(ls(K_NUDGE) || "0", 10);
      if (last && Date.now() - last < NUDGE_COOLDOWN) return;
      this.nudgeT = setTimeout(() => this.fireNudge(), NUDGE_MS);
    }
    async fireNudge() {
      if (this.nudgeDone || this.busy || !sessionId) return;
      if (document.hidden) return;             // khách chuyển tab thì thôi
      this.nudgeDone = true;
      ls(K_NUDGE, String(Date.now()));
      if (!this.panel.classList.contains("open")) await this.toggle();
      this.send("/_nudge_");
    }

    // Khách xem trang học phí lần thứ 2 → tín hiệu cân nhắc thật
    checkPricePageRevisit() {
      const p = (location.pathname || "").toLowerCase();
      if (!(p.includes("hoc-phi") || p.includes("bang-gia"))) return;
      const n = parseInt(ls(K_PRICE_HIT) || "0", 10) + 1;
      ls(K_PRICE_HIT, String(n));
      if (n === 2 && ls(K_SEEN) === "1") {
        setTimeout(() => {
          if (!this.panel.classList.contains("open")) this.toggle();
          setTimeout(() => this.send("/_gia_lan_2_"), 400);
        }, 4000);
      }
    }

    // ── Gửi tin ────────────────────────────────────────────────────────
    async send(rawMsg) {
      if (this.busy) return;
      const HIDDEN = ["/_greet_", "/_nudge_", "/_channel_zalo_", "/_gia_lan_2_"];
      const isHidden = HIDDEN.indexOf(rawMsg) >= 0;
      const msg = isHidden ? rawMsg : String(rawMsg || this.ta.value).trim();
      if (!msg) return;

      this.busy = true;
      this.sendBtn.disabled = true;

      if (!isHidden) {
        this.addMsg(msg, "user");
        ls(K_SEEN, "1");
        ls(K_LAST_MSG, msg.slice(0, 200));
        this.ta.value = "";
        this.ta.style.height = "auto";
      }
      this.addTyping();

      try {
        await this.stream(msg);
      } catch (e) {
        this.removeTyping();
        this.addMsg("Em đang kẹt kết nối, anh/chị thử lại sau 1 phút giúp em nha 🙏", "error");
      } finally {
        this.busy = false;
        this.sendBtn.disabled = false;
        this.armNudge();
      }
    }

    async stream(message) {
      const resp = await fetch(API + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({
          message: message,
          session_id: sessionId,
          visitor_id: visitorId,
          context: captureContext(),
          channel: "web"
        })
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status);

      const reader = resp.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      for (;;) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buf += dec.decode(chunk.value, { stream: true });
        const events = buf.split(/\r?\n\r?\n/);
        buf = events.pop() || "";
        events.forEach((e) => this.handleEvent(e));
      }
    }

    handleEvent(rawEvent) {
      let type = "message";
      let data = "";
      rawEvent.split(/\r?\n/).forEach((line) => {
        if (line.indexOf("event:") === 0) type = line.slice(6).trim();
        else if (line.indexOf("data:") === 0) data += line.slice(5).trim();
      });
      if (!data) return;

      let p;
      try { p = JSON.parse(data); } catch (_) { return; }

      switch (type) {
        case "session":
          persistSession(p.session_id);
          break;
        case "typing":
          this.addTyping();
          break;
        case "message":
          this.removeTyping();
          this.addMsg(p.text, "bot");
          break;
        case "tag":
          // Bot tự chấm khách — không hiện ra, chỉ để debug
          if (window.__GIAN_DEBUG__) console.debug("[Bé Giản tag]", p);
          break;
        case "error":
          this.removeTyping();
          break;
        case "done":
          this.removeTyping();
          break;
      }
    }
  }

  // ─── Mount ───────────────────────────────────────────────────────────
  function mount() {
    if (!customElements.get("gian-widget")) {
      customElements.define("gian-widget", GianWidget);
    }
    if (!document.querySelector("gian-widget")) {
      document.body.appendChild(document.createElement("gian-widget"));
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }

  // ─── API toàn cục: gắn nút bất kỳ trên site vào chat ─────────────────
  //   <button onclick="Gian.open('Em ơi CCSC học bao lâu?')">Hỏi Bé Giản</button>
  //   <button onclick="Gian.openCampaign('ccsc-t8','Cho em hỏi về CCSC')">...</button>
  function el() { return document.querySelector("gian-widget"); }
  window.Gian = {
    open: function (m) { const e = el(); if (e) e.openWidget(m); },
    openCampaign: function (key, opener) {
      if (key) setCampaign(key);
      const e = el();
      if (e) e.openWidget(opener || "Mình muốn tìm hiểu thêm về cái này");
    },
    isReady: function () { return !!el(); }
  };
})();
