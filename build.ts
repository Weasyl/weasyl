import { encodeBase64Url } from '@std/encoding/base64url';
import { parseArgs } from '@std/cli/parse-args';
import * as path from '@std/path';
import autoprefixer from 'autoprefixer';
import esbuild from 'esbuild';
import postcss from 'postcss';
import * as sass from 'sass-embedded';

interface Task {
    /** Inputs that can change the output of this task (not always comprehensive, but good enough for watch mode). */
    inputs: Source[];

    /** Key/value pairs to be written to manifest.json, mapping asset ids to hash-suffixed output file paths. */
    entries: [string, string][];

    /** Any further build work that wasn’t required in order to compute {@link entries}. */
    work: Promise<unknown>;
}

class PackageSource {
    readonly package: string;

    constructor(
        package_: string,
        readonly path: string,
    ) {
        this.package = package_;
    }
}

class AbsoluteSource {
    constructor(readonly path: string) {}
}

type RelativeSource = string;

type Source =
    | RelativeSource
    | PackageSource
    | AbsoluteSource;

class Context {
    readonly absoluteAssetsRoot: string;

    copyImages?: Promise<Task>;

    constructor(
        readonly verbose: boolean,
        readonly touch: Promise<unknown>,
        readonly assetsRoot: string,
        readonly outputRoot: string,
    ) {
        this.absoluteAssetsRoot = path.resolve(assetsRoot);
    }

    resolveSource(source: Source) {
        if (typeof source === 'string') {
            return path.join(this.assetsRoot, source);
        }

        if (source instanceof AbsoluteSource) {
            return source.path;
        }

        if (import.meta.dirname === undefined) {
            throw new Error();
        }

        return path.join(import.meta.dirname, 'node_modules', source.package, source.path);
    }

    resolveOutput(output: string) {
        return path.join(this.outputRoot, output);
    }

    setCopyImages(copyImages: Promise<Task>): asserts this is CopyImagesContext {
        this.copyImages = copyImages;
    }
}

interface CopyImagesContext extends Context {
    copyImages: Promise<Task>;

    setCopyImages(copyImages: never): never;
}

/** Indicates that error information was already written to stderr. */
const $hasStderr = Symbol('hasStderr');

interface CanHaveStderr {
    [$hasStderr]: boolean;
}

const hasStderr = (error: unknown): boolean =>
    error != null
    && Boolean((error as {[$hasStderr]?: boolean})[$hasStderr]);

/**
 * Gets a 10-character digest from a SHA-512 digest buffer using characters from the URL-safe base64 set.
 */
const getShortDigest = (digest: Uint8Array): string => {
    if (digest.length < 8) {
        throw new RangeError('Digest too short');
    }

    return encodeBase64Url(digest)
        .substring(0, 10);
};

const addFilenameSuffix = (relativePath: string, suffix: string): string => {
    const pathInfo = path.parse(relativePath);

    return path.format({
        dir: pathInfo.dir,
        name: pathInfo.name + '-' + suffix,
        ext: pathInfo.ext,
    });
};

const removePrefix = (s: string, prefix: string) => {
    if (!s.startsWith(prefix)) {
        throw new Error('String didn’t start with expected prefix');
    }

    return s.substring(prefix.length);
};

declare global {
    interface PromiseConstructor {
        // XXX: simplified while waiting for this to work out of the box
        try<T>(action: () => T | PromiseLike<T>): Promise<Awaited<T>>;
    }
}

/** Prevents an idempotent async action from running multiple times concurrently, queuing one run as necessary. */
class LimitOne {
    #action: () => Promise<void>;
    #running = false;
    #waiting: PromiseWithResolvers<void> = Promise.withResolvers();

    constructor(action: () => Promise<void>) {
        this.#action = action;
    }

    get running(): boolean {
        return this.#running;
    }

    run = (): Promise<void> => {
        if (this.#running) {
            return this.#waiting.promise;
        }

        const oldWaiting = this.#waiting;
        this.#waiting = Promise.withResolvers();
        this.#running = true;
        oldWaiting.resolve(Promise.try(this.#action).finally(() => {
            this.#running = false;
        }));
        return oldWaiting.promise;
    };
}

/** Merges multiple attempts to perform an action separated by at most some interval into a single attempt. */
const debounce = (action: () => Promise<void>, ms: number) => {
    let timer: ReturnType<typeof setTimeout> | null = null;

    return () => {
        if (timer !== null) {
            clearTimeout(timer);
        }

        timer = setTimeout(() => {
            timer = null;
            action();
        }, ms);
    };
};

interface SourceOutputPair<T = Source> {
    from: T;
    to: string;
}

type SourceOutputSame = string;

type SourceOutputSpec<T = Source> = SourceOutputSame | SourceOutputPair<T>;

const expandSpec = <T>(spec: SourceOutputSpec<T>): SourceOutputPair<T | string> =>
    typeof spec === 'string'
        ? {
            from: spec,
            to: spec,
        }
        : spec;

const copyUnversionedStaticFile = (
    ctx: Context,
    spec: SourceOutputSpec,
): Task => {
    spec = expandSpec(spec);

    const outputFullPath = ctx.resolveOutput(spec.to);

    return {
        inputs: [spec.from],
        entries: [],
        work: ctx.touch.then(() =>
            Deno.copyFile(ctx.resolveSource(spec.from), outputFullPath)),
    };
};

const shortHash = async (data: Uint8Array) =>
    getShortDigest(new Uint8Array(await crypto.subtle.digest('SHA-512', data)));

const copyStaticFile = async (ctx: Context, file: SourceOutputSpec): Promise<Task> => {
    file = expandSpec(file);

    const tempPath = await Deno.makeTempFile({dir: ctx.outputRoot});

    const cleanup = async () => {
        try {
            await Deno.remove(tempPath);
        } catch (removeError) {
            if (!(removeError instanceof Deno.errors.NotFound)) {
                console.error('Failed to remove temporary file: %o', removeError);
            }
        }
    };

    try {
        await Deno.copyFile(ctx.resolveSource(file.from), tempPath);

        const shortDigest = await Deno.readFile(tempPath).then(shortHash);
        const suffixedOutputPath = addFilenameSuffix(file.to, shortDigest);
        const outputFullPath = ctx.resolveOutput(suffixedOutputPath);

        return {
            inputs: [file.from],
            entries: [[file.to, suffixedOutputPath]],
            work: ctx.touch
                .then(() => Deno.rename(tempPath, outputFullPath))
                .catch(cleanup),
        };
    } catch (error) {
        await cleanup();
        throw error;
    }
};

const copyStaticFiles = async (ctx: Context, spec: SourceOutputSpec): Promise<Task> => {
    spec = expandSpec(spec);

    const subtasks = [];
    const resolvedSource = ctx.resolveSource(spec.from);

    for await (const entry of Deno.readDir(resolvedSource)) {
        if (!entry.isDirectory) {
            subtasks.push(copyStaticFile(ctx, {
                from: new AbsoluteSource(path.join(resolvedSource, entry.name)),
                to: path.join(spec.to, entry.name),
            }));
        }
    }

    const subtasks_ = await Promise.all(subtasks);
    return {
        inputs: subtasks_.flatMap(task => task.inputs),
        entries: subtasks_.flatMap(task => task.entries),
        work: Promise.all(subtasks_.map(task => task.work)),
    };
};

const copyRuffleComponents = async (ctx: Context): Promise<Task> => {
    const ruffleRoot = ctx.resolveSource(new PackageSource('@ruffle-rs/ruffle', '.'));
    const subtasks = [];

    for await (const {name} of Deno.readDir(ruffleRoot)) {
        if (
            name.endsWith('.wasm')
            || (name.startsWith('core.ruffle.') && name.endsWith('.js'))
        ) {
            subtasks.push(
                // These components already include hashes in their names.
                copyUnversionedStaticFile(ctx, {
                    from: new PackageSource('@ruffle-rs/ruffle', name),
                    to: 'js/ruffle/' + name,
                })
            );
        }
    }

    return {
        inputs: [],
        entries: subtasks.flatMap(task => task.entries),
        work: Promise.all(subtasks.map(task => task.work)),
    };
};

const sasscFile = async (ctx: CopyImagesContext, spec: SourceOutputPair<RelativeSource>): Promise<Task> => {
    const sassResult = await sass.compileAsync(ctx.resolveSource(spec.from));

    const result = postcss([autoprefixer()]).process(sassResult.css, {
        from: undefined,
        map: false,
    });

    result.warnings().forEach(warning => {
        console.error(String(warning));
    });

    // ew
    const subresources = new Map(
        [
            ...(await ctx.copyImages).entries,
            // font license does not allow distribution with source code
            ...[
                'fonts/Museo500.woff2',
                'fonts/Museo500.woff',
            ].map(p => [p, p]),
        ]
            .map(([k, v]) => [new URL('http://localhost/' + k).href, v])
    );

    const urlTranslatedCss = result.css.replace(/(url\()([^)]*)\)/gi, (_match, left, link) => {
        if (/^["']./.test(link) && link.slice(-1) === link.charAt(0)) {
            link = link.slice(1, -1);
        }

        const expandedLink = new URL(link, 'http://localhost/' + spec.from).href;

        if (!subresources.has(expandedLink)) {
            throw new Error(`Unresolvable url() in ${spec.from}: ${link}`);
        }

        return left + '/' + subresources.get(expandedLink) + ')';
    });
    const urlTranslatedCssBytes = new TextEncoder().encode(urlTranslatedCss);

    const shortDigest = await shortHash(urlTranslatedCssBytes);
    const outputPath = addFilenameSuffix(spec.to, shortDigest);
    const outputFullPath = ctx.resolveOutput(outputPath);

    return {
        inputs: sassResult.loadedUrls.map(url =>
            removePrefix(path.fromFileUrl(url), ctx.absoluteAssetsRoot + '/')),
        entries: [[spec.to, outputPath]],
        work: ctx.touch.then(() => Deno.writeFile(outputFullPath, urlTranslatedCssBytes)),
    };
};

const esbuildFiles = async (ctx: Context, relativePaths: SourceOutputSame[], options: esbuild.BuildOptions) => {
    const entryPoints = relativePaths.map(p => ctx.resolveSource(p));
    const cwd = Deno.cwd();

    // TODO: use build contexts
    const result = await esbuild.build({
        entryPoints,
        outdir: '.',  // `outdir` is required even when `write: false`
        outbase: ctx.assetsRoot,
        bundle: true,
        minify: true,
        target: 'es5',
        banner: {
            js: '"use strict";',
        },
        ...options,
        write: false,
        metafile: true,
    });

    if (result.warnings.length !== 0) {
        for (const warning of result.warnings) {
            console.warn(warning);
        }

        throw new Error('Unexpected warnings');
    }

    if (ctx.verbose) {
        console.log(await esbuild.analyzeMetafile(result.metafile, {verbose: true}));
    }

    const entries: [string, string][] = [];
    const writes: [string, Uint8Array][] = [];

    // output metadata keyed by esbuild’s output files’ `path` property, which seems to be an absolute path based on the resolved value of `outdir`
    // XXX: not yet tested on Windows
    const outputsByAbsPath = new Map(
        Object.entries(result.metafile.outputs)
        .map(([assetId, output]) => [path.join(cwd, assetId), {
            assetId,
            output,  // XXX: unused for now
        }])
    );

    for (const outputFile of result.outputFiles) {
        const {assetId} = outputsByAbsPath.get(outputFile.path)!;
        const bundleContents = outputFile.contents;

        const shortDigest = await shortHash(bundleContents);

        const outputPath = addFilenameSuffix(assetId, shortDigest);

        entries.push([assetId, outputPath]);
        writes.push([outputPath, bundleContents]);
    }

    const inputs = Object.keys(result.metafile.inputs).map(inputPath =>
        removePrefix(path.join(cwd, inputPath), ctx.absoluteAssetsRoot + '/'));

    return {
        inputs,
        entries,
        work: ctx.touch.then(() =>
            Promise.all(
                writes.map(([outputPath, bundleContents]) =>
                    Deno.writeFile(ctx.resolveOutput(outputPath), bundleContents)
                )
            )
        ),
    };
};

const showUsage = () => {
    console.error('Usage: deno run build.ts --assets=<asset-dir> --output=<output-dir>');
};

class UsageError extends Error implements CanHaveStderr {
    get [$hasStderr]() {
        return true;
    }
}

const main = async () => {
    const args = parseArgs(Deno.args, {
        string: ['assets', 'output'],
        boolean: ['watch'],
        default: {
            watch: false,
        },
        unknown: () => {
            showUsage();
            throw new UsageError();
        },
    });

    if (args.assets === undefined || args.output === undefined) {
        showUsage();
        throw new UsageError();
    }

    const assetsRoot: string = args.assets;
    const outputRoot: string = args.output;

    const manifestPath = path.join(outputRoot, 'rev-manifest.json');

    const touch: Promise<unknown> = Promise.all([
        Deno.mkdir(path.join(outputRoot, 'css'), {recursive: true}),
        Deno.mkdir(path.join(outputRoot, 'fonts'), {recursive: true}),
        Deno.mkdir(path.join(outputRoot, 'img', 'help'), {recursive: true}),
        Deno.mkdir(path.join(outputRoot, 'js', 'ruffle'), {recursive: true}),
    ]);

    const verbose = !args.watch;
    const ctx: Context = new Context(verbose, touch, assetsRoot, outputRoot);

    const PRIVATE_FIELDS_ESM: esbuild.BuildOptions = {
        format: 'esm',
        target: [
            'chrome84',
            'firefox90',
            'ios15',
            'safari15',
        ],
        banner: {},
    };

    // Node:
    //     apparently no race on Linux (uncomfortable and not documented; I would expect watcher readiness to be async): https://github.com/nodejs/node/issues/52601
    //     can’t just use `fs[.promises].watch` with `recursive`: https://github.com/nodejs/node/blob/v23.11.0/lib/internal/fs/promises.js#L1248-L1250
    //
    // Deno:
    //     unknown. TODO
    //
    // Preferably shouldn’t miss any events during (or after!) the first build.
    //
    // We don’t really want this to produce absolute paths in events at all, but not only does it, it can actually produce weird paths like `/weasyl-build/./assets/…` with a relative path argument, so pass an absolute path.
    const watcher = Deno.watchFs(ctx.absoluteAssetsRoot, {recursive: true});
    const watcherPrefix = ctx.absoluteAssetsRoot + '/';

    // https://stackoverflow.com/questions/73946077/typescript-incorrectly-narrows-the-type
    let watchSet = null as Set<string> | null;

    const rebuild = async () => {
        try {
            ctx.setCopyImages(copyStaticFiles(ctx, 'img'));

            const tasks_: (Task | Promise<Task>)[] = [
                sasscFile(ctx, {from: 'scss/site.scss', to: 'css/site.css'}),
                sasscFile(ctx, {from: 'scss/help.scss', to: 'css/help.css'}),
                sasscFile(ctx, {from: 'scss/imageselect.scss', to: 'css/imageselect.css'}),
                sasscFile(ctx, {from: 'scss/mod.scss', to: 'css/mod.css'}),
                sasscFile(ctx, {from: 'scss/signup.scss', to: 'css/signup.css'}),
                esbuildFiles(ctx, ['js/scripts.js'], {}),
                esbuildFiles(ctx, [
                    'js/main.js',
                    'js/message-list.js',
                    'js/tags-edit.js',
                    'js/signup.js',
                ], PRIVATE_FIELDS_ESM),
                esbuildFiles(ctx, ['js/flash.js'], {
                    format: 'esm',
                    target: 'es6',
                    banner: {},
                }),
                copyStaticFiles(ctx, 'img/help'),
                copyUnversionedStaticFile(ctx, 'opensearch.xml'),
                ctx.copyImages,

                // libraries
                copyStaticFile(ctx, 'js/jquery-2.2.4.min.js'),
                copyStaticFile(ctx, 'js/imageselect.js'),
                copyStaticFile(ctx, 'js/marked.js'),
                copyStaticFile(ctx, 'js/zxcvbn.js'),
                copyRuffleComponents(ctx),
                copyStaticFile(ctx, {
                    from: new PackageSource('@ruffle-rs/ruffle', 'ruffle.js'),
                    to: 'js/ruffle/ruffle.js',
                }),

                // site
                copyStaticFile(ctx, 'js/notification-list.js'),
                copyStaticFile(ctx, 'js/search.js'),
                copyStaticFile(ctx, 'js/zxcvbn-check.js'),
            ];

            const tasks = await Promise.all(tasks_);

            watchSet = new Set(
                tasks.flatMap(task => task.inputs)
                .filter(input => typeof input === 'string')  // only `RelativeSource`s can be watched
            );

            await touch;
            await Deno.writeTextFile(
                manifestPath,
                JSON.stringify(
                    Object.fromEntries(
                        tasks.flatMap(task => task.entries))),
            );
            await Promise.all(tasks.map(task => task.work));
            return true;
        } catch (error) {
            if (!args.watch) {
                throw error;
            }

            if (!hasStderr(error)) {
                console.error('%s', error);
            }

            watchSet = null;
            return false;
        }
    };

    await rebuild();

    if (!args.watch) {
        return;
    }

    /** Changes since the last build started or was enqueued. */
    const changes = new Set<string>();
    let changesUnknown = false;

    const rebuilder = new LimitOne(async () => {
        changes.clear();
        changesUnknown = false;

        const success = await rebuild();

        // Handle changes that occurred during the build.
        // TODO: Could reduce delay by allowing the changes themselves to set the debounce period.
        const needed = debouncedRebuildIfNeeded();

        console.debug(
            'watch: rebuild '
            + (success ? 'done' : 'failed')
            + (needed ? ', rebuilding again' : '')
        );
    });

    const debouncedRebuild = debounce(rebuilder.run, 100);

    const debouncedRebuildIfNeeded = (): boolean => {
        const needed = (
            changesUnknown
            || (watchSet !== null && !changes.isDisjointFrom(watchSet))
            || (watchSet === null && changes.size !== 0)
        );

        // Avoid building up and rechecking unnecessary changes during the debounce period, as well as ignored files.
        changes.clear();

        if (needed) {
            debouncedRebuild();
        }

        return needed;
    };

    for await (const event of watcher) {
        // https://docs.rs/notify/latest/notify/enum.EventKind.html
        switch (event.kind) {
            case 'access':
                continue;

            case 'rename':
            case 'remove':
            case 'modify':
            case 'create':
                for (const p of event.paths) {
                    if (p.startsWith(watcherPrefix)) {
                        changes.add(removePrefix(p, watcherPrefix));
                    } else {
                        console.warn('warning: ignoring unexpected file watcher path %o', p);
                    }
                }

                break;

            default:  // 'other' or 'any'
                console.warn('warning: ignoring unknown file watcher event %o', event);
                continue;
        }

        changesUnknown ||= event.flag === 'rescan';

        let reaction;

        if (rebuilder.running) {
            reaction = 'deferred';
        } else {
            reaction = debouncedRebuildIfNeeded() ? 'will rebuild' : 'ignored';
        }

        console.debug('watch: %s %o (%s)', event.kind, event.paths, reaction);
    }
};

try {
    await main();
} catch (error) {
    if (hasStderr(error)) {
        Deno.exitCode = 1;
    } else {
        throw error;
    }
}
