// viz-core i18n — English main, Korean as locale.
// Usage:
//   <script src="/i18n.js"></script>
//   text content: <span data-i18n="library.title">My Library</span>
//   placeholder: <input data-i18n-attr="placeholder" data-i18n="library.search.placeholder">
//   programmatic: i18n.t("nav.home")
//   toggle: i18n.toggle()

(function () {
  const STORAGE_KEY = "viz-core-lang";
  const LANGS = ["en", "ko"];
  const DEFAULT_LANG = "en";

  const DICT = {
    en: {
      // common nav
      "nav.back": "← viz-core",
      "nav.home": "Home",
      "nav.library": "📚 My Library",
      "nav.concepts": "💡 Concepts",
      "nav.stats": "📊 Stats",
      "nav.showcase": "🎨 Samples",
      "nav.spec": "📜 Spec",
      "nav.toggle.title": "Switch language (English / 한국어)",

      // index (main)
      "index.identity.title": "📚 Your viz knowledge vault",
      "index.identity.sub": "Save concepts and systems you've understood as visuals. Recall in 0.5s.",
      "index.identity.count": "current",
      "index.identity.assets": "assets",
      "index.identity.kinds": "kinds",
      "index.status.idle": "Idle",
      "index.status.active": "Active",
      "index.llm.on": "LLM ON",
      "index.llm.off": "LLM OFF",
      "index.events.unit": "events",

      // library page
      "library.title": "📚 Asset Library",
      "library.subtitle": "Your assets across all 24 viz kinds. One click to push to side tab.",
      "library.search.placeholder": "🔍 Search (title / tag / category)",
      "library.btn.add": "+ New Asset",
      "library.btn.backup": "⬇ Backup",
      "library.btn.restore": "⬆ Restore",
      "library.empty": "No assets match this filter",
      "library.filter.all": "All",
      "library.view.delete": "🗑 Delete",
      "library.view.edit": "✏️ Edit JSON",
      "library.view.push": "📺 Push to main tab",
      "library.add.title": "+ New Asset",
      "library.add.title.edit": "✏️ Edit",
      "library.add.field.vizkind": "viz_kind *",
      "library.add.field.vizkind.hint": "Visualization type. Cannot change later.",
      "library.add.field.slug": "slug *",
      "library.add.field.slug.hint": "Filename. lowercase/digits/hyphen only. Cannot change later.",
      "library.add.field.title": "Title *",
      "library.add.field.tagline": "Tagline",
      "library.add.field.tagline.placeholder": "Optional one-liner",
      "library.add.field.category": "Category",
      "library.add.field.tags": "Tags",
      "library.add.field.tags.hint": "Comma-separated",
      "library.add.field.data": "data (JSON) *",
      "library.add.field.data.hint": "JSON matching viz_kind schema. See /spec.",
      "library.add.btn.template": "📋 Load template",
      "library.add.btn.cancel": "Cancel",
      "library.add.btn.save": "💾 Save",
      "library.json.show": "▶ Show JSON",
      "library.json.hide": "▼ Hide JSON",
      "library.confirm.delete": "Delete this? Cannot undo.",
      "library.alert.pushed": "Pushed to main tab.",
      "library.alert.imported": "Restored {imported} items, skipped {skipped}.",
      "library.alert.import_fail": "Restore failed: ",
      "library.alert.slug_required": "slug required",
      "library.alert.title_required": "title required",
      "library.alert.json_parse_fail": "JSON parse failed: ",

      // concepts page
      "concepts.title": "💡 Concepts",
      "concepts.subtitle": "Save tech concepts you've understood (analogy + visual + tradeoffs). Recall in 0.5s.",
      "concepts.search.placeholder": "🔍 Search (concept / tag / category)",
      "concepts.btn.add": "+ New Concept",
      "concepts.empty": "No concepts yet — click '+ New Concept' to start",
      "concepts.analogy.prefix": "analogy:",

      // stats page
      "stats.title": "📊 Usage Stats — Dogfood",
      "stats.subtitle": "Tracks how I use viz-core daily. Proof for portfolio/interview.",
      "stats.metric.assets": "Total assets",
      "stats.metric.events": "Total events",
      "stats.metric.events.sub": "viz shown / asset pushed",
      "stats.metric.days": "Days used",
      "stats.metric.last": "Last used",
      "stats.metric.first": "Started",
      "stats.section.calendar": "📅 Usage Calendar — 90 days",
      "stats.section.top": "⭐ Most-viewed assets",
      "stats.section.kinds": "🎨 viz_kind distribution",
      "stats.section.sources": "🌐 Sources",
      "stats.calendar.less": "less",
      "stats.calendar.more": "more",
      "stats.table.asset": "Asset",
      "stats.table.kind": "viz_kind",
      "stats.table.source": "Source",
      "stats.table.count": "Count",
      "stats.empty.tracking": "No tracking yet",
      "stats.fmt.justnow": "just now",
      "stats.fmt.minutes_ago": "{n}m ago",
      "stats.fmt.hours_ago": "{n}h ago",
      "stats.fmt.days_ago": "{n}d ago",
      "stats.fmt.no_record": "no record",
      "stats.fmt.days_since": "{n}d ago",
    },
    ko: {
      // common nav
      "nav.back": "← viz-core",
      "nav.home": "메인",
      "nav.library": "📚 내 저장소",
      "nav.concepts": "💡 병신교육소",
      "nav.stats": "📊 통계",
      "nav.showcase": "🎨 샘플",
      "nav.spec": "📜 명세",
      "nav.toggle.title": "언어 전환 (English / 한국어)",

      "index.identity.title": "📚 너의 viz 지식 저장소",
      "index.identity.sub": "본인이 이해한 개념과 시스템을 시각으로 영구 저장. 다시 찾을 때 0.5초.",
      "index.identity.count": "현재",
      "index.identity.assets": "개 자산",
      "index.identity.kinds": "종",
      "index.status.idle": "대기 중",
      "index.status.active": "활성",
      "index.llm.on": "LLM ON",
      "index.llm.off": "LLM OFF",
      "index.events.unit": "이벤트",

      "library.title": "📚 자산 라이브러리",
      "library.subtitle": "24종 viz_kind 의 본인 자산 통합. 한 번 등록하면 옆 탭에 즉시 띄울 수 있음.",
      "library.search.placeholder": "🔍 검색 (제목 / 태그 / 카테고리)",
      "library.btn.add": "+ 새 자산",
      "library.btn.backup": "⬇ 백업",
      "library.btn.restore": "⬆ 복원",
      "library.empty": "필터에 해당하는 자산 없음",
      "library.filter.all": "전체",
      "library.view.delete": "🗑 삭제",
      "library.view.edit": "✏️ JSON 수정",
      "library.view.push": "📺 메인 탭에 띄우기",
      "library.add.title": "+ 새 자산",
      "library.add.title.edit": "✏️ 수정",
      "library.add.field.vizkind": "viz_kind *",
      "library.add.field.vizkind.hint": "자산의 시각화 종류. 한 번 정하면 변경 X.",
      "library.add.field.slug": "slug *",
      "library.add.field.slug.hint": "파일명. 소문자/숫자/하이픈만. 한 번 정하면 변경 X.",
      "library.add.field.title": "제목 *",
      "library.add.field.tagline": "태그라인",
      "library.add.field.tagline.placeholder": "한 줄 핵심 (선택)",
      "library.add.field.category": "카테고리",
      "library.add.field.tags": "태그",
      "library.add.field.tags.hint": "쉼표 구분",
      "library.add.field.data": "data (JSON) *",
      "library.add.field.data.hint": "viz_kind 의 schema 에 맞는 JSON. /spec 참고.",
      "library.add.btn.template": "📋 템플릿 채우기",
      "library.add.btn.cancel": "취소",
      "library.add.btn.save": "💾 저장",
      "library.json.show": "▶ JSON 보기",
      "library.json.hide": "▼ JSON 숨기기",
      "library.confirm.delete": "삭제? 되돌릴 수 없음.",
      "library.alert.pushed": "옆 탭 viz-core 메인에 표시됨!",
      "library.alert.imported": "복원 완료 — {imported}개 가져옴, {skipped}개 건너뜀.",
      "library.alert.import_fail": "복원 실패: ",
      "library.alert.slug_required": "slug 필요",
      "library.alert.title_required": "제목 필요",
      "library.alert.json_parse_fail": "data JSON 파싱 실패: ",

      "concepts.title": "💡 병신교육소",
      "concepts.subtitle": "본인이 이해한 개념을 시각으로 저장. 나중에 AI 가 추천하면 0.5초에 다시 떠올림.",
      "concepts.search.placeholder": "🔍 검색 (개념 이름 / 태그 / 카테고리)",
      "concepts.btn.add": "+ 새 개념 추가",
      "concepts.empty": "아직 개념 없음 — 위 '새 개념 추가' 로 시작",
      "concepts.analogy.prefix": "비유:",

      "stats.title": "📊 사용 통계 — Dogfood",
      "stats.subtitle": "본인이 매일 viz-core 를 어떻게 쓰는지 추적. 포폴/면접 시 증명용.",
      "stats.metric.assets": "총 자산",
      "stats.metric.events": "총 사용 이벤트",
      "stats.metric.events.sub": "viz 표시 / 자산 push",
      "stats.metric.days": "사용한 날",
      "stats.metric.last": "마지막 사용",
      "stats.metric.first": "시작일",
      "stats.section.calendar": "📅 사용 캘린더 — 90일",
      "stats.section.top": "⭐ 가장 자주 본 자산",
      "stats.section.kinds": "🎨 viz_kind 분포",
      "stats.section.sources": "🌐 사용 소스",
      "stats.calendar.less": "적음",
      "stats.calendar.more": "많음",
      "stats.table.asset": "자산",
      "stats.table.kind": "viz_kind",
      "stats.table.source": "소스",
      "stats.table.count": "횟수",
      "stats.empty.tracking": "아직 기록 없음",
      "stats.fmt.justnow": "방금",
      "stats.fmt.minutes_ago": "{n}분 전",
      "stats.fmt.hours_ago": "{n}시간 전",
      "stats.fmt.days_ago": "{n}일 전",
      "stats.fmt.no_record": "기록 없음",
      "stats.fmt.days_since": "{n}일 전",
    },
  };

  function getLang() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && LANGS.includes(stored)) return stored;
    } catch (_) {}
    return DEFAULT_LANG;
  }

  function setLang(lang) {
    if (!LANGS.includes(lang)) return;
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (_) {}
    apply();
    // 페이지가 동적 콘텐츠 다시 그릴 hook
    document.dispatchEvent(new CustomEvent("i18n:changed", { detail: { lang } }));
  }

  function toggle() {
    const cur = getLang();
    setLang(cur === "en" ? "ko" : "en");
  }

  function t(key, vars) {
    const lang = getLang();
    let s = (DICT[lang] && DICT[lang][key]) || (DICT[DEFAULT_LANG] && DICT[DEFAULT_LANG][key]) || key;
    if (vars && typeof s === "string") {
      Object.keys(vars).forEach(k => { s = s.replace(`{${k}}`, vars[k]); });
    }
    return s;
  }

  function apply(root) {
    const scope = root || document;
    // text content
    scope.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      const attr = el.getAttribute("data-i18n-attr");
      if (attr) {
        el.setAttribute(attr, t(key));
      } else {
        el.textContent = t(key);
      }
    });
    // title attribute
    scope.querySelectorAll("[data-i18n-title]").forEach(el => {
      el.setAttribute("title", t(el.getAttribute("data-i18n-title")));
    });
    // html lang attr
    document.documentElement.lang = getLang();
    // toggle button visuals
    document.querySelectorAll(".i18n-toggle").forEach(btn => {
      btn.textContent = getLang() === "en" ? "🇺🇸 EN" : "🇰🇷 한국어";
    });
  }

  function injectToggleStyles() {
    if (document.getElementById("i18n-styles")) return;
    const style = document.createElement("style");
    style.id = "i18n-styles";
    style.textContent = `
      .i18n-toggle {
        padding: 6px 12px; background: var(--panel, #161b22);
        border: 1px solid var(--border, #30363d); border-radius: 6px;
        color: var(--text, #e6edf3); cursor: pointer; font-size: 12px;
        font-family: ui-monospace, monospace;
      }
      .i18n-toggle:hover { border-color: var(--accent, #58a6ff); color: var(--accent, #58a6ff); }
    `;
    document.head.appendChild(style);
  }

  window.i18n = { t, getLang, setLang, toggle, apply, LANGS };

  document.addEventListener("DOMContentLoaded", () => {
    injectToggleStyles();
    apply();
  });
  // also apply immediately for scripts loaded after content
  if (document.readyState !== "loading") {
    injectToggleStyles();
    apply();
  }
})();
