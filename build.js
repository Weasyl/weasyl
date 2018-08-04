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

const deleteFile = filePath =>
    new Promise((resolve, reject) => {
        fs.unlink(filePath, error => {
            if (error) {
                reject(error);
                return;
            }

            resolve();
        });
    });

const readAndDeleteFile = (filePath, options) =>
    new Promise((resolve, reject) => {
        fs.readFile(filePath, options, (error, data) => {
            if (error) {
                reject(error);
                return;
            }

            resolve(data);

            fs.unlink(filePath, error => {
                if (error) {
                    throw error;
                }
            });
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

const sassc = (inputPath, outputPath, generateMap) =>
    new Promise((resolve, reject) => {
        const args = ['--style=compressed'];

        if (generateMap) {
            args.push('--sourcemap', '--omit-map-comment');
        }

        args.push('--', inputPath, outputPath);

        const sassProcess = child_process.spawn(
            'sassc', args,
            {stdio: ['ignore', 'inherit', 'inherit']}
        );

        const errorListener = error => {
            sassProcess.removeListener('exit', exitListener);
            reject(error);
        };

        const exitListener = (code, signal) => {
            sassProcess.removeListener('error', errorListener);

            if (code !== 0) {
                const message = 'Process exited with ' + (
                    code === undefined ?
                        'signal ' + signal :
                        'code ' + code
                );

                reject(new Error(message));
                return;
            }

            resolve();
        };

        sassProcess.once('error', errorListener);
        sassProcess.once('exit', exitListener);
    });

const main = enableSourceMaps => {
    const inputPath = path.join(ASSETS, 'scss/site.scss');
    const temporaryPath = path.join(BUILD, 'css/site.css.tmp');
    const manifestPath = path.join(BUILD, 'rev-manifest.json');

    return touchDir(path.join(BUILD, 'css'))
        .catch(() =>
            touchDir(BUILD).then(() =>
                touchDir(path.join(BUILD, 'css'))))
        .then(() =>
            sassc(inputPath, temporaryPath, enableSourceMaps))
        .then(() =>
            Promise.all([
                readAndDeleteFile(temporaryPath, 'utf8'),
                enableSourceMaps && readAndDeleteFile(temporaryPath + '.map', 'utf8'),
            ]))
        .then(([css, map]) =>
            postcss([autoprefixer(autoprefixerOptions)]).process(css, {
                from: temporaryPath,
                to: temporaryPath,
                map: map && {
                    inline: false,
                    prev: map,
                },
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

            const mapSuffix =
                enableSourceMaps ?
                    '-with-map' :
                    '';

            const outputPath = `css/site-${hash}${mapSuffix}.css`;
            const outputFullPath = path.join(BUILD, outputPath);

            let css = result.css;
            let mapWrite;

            if (enableSourceMaps) {
                css += `\n/*# sourceMappingURL=site-${hash}-with-map.css.map */`;

                const map = JSON.parse(String(result.map));
                map.sources = map.sources.map(sourcePath =>
                    'file:///' + path.join(BUILD, 'css', sourcePath).replace(/^\//, ''));
                map.file = undefined;

                mapWrite = writeFile(outputFullPath + '.map', JSON.stringify(map), 'utf8');
            } else {
                mapWrite = deleteFile(outputFullPath + '.map')
                    .catch(error => {
                        if (error.code !== 'ENOENT') {
                            throw error;
                        }
                    });
            }

            return Promise.all([
                writeFile(outputFullPath, css, 'utf8'),
                mapWrite,
                writeFile(manifestPath, JSON.stringify({
                    'css/site.css': outputPath,
                }), 'utf8'),
            ]);
        });
};

if (module === require.main) {
    const enableSourceMaps = process.argv.indexOf('--enable-source-maps', 2) !== -1;

    if (process.argv.length !== 2 + enableSourceMaps) {
        console.error('Usage: node build.js [--enable-source-maps]');
        process.exitCode = 1;
        return;
    }

    main(enableSourceMaps)
        .catch(terminate);
}
