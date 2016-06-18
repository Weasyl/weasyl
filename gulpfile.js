'use strict';

var gulp = require('gulp');
var autoprefixer = require('gulp-autoprefixer');
var rename = require('gulp-rename');
var rev = require('gulp-rev');
var sass = require('gulp-ruby-sass');

gulp.task('sass', function () {
    return sass('assets/scss/site.scss', {style: 'compressed'})
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
