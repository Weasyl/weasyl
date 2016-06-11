'use strict';

var gulp = require('gulp');
var rename = require('gulp-rename');
var rev = require('gulp-rev');
var sass = require('gulp-sass');

gulp.task('sass', function () {
    return gulp.src('assets/scss/site.scss')
        .pipe(
            sass({outputStyle: 'compressed'})
                .on('error', sass.logError))
        .pipe(rev())
        .pipe(rename({dirname: 'css/'}))
        .pipe(gulp.dest('build/'))
        .pipe(rev.manifest())
        .pipe(gulp.dest('build/'));
});
