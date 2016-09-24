'use strict';

const gulp = require('gulp');
const merge = require('merge-stream');

const autoprefixer = require('gulp-autoprefixer');
const rename = require('gulp-rename');
const rev = require('gulp-rev');
const sass = require('gulp-sass');
const webpack = require('webpack-stream');

function webpackNamed(scriptPath) {
    return gulp.src('assets/js/' + scriptPath)
        .pipe(webpack({
            output: {
                filename: scriptPath,
            },
        }))
        .pipe(rename({dirname: 'js/'}));
}

function scriptAssets() {
    return webpackNamed('main.js');
}

function stylesheetAssets() {
    return gulp.src('assets/scss/site.scss')
        .pipe(
            sass({outputStyle: 'compressed'})
                .on('error', sass.logError))
        .pipe(
            autoprefixer({
                browsers: ['last 2 versions', 'Android >= 4.4'],
            }))
        .pipe(rename({dirname: 'css/'}));
}

gulp.task('default', function () {
    return merge([scriptAssets(), stylesheetAssets()])
        .pipe(rev())
        .pipe(gulp.dest('build/'))
        .pipe(rev.manifest())
        .pipe(gulp.dest('build/'));
});
