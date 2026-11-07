/* Continuous geometry on one portrait; no image swaps or frame-sequence animation. */
(() => {
    "use strict";
    const sky = document.querySelector(".night-sky");
    if (!sky) return;
    const portrait = sky.querySelector(".wall-portrait");
    const caption = sky.querySelector("[data-reaction-caption]");
    const image = portrait.querySelector("img");
    const halo = portrait.querySelector(".gratitude-halo");
    const phrases = window.TODDY_SUPPORTER_THANKS || ["You have my attention."];
    const scroller = sky.querySelector(".starfield-scroll");
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    let selected;
    let frame;
    let lastPhrase = -1;
    let nod;
    let glow;
    const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
    function geometry() {
        frame = undefined;
        if (!selected) return;
        const bounds = sky.getBoundingClientRect();
        const dog = portrait.getBoundingClientRect();
        const name = selected.getBoundingClientRect();
        const x = dog.x + dog.width / 2 - bounds.x;
        const y = dog.y + dog.height * .55 - bounds.y;
        const nx = name.x + name.width / 2 - bounds.x;
        const ny = name.y + name.height / 2 - bounds.y;
        if (!motion.matches) {
            portrait.style.setProperty("--look-x", clamp((nx - x) / bounds.width * 20, -13, 13) + "deg");
            portrait.style.setProperty("--look-y", clamp(-(ny - y) / bounds.height * 15, -8, 8) + "deg");
            portrait.style.setProperty("--look-roll", clamp((nx - x) / bounds.width * 4, -3, 3) + "deg");
        }
    }
    function thankYou() {
        let index = Math.floor(Math.random() * (phrases.length - (lastPhrase >= 0 && phrases.length > 1 ? 1 : 0)));
        if (phrases.length > 1 && lastPhrase >= 0 && index >= lastPhrase) index++;
        lastPhrase = index;
        sky.dataset.thanksIndex = String(index);
        return phrases[index];
    }
    function react() {
        if (motion.matches) return;
        const start = getComputedStyle(image).transform;
        nod?.cancel();
        nod = image.animate([
            {transform:start, offset:0, easing:"ease-in-out"},
            {transform:"translateY(-3px) rotate(-4deg)", offset:.3, easing:"ease-in-out"},
            {transform:"translateY(2px) rotate(3deg)", offset:.65, easing:"ease-in-out"},
            {transform:"none", offset:1}
        ], {duration:1300});
        const opacity = getComputedStyle(halo).opacity;
        const transform = getComputedStyle(halo).transform;
        glow?.cancel();
        glow = halo.animate([
            {opacity, transform},
            {opacity:.8, transform:"scale(1.08)", offset:.4},
            {opacity:0, transform:"scale(1.3)"}
        ], {duration:1500, easing:"ease-out"});
    }
    function schedule() { if (!frame) frame = requestAnimationFrame(geometry); }
    function reset() {
        if (selected) selected.setAttribute("aria-pressed", "false");
        selected = undefined;
        portrait.removeAttribute("style");
        caption.replaceChildren(document.createTextNode("I checked the list."), document.createElement("br"), document.createTextNode("Good humans."));
    }
    sky.addEventListener("click", event => {
        const button = event.target.closest(".supporter-star");
        if (!button) return;
        if (selected) selected.setAttribute("aria-pressed", "false");
        selected = button;
        selected.setAttribute("aria-pressed", "true");
        const name = document.createElement("span");
        name.setAttribute("data-no-translate", "");
        name.textContent = button.textContent;
        caption.replaceChildren(document.createTextNode("Thanks, "), name, document.createElement("br"), document.createTextNode(thankYou()));
        react();
        schedule();
    });
    sky.addEventListener("keydown", event => { if (event.key === "Escape") reset(); });
    scroller.addEventListener("scroll", schedule, {passive:true});
    window.addEventListener("resize", schedule, {passive:true});
    motion.addEventListener("change", () => { portrait.removeAttribute("style"); nod?.cancel(); glow?.cancel(); schedule(); });
    let visible = false;
    const pause = () => sky.classList.toggle("is-offscreen", !visible || document.hidden);
    const observer = new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        pause();
    });
    observer.observe(sky);
    const stars = new IntersectionObserver(entries => {
        for (const entry of entries) entry.target.classList.toggle("is-out-of-view", !entry.isIntersecting);
    }, {root:scroller, rootMargin:"40px"});
    for (const star of scroller.querySelectorAll("li")) stars.observe(star);
    document.addEventListener("visibilitychange", pause);
})();
