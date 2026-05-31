// Privilege separation module for dependencies that can only affect CSS output.

/// <reference lib="deno.worker" />

import autoprefixer from 'autoprefixer';
import browserslist from 'browserslist';
import postcss from 'postcss';
import * as sass from 'sass';

import type {CssRequest, CssResponse} from './build.ts';

self.onmessage = (e: MessageEvent<CssRequest>) => {
    const {
        messageId,
        resolvedSource,
    } = e.data;

    const sassResult = sass.compile(resolvedSource, {
        style: 'compressed',
    });

    const result = postcss([
        autoprefixer({
            // avoid needing excessive privileges to search for nonexistent configuration
            overrideBrowserslist: browserslist.defaults as (typeof browserslist.defaults[0])[],
            stats: {},
        }),
    ]).process(sassResult.css, {
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
