export function buildQuoteUrl(canonicalUrl, quoteIndex) {
    const url = new URL(canonicalUrl);
    url.hash = `quote-${quoteIndex + 1}`;
    return url.toString();
}

export function formatQuoteCopy({ quote, postTitle, siteTitle, url }) {
    return `${quote.trim()}\n\n— From “${postTitle.trim()}” on ${siteTitle.trim()}\n${url}`;
}

export function quoteSelector(hash) {
    return /^#quote-[1-9]\d*$/.test(hash) ? hash : null;
}

function copyButtonMarkup() {
    return `
        <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="11" height="11" rx="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span>Copy</span>
    `;
}

function quoteText(blockquote) {
    const copy = blockquote.cloneNode(true);
    copy.querySelector(".copy-quote-button")?.remove();
    return copy.innerText.trim();
}

async function writeToClipboard(text) {
    if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        return;
    }

    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();

    const copied = document.execCommand("copy");
    textarea.remove();

    if (!copied) {
        throw new Error("Unable to copy quote");
    }
}

function setButtonState(button, label, className) {
    button.classList.remove("is-copied", "is-error");
    if (className) {
        button.classList.add(className);
    }
    button.querySelector("span").textContent = label;
    button.setAttribute("aria-label", `${label} quote and link`);
}

export function enhanceCopyableQuotes(doc = document) {
    const blockquotes = doc.querySelectorAll(".post-content blockquote");
    if (!blockquotes.length) {
        return;
    }

    const canonicalUrl = doc.querySelector('link[rel="canonical"]')?.href
        || window.location.href.split("#")[0];
    const postTitle = doc.querySelector('meta[property="og:title"]')?.content
        || doc.querySelector("h1.post-title")?.textContent.trim()
        || doc.title;
    const siteTitle = doc.querySelector('meta[property="og:site_name"]')?.content
        || "this blog";

    blockquotes.forEach((blockquote, index) => {
        if (blockquote.querySelector(".copy-quote-button")) {
            return;
        }

        blockquote.id = `quote-${index + 1}`;

        const button = doc.createElement("button");
        button.type = "button";
        button.className = "copy-quote-button";
        button.setAttribute("aria-label", "Copy quote and link");
        button.setAttribute("title", "Copy quote and link");
        button.innerHTML = copyButtonMarkup();

        button.addEventListener("click", async () => {
            const text = formatQuoteCopy({
                quote: quoteText(blockquote),
                postTitle,
                siteTitle,
                url: buildQuoteUrl(canonicalUrl, index),
            });

            try {
                await writeToClipboard(text);
                setButtonState(button, "Copied", "is-copied");
            } catch {
                setButtonState(button, "Retry", "is-error");
            }

            window.setTimeout(() => setButtonState(button, "Copy", ""), 2000);
        });

        blockquote.appendChild(button);
    });

    const selector = quoteSelector(window.location.hash);
    const linkedQuote = selector ? doc.querySelector(selector) : null;
    if (linkedQuote?.matches(".post-content blockquote")) {
        window.requestAnimationFrame(() => linkedQuote.scrollIntoView());
    }
}

if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => enhanceCopyableQuotes());
    } else {
        enhanceCopyableQuotes();
    }
}
