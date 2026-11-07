/* A small, interaction-only website easter egg. No OS behavior or telemetry. */
(() => {
    "use strict";
    const button = document.querySelector("[data-mascot-button]");
    const caption = document.querySelector("[data-mascot-caption]");
    if (!button || !caption) return;

    const comments = [
        ["Great at dependencies.", "Terrible at personal space."],
        ["Another meeting?", "Wake me when there are treats."],
        ["I have a suggestion.", "Fewer meetings. More treats."],
        ["I'm not ignoring you.", "I'm optimizing my attention."],
        ["Your code can wait.", "My snack schedule cannot."],
        ["Dependencies resolved.", "Attention requirements remain high."],
        ["Yes, I heard you.", "I'm choosing a dramatic pause."],
        ["I fetch files.", "You fetch treats."],
        ["That's an interesting idea.", "I'll judge it after my nap."],
        ["Strong opinions.", "Tiny paws."],
    ];
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    const frames = [...button.querySelectorAll("[data-yawn-src]")];
    let index = 0;
    let playing = false;
    let load;
    let timer;
    let generation = 0;

    function reset() {
        generation++;
        clearTimeout(timer);
        button.classList.remove("is-yawning");
        button.dataset.yawnState = "idle";
        playing = false;
    }

    function nextComment() {
        index = (index + 1) % comments.length;
        caption.replaceChildren(
            document.createTextNode(comments[index][0]),
            document.createElement("br"),
            document.createTextNode(comments[index][1]),
        );
        button.dataset.captionIndex = String(index);
    }

    function prepareFrames() {
        if (!load) {
            load = Promise.all(
                frames.map((image) => {
                    image.src = image.dataset.yawnSrc;
                    return image.decode();
                }),
            ).then(
                () => true,
                () => false,
            );
        }
        return load;
    }

    async function react() {
        if (playing) return;
        nextComment();
        // Text remains interactive without animation or extra image downloads.
        if (motion.matches) return;
        playing = true;
        const ticket = ++generation;
        button.dataset.yawnState = "loading";
        const ready = await prepareFrames();
        if (ticket !== generation) return;
        if (!ready || motion.matches || document.hidden) {
            reset();
            return;
        }
        button.dataset.yawnState = "playing";
        button.classList.add("is-yawning");
        timer = setTimeout(reset, 2700);
    }

    button.addEventListener("pointerenter", (event) => {
        if (event.pointerType === "mouse") react();
    });
    button.addEventListener("click", react);
    motion.addEventListener("change", () => {
        if (motion.matches) reset();
    });
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) reset();
    });
})();
