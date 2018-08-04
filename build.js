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

const touchDir = dirPath =>
    new Promise((resolve, reject) => {
        fs.mkdir(dirPath, error => {
            if (error && error.code !== 'EEXIST') {
                reject(error);
                return;
            }

            resolve();
        });
    });

const writeFile = (filePath, content, options) =>
    new Promise((resolve, reject) => {
        fs.writeFile(filePath, content, options, error => {
            if (error) {
                reject(error);
                return;
            }

            resolve();
        });
    });

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

const main = () => {
    const inputPath = path.join(ASSETS, 'scss/site.scss');
    const manifestPath = path.join(BUILD, 'rev-manifest.json');

    const touch =
        touchDir(path.join(BUILD, 'css'))
            .catch(() =>
                touchDir(BUILD).then(() =>
                    touchDir(path.join(BUILD, 'css'))));

    return sassc(inputPath)
        .then(css =>
            postcss([autoprefixer(autoprefixerOptions)]).process(css, {
                from: undefined,
                map: false,
            }))
        .then(result => {
            result.warnings().forEach(warning => {
                console.error(String(warning));
            });

            const hash =
                crypto.createHash('sha512')
                    .update(result.css, 'utf8')
                    .digest('hex')
                    .substring(0, 10);

            const outputPath = `css/site-${hash}.css`;
            const outputFullPath = path.join(BUILD, outputPath);

            return touch.then(() =>
                Promise.all([
                    writeFile(outputFullPath, result.css, 'utf8'),
                    writeFile(manifestPath, JSON.stringify({
                        'css/site.css': outputPath,
                    }), 'utf8'),
                ])
            );
        });
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
