import { debounce } from '@std/async/debounce';
import { encodeBase64Url } from '@std/encoding/base64url';
import { parseArgs } from '@std/cli/parse-args';
import { mapValues } from '@std/collections/map-values';
import * as path from '@std/path';
import autoprefixer from 'autoprefixer';
import esbuild from 'esbuild';
import postcss from 'postcss';
import * as sass from 'sass-embedded';

type Awaitable<T> = T | PromiseLike<T>;
type Timer = ReturnType<typeof setTimeout>;

/** Asserts (like a cast) that an array contains no `null` elements. */
// XXX: Arrays are covariant on their element types in TypeScript, so this will accept a T[] where null is not a member of T.
const asNoNulls = <T>(arr: (T | null)[]): T[] => arr as T[];

interface TaskResult {
    /** Inputs that can change the output of this task (not always comprehensive, but good enough for watch mode). */
    readonly inputs: readonly Source[];

    /** Key/value pairs to be written to manifest.json, mapping asset ids to hash-suffixed output file paths. */
    readonly entries: readonly (readonly [string, string])[];

    /** Any further build work that wasn’t required in order to compute {@link entries}. */
    readonly work: Promise<unknown>;

    readonly cache?: TaskCache | null;
}

interface TaskResultWithCache<Cache extends TaskCache> extends TaskResult {
    readonly cache: Cache | null;
}

interface TaskResultWithInputMap extends TaskResult {
    readonly inputsByEntry: Map<string, readonly Source[]>;
}

interface TaskCache {
    dispose(): void;
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

    constructor(
        readonly verbose: boolean,
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
}

/** Indicates that error information was already written to stderr. */
const $hasStderr = Symbol('hasStderr');

interface CanHaveStderr {
    readonly [$hasStderr]: boolean;
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

const tryRemovePrefix = (s: string, prefix: string): string | null =>
    s.startsWith(prefix)
        ? s.substring(prefix.length)
        : null;

const removePrefix = (s: string, prefix: string): string => {
    const r = tryRemovePrefix(s, prefix);

    if (r === null) {
        throw new Error('String didn’t start with expected prefix');
    }

    return r;
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

interface SourceOutputPair<T = Source> {
    readonly from: T;
    readonly to: string;
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

type AnyDependencies = Readonly<Record<string, TaskResult>>;
type AnyTask<Result extends TaskResult = TaskResult> = Task<AnyDependencies, Result, TaskCache | undefined>;

interface Task<
    Dependencies extends AnyDependencies,
    Result extends TaskResult = TaskResult,
    Cache extends TaskCache | undefined = undefined,
> {
    readonly dependencies: {readonly [k in keyof Dependencies]: AnyTask<Dependencies[k]>};

    run(
        ctx: Context,
        deps: {readonly [k in keyof Dependencies]: Promise<Dependencies[k]>},
        cache: Cache | null,
    ): Awaitable<
        undefined extends Cache
            ? Result
            : TaskResultWithCache<Exclude<Cache, undefined>> & Result
    >;
}

type Dependencies<T> = T extends Task<infer U> ? U : never;
type Providers<D extends AnyDependencies> = {readonly [k in keyof D]: AnyTask<D[k]>};
type Provided<D extends AnyDependencies> = {readonly [k in keyof D]: Promise<D[k]>};

type Touch = {touch: TaskResult};

class CopyUnversionedStaticFile implements Task<Touch> {
    readonly #spec: SourceOutputPair;

    constructor(
        spec: SourceOutputSpec,
        readonly dependencies: Providers<Touch>,
    ) {
        this.#spec = expandSpec(spec);
    }

    run(ctx: Context, deps: Provided<Touch>): TaskResult {
        const outputFullPath = ctx.resolveOutput(this.#spec.to);

        return {
            inputs: [this.#spec.from],
            entries: [],
            work: deps.touch.then(() =>
                Deno.copyFile(ctx.resolveSource(this.#spec.from), outputFullPath)),
        };
    }
}

const shortHash = async (data: Uint8Array) =>
    getShortDigest(new Uint8Array(await crypto.subtle.digest('SHA-512', data)));

class CopyStaticFile implements Task<Touch> {
    readonly #file: SourceOutputPair;

    constructor(
        file: SourceOutputSpec,
        readonly dependencies: Providers<Touch>,
    ) {
        this.#file = expandSpec(file);
    }

    async run(ctx: Context, deps: Provided<Touch>): Promise<TaskResult> {
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
            await Deno.copyFile(ctx.resolveSource(this.#file.from), tempPath);

            const shortDigest = await Deno.readFile(tempPath).then(shortHash);
            const suffixedOutputPath = addFilenameSuffix(this.#file.to, shortDigest);
            const outputFullPath = ctx.resolveOutput(suffixedOutputPath);

            return {
                inputs: [this.#file.from],
                entries: [[this.#file.to, suffixedOutputPath]],
                work: deps.touch
                    .then(() => Deno.rename(tempPath, outputFullPath))
                    .catch(cleanup),
            };
        } catch (error) {
            await cleanup();
            throw error;
        }
    }
}

const joinSource = (source: Source, subpath: string): Source =>
    typeof source === 'string' ? path.join(source, subpath)
    : source instanceof AbsoluteSource ? new AbsoluteSource(path.join(source.path, subpath))
    : new PackageSource(source.package, path.join(source.path, subpath));

class CopyStaticFiles implements Task<Touch> {
    readonly #spec: SourceOutputPair;

    constructor(
        spec: SourceOutputSpec,
        readonly dependencies: Providers<Touch>,
    ) {
        this.#spec = expandSpec(spec);
    }

    async run(ctx: Context, deps: Provided<Touch>): Promise<TaskResultWithInputMap> {
        const subtasks = [];
        const resolvedSource = ctx.resolveSource(this.#spec.from);

        for await (const entry of Deno.readDir(resolvedSource)) {
            if (!entry.isDirectory) {
                const subtask = new CopyStaticFile({
                    from: joinSource(this.#spec.from, entry.name),
                    to: path.join(this.#spec.to, entry.name),
                }, this.dependencies);

                subtasks.push(subtask.run(ctx, deps));
            }
        }

        const subtasks_ = await Promise.all(subtasks);
        return {
            inputs: subtasks_.flatMap(task => task.inputs),
            entries: subtasks_.flatMap(task => task.entries),
            work: Promise.all(subtasks_.map(task => task.work)),
            inputsByEntry: new Map(subtasks_.flatMap(task =>
                task.entries.map(([k]) => [k, task.inputs]))),
        };
    }
}

class CopyRuffleComponents implements Task<Dependencies<CopyUnversionedStaticFile>> {
    constructor(
        readonly dependencies: Providers<Dependencies<CopyUnversionedStaticFile>>,
    ) {}

    async run(
        ctx: Context,
        deps: Provided<Dependencies<CopyUnversionedStaticFile>>,
    ): Promise<TaskResult> {
        const ruffleRoot = ctx.resolveSource(new PackageSource('@ruffle-rs/ruffle', '.'));
        const subtasks = [];

        for await (const {name} of Deno.readDir(ruffleRoot)) {
            if (
                name.endsWith('.wasm')
                || (name.startsWith('core.ruffle.') && name.endsWith('.js'))
            ) {
                subtasks.push(
                    // These components already include hashes in their names.
                    new CopyUnversionedStaticFile({
                        from: new PackageSource('@ruffle-rs/ruffle', name),
                        to: 'js/ruffle/' + name,
                    }, this.dependencies).run(ctx, deps)
                );
            }
        }

        return {
            inputs: [],  // This task type doesn’t watch.
            entries: subtasks.flatMap(task => task.entries),
            work: Promise.all(subtasks.map(task => task.work)),
        };
    }
}

const updateSet = <T>(set: Set<T>, values: Iterable<T>) => {
    for (const x of values) {
        set.add(x);
    }
};

class Sass implements Task<Touch & {images: TaskResultWithInputMap}> {
    readonly #spec: SourceOutputPair<RelativeSource>;

    constructor(
        spec: SourceOutputPair<RelativeSource>,
        readonly dependencies: Providers<Touch & {images: TaskResultWithInputMap}>,
    ) {
        this.#spec = spec;
    }

    async run(ctx: Context, deps: Provided<Touch & {images: TaskResultWithInputMap}>): Promise<TaskResult> {
        const sassResult = await sass.compileAsync(ctx.resolveSource(this.#spec.from), {
            style: 'compressed',
        });

        const result = postcss([autoprefixer()]).process(sassResult.css, {
            from: undefined,
            map: false,
        });

        result.warnings().forEach(warning => {
            console.error(String(warning));
        });

        // ew
        const images = await deps.images;
        const subresources = new Map<string, {inputs: readonly Source[], resolved: string}>(
            [
                ...images.entries.map(([k, v]) => [k, {
                    inputs: images.inputsByEntry.get(k)!,
                    resolved: v,
                }] as const),
                // font license does not allow distribution with source code
                ...[
                    'fonts/Museo500.woff2',
                    'fonts/Museo500.woff',
                ].map(p => [p, {inputs: [], resolved: p}] as const),
            ]
                .map(([k, v]) => [new URL('http://localhost/' + k).href, v])
        );

        const subresourceInputs = new Set<Source>();

        const urlTranslatedCss = result.css.replace(/(url\()([^)]*)\)/gi, (_match: string, left: string, link: string) => {
            if (/^["']./.test(link) && link.slice(-1) === link.charAt(0)) {
                link = link.slice(1, -1);
            }

            const expandedLink = new URL(link, 'http://localhost/' + this.#spec.from).href;
            const subresource = subresources.get(expandedLink);

            if (!subresource) {
                throw new Error(`Unresolvable url() in ${this.#spec.from}: ${link}`);
            }

            updateSet(subresourceInputs, subresource.inputs);

            return left + '/' + subresource.resolved + ')';
        });
        const urlTranslatedCssBytes = new TextEncoder().encode(urlTranslatedCss);

        const shortDigest = await shortHash(urlTranslatedCssBytes);
        const outputPath = addFilenameSuffix(this.#spec.to, shortDigest);
        const outputFullPath = ctx.resolveOutput(outputPath);

        return {
            inputs: [
                ...subresourceInputs,
                ...sassResult.loadedUrls.map(url =>
                    removePrefix(path.fromFileUrl(url), ctx.absoluteAssetsRoot + '/')),
            ],
            entries: [[this.#spec.to, outputPath]],
            work: deps.touch.then(() => Deno.writeFile(outputFullPath, urlTranslatedCssBytes)),
        };
    }
}

class EsbuildFilesWithDeps<Deps extends AnyDependencies> implements Task<Touch & Deps, TaskResult, esbuild.BuildContext> {
    #relativePaths: readonly SourceOutputSame[];
    #options: (d: Provided<Deps>) => Awaitable<esbuild.BuildOptions>;

    constructor(
        relativePaths: readonly SourceOutputSame[],
        options: (d: Provided<Deps>) => Awaitable<esbuild.BuildOptions>,
        readonly dependencies: Providers<Touch & Deps>,
    ) {
        this.#relativePaths = relativePaths;
        this.#options = options;
    }

    private async createBuildContext(ctx: Context, deps: Provided<Deps>, entryPoints: string[]) {
        return esbuild.context({
            entryPoints,
            outdir: '.',  // `outdir` is required even when `write: false`
            outbase: ctx.assetsRoot,
            bundle: true,
            minify: true,
            target: 'es6',
            banner: {
                js: '"use strict";',
            },
            mangleProps: /^m_/,
            ...await this.#options(deps),
            write: false,
            metafile: true,
        });
    }

    async run(
        ctx: Context,
        deps: Provided<Touch & Deps>,
        buildContext: Awaited<ReturnType<typeof this.createBuildContext>> | null,
    ): Promise<TaskResultWithCache<typeof buildContext & NonNullable<unknown>>> {
        const entryPoints = this.#relativePaths.map(p => ctx.resolveSource(p));
        const cwd = Deno.cwd();

        buildContext ??= await this.createBuildContext(ctx, deps, entryPoints);

        const result = await buildContext.rebuild();

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

        const inputs =
            Object.keys(result.metafile.inputs)
                .map(inputPath => tryRemovePrefix(path.join(cwd, inputPath), ctx.absoluteAssetsRoot + '/'))
                // npm dependencies aren’t watched
                .filter(x => x !== null);

        return {
            inputs,
            entries,
            work: deps.touch.then(() =>
                Promise.all(
                    writes.map(([outputPath, bundleContents]) =>
                        Deno.writeFile(ctx.resolveOutput(outputPath), bundleContents)
                    )
                )
            ),
            cache: buildContext,
        };
    }
}

class EsbuildFiles extends EsbuildFilesWithDeps<Touch> {
    constructor(
        relativePaths: readonly SourceOutputSame[],
        options: esbuild.BuildOptions,
        dependencies: Providers<Touch>,
    ) {
        super(relativePaths, () => options, dependencies);
    }
}

const showUsage = () => {
    console.error('Usage: deno run build.ts --assets=<asset-dir> --output=<output-dir>');
};

class UsageError extends Error implements CanHaveStderr {
    get [$hasStderr]() {
        return true;
    }
}

class CreateFolders implements Task<Record<string, never>> {
    constructor(
        readonly folders: readonly string[],
    ) {}

    get dependencies() {
        return {};
    }

    async run(ctx: Context): Promise<TaskResult> {
        await Promise.all(
            this.folders.map(p =>
                Deno.mkdir(
                    path.join(ctx.outputRoot, p),
                    {recursive: true}
                )
            )
        );

        return {
            inputs: [],
            entries: [],
            work: Promise.resolve(),
        };
    }
}

const getSingleEntry = (result: TaskResult, expectedKey: string): string => {
    const {entries} = result;

    if (entries.length !== 1 || entries[0][0] !== expectedKey) {
        console.error('Expected task to produce single entry with key %o, but got %o.', expectedKey, entries);
        throw new Error();
    }

    return entries[0][1];
};

const touch = new CreateFolders([
    'css',
    'fonts',
    'img/help',
    'js/mod',
    'js/ruffle',
]);

const images = new CopyStaticFiles('img', {touch});

const marked = new CopyStaticFile('js/marked.js', {touch});

const ruffle = new CopyStaticFile({
    from: new PackageSource('@ruffle-rs/ruffle', 'ruffle.js'),
    to: 'js/ruffle/ruffle.js',
}, {touch});

const PRIVATE_FIELDS: esbuild.BuildOptions = {
    target: [
        'chrome84',
        'firefox90',
        'ios15',
        'safari15',
    ],
};

const PRIVATE_FIELDS_ESM: esbuild.BuildOptions = {
    ...PRIVATE_FIELDS,
    format: 'esm',
    banner: {},
};

const tasks: readonly AnyTask[] = [
    touch,
    images,
    marked,
    new Sass({from: 'scss/site.scss', to: 'css/site.css'}, {touch, images}),
    new Sass({from: 'scss/help.scss', to: 'css/help.css'}, {touch, images}),
    new Sass({from: 'scss/imageselect.scss', to: 'css/imageselect.css'}, {touch, images}),
    new Sass({from: 'scss/mod.scss', to: 'css/mod.css'}, {touch, images}),
    new Sass({from: 'scss/signup.scss', to: 'css/signup.css'}, {touch, images}),
    new EsbuildFilesWithDeps<{marked: TaskResult}>([
        'js/scripts.js',
    ], async (deps) => {
        const markedSrc = getSingleEntry(await deps.marked, 'js/marked.js');

        return ({
            define: {
                MARKED_SRC: JSON.stringify('/' + markedSrc),
            },
        });
    }, {touch, marked}),
    new EsbuildFiles([
        'js/search.js',
        'js/zxcvbn-check.js',
    ], {}, {touch}),

    // main.js has a `Link: …;rel=preload`, and Cloudflare’s Early Hints implementation doesn’t support `modulepreload` yet
    new EsbuildFiles(['js/main.js'], PRIVATE_FIELDS, {touch}),

    new EsbuildFiles([
        'js/forms.js',
        'js/login-box.js',
        'js/message-list.js',
        'js/notification-list.js',
        'js/rating-override.js',
        'js/tags-edit.js',
        'js/submit.js',
        'js/view-count.js',
        'js/mod/suspenduser.js',
    ], PRIVATE_FIELDS_ESM, {touch}),
    new EsbuildFilesWithDeps<{ruffle: TaskResult}>([
        'js/flash.js',
    ], async (deps) => {
        const ruffleSrc = getSingleEntry(await deps.ruffle, 'js/ruffle/ruffle.js');

        return ({
            ...PRIVATE_FIELDS_ESM,
            define: {
                RUFFLE_SRC: JSON.stringify('/' + ruffleSrc),
            },
        });
    }, {touch, ruffle}),
    new CopyStaticFiles('img/help', {touch}),
    new CopyUnversionedStaticFile('opensearch.xml', {touch}),

    // libraries
    new CopyStaticFile('js/jquery-2.2.4.min.js', {touch}),
    new CopyStaticFile('js/imageselect.js', {touch}),
    new CopyStaticFile('js/zxcvbn.js', {touch}),
    new CopyRuffleComponents({touch}),
    ruffle,
];

const ORDER_UNSET = -1;
const ORDER_IN_PROGRESS = -2;

const getTopologicalOrder = (
    tasks: readonly AnyTask[],
    indexOf: (t: AnyTask) => number | undefined,
): number[] => {
    const order: number[] = Array(tasks.length).fill(ORDER_UNSET);
    let nextOrder = 0;

    const traverse = (i: number) => {
        if (order[i] >= 0) {
            // dependency already satisfied
            return;
        }

        if (order[i] === ORDER_IN_PROGRESS) {
            throw new Error('dependency cycle');
        }

        order[i] = ORDER_IN_PROGRESS;

        // satisfy all dependencies of this task
        for (const dep in tasks[i].dependencies) {
            const depIndex = indexOf(tasks[i].dependencies[dep]);

            if (depIndex === undefined) {
                throw new Error(`dependency not in tasks: ${dep}`);
            }

            traverse(depIndex);
        }

        // all dependencies of this task are now satisfied
        order[i] = nextOrder++;
    };

    for (let i = 0; i < tasks.length; i++) {
        traverse(i);
    }

    return order;
};

const enum Condition {
    set,
    unset,
    handled,
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

    const verbose = !args.watch;
    const ctx: Context = new Context(verbose, assetsRoot, outputRoot);

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
    const watcher = args.watch ? Deno.watchFs(ctx.absoluteAssetsRoot, {recursive: true}) : null;
    const watcherPrefix = ctx.absoluteAssetsRoot + '/';

    const watchMap = new Map<string, number[]>();
    let buildFailed = Condition.unset;

    const indexes = new Map(tasks.entries().map(([i, task]) => [task, i]));

    const order = getTopologicalOrder(tasks, t => indexes.get(t));

    const latestRuns: (Awaitable<TaskResult> | null)[] = Array(tasks.length).fill(null);
    const latestCache: (TaskCache | null)[] = Array(tasks.length).fill(null);

    const rebuild = async () => {
        watchMap.clear();
        buildFailed = Condition.unset;

        let startedRuns = null;

        try {
            for (const i of order) {
                if (latestRuns[i] === null) {
                    const task = tasks[i];

                    const deps = mapValues(task.dependencies, dep =>
                        Promise.resolve(latestRuns[indexes.get(dep)!]!));

                    latestRuns[i] = task.run(ctx, deps, latestCache[i]);
                }
            }

            startedRuns = asNoNulls(latestRuns);
            const taskResults = await Promise.all(startedRuns);

            for (const [i, r] of taskResults.entries()) {
                if (args.watch) {
                    latestCache[i] = r.cache ?? null;
                } else {
                    r.cache?.dispose();
                }

                for (const input of r.inputs) {
                    if (typeof input !== 'string') {
                        // only `RelativeSource`s can be watched
                        continue;
                    }

                    let inputTasks = watchMap.get(input);
                    if (inputTasks === undefined) {
                        watchMap.set(input, inputTasks = []);
                    }

                    inputTasks.push(i);
                }
            }

            await Deno.writeTextFile(
                manifestPath,
                JSON.stringify(
                    Object.fromEntries(
                        taskResults.flatMap(r => r.entries))),
            );
            await Promise.all(taskResults.map(r => r.work));
            return true;
        } catch (error) {
            if (startedRuns !== null) {
                let timer: Timer | null = setTimeout(() => {
                    timer = null;
                    console.debug('waiting for other tasks to finish after build failure…');
                }, 100);

                await Promise.allSettled(startedRuns);

                if (timer === null) {
                    console.debug('other tasks done');
                } else {
                    clearTimeout(timer);
                }
            }

            watchMap.clear();
            buildFailed = Condition.set;

            if (!args.watch) {
                throw error;
            }

            if (!hasStderr(error)) {
                console.error('%s', error);
            }

            return false;
        }
    };

    await rebuild();

    if (watcher === null) {
        return;
    }

    /** Changes since the last build started or was enqueued. */
    const changes = new Set<string>();
    let changesUnknown = Condition.unset;

    const rebuilder = new LimitOne(async () => {
        changes.clear();
        changesUnknown = Condition.unset;

        performance.mark('rebuild-start');
        const success = await rebuild();
        performance.mark('rebuild-end');

        // Handle changes that occurred during the build.
        // TODO: Could reduce delay by allowing the changes themselves to set the debounce period.
        const needed = debouncedRebuildIfNeeded();

        const measure = performance.measure('rebuild', {
            start: 'rebuild-start',
            end: 'rebuild-end',
        });

        console.debug(
            'watch: rebuild '
            + (success ? 'done' : 'failed')
            + ` in ${measure.duration.toFixed(1)} ms`
            + (needed ? ', rebuilding again' : '')
        );
    });

    const debouncedRebuild = debounce(rebuilder.run, 100);

    const debouncedRebuildIfNeeded = (): boolean => {
        let needed = false;

        if (changesUnknown !== Condition.unset) {
            if (changesUnknown !== Condition.handled) {
                // Mark every task that depends on inputs at all as needing to be rerun.
                for (const taskIndexes of watchMap.values()) {
                    for (const i of taskIndexes) {
                        latestRuns[i] = null;
                    }
                }

                needed = true;
                changesUnknown = Condition.handled;
            }
        } else if (buildFailed !== Condition.unset && changes.size !== 0) {
            if (buildFailed !== Condition.handled) {
                // Mark every task as needing to be rerun.
                latestRuns.fill(null);

                needed = true;
                buildFailed = Condition.handled;
            }
        } else {
            // Mark tasks that depend on changed inputs as needing to be rerun.
            for (const change of changes) {
                const taskIndexes = watchMap.get(change);

                if (taskIndexes !== undefined) {
                    needed = true;

                    for (const i of taskIndexes) {
                        latestRuns[i] = null;
                    }
                }
            }
        }

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
                    const r = tryRemovePrefix(p, watcherPrefix);

                    if (r !== null) {
                        changes.add(r);
                    } else {
                        console.warn('warning: ignoring unexpected file watcher path %o', p);
                    }
                }

                break;

            default:  // 'other' or 'any'
                console.warn('warning: ignoring unknown file watcher event %o', event);
                continue;
        }

        if (event.flag === 'rescan' && changesUnknown === Condition.unset) {
            changesUnknown = Condition.set;
        }

        let reaction;

        if (rebuilder.running) {
            reaction = 'deferred';
        } else {
            reaction = debouncedRebuildIfNeeded() ? 'will rebuild' : 'ignored';
        }

        const nicePaths = event.paths.map(p =>
            tryRemovePrefix(p, watcherPrefix) ?? p);
        console.debug('watch: %s %o (%s)', event.kind, nicePaths, reaction);
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
