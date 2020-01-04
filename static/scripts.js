/* global marked, Bloodhound, socialSiteList */

(function () {
    'use strict';

    var monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June', 'July',
        'August', 'September', 'October', 'November', 'December', 'Smarch'
    ];

    var csrfToken = document.documentElement.getAttribute('data-csrf-token');

    function forEach(list, callback) {
        for (var i = 0, l = list.length; i < l; i++) {
            callback(list[i]);
        }
    }

    function some(list, predicate) {
        for (var i = 0, l = list.length; i < l; i++) {
            if (predicate(list[i])) {
                return true;
            }
        }

        return false;
    }

    function EventStream() {
        this.listeners = [];
    }

    EventStream.prototype.emit = function emit(data) {
        forEach(this.listeners, function (listener) {
            listener(data);
        });
    };

    EventStream.prototype.listen = function listen(listener) {
        this.listeners.push(listener);
    };

    // thumbnails: config
    var thumbnailContainers = document.getElementsByClassName('thumbnail-grid'),
        thumbnailOptions = {
            minWidth: 125,  // minimum width per cell (should match min thumbnail width)
            maxWidth: 500,  // thumbnails over this width will be cropped
            rowBasis: 250,  // row height basis (should match max thumbnail height)
            itemGap: 8,     // common item padding
            breakpoint: '(max-width: 29.9em)'
        };

    // thumbnails: thumbnail data-width attribute helper
    function getWidthAttr(item) {
        return Math.max(parseInt(item.getAttribute('data-width')), thumbnailOptions.minWidth) || thumbnailOptions.rowBasis;
    }

    // thumbnails: calculate layout
    var thumbnailLayoutCalculated = new EventStream();

    function calculateThumbnailLayout() {
        forEach(thumbnailContainers, function (container) {
            if (container.offsetWidth === 0 || container.offsetHeight === 0) {
                return;
            }
            var items = Array.prototype.slice.call(container.getElementsByClassName('thumb-bounds'), 0),
                containerWidth = container.clientWidth,
                startHeight = Math.min(Math.floor(containerWidth / 1.65), thumbnailOptions.rowBasis),
                thumbRatio = startHeight / thumbnailOptions.rowBasis,
                maxRows = -1, rowCount = -1;

            if (container.classList.contains('tiny-footprint')) {
                maxRows = 1;
            } else if (container.classList.contains('small-footprint')) {
                if (window.matchMedia(thumbnailOptions.breakpoint).matches) {
                    maxRows = 2;
                } else {
                    maxRows = 1;
                }
            } else if (container.classList.contains('medium-footprint')) {
                if (window.matchMedia(thumbnailOptions.breakpoint).matches) {
                    maxRows = 4;
                } else {
                    maxRows = 2;
                }
            } else if (container.classList.contains('large-footprint')) {
                if (window.matchMedia(thumbnailOptions.breakpoint).matches) {
                    maxRows = 6;
                } else {
                    maxRows = 3;
                }
            }

            // reset on resize
            forEach(items, function (item) {
                item.style.width = '';
                item.style.height = '';
                item.parentNode.parentNode.style.display = '';
            });

            while (items.length > 0) {
                rowCount++;
                if (rowCount === maxRows) {
                    break;
                }

                var row = [],
                    rowWidth = 0,
                    difference = 1;

                // construct a row
                while (rowWidth < containerWidth) {
                    var item = items.shift();
                    if (!item) {
                        break;
                    }
                    rowWidth += getWidthAttr(item) * thumbRatio + thumbnailOptions.itemGap;
                    row.push(item);
                }

                // fit row
                if (rowWidth > containerWidth) {
                    difference = containerWidth / rowWidth;
                }
                forEach(row, function (item) {
                    var width = getWidthAttr(item) * thumbRatio * difference - thumbnailOptions.itemGap;
                    var height = startHeight * difference - thumbnailOptions.itemGap;

                    item.style.width = width + 'px';
                    item.style.height = height + 'px';

                    thumbnailLayoutCalculated.emit({
                        item: item,
                        width: width,
                        height: height
                    });
                });
            }

            // if any items did not get placed, hide them
            forEach(items, function (item) {
                item.parentNode.parentNode.style.display = 'none';

                thumbnailLayoutCalculated.emit({
                    item: item,
                    width: null,
                    height: null
                });
            });
        });
    }


    $(document).ready(function () {
        // thumbnails
        // give enhanced layout to modern browsers
        if ('classList' in document.createElement('_') && typeof window.matchMedia === 'function') {
            document.documentElement.classList.add('enhanced-thumbnails');
            if (thumbnailContainers.length > 0) {
                calculateThumbnailLayout();
                window.addEventListener('resize', calculateThumbnailLayout);
            }
        }

        // call appropriate functions and plugins
        $('textarea.expanding').autosize();

        $('.tags-textarea')
            .listbuilder({ width: '100%' })
            .addClass('proxy');

        // mobile nav
        $('#nav-toggle').on('click', function (ev) {
            ev.preventDefault();
            $('#header-nav, #nav-toggle').toggleClass('open');
        });

        // tags
        $('.di-tags .modify').on('click', function (ev) {
            ev.preventDefault();
            $(this).closest('.di-tags').find('.tags-form, .tags').toggleClass('open');
            $('.listbuilder-entry-add input').focus();
        });

        // report
        $('#detail-report-button').on('click', function (ev) {
            ev.preventDefault();
            $(this).addClass('active');
            $('#detail-report').slideDown(250);
        });

        $('#report-cancel').on('click', function (ev) {
            ev.preventDefault();
            $('#detail-report-button').removeClass('active');
            $('#detail-report').slideUp(250);
        });

        $('#detail_report_violation').on('change', function () {
            var reminder = document.getElementById('detail_report_reminder');
            var comment = document.getElementById('detail_report_content');
            var required = this.options[this.selectedIndex].getAttribute('data-comment-required').toLowerCase() === 'true';

            comment.required = required;
            reminder.style.visibility = required ? 'visible' : 'hidden';
        });

        // modal login
        $('#hg-login').on('click', function (ev) {
            ev.preventDefault();

            $('body').addClass('modal-login');

            $('#login-box-container').empty().append(
                $('<div>', { id: 'login-box', class: 'content' }).append(
                    $('<img>', { id: 'modal-loader', src: '/static/images/loader.gif', alt: '' })
                )
            ).load('/signin #login-box', function () {
                $('#login-user').focus();

                $('#lb-close').on('click', function (ev) {
                    ev.preventDefault();
                    $('body').removeClass('modal-login');
                });

                $(document).keyup(function (e) {
                    if (e.keyCode === 27) {
                        $('body').removeClass('modal-login');
                    }
                });
            });
        });

        // submission notifs buttons
        $('.selection-toggle').on('click', function (ev) {
            ev.preventDefault();
            $(this).closest('form').find('input[type=checkbox]').each(function () {
                this.checked = !this.checked;
            }).change();
        });
        $('.do-check').on('click', function (ev) {
            ev.preventDefault();
            $(this).closest('form').find('input[type=checkbox]').prop('checked', true).change();
        });
        $('.do-uncheck').on('click', function (ev) {
            ev.preventDefault();
            $(this).closest('form').find('input[type=checkbox]').prop('checked', false).change();
        });

        // Marketplace result "Show More" button
        $('.marketplace-desc-fade button').on('click', function (ev) {
            var fadebox = $(this).parent();
            fadebox.parent().removeClass('marketplace-desc-preview');
            fadebox.remove();
        });

        // Commishinfo prices "autopopulate" dropdown
        $('#commish-edit-select').on('change', function () {
            var selectedID = $(this).val();
            console.log(selectedID);
            forEach(document.getElementsByClassName('select-priceid'), function (field) {
                var myID = field.getAttribute('data-priceid');
                var visible = selectedID == myID;
                field.style.display = visible ? '' : 'none';
            });
        });

        // checkbox containers
        $('.input-checkbox input[type=checkbox]').each(function () {
            var that = this;
            var $this = $(this);
            var container = $this.closest('.input-checkbox');

            function updateChecked() {
                container.toggleClass('checked', that.checked);
            }

            $this.change(updateChecked);
            updateChecked();
        });

        // styled file inputs
        $('.styled-input').each(function () {
            var nativeInput = $(this).on({
                mouseover: function () {
                    container.addClass('hover');
                },
                mouseout: function () {
                    container.removeClass('hover');
                },
                focus: function () {
                    container.addClass('focus');
                    nativeInput.data('val', nativeInput.val());
                },
                blur: function () {
                    container.removeClass('focus');
                    $(this).trigger('checkChange');
                },
                checkChange: function () {
                    if (nativeInput.val() && nativeInput.val() !== nativeInput.data('val')) {
                        nativeInput.trigger('change');
                    }
                },
                change: function () {
                    var fileName = this.value.split('\\').pop();
                    var fileExt = 'ext-' + fileName.split('.').pop().toLowerCase();
                    uploadFeedback
                        .removeClass(uploadFeedback.data('fileExt') || '')
                        .addClass(fileExt)
                        .data('fileExt', fileExt)
                        .addClass('populated')
                        .find('.text').text(fileName);
                    uploadButton.text('Change');
                },
                click: function () {
                    nativeInput.data('val', nativeInput.val());
                    setTimeout(function () {
                        nativeInput.trigger('checkChange');
                    }, 100);
                }
            });

            var container =
                $('<div>', { class: 'file-input-wrapper stage clear' });
            var innerContainer =
                $('<div>', { class: 'fake-input clear', 'aria-hidden': true });
            var uploadButton =
                $('<span>', { class: 'button', text: 'Choose' });
            var uploadFeedback =
                $('<span>', { class: 'feedback', 'aria-hidden': true }).append(
                    $('<span>', { class: 'icon icon-20 icon-file' }),
                    ' ',
                    $('<span>', { class: 'text' }).append(
                        $('<i>', { text: 'No file selected' })
                    )
                );

            nativeInput
                .wrap(container)
                .after(innerContainer.append(uploadButton, uploadFeedback));
        });

        var staffNoteArea = $('#note-compose-staff-note #staff-note-area').hide();

        $('#note-compose-staff-note #mod-copy').change(function () {
            staffNoteArea.slideToggle(400);
        });

        if (window.socialSiteList) {
            // social media autocomplete
            var socialMedia = new Bloodhound({
                datumTokenizer: Bloodhound.tokenizers.obj.whitespace('val'),
                queryTokenizer: Bloodhound.tokenizers.whitespace,
                local: socialSiteList,
            });

            socialMedia.initialize();

            var typeaheadOptions = {
                hint: true,
                highlight: true,
                minlength: 1,
            };
            var typeaheadDataset = {
                name: 'social-media',
                displayKey: 'val',
                source: socialMedia.ttAdapter(),
            };
            $('.social input.site-name').typeahead(typeaheadOptions, typeaheadDataset);

            var addContactButton = $('#add-contact-button');
            addContactButton.click(function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                var group = $('<div>', { class: 'group' });
                var siteField = $('<input>', {
                    type: 'text',
                    class: 'input site-name',
                    placeholder: 'Site',
                    name: 'site_names',
                });
                group.append(siteField);
                group.append(
                    $('<input>', {
                        type: 'text',
                        class: 'input',
                        placeholder: 'Username or URL',
                        name: 'site_values',
                    }));
                addContactButton.parent().before(group);
                siteField.typeahead(typeaheadOptions, typeaheadDataset);
            });
        }
    });

    $('#detail-flash a').click(function (ev) {
        var $parent = $(this).parent();
        var flashURL = $parent.data('flash-url');
        var flashWidth = parseFloat($parent.data('flash-width'));
        var flashHeight = parseFloat($parent.data('flash-height'));
        $parent.css({
            'max-width': flashWidth + 'px',
            'max-height': flashHeight + 'px',
            margin: '0 auto',
        });
        var container = $('<div>', {id: 'flash-container'}).css({
            padding: (flashHeight / flashWidth * 100).toFixed(1) + '% 0 0',
        });
        var obj = $('<object>');
        $('<param>', {
            name: 'allowScriptAccess',
            value: 'never',
        }).appendTo(obj);
        $('<param>', {
            name: 'allowNetworking',
            value: 'none',
        }).appendTo(obj);
        $('<param>', {
            name: 'src',
            value: flashURL,
        }).appendTo(obj);
        $('<embed>', {
            type: 'application/x-shockwave-flash',
            src: flashURL,
            allowScriptAccess: 'never',
            allowNetworking: 'none',
        }).appendTo(obj);
        $parent
            .empty()
            .append(container.append(obj));
        ev.preventDefault();
    });

    var reportButtons = $('#report_buttons .enableable');
    var reportClosureWarning = $('#report-closure-warning');
    var noteTitle = $('#note-title');
    var noteTitleBox = $('#note-title-box');
    var closureExplanation = $('#closure-explanation');
    var closureExplanationBox = $('#closure-explanation-box');
    var userNote = $('#user-note');
    var userNoteBox = $('#user-note-box');

    // This is required because expanding textareas don't work right if they
    // start out hidden. So, only hide them after they've been autosized.
    $(document).ready(function () {
        closureExplanationBox.hide();
        userNoteBox.hide();
    });

    function reportInputChanged() {
        var action = reportClosureAction.val();
        if (action === 'action_taken') {
            noteTitleBox.show();
            closureExplanationBox.show();
            userNoteBox.show();
            reportButtons.prop(
                'disabled',
                !noteTitle.val() || !closureExplanation.val() || !userNote.val());
            reportClosureWarning.text(
                'The user note will be sent to the reported user with the ' +
                    'note title given. The report closure explanation will ' +
                    'also be saved to the reported user\'s staff notes, and ' +
                    'will not be visible to non-moderators.');
        } else if (action === 'no_action_taken') {
            noteTitleBox.hide();
            closureExplanationBox.show();
            userNoteBox.hide();
            reportButtons.prop('disabled', !closureExplanation.val());
            reportClosureWarning.text(
                'The report closure explanation entered will be visible to ' +
                    'all users who reported this content.');
        } else if (action === 'invalid') {
            noteTitleBox.hide();
            closureExplanationBox.hide();
            userNoteBox.hide();
            reportButtons.prop('disabled', false);
            reportClosureWarning.empty();
        } else {
            noteTitleBox.hide();
            closureExplanationBox.hide();
            userNoteBox.hide();
            reportButtons.prop('disabled', true);
            reportClosureWarning.empty();
        }
    }

    var reportClosureAction = $('#report-closure-action').change(function () {
        setTimeout(reportInputChanged);
    });

    $('#closure-explanation, #user-note').keydown(function () {
        setTimeout(reportInputChanged);
    });

    // all below plugins are under MIT licenses

    // expanding textareas
    // Jack Moore - jacklmoore.com
    /* jshint ignore:start */
    (function(e){var t="hidden",n="border-box",r='<textarea tabindex="-1" style="position:absolute; top:-9999px; left:-9999px; right:auto; bottom:auto; -moz-box-sizing:content-box; -webkit-box-sizing:content-box; box-sizing:content-box; word-wrap:break-word; height:0 !important; min-height:0 !important; overflow:hidden">',i=["fontFamily","fontSize","fontWeight","fontStyle","letterSpacing","textTransform","wordSpacing","textIndent"],s="oninput",o="onpropertychange",u=e(r)[0];u.setAttribute(s,"return"),e.isFunction(u[s])||o in u?e.fn.autosize=function(u){return this.each(function(){function g(){var e,n;p||(p=!0,l.value=a.value,l.style.overflowY=a.style.overflowY,l.style.width=f.css("width"),l.scrollTop=0,l.scrollTop=9e4,e=l.scrollTop,n=t,e>h?(e=h,n="scroll"):e<c&&(e=c),a.style.overflowY=n,a.style.height=e+m+"px",setTimeout(function(){p=!1},1))}var a=this,f=e(a),l,c=f.height(),h=parseInt(f.css("maxHeight"),10),p,d=i.length,v,m=0;if(f.css("box-sizing")===n||f.css("-moz-box-sizing")===n||f.css("-webkit-box-sizing")===n)m=f.outerHeight()-f.height();if(f.data("mirror")||f.data("ismirror"))return;l=e(r).data("ismirror",!0).addClass(u||"autosizejs")[0],v=f.css("resize")==="none"?"none":"horizontal",f.data("mirror",e(l)).css({overflow:t,overflowY:t,wordWrap:"break-word",resize:v}),h=h&&h>0?h:9e4;while(d--)l.style[i[d]]=f.css(i[d]);e("body").append(l),o in a?s in a?a[s]=a.onkeyup=g:a[o]=g:a[s]=g,e(window).resize(g),f.on("autosize",g),g()})}:e.fn.autosize=function(){return this}})(jQuery);
    /* jshint ignore:end */

    // list builder made with help from Filament Group's book
    $.fn.listbuilder = function (settings) {
        var delimChar = ' ';
        var options = $.extend({
            completeChars: [188, 13, 32], // completion keycodes
            userDirections: 'To add an item to this list, type a name and press enter or comma.' // input tooltip
        }, settings);

        return this.each(function () {
            var textarea = this;

            // make container
            var listbuilder = $('<ul>', {
                class: 'listbuilder',
                width: options.width || $(textarea).width()
            });

            // make typeable component
            var input = $('<input>', {
                type: 'text',
                value: '',
                title: options.userDirections
            });

            // function to return a new listbuilder entry
            function listUnit(val) {
                return $('<li>', { class: 'listbuilder-entry', unselectable: 'on' }).append(
                    $('<span>', { class: 'listbuilder-entry-text', text: val }),
                    $('<a>', {
                        class: 'listbuilder-entry-remove',
                        href: '#',
                        role: 'button',
                        title: 'Remove ' + val + ' from the list.'
                    })
                );
            }

            // function to populate listbuilder from textarea
            function populateList() {
                listbuilder.empty();

                forEach(textarea.value.split(delimChar), function (value) {
                    if (value) {
                        listbuilder.append(listUnit(value));
                    }
                });

                // append typeable component
                listbuilder.append(
                    $('<li>', { class: 'listbuilder-entry-add' }).append(input));
            }

            // function to populate textarea from current listbuilder
            function updateValue() {
                var tags = listbuilder.find('.listbuilder-entry-text').map(function () {
                    return $(this).text();
                }).get();

                tags.push(input.val());

                textarea.value = tags.join(delimChar);
            }

            // populate initial listbuilderfrom textarea
            populateList();

            // add key behavior to input
            input.keydown(function (ev) {
                var parent = input.parent();

                // check if key was one of the completeChars, if so, create a new item and empty the field
                forEach(options.completeChars, function (completeChar) {
                    if (ev.keyCode === completeChar) {
                        forEach(input.val().split(delimChar), function (value) {
                            if (value) {
                                parent.before(listUnit(value));
                            }
                        });

                        input.val('');

                        ev.preventDefault();
                    }
                });

                var prevUnit = parent.prev();

                if (!input.val() && ev.keyCode === 8) {
                    ev.stopPropagation();

                    if (prevUnit.is('.listbuilder-entry-selected')) {
                        prevUnit.remove();
                    } else {
                        prevUnit.addClass('listbuilder-entry-selected');
                    }
                } else {
                    prevUnit.removeClass('listbuilder-entry-selected');
                }
            });

            input.on('input keyup', function () {
                var $this = $(this);

                updateValue();

                // approx width for input
                var testWidth =
                    $('<span>', {
                        text: $this.val(),
                        css: {
                            visibility: 'hidden',
                            position: 'absolute',
                            left: '-9999px',
                            fontSize: $this.css('font-size')
                        }
                    }).appendTo('body');

                $this.width(testWidth.width() + 20);

                testWidth.remove();
            });

            // apply delete key event at document level
            $(document)
                .click(function () {
                    listbuilder.find('.listbuilder-entry-selected').removeClass('listbuilder-entry-selected');
                    listbuilder.removeClass('listbuilder-focus');
                })
                .keydown(function (ev) {
                    if (ev.keyCode === 8) {
                        listbuilder.find('.listbuilder-entry-selected').remove();
                        updateValue();
                    }
                });

            // click events for delete buttons and focus
            listbuilder.on('click', '.listbuilder-entry-remove', function (e) {
                e.stopPropagation();
                e.preventDefault();

                $(this).parent().remove();
                updateValue();
            });

            listbuilder.on('click', '.listbuilder-entry', function (e) {
                e.stopPropagation();
                e.preventDefault();

                var $this = $(this);
                var toggleSelect = e.shiftKey || e.ctrlKey || e.metaKey;

                if (toggleSelect) {
                    $this.toggleClass('listbuilder-entry-selected');
                } else {
                    listbuilder
                        .find('.listbuilder-entry-selected')
                        .removeClass('listbuilder-entry-selected');

                    $this.addClass('listbuilder-entry-selected');
                }
            });

            listbuilder.click(function (e) {
                e.stopPropagation();

                listbuilder
                    .addClass('listbuilder-focus')
                    .find('.listbuilder-entry-selected').removeClass('listbuilder-entry-selected');

                input.focus();
            });

            // set focus/blur states from input state and focus on input
            input.focus(function () {
                listbuilder.addClass('listbuilder-focus');
            });

            input.blur(function () {
                listbuilder.removeClass('listbuilder-focus');
            });

            // insert listbuilder after textarea (and hide textarea)
            listbuilder.insertAfter(textarea);
        });
    };

    $(document).on('submit', 'form[data-confirm]', function (e) {
        if (confirm(this.getAttribute('data-confirm'))) {
            var field = document.createElement('input');
            field.type = 'hidden';
            field.name = 'confirmed';
            this.appendChild(field);
        } else {
            e.preventDefault();
        }
    });

    $(document).on('click', 'button[data-confirm]', function (e) {
        if (confirm(this.getAttribute('data-confirm'))) {
            var field = document.createElement('input');
            field.type = 'hidden';
            field.name = 'confirmed';
            this.parentNode.appendChild(field);
        } else {
            e.preventDefault();
        }
    });

    var defang = (function () {
        var allowedTags = [
            'section', 'nav', 'article', 'aside',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'header', 'footer', 'address',
            'p', 'hr', 'pre', 'blockquote', 'ol', 'ul', 'li',
            'dl', 'dt', 'dd', 'figure', 'figcaption', 'div',
            'em', 'strong', 'small', 's', 'cite', 'q', 'dfn',
            'abbr', 'time', 'code', 'var', 'samp', 'kbd',
            'sub', 'sup', 'i', 'b', 'u', 'mark',
            'ruby', 'rt', 'rp', 'bdi', 'bdo', 'span', 'br', 'wbr',
            'del',
            'table', 'caption',
            'tbody', 'thead', 'tfoot', 'tr', 'td', 'th',
            'a', 'img'
        ];

        var allowedAttributes = [
            'title', 'alt', 'colspan', 'rowspan', 'start', 'type'
        ];

        var allowedSchemes = [
            '', 'http', 'https', 'mailto', 'irc', 'magnet'
        ];

        var allowedClasses = [
            'align-left', 'align-center', 'align-right', 'align-justify',
            'user-icon'
        ];

        var ALLOWED_STYLE = /^\s*color:\s*(?:#[0-9a-f]{3}|#[0-9a-f]{6})(?:\s*;)?\s*$/i;

        function isAllowedClass(class_) {
            return allowedClasses.indexOf(class_) !== -1;
        }

        function defang(node) {
            var i;

            for (i = node.childNodes.length; i--;) {
                var child = node.childNodes[i];

                if (child.nodeType === 1) {
                    defang(child);
                }
            }

            if (allowedTags.indexOf(node.nodeName.toLowerCase()) === -1) {
                while (node.childNodes.length) {
                    node.parentNode.insertBefore(node.firstChild, node);
                }

                node.parentNode.removeChild(node);
            } else {
                for (i = node.attributes.length; i--;) {
                    var attribute = node.attributes[i];
                    var scheme = attribute.value && attribute.value.substring(0, attribute.value.indexOf(':'));

                    if (node.nodeName === 'A' && attribute.name === 'href' && allowedSchemes.indexOf(scheme) !== -1) {
                        node.rel = 'nofollow';
                        continue;
                    }

                    if (node.nodeName === 'IMG' && attribute.name === 'src' && allowedSchemes.indexOf(scheme) !== -1) {
                        continue;
                    }

                    if (attribute.name === 'style' && ALLOWED_STYLE.test(attribute.value)) {
                        continue;
                    }

                    if (attribute.name === 'class') {
                        var classes = attribute.value.split(/\s+/);

                        attribute.value = classes.filter && classes.filter(isAllowedClass).join(' ');

                        if (attribute.value) {
                            continue;
                        }
                    }

                    if (allowedAttributes.indexOf(attribute.name) !== -1) {
                        continue;
                    }

                    node.removeAttribute(attribute.name);
                }
            }
        }

        return defang;
    })();

    function loginName(username) {
        return username.replace(/[^a-z0-9]/gi, '');
    }

    var weasylMarkdown = (function () {
        var USER_LINK = /\\(.)|<(!~|[!~])(\w+)>|./gi;

        var NO_USER_LINKING = ['a', 'pre', 'code'];

        function addUserLinks(fragment) {
            for (var i = 0; i < fragment.childNodes.length; i++) {
                var child = fragment.childNodes[i];

                if (child.nodeType === 1) {
                    if (NO_USER_LINKING.indexOf(child.nodeName) === -1) {
                        addUserLinks(child);
                    }
                } else if (child.nodeType === 3) {
                    var m;
                    var text = '';
                    var altered = false;

                    while ((m = USER_LINK.exec(child.nodeValue))) {
                        if (m[1] !== undefined) {
                            text += m[1];
                            altered = true;
                            continue;
                        }

                        if (m[2] === undefined) {
                            text += m[0];
                            continue;
                        }

                        altered = true;

                        var link = document.createElement('a');
                        link.href = '/~' + loginName(m[3]);

                        if (m[2] === '~') {
                            link.textContent = m[3];
                        } else {
                            link.className = 'user-icon';

                            var image = document.createElement('img');
                            image.src = '/~' + loginName(m[3]) + '/avatar';
                            link.appendChild(image);

                            if (m[2] === '!') {
                                image.alt = m[3];
                            } else {
                                var usernameContainer = document.createTextNode('span');
                                usernameContainer.textContent = m[3];

                                link.appendChild(document.createTextNode(' '));
                                link.appendChild(usernameContainer);
                            }
                        }

                        fragment.insertBefore(document.createTextNode(text), child);
                        fragment.insertBefore(link, child);
                        text = '';
                    }

                    if (altered) {
                        fragment.insertBefore(document.createTextNode(text), child);
                        i = Array.prototype.indexOf.call(fragment.childNodes, child) - 1;
                        fragment.removeChild(child);
                    }
                }
            }
        }

        function weasylMarkdown(fragment) {
            var links = fragment.getElementsByTagName('a');

            forEach(links, function (link) {
                var href = link.getAttribute('href');
                var i = href.indexOf(':');
                var scheme = href.substring(0, i);
                var user = href.substring(i + 1);

                switch (scheme) {
                    case 'user':
                        link.href = '/~' + user;
                        break;

                    case 'da':
                        link.href = 'https://www.deviantart.com/' + user;
                        break;

                    case 'sf':
                        link.href = 'https://' + user + '.sofurry.com/';
                        break;

                    case 'ib':
                        link.href = 'https://inkbunny.net/' + user;
                        break;

                    case 'fa':
                        link.href = 'https://www.furaffinity.net/user/' + user;
                        break;

                    default:
                        return;
                }

                if (!link.textContent || link.textContent === href) {
                    link.textContent = user;
                }
            });

            var images = fragment.querySelectorAll('img');

            forEach(images, function (image) {
                var src = image.getAttribute('src');
                var i = src.indexOf(':');
                var scheme = src.substring(0, i);
                var link = document.createElement('a');

                if (scheme === 'user') {
                    var user = src.substring(i + 1);
                    image.className = 'user-icon';
                    image.src = '/~' + user + '/avatar';

                    link.href = '/~' + user;

                    image.parentNode.replaceChild(link, image);
                    link.appendChild(image);

                    if (image.alt) {
                        link.appendChild(document.createTextNode(' ' + image.alt));
                        image.alt = '';
                    } else {
                        image.alt = user;
                    }

                    if (image.title) {
                        link.title = image.title;
                        image.title = '';
                    }
                } else {
                    link.href = image.src;
                    link.appendChild(document.createTextNode(image.alt || image.src));

                    image.parentNode.replaceChild(link, image);
                }
            });

            addUserLinks(fragment);
        }

        return weasylMarkdown;
    })();

    var markdownOptions = {
        breaks: true,
        smartLists: true,
        noIndentedCode: true
    };

    var ATTEMPTED_BBCODE = /\[(\w+)\][\s\S]+\[\/\1\]/i;

    function renderMarkdown(content, container) {
        var markdown = marked(content, markdownOptions);
        var fragment = document.createElement('div');
        fragment.innerHTML = markdown;

        weasylMarkdown(fragment);
        defang(fragment);

        while (fragment.childNodes.length) {
            container.appendChild(fragment.firstChild);
        }
    }

    function addMarkdownPreview(input) {
        var preview = document.createElement('div');
        preview.className = 'markdown-preview formatted-content';

        function showPreview() {
            while (preview.childNodes.length) {
                preview.removeChild(preview.firstChild);
            }

            renderMarkdown(input.value, preview);
        }

        input.addEventListener('input', showPreview, false);

        showPreview();
        input.parentNode.insertBefore(preview, input.nextSibling);
    }

    function addMarkdownWarning(input) {
        var helpLink = document.createElement('a');
        helpLink.href = '/help/markdown';
        helpLink.target = '_blank';
        helpLink.appendChild(document.createTextNode('Read about Markdown!'));

        var warning = document.createElement('div');
        warning.className = 'bbcode-warning';
        warning.appendChild(document.createTextNode('Trying to use BBCode? '));
        warning.appendChild(helpLink);

        function showWarning() {
            warning.style.display = ATTEMPTED_BBCODE.test(input.value) ? 'block' : 'none';
        }

        input.addEventListener('input', showWarning, false);

        showWarning();
        input.parentNode.insertBefore(warning, input.nextSibling);
    }

    forEach(document.getElementsByClassName('markdown'), function (input) {
        addMarkdownPreview(input);
        addMarkdownWarning(input);
    });

    function getCommentInfo(commentActionLink) {
        var comment = commentActionLink;

        do {
            comment = comment.parentNode;
        } while (!comment.classList.contains('comment'));

        var comments = comment;

        do {
            comments = comments.parentNode;
        } while (!comments.classList.contains('comments'));

        return {
            comment: comment,
            comments: comments,
            id: parseInt(comment.dataset.id, 10),
            feature: comments.dataset.feature,
            removalPrivileges: comments.dataset.removalPrivileges
        };
    }

    function formatDate(date) {
        function pad(n) {
            return n < 10 ? '0' + n : '' + n;
        }

        var formattedDate = date.getUTCDate() + ' ' + monthNames[date.getUTCMonth()] + ' ' + date.getUTCFullYear();

        var formattedHour = pad(date.getUTCHours());
        var formattedMinute = pad(date.getUTCMinutes());
        var formattedSecond = pad(date.getUTCSeconds());
        var formattedTime = formattedHour + ':' + formattedMinute + ':' + formattedSecond + ' UTC';

        var timeElement = document.createElement('time');
        timeElement.dateTime = date.toISOString();

        var emphAt = document.createElement('i');
        emphAt.textContent = 'at';

        var datePart = document.createElement('b');
        datePart.textContent = formattedDate;

        timeElement.appendChild(datePart);
        timeElement.appendChild(document.createTextNode(' '));
        timeElement.appendChild(emphAt);
        timeElement.appendChild(document.createTextNode(' ' + formattedTime));

        return timeElement;
    }

    document.addEventListener('click', function (e) {
        var target = e.target;
        var commentInfo;
        var comment;
        var children;

        if (target.classList.contains('comment-hide-link')) {
            commentInfo = getCommentInfo(target);
            comment = commentInfo.comment;
            children = comment.nextElementSibling;

            if (children && children.nodeName !== 'UL') {
                children = null;
            }

            if (confirm('Hide this comment and any replies?')) {
                var rq = new XMLHttpRequest();

                rq.open('POST', '/remove/comment', true);
                rq.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

                rq.onreadystatechange = function () {
                    if (rq.readyState === 4) {
                        var result = null;

                        if (rq.status === 200) {
                            try {
                                result = JSON.parse(rq.responseText);
                            } catch (ex) {}

                            if (result && result.success) {
                                if (children && children.nodeName === 'UL') {
                                    children.parentNode.removeChild(children);
                                }

                                if (comment.parentNode.children.length === 1) {
                                    if (comment.parentNode.parentNode.children.length === 1) {
                                        comment.parentNode.parentNode.parentNode.removeChild(comment.parentNode.parentNode);
                                    } else {
                                        comment.parentNode.parentNode.removeChild(comment.parentNode);
                                    }
                                } else {
                                    comment.parentNode.removeChild(comment);
                                }

                                return;
                            }
                        }

                        target.classList.add('error');
                        target.textContent = 'Failed to hide comment';

                        comment.classList.remove('removing');

                        if (children) {
                            forEach(children.getElementsByClassName('comment'), function (descendant) {
                                descendant.classList.remove('removing');
                            });
                        }
                    }
                };

                rq.send(
                    'format=json&feature=' + commentInfo.feature +
                    '&token=' + encodeURIComponent(csrfToken) +
                    '&commentid=' + commentInfo.id);

                comment.classList.add('removing');

                if (children) {
                    forEach(children.getElementsByClassName('comment'), function (descendant) {
                        descendant.classList.add('removing');
                    });
                }
            }

            e.preventDefault();
        } else if (target.classList.contains('comment-reply-link')) {
            commentInfo = getCommentInfo(target);
            comment = commentInfo.comment;
            children = comment.nextElementSibling;

            var newForm = commentInfo.comments.parentNode.getElementsByClassName('comment-form')[0].cloneNode(true);
            var newFormContent = newForm.getElementsByClassName('comment-content')[0];
            var newFormError = null;
            var targetIdField = newForm.getElementsByClassName('form-target-id')[0];
            var targetId = parseInt(targetIdField.value, 10);
            var contentField = newFormContent.getElementsByClassName('form-content')[0];

            // Remove the original form’s non-functional Markdown preview and warning elements
            contentField.parentNode.removeChild(contentField.nextElementSibling);
            contentField.parentNode.removeChild(contentField.nextElementSibling);

            if (!children || children.nodeName !== 'UL') {
                children = document.createElement('ul');
                comment.parentNode.insertBefore(children, comment.nextElementSibling);
            }

            var newListItem = document.createElement('li');

            newListItem.appendChild(newForm);
            children.insertBefore(newListItem, children.firstChild);

            var cancelReply = function cancelReply(e) {
                e.preventDefault();
                e.stopPropagation();

                target.textContent = 'Reply';
                target.removeEventListener('click', cancelReply, false);

                if (children.childNodes.length === 1) {
                    children.parentNode.removeChild(children);
                } else {
                    children.removeChild(newListItem);
                }

                target.focus();
            };

            var handleShortcuts = function handleShortcuts(e) {
                if (e.keyCode === 27 && !contentField.value) {
                    contentField.removeEventListener('keydown', handleShortcuts, false);
                    cancelReply(e);
                } else if (e.keyCode === 13 && e.ctrlKey) {
                    e.preventDefault();
                    submitComment();
                }
            };

            var submitComment = function submitComment() {
                if (newForm.checkValidity()) {
                    var posterUsername = document.getElementById('username').textContent;

                    var newComment = document.createElement('div');
                    newComment.className = 'comment';

                    var commentAvatar = document.createElement('a');
                    commentAvatar.className = 'avatar';
                    commentAvatar.href = '/~' + loginName(posterUsername);

                    var commentAvatarImage = document.createElement('img');
                    commentAvatarImage.alt = 'Your avatar';
                    commentAvatarImage.src = document.getElementById('avatar').src;

                    commentAvatar.appendChild(commentAvatarImage);

                    var commentContent = document.createElement('div');
                    commentContent.className = 'comment-content';

                    var commentActions = document.createElement('p');
                    commentActions.className = 'actions';

                    var replyLink = document.createElement('a');
                    replyLink.href = '#';
                    replyLink.className = 'comment-reply-link';
                    replyLink.textContent = 'Reply';

                    var hideLink = document.createElement('a');
                    hideLink.href = '#';
                    hideLink.className = 'comment-hide-link';
                    hideLink.textContent = 'Hide';

                    commentActions.appendChild(replyLink);
                    commentActions.appendChild(document.createTextNode(' '));
                    commentActions.appendChild(hideLink);

                    var commentByline = document.createElement('p');
                    commentByline.className = 'byline';

                    var commentUserLink = document.createElement('a');
                    commentUserLink.href = '/~' + loginName(posterUsername);
                    commentUserLink.className = 'username';
                    commentUserLink.textContent = posterUsername;

                    commentByline.appendChild(commentUserLink);

                    var userType = document.getElementById('header-user').dataset.userType;

                    if (userType) {
                        var typeBadge = document.createElement('strong');
                        typeBadge.className = 'user-type-' + userType;
                        typeBadge.textContent = '(' + userType + ')';

                        commentByline.appendChild(document.createTextNode(' '));
                        commentByline.appendChild(typeBadge);
                    }

                    // TODO: Update this on response. API. Again.
                    var posted = new Date();

                    var emphOn = document.createElement('i');
                    emphOn.textContent = 'on';

                    commentByline.appendChild(document.createTextNode(' '));
                    commentByline.appendChild(emphOn);
                    commentByline.appendChild(document.createTextNode(' '));
                    commentByline.appendChild(formatDate(posted));

                    var commentBody = document.createElement('div');
                    commentBody.className = 'formatted-content';
                    renderMarkdown(contentField.value, commentBody);

                    commentContent.appendChild(commentActions);
                    commentContent.appendChild(commentByline);
                    commentContent.appendChild(commentBody);

                    newComment.appendChild(commentAvatar);
                    newComment.appendChild(commentContent);
                    newComment.classList.add('submitting');

                    var rq = new XMLHttpRequest();

                    rq.open('POST', newForm.action, true);
                    rq.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

                    rq.onreadystatechange = function () {
                        if (rq.readyState === 4) {
                            var result = null;

                            if (rq.status === 200) {
                                try {
                                    result = JSON.parse(rq.responseText);
                                } catch (ex) {}

                                if (result && result.id) {
                                    newComment.dataset.id = result.id;
                                    newComment.id = 'cid' + result.id;
                                    newComment.classList.remove('submitting');
                                    newForm.parentNode.removeChild(newForm);

                                    if (commentInfo.removalPrivileges !== 'all') {
                                        var parentComment = newComment.parentNode.parentNode.previousElementSibling;
                                        var parentHideLink = parentComment && parentComment.getElementsByClassName('comment-hide-link')[0];

                                        if (parentHideLink) {
                                            parentHideLink.parentNode.removeChild(parentHideLink);
                                        }
                                    }

                                    var linkLink = document.createElement('a');
                                    linkLink.href = '#cid' + result.id;
                                    linkLink.textContent = 'Link';
                                    commentActions.appendChild(document.createTextNode(' '));
                                    commentActions.appendChild(linkLink);

                                    return;
                                }
                            }

                            newForm.style.display = 'block';
                            newComment.parentNode.removeChild(newComment);

                            if (!newFormError) {
                                newFormError = document.createElement('div');
                                newFormError.className = 'error';
                                newFormContent.insertBefore(newFormError, newFormContent.firstChild);
                            }

                            newFormError.textContent = result && result.error ? result.message : 'Sorry; an unexpected error occurred. Try refreshing.';
                        }
                    };

                    rq.send(
                        'format=json' +
                        '&token=' + encodeURIComponent(csrfToken) +
                        '&' + targetIdField.name + '=' + targetId +
                        '&parentid=' + commentInfo.id +
                        '&content=' + encodeURIComponent(contentField.value)
                    );

                    target.textContent = 'Reply';
                    target.removeEventListener('click', cancelReply, false);
                    contentField.removeEventListener('keydown', handleShortcuts, false);

                    newForm.style.display = 'none';
                    newForm.parentNode.insertBefore(newComment, newForm);

                    if (newFormError) {
                        newFormContent.removeChild(newFormError);
                        newFormError = null;
                    }
                }
            };

            target.textContent = 'Cancel (esc)';
            target.addEventListener('click', cancelReply, false);
            contentField.addEventListener('keydown', handleShortcuts, false);

            newForm.addEventListener('submit', function (e) {
                submitComment();
                e.preventDefault();
            }, false);

            e.preventDefault();

            addMarkdownPreview(contentField);
            addMarkdownWarning(contentField);

            $(contentField).autosize();
            contentField.focus();
        }
    }, false);

    function addLocationChangerForKeyCodeAndHref(keyCode, href) {
        document.addEventListener('keydown', function (e) {
            if (e.ctrlKey || e.shiftKey || e.altKey || e.metaKey ||
                    e.target.nodeName === 'INPUT' || e.target.nodeName === 'TEXTAREA') {
                return;
            }

            if (e.keyCode === keyCode) {
                document.location = href;
            }
        });
    }

    (function () {
        var folderNavPrev, folderNavNext;
        if ((folderNavPrev = document.getElementById('folder-nav-prev'))) {
            addLocationChangerForKeyCodeAndHref(37, folderNavPrev.href);
        }
        if ((folderNavNext = document.getElementById('folder-nav-next'))) {
            addLocationChangerForKeyCodeAndHref(39, folderNavNext.href);
        }

        if (!document.getElementsByClassName) {
            return;
        }

        var rootCommentForm = document.getElementsByClassName('comment-form')[0];

        if (!rootCommentForm) {
            return;
        }

        var rootCommentBox = document.getElementsByClassName('form-content')[0];

        // ctrl+enter comment submit
        rootCommentBox.addEventListener('keydown', function (e) {
            if (e.keyCode === 13 && e.ctrlKey) {
                e.preventDefault();
                rootCommentForm.submit();
            }
        }, false);

        // 'c' to focus comment box
        document.addEventListener('keydown', function (e) {
            if (e.keyCode === 67 && e.target === document.body &&
                !e.ctrlKey && !e.shiftKey && !e.altKey && !e.metaKey) {
                e.preventDefault();
                rootCommentBox.focus();
            }
        });

        // 'f' to favorite
        var faveForm = document.getElementById('submission-favorite-form');
        if (faveForm) {
            document.addEventListener('keydown', function (e) {
                if (e.keyCode === 70 && e.target === document.body &&
                    !e.ctrlKey && !e.shiftKey && !e.altKey && !e.metaKey) {
                    e.preventDefault();
                    faveForm.getElementsByTagName('button')[0].click();
                }
            });
        }

    })();

    function disableWithLabel(inputElement, disable) {
        inputElement.disabled = disable;
        inputElement.parentNode.classList.toggle('disabled', disable);
    }

    document.addEventListener('change', function (e) {
        var disableId = e.target.dataset.disables;

        if (disableId) {
            var disables = document.getElementById(disableId);
            var disable = e.target.checked;

            disableWithLabel(disables, disable);
        }
    });

    forEach(document.querySelectorAll('[data-disables]'), function (checkbox) {
        var disables = document.getElementById(checkbox.dataset.disables);

        disableWithLabel(disables, checkbox.checked);
    });

    (function () {
        function isOtherOption(option) {
            return option.hasAttribute('data-select-other');
        }

        forEach(document.getElementsByClassName('data-select-other'), function (field) {
            var select = document.getElementById(field.getAttribute('data-select'));

            function updateVisibility() {
                var visible = some(this.selectedOptions, isOtherOption);

                field.style.display = visible ? '' : 'none';
            }

            updateVisibility.call(select);
            select.addEventListener('change', updateVisibility, {passive: true});
        });
    })();

    // Ajax favorites
    (function () {
        var favoriteForm = document.getElementById('submission-favorite-form');

        if (!favoriteForm) {
            return;
        }

        var favoriteButton = favoriteForm.getElementsByTagName('button')[0];
        var favoriteActionBase = favoriteForm.getAttribute('data-action-base');
        var favoriteAction = favoriteForm.querySelector('input[name="action"]');

        favoriteForm.addEventListener('submit', function (e) {
            if (favoriteButton.classList.contains('pending')) {
                e.preventDefault();
                return;
            }

            var rq = new XMLHttpRequest();

            rq.open('POST', favoriteActionBase + favoriteAction.value, true);
            rq.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

            rq.onreadystatechange = function () {
                if (rq.readyState !== 4) {
                    return;
                }

                if (rq.status === 200) {
                    var success;

                    try {
                        success = JSON.parse(rq.responseText).success;
                    } catch (e) {}

                    if (success) {
                        favoriteButton.classList.remove('pending');

                        var newState = favoriteButton.classList.toggle('active');
                        favoriteButton.replaceChild(document.createTextNode(newState ? ' Favorited' : ' Favorite'), favoriteButton.lastChild);
                        favoriteAction.value = newState ? 'unfavorite' : 'favorite';

                        return;
                    }
                }

                // If there was any error, resubmit the form so the user can see it in full.
                favoriteForm.submit();
            };

            rq.send('token=' + encodeURIComponent(csrfToken));

            favoriteButton.classList.add('pending');

            e.preventDefault();
        }, false);
    })();

    // Home tabs
    (function () {
        function logStorageError(error) {
            try {
                console.warn(error);
            } catch (consoleError) {}
        }

        var homePaneLinks = $('.home-pane-link');
        var homePanes = $('#home-panes .pane');
        var homePaneGrids = homePanes.find('.thumbnail-grid');

        $('#home-art').on('click', '.home-pane-link', function (e) {
            e.preventDefault();

            var paneId = this.getAttribute('href').substring(1);

            homePaneLinks.removeClass('current');
            homePanes.removeClass('current');
            homePaneGrids.removeClass('current');

            // Select this tab or disclosure button and the corresponding
            // disclosure button or tab. This approach works for both the tabs
            // and disclosures. It relies on the fact that there are n tabs and
            // n corresponding disclosure buttons selected by .home-pane-link
            // in the same order.
            $(this).addClass('current');
            homePaneLinks
                .eq((homePaneLinks.index(this) + homePanes.length) % homePaneLinks.length)
                .addClass('current');

            $(document.getElementById(paneId)).addClass('current')
                .children('.thumbnail-grid').addClass('current loaded');

            calculateThumbnailLayout();

            try {
                localStorage['home-tab'] = paneId;
            } catch (error) {
                logStorageError(error);
            }
        });

        var savedTabId = null;

        try {
            savedTabId = localStorage['home-tab'];
        } catch (error) {
            logStorageError(error);
        }

        var savedTab = savedTabId && document.getElementById(savedTabId);

        if (savedTab) {
            savedTab.children[0].click();
        }
    })();

    // In-gallery audio playback
    (function () {
        var currentlyPlaying = null;
        var currentButton = null;

        function formatTime(totalSeconds) {
            var minutes = totalSeconds / 60 | 0;
            var seconds = totalSeconds % 60 | 0;

            return minutes + ':' + (seconds < 10 ? '0' + seconds : seconds);
        }

        forEach(document.getElementsByClassName('playable-media'), function (playableMedia) {
            // This returns a string, but it’s an empty string for “absolutely not playable”
            if (!playableMedia.canPlayType('audio/mpeg')) {
                return;
            }

            var playableContainer = playableMedia.parentNode;

            var playableOverlay = document.createElement('div');
            playableOverlay.className = 'playable-overlay';

            var playButton = document.createElement('button');
            playButton.type = 'button';
            playButton.className = 'playable-toggle';

            var timeIndicator = document.createElement('span');
            timeIndicator.className = 'playable-time';

            var timeText = document.createElement('span');
            timeText.className = 'playable-time-text';

            var timeCurrent = document.createElement('span');
            timeCurrent.className = 'playable-time-current';
            timeCurrent.textContent = '0:00';

            var timeTotal = document.createElement('span');
            timeTotal.className = 'playable-time-total';
            timeTotal.textContent = ' / 0:00';

            var timeTrack = document.createElement('span');
            timeTrack.className = 'playable-time-track';

            var timeTrackInner = document.createElement('span');
            timeTrackInner.style.width = '0%';

            playButton.addEventListener('click', function () {
                if (currentlyPlaying) {
                    currentlyPlaying.pause();
                    currentButton.classList.remove('playing');

                    if (currentlyPlaying === playableMedia) {
                        currentlyPlaying = null;
                        currentButton = null;
                        return;
                    }
                }

                currentlyPlaying = playableMedia;
                currentButton = playButton;

                playableMedia.play();

                playButton.classList.add('playing');
                playableOverlay.classList.add('open');
            }, false);

            playableMedia.addEventListener('timeupdate', function () {
                timeCurrent.textContent = formatTime(playableMedia.currentTime);
                timeTotal.textContent = ' / ' + formatTime(playableMedia.duration);
                timeTrackInner.style.width = playableMedia.currentTime / playableMedia.duration * 100 + '%';
            }, false);

            playableMedia.addEventListener('ended', function () {
                currentlyPlaying = null;
                currentButton = null;
                playButton.classList.remove('playing');
            }, false);

            timeTrack.appendChild(timeTrackInner);
            timeText.appendChild(timeCurrent);
            timeText.appendChild(timeTotal);
            timeIndicator.appendChild(timeText);
            timeIndicator.appendChild(timeTrack);
            playableOverlay.appendChild(playButton);
            playableOverlay.appendChild(timeIndicator);
            playableContainer.appendChild(playableOverlay);
        });

        thumbnailLayoutCalculated.listen(function (layout) {
            var playableContainer = layout.item.parentNode.querySelector('.playable-container');

            if (playableContainer) {
                playableContainer.style.width = layout.width + 'px';
                playableContainer.style.height = layout.height + 'px';

                playableContainer.classList.toggle('small', layout.width < 155);
                playableContainer.classList.toggle('tiny', layout.width < 115);
            }
        });
    })();

    // Confirm removing friends
    (function () {
        var hasUnfriend = $('input[name="action"][value="unfriend"]')[0];
        if (!hasUnfriend) {
            return;
        }

        $('form[name="frienduser"]').on('submit', function (e) {
            var shouldUnfriend = confirm('Are you sure you wish to remove this friend?');

            if (!shouldUnfriend) {
                e.preventDefault();
            }
        });
    })();

    (function () {
        var siterating = $('#siterating');
        var sfwrating = $('#sfwrating');
        siterating.change(function (e) {
            var maxvalue = siterating.children("option:selected").val();
            $('#sfwrating option').each(function(i, element){
                if(element.value >= maxvalue && i !== 0){
                    $(element).hide();
                }
                else {
                    $(element).show();
                }
            });
            if (sfwrating.children("option:selected").val() >= maxvalue) {
                if (maxvalue > 10) {
                    sfwrating.val(String(maxvalue - 10));
                } else {
                    sfwrating.val(String(10)).change();
                    sfwrating.trigger("updated");
                }
            }
        });
        siterating.trigger("change");
    })();
})();
