// Privilege separation module for dependencies that can only affect CSS output.

/// <reference lib="deno.worker" />

import Browsers from 'autoprefixer/lib/browsers.js';
import Prefixes from 'autoprefixer/lib/prefixes.js';
import {agents} from 'caniuse-lite/dist/unpacker/agents.js';
import dataPrefixes from 'autoprefixer/data/prefixes.js';
import browserslist from 'browserslist';
import postcss from 'postcss';
import * as sass from 'sass';

import type {CssRequest, CssResponse} from './build.ts';

// simplified from autoprefixer/index.js
const browsers = new Browsers(agents, browserslist.defaults, {}, {
    // avoid needing excessive privileges to search for nonexistent configuration
    stats: {},
});
const prefixes = new Prefixes(dataPrefixes, browsers, {});
const cssProcessor = postcss([
    {
        postcssPlugin: 'autoprefixer',
        prepare: result => ({
            OnceExit(root) {
                prefixes.processor.remove(root, result);
                prefixes.processor.add(root, result);
            },
        }),
    },
]);

self.onmessage = (e: MessageEvent<CssRequest>) => {
    const {
        messageId,
        resolvedSource,
    } = e.data;

    const sassResult = sass.compile(resolvedSource, {
        style: 'compressed',
    });

    const result = cssProcessor.process(sassResult.css, {
        from: undefined,
        map: false,
    });

    self.postMessage({
        messageId,
        css: result.css,
        loadedUrls: sassResult.loadedUrls.map(url => url.href),
        warnings: result.warnings().map(String),
    } satisfies CssResponse);
};
