'use strict';

const autoprefixer = require('autoprefixer');
const child_process = require('child_process');
const crypto = require('crypto');
const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');
const postcss = require('postcss');

const ASSETS = path.join(__dirname, 'assets');
const BUILD = path.join(__dirname, 'build');

const terminate = error => {
    process.nextTick(() => {
        throw error;
    });
};

const sassc = inputPath =>
    new Promise((resolve, reject) => {
        const sassProcess = child_process.execFile(
            'sassc', ['--style=compressed', '--', inputPath],
            (error, stdout, stderr) => {
                if (error) {
                    error.message = error.message.replace('\n' + stderr, '');
                    error.hasStderr = Boolean(stderr);
                    reject(error);
                    return;
                }

                resolve(stdout);
            }
        );

        sassProcess.stderr.pipe(process.stderr);
    });

/**
 * Gets a 10-character digest from a SHA-512 digest buffer using characters from the URL-safe base64 set.
 */
const getShortDigest = digest => {
    if (digest.length < 8) {
        throw new RangeError('Digest too short');
    }

    return digest
        .toString('base64')
        .substring(0, 10)
        .replace(/\+/g, '-')
        .replace(/\//g, '_');
};

const packageSource = packagePath =>
    path.join(__dirname, 'node_modules', packagePath);

const addFilenameSuffix = (relativePath, suffix) => {
    const pathInfo = path.parse(relativePath);

    return path.format({
        dir: pathInfo.dir,
        name: pathInfo.name + '-' + suffix,
        ext: pathInfo.ext,
    });
};

const fallbackFile = file =>
    typeof file === 'string'
        ? {
            from: path.join(ASSETS, file),
            to: file,
        }
        : file;

const copyUnversionedStaticFile = (file, touch) => {
    file = fallbackFile(file);

    const outputFullPath = path.join(BUILD, file.to);

    return {
        entries: [],
        work: touch.then(() =>
            fs.promises.copyFile(file.from, outputFullPath)),
    };
};

const copyStaticFile = (file, touch) => {
    file = fallbackFile(file);

    const stream = fs.createReadStream(file.from);
    const hash = crypto.createHash('sha512');

    stream.pipe(hash);

    return new Promise((resolve, reject) => {
        stream.once('error', reject);

        hash.once('readable', () => {
            const shortDigest = getShortDigest(hash.read());
            const suffixedOutputPath = addFilenameSuffix(file.to, shortDigest);
            const outputFullPath = path.join(BUILD, suffixedOutputPath);

            resolve({
                entries: [[file.to, suffixedOutputPath]],
                work: touch.then(() =>
                    fs.promises.copyFile(file.from, outputFullPath)),
            });
        });
    });
};

const copyStaticFiles = async (relativePath, touch) => {
    const names = await fs.promises.readdir(path.join(ASSETS, relativePath));
    const subtasks = await Promise.all(
        names.map(async name => {
            const subpath = path.join(relativePath, name);
            const subpathStat = await fs.promises.stat(path.join(ASSETS, subpath));

            if (subpathStat.isDirectory()) {
                return {
                    entries: [],
                    work: Promise.resolve(),
                };
            }

            return await copyStaticFile(subpath, touch);
        })
    );

    return {
        entries: subtasks.flatMap(task => task.entries),
        work: Promise.all(subtasks.map(task => task.work)),
    };
};

const copyRuffleComponents = async (touch) => {
    const names = await fs.promises.readdir(packageSource('@ruffle-rs/ruffle'));
    const subtasks = await Promise.all(
        names
            .filter(name =>
                name.endsWith('.wasm')
                || (name.startsWith('core.ruffle.') && name.endsWith('.js'))
            )
            .map(name =>
                // These components already include hashes in their names.
                copyUnversionedStaticFile({
                    from: packageSource('@ruffle-rs/ruffle/' + name),
                    to: 'js/ruffle/' + name,
                }, touch)
            )
    );

    return {
        entries: subtasks.flatMap(task => task.entries),
        work: Promise.all(subtasks.map(task => task.work)),
    };
};

const sasscFile = async (relativeInputPath, relativeOutputPath, touch, copyImages) => {
    const inputPath = path.join(ASSETS, relativeInputPath);

    const css = await sassc(inputPath);

    const result = postcss([autoprefixer()]).process(css, {
        from: undefined,
        map: false,
    });

    result.warnings().forEach(warning => {
        console.error(String(warning));
    });

    // ew
    const subresources = new Map(
        [
            ...(await copyImages).entries,
            // font license does not allow distribution with source code
            ...[
                'fonts/Museo500.woff2',
                'fonts/Museo500.woff',
            ].map(p => [p, p]),
        ]
            .map(([k, v]) => [new URL('http://localhost/' + k).href, v])
    );

    const urlTranslatedCss = result.css.replace(/(url\()([^)]*)\)/gi, (match, left, link) => {
        if (/^["']./.test(link) && link.slice(-1) === link.charAt(0)) {
            link = link.slice(1, -1);
        }

        const expandedLink = new URL(link, 'http://localhost/' + relativeInputPath).href;

        if (!subresources.has(expandedLink)) {
            throw new Error(`Unresolvable url() in ${relativeInputPath}: ${link}`);
        }

        return left + '/' + subresources.get(expandedLink) + ')';
    });

    const shortDigest = getShortDigest(
        crypto.createHash('sha512')
            .update(urlTranslatedCss, 'utf8')
            .digest()
    );

    const outputPath = addFilenameSuffix(relativeOutputPath, shortDigest);
    const outputFullPath = path.join(BUILD, outputPath);

    return {
        entries: [[relativeOutputPath, outputPath]],
        work: touch.then(() => fs.promises.writeFile(outputFullPath, urlTranslatedCss, 'utf8')),
    };
};

// For convenience, this function accepts an array of `relativePaths` that represent both input paths relative to `ASSETS` and output paths relative to `BUILD`.
const esbuildFiles = async (relativePaths, touch, options) => {
    const entryPoints = relativePaths.map(p => path.join(ASSETS, p));
    const cwd = process.cwd();

    // TODO: use build contexts
    const result = await esbuild.build({
        entryPoints,
        outdir: '.',  // `outdir` is required even when `write: false`
        outbase: ASSETS,
        write: false,
        metafile: true,
        bundle: true,
        minify: true,
        target: 'es5',
        banner: {
            js: '"use strict";',
        },
        ...options,
    });

    if (result.warnings.length !== 0) {
        for (const warning of result.warnings) {
            console.warn(warning);
        }

        throw new Error('Unexpected warnings');
    }

    console.log(await esbuild.analyzeMetafile(result.metafile, {verbose: true}));

    const entries = [];
    const writes = [];

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
        const {assetId} = outputsByAbsPath.get(outputFile.path);
        const bundleContents = outputFile.contents;

        const shortDigest = getShortDigest(
            crypto.createHash('sha512')
                .update(bundleContents)
                .digest()
        );

        const outputPath = addFilenameSuffix(assetId, shortDigest);

        entries.push([assetId, outputPath]);
        writes.push([outputPath, bundleContents]);
    }

    return {
        entries,
        work: touch.then(() =>
            Promise.all(
                writes.map(([outputPath, bundleContents]) =>
                    fs.promises.writeFile(path.join(BUILD, outputPath), bundleContents)
                )
            )
        ),
    };
};

const main = async () => {
    const manifestPath = path.join(BUILD, 'rev-manifest.json');

    const touch = Promise.all([
        fs.promises.mkdir(path.join(BUILD, 'css'), {recursive: true}),
        fs.promises.mkdir(path.join(BUILD, 'fonts'), {recursive: true}),
        fs.promises.mkdir(path.join(BUILD, 'img', 'help'), {recursive: true}),
        fs.promises.mkdir(path.join(BUILD, 'js', 'ruffle'), {recursive: true}),
    ]);

    const copyImages = copyStaticFiles('img', touch);

    const PRIVATE_FIELDS_ESM = {
        format: 'esm',
        target: [
            'chrome84',
            'firefox90',
            'ios15',
            'safari15',
        ],
        banner: {},
    };

    const tasks = await Promise.all([
        sasscFile('scss/site.scss', 'css/site.css', touch, copyImages),
        sasscFile('scss/help.scss', 'css/help.css', touch, copyImages),
        sasscFile('scss/imageselect.scss', 'css/imageselect.css', touch, copyImages),
        sasscFile('scss/mod.scss', 'css/mod.css', touch, copyImages),
        sasscFile('scss/signup.scss', 'css/signup.css', touch, copyImages),
        esbuildFiles(['js/scripts.js'], touch, {}),
        esbuildFiles([
            'js/main.js',
            'js/message-list.js',
            'js/tags-edit.js',
            'js/signup.js',
        ], touch, PRIVATE_FIELDS_ESM),
        esbuildFiles(['js/flash.js'], touch, {
            format: 'esm',
            target: 'es6',
            banner: {},
        }),
        copyStaticFiles('img/help', touch),
        copyUnversionedStaticFile('opensearch.xml', touch),
        copyImages,

        // libraries
        copyStaticFile('js/jquery-2.2.4.min.js', touch),
        copyStaticFile('js/imageselect.js', touch),
        copyStaticFile('js/marked.js', touch),
        copyStaticFile('js/zxcvbn.js', touch),
        copyRuffleComponents(touch),
        copyStaticFile({
            from: packageSource('@ruffle-rs/ruffle/ruffle.js'),
            to: 'js/ruffle/ruffle.js',
        }, touch),

        // site
        copyStaticFile('js/notification-list.js', touch),
        copyStaticFile('js/search.js', touch),
        copyStaticFile('js/zxcvbn-check.js', touch),
    ]);

    await touch;
    await fs.promises.writeFile(
        manifestPath,
        JSON.stringify(
            Object.fromEntries(
                tasks.flatMap(task => task.entries))),
    );
    await Promise.all(tasks.map(task => task.work));
};

if (module === require.main) {
    main()
        .catch(error => {
            if (error.code === 1 && error.hasStderr) {
                process.exitCode = 1;
                return;
            }

            throw error;
        })
        .catch(terminate);
}
