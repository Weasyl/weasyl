'use strict';

const autoprefixer = require('autoprefixer');
const child_process = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const postcss = require('postcss');

const ASSETS = path.join(__dirname, 'assets');
const BUILD = path.join(__dirname, 'build');

const autoprefixerOptions = {
    env: [
        'last 2 versions',
        'Android >= 4.4',
    ],
};

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

const addFilenameSuffix = (relativePath, suffix) => {
    const pathInfo = path.parse(relativePath);

    return path.format({
        dir: pathInfo.dir,
        name: pathInfo.name + '-' + suffix,
        ext: pathInfo.ext,
    });
};

const copyStaticFile = (relativePath, touch) => {
    const inputPath = path.join(ASSETS, relativePath);
    const stream = fs.createReadStream(inputPath);
    const hash = crypto.createHash('sha512');

    stream.pipe(hash);

    return new Promise((resolve, reject) => {
        stream.once('error', reject);

        hash.once('readable', () => {
            const shortDigest = getShortDigest(hash.read());
            const outputPath = addFilenameSuffix(relativePath, shortDigest);
            const outputFullPath = path.join(BUILD, outputPath);

            resolve({
                entries: [[relativePath, outputPath]],
                work: touch.then(() =>
                    fs.promises.copyFile(inputPath, outputFullPath)),
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

const sasscFile = async (relativeInputPath, relativeOutputPath, touch, copyImages) => {
    const inputPath = path.join(ASSETS, relativeInputPath);

    const css = await sassc(inputPath);

    const result = postcss([autoprefixer(autoprefixerOptions)]).process(css, {
        from: undefined,
        map: false,
    });

    result.warnings().forEach(warning => {
        console.error(String(warning));
    });

    // ew
    const images = new Map(
        (await copyImages).entries
            .map(([k, v]) => [new URL('http://localhost/' + k).href, v])
    );

    const urlTranslatedCss = result.css.replace(/(url\()([^)]*)\)/gi, (match, left, link) => {
        if (/^["']./.test(link) && link.slice(-1) === link.charAt(0)) {
            link = link.slice(1, -1);
        }

        const expandedLink = new URL(link, 'http://localhost/' + relativeInputPath).href;

        if (!images.has(expandedLink)) {
            throw new Error(`Unresolvable url() in ${relativeInputPath}: ${link}`);
        }

        return left + '/' + images.get(expandedLink) + ')';
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

const main = async () => {
    const manifestPath = path.join(BUILD, 'rev-manifest.json');

    const touch = Promise.all([
        fs.promises.mkdir(path.join(BUILD, 'css'), {recursive: true}),
        fs.promises.mkdir(path.join(BUILD, 'fonts'), {recursive: true}),
        fs.promises.mkdir(path.join(BUILD, 'img', 'help'), {recursive: true}),
        fs.promises.mkdir(path.join(BUILD, 'js'), {recursive: true}),
    ]);

    const copyImages = copyStaticFiles('img', touch);

    const tasks = await Promise.all([
        sasscFile('scss/site.scss', 'css/site.css', touch, copyImages),
        copyStaticFiles('img/help', touch),
        copyImages,
        copyStaticFiles('js', touch),
    ]);

    await touch;
    await fs.promises.writeFile(
        manifestPath,
        JSON.stringify(
            Object.fromEntries(
                [
                    ...tasks.flatMap(task => task.entries),
                    ['fonts/museo500.css', 'fonts/museo500.css'],
                ])),
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
