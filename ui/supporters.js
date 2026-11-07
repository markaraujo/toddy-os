/* Continuous geometry on one portrait; no image swaps or frame-sequence animation. */
(() => {
    "use strict";
    const sky = document.querySelector(".night-sky");
    if (!sky) return;
    const portrait = sky.querySelector(".wall-portrait");
    const caption = sky.querySelector("[data-reaction-caption]");
    const path = sky.querySelector(".constellation-link path");
    const scroller = sky.querySelector(".starfield-scroll");
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    let selected;
    let frame;
    const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
    function geometry() {
        frame = undefined;
        if (!selected) return;
        const bounds = sky.getBoundingClientRect();
        const dog = portrait.getBoundingClientRect();
        const name = selected.getBoundingClientRect();
        const viewport = scroller.getBoundingClientRect();
        const visible = name.bottom > viewport.top && name.top < viewport.bottom;
        sky.classList.toggle("has-selection", visible);
        const x = dog.x + dog.width / 2 - bounds.x;
        const y = dog.y + dog.height * .55 - bounds.y;
        const nx = name.x + name.width / 2 - bounds.x;
        const ny = name.y + name.height / 2 - bounds.y;
        if (!motion.matches) {
            portrait.style.setProperty("--look-x", clamp((nx - x) / bounds.width * 20, -13, 13) + "deg");
            portrait.style.setProperty("--look-y", clamp(-(ny - y) / bounds.height * 15, -8, 8) + "deg");
            portrait.style.setProperty("--look-roll", clamp((nx - x) / bounds.width * 4, -3, 3) + "deg");
        }
        path.setAttribute("d", `M ${x} ${y} Q ${(x + nx) / 2} ${Math.min(y, ny) - 50} ${nx} ${ny}`);
    }
    function schedule() { if (!frame) frame = requestAnimationFrame(geometry); }
    function reset() {
        if (selected) selected.setAttribute("aria-pressed", "false");
        selected = undefined;
        sky.classList.remove("has-selection");
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
        caption.replaceChildren(document.createTextNode("Thanks, "), name, document.createElement("br"), document.createTextNode("You have my attention."));
        schedule();
    });
    sky.addEventListener("keydown", event => { if (event.key === "Escape") reset(); });
    scroller.addEventListener("scroll", schedule, {passive:true});
    window.addEventListener("resize", schedule, {passive:true});
    motion.addEventListener("change", () => { portrait.removeAttribute("style"); schedule(); });
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
