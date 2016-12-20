'use strict';

var gulp = require('gulp');
var autoprefixer = require('gulp-autoprefixer');
var rename = require('gulp-rename');
var rev = require('gulp-rev');
var sass = require('gulp-sass');

gulp.task('sass', function () {
    return gulp.src('assets/scss/site.scss')
        .pipe(
            sass({outputStyle: 'compressed'})
                .on('error', sass.logError))
        .pipe(
            autoprefixer({
                browsers: ['last 2 versions', 'Android >= 4.4'],
            }))
        .pipe(rev())
        .pipe(rename({dirname: 'css/'}))
        .pipe(gulp.dest('build/'))
        .pipe(rev.manifest())
        .pipe(gulp.dest('build/'));
});

gulp.task('sass:watch', function () {
    gulp.watch('assets/scss/**/*.scss', ['sass']);
});
