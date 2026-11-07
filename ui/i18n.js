/* Offline, dependency-free UI localization. Technical source and artwork are retained. */
(() => {
    "use strict";
    const locales = ["en", "pt-BR", "es", "zh-Hans", "ja", "ru"];
    const storageKey = "toddy-language";
    const catalog = window.TODDY_TRANSLATIONS || {};
    const originals = new WeakMap();
    const attributes = new WeakMap();
    const normalize = (value) => value.replace(/\s+/g, " ").trim();
    const resolve = (value) => {
        const tag = String(value || "").toLowerCase();
        return (
            locales.find((code) => code.toLowerCase() === tag) ||
            (tag.startsWith("pt")
                ? "pt-BR"
                : tag.startsWith("zh")
                  ? "zh-Hans"
                  : ["en", "es", "ja", "ru"].find(
                        (code) => tag === code || tag.startsWith(code + "-"),
                    ))
        );
    };
    let saved;
    try {
        saved = localStorage.getItem(storageKey);
    } catch {
        /* Storage can be disabled. */
    }
    const requested = resolve(new URL(location.href).searchParams.get("lang"));
    let language =
        requested ||
        resolve(saved) ||
        (navigator.languages || [navigator.language])
            .map(resolve)
            .find(Boolean) ||
        "en";
    function translate(source) {
        const key = normalize(source);
        if (language === "en" || !key) return source;
        const column = locales.indexOf(language) - 1;
        let result = catalog[key]?.[column];
        if (result === undefined) {
            let match;
            if ((match = key.match(/^(\d+) stories$/))) {
                result = (
                    catalog["{count} stories"]?.[column] || "{count} stories"
                ).replace("{count}", match[1]);
            } else if (
                (match = key.match(
                    /^(not started|in progress|blocked|completed) · (\d+) points$/,
                ))
            ) {
                result =
                    translate(match[1]) +
                    " · " +
                    translate("{count} points").replace("{count}", match[2]);
            } else if ((match = key.match(/^Prerequisites: (.+)$/))) {
                result =
                    translate("Prerequisites:") + " " + translate(match[1]);
            } else if (
                (match = key.match(
                    /^G1 (passed|pending) · G2 (passed|pending)$/,
                ))
            ) {
                result =
                    "G1 " +
                    translate(match[1]) +
                    " · G2 " +
                    translate(match[2]);
            } else if (
                (match = key.match(
                    /^Updated (\d{4}-\d{2}-\d{2}) · Published snapshot, not a live process monitor\.$/,
                ))
            ) {
                result = translate(
                    "Updated {date} · Published snapshot, not a live process monitor.",
                ).replace("{date}", match[1]);
            } else if (key.startsWith("Explore: ")) {
                result = translate("Explore:") + " " + translate(key.slice(9));
            }
        }
        if (result === undefined) return source;
        return source.replace(
            /^(\s*)[\s\S]*?(\s*)$/,
            (_, before, after) => before + result + after,
        );
    }
    const excluded = (element) =>
        !element ||
        element.closest("script,style,code,pre,[data-no-translate]");
    function textNode(node) {
        if (excluded(node.parentElement)) return;
        const previous = originals.get(node);
        const source =
            previous && node.nodeValue === previous.applied
                ? previous.source
                : node.nodeValue;
        const value = translate(source);
        originals.set(node, { source, applied: value });
        if (node.nodeValue !== value) node.nodeValue = value;
    }
    function localizedLink(element) {
        if (!element.matches("a[href]") || element.hasAttribute("download"))
            return;
        const href = element.getAttribute("href");
        if (!href || href.startsWith("#")) return;
        try {
            const url = new URL(href, location.href);
            if (
                url.origin !== location.origin ||
                !url.pathname.endsWith(".html")
            )
                return;
            url.searchParams.set("lang", language);
            if (element.href !== url.href) element.href = url.href;
        } catch {
            /* Invalid/external links are not rewritten. */
        }
    }
    function elementAttributes(element) {
        if (excluded(element)) return;
        localizedLink(element);
        let record = attributes.get(element);
        if (!record) {
            record = {};
            attributes.set(element, record);
        }
        for (const key of ["alt", "aria-label", "placeholder", "title"]) {
            const current = element.getAttribute(key);
            if (current === null) continue;
            const previous = record[key];
            const source =
                previous && current === previous.applied
                    ? previous.source
                    : current;
            const value = translate(source);
            record[key] = { source, applied: value };
            if (current !== value) element.setAttribute(key, value);
        }
        if (element.matches('meta[name="description"]')) {
            const current = element.content;
            const previous = record.content;
            const source =
                previous && current === previous.applied
                    ? previous.source
                    : current;
            const value = translate(source);
            record.content = { source, applied: value };
            if (current !== value) element.content = value;
        }
    }
    function apply(root) {
        if (root.nodeType === Node.TEXT_NODE) {
            textNode(root);
            return;
        }
        if (
            root.nodeType !== Node.ELEMENT_NODE &&
            root.nodeType !== Node.DOCUMENT_NODE
        )
            return;
        if (root.nodeType === Node.ELEMENT_NODE) elementAttributes(root);
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) textNode(walker.currentNode);
        root.querySelectorAll?.(
            '[alt],[aria-label],[placeholder],[title],a[href],meta[name="description"]',
        ).forEach(elementAttributes);
    }
    function select(code, updateURL) {
        language = resolve(code) || "en";
        document.documentElement.lang = language;
        document
            .querySelectorAll("[data-language-picker]")
            .forEach((picker) => (picker.value = language));
        try {
            localStorage.setItem(storageKey, language);
        } catch {
            /* Selection still works without storage. */
        }
        if (updateURL) {
            const url = new URL(location.href);
            url.searchParams.set("lang", language);
            try {
                history.replaceState(null, "", url);
            } catch {
                /* File previews may disallow history changes. */
            }
        }
        apply(document);
    }
    document
        .querySelectorAll("[data-language-picker]")
        .forEach((picker) =>
            picker.addEventListener("change", () => select(picker.value, true)),
        );
    select(language, false);
    const observer = new MutationObserver((records) => {
        const roots = new Set();
        for (const record of records) {
            if (record.type === "characterData") roots.add(record.target);
            else if (record.type === "attributes")
                elementAttributes(record.target);
            else record.addedNodes.forEach((node) => roots.add(node));
        }
        roots.forEach(apply);
    });
    observer.observe(document.documentElement, {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true,
        attributeFilter: [
            "alt",
            "aria-label",
            "placeholder",
            "title",
            "content",
            "href",
        ],
    });
})();
