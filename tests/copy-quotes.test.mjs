import assert from "node:assert/strict";
import test from "node:test";

let copyQuotes = {};

try {
    copyQuotes = await import("../assets/js/copy-quotes.mjs");
} catch (error) {
    if (error.code !== "ERR_MODULE_NOT_FOUND") {
        throw error;
    }
}

test("buildQuoteUrl creates a direct link to the selected quote", () => {
    assert.equal(
        typeof copyQuotes.buildQuoteUrl,
        "function",
        "buildQuoteUrl must be implemented"
    );
    assert.equal(
        copyQuotes.buildQuoteUrl(
            "https://mbhall88.github.io/post/writing-with-ai/",
            2
        ),
        "https://mbhall88.github.io/post/writing-with-ai/#quote-3"
    );
});

test("formatQuoteCopy includes the quote, its post, and its deep link", () => {
    assert.equal(
        typeof copyQuotes.formatQuoteCopy,
        "function",
        "formatQuoteCopy must be implemented"
    );
    assert.equal(
        copyQuotes.formatQuoteCopy({
            quote: "The purity test for AI writing will die.\nThe quality test won't.",
            postTitle: "Writing With AI, Reading in Good Faith",
            siteTitle: "Microbes made me do it",
            url: "https://mbhall88.github.io/post/writing-with-ai/#quote-4",
        }),
        "The purity test for AI writing will die.\nThe quality test won't.\n\n— From “Writing With AI, Reading in Good Faith” on Microbes made me do it\nhttps://mbhall88.github.io/post/writing-with-ai/#quote-4"
    );
});

test("quoteSelector ignores empty and unrelated URL fragments", () => {
    assert.equal(
        typeof copyQuotes.quoteSelector,
        "function",
        "quoteSelector must be implemented"
    );
    assert.equal(copyQuotes.quoteSelector(""), null);
    assert.equal(copyQuotes.quoteSelector("#footnotes"), null);
    assert.equal(copyQuotes.quoteSelector("#quote-3"), "#quote-3");
});

test("quoteText removes every nested copy control", () => {
    let removals = 0;
    const blockquote = {
        cloneNode() {
            return {
                innerText: "A nested quotation",
                querySelectorAll(selector) {
                    assert.equal(selector, ".copy-quote-button");
                    return [
                        { remove: () => removals++ },
                        { remove: () => removals++ },
                    ];
                },
            };
        },
    };

    assert.equal(copyQuotes.quoteText(blockquote), "A nested quotation");
    assert.equal(removals, 2);
});

test("enhanceCopyableQuotes numbers quotes and scrolls only to a valid existing quote", () => {
    const makeQuote = () => ({
        id: "",
        children: [],
        querySelector: () => null,
        appendChild(child) {
            this.children.push(child);
        },
        matches: (selector) => selector === ".post-content blockquote",
        scrollIntoView() {
            this.scrolls = (this.scrolls || 0) + 1;
        },
    });
    const quotes = [makeQuote(), makeQuote()];
    const makeButton = () => ({
        classList: { add() {}, remove() {} },
        setAttribute() {},
        addEventListener() {},
    });
    const doc = {
        title: "Post title",
        querySelectorAll: () => quotes,
        createElement: makeButton,
        querySelector(selector) {
            if (selector === 'link[rel="canonical"]') {
                return { href: "https://example.com/post/" };
            }
            if (selector === 'meta[property="og:title"]') {
                return { content: "Post title" };
            }
            if (selector === 'meta[property="og:site_name"]') {
                return { content: "Site title" };
            }
            return quotes.find((quote) => `#${quote.id}` === selector) || null;
        },
    };
    const originalWindow = globalThis.window;

    try {
        globalThis.window = {
            location: { href: "https://example.com/post/#quote-2", hash: "#quote-2" },
            requestAnimationFrame: (callback) => callback(),
            setTimeout() {},
        };
        copyQuotes.enhanceCopyableQuotes(doc);

        assert.deepEqual(quotes.map((quote) => quote.id), ["quote-1", "quote-2"]);
        assert.equal(quotes[0].scrolls || 0, 0);
        assert.equal(quotes[1].scrolls, 1);

        globalThis.window.location.hash = "#missing";
        copyQuotes.enhanceCopyableQuotes(doc);
        assert.equal(quotes[1].scrolls, 1);
    } finally {
        globalThis.window = originalWindow;
    }
});
