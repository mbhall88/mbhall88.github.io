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
