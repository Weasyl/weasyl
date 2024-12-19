/* global marked */

(function () {
    'use strict';

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

    var empty = containerNode => {
        var child;

        while (child = containerNode.firstChild) {
            containerNode.removeChild(child);
        }
    };

    var hasModifierKeys = e =>
        e.ctrlKey || e.shiftKey || e.altKey || e.metaKey;

    // thumbnails: config
    var thumbnailContainers = document.getElementsByClassName('thumbnail-grid'),
        thumbnailOptions = {
            minWidth: 125,  // minimum width per cell (should match min thumbnail width)
            rowBasis: 250,  // row height basis (should match max thumbnail height)
            itemGap: 8,     // common item padding
            breakpoint: '(max-width: 29.9em)'
        };

    // thumbnails: thumbnail data-width attribute helper
    function getWidthAttr(item) {
        return Math.max(parseInt(item.getAttribute('data-width')), thumbnailOptions.minWidth) || thumbnailOptions.rowBasis;
    }

    // thumbnails: calculate layout
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

            while (items.length > 0) {
                rowCount++;
                if (rowCount === maxRows) {
                    break;
                }

                var row = [],
                    rowWidth = thumbnailOptions.itemGap,
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
                    var totalGap = (row.length + 1) * thumbnailOptions.itemGap;
                    difference = (containerWidth - totalGap) / (rowWidth - totalGap);
                }
                forEach(row, function (item) {
                    var width = getWidthAttr(item) * thumbRatio * difference;
                    var height = startHeight * difference;

                    item.style.width = width + 'px';
                    item.style.height = height + 'px';

                    // reset on resize
                    item.parentNode.parentNode.style.display = '';
                });
            }

            // if any items did not get placed, hide them
            forEach(items, function (item) {
                item.parentNode.parentNode.style.display = 'none';
            });
        });
    }


    $(document).ready(function () {
        // thumbnails
        // give enhanced layout to modern browsers
        if ('classList' in document.createElement('_') && typeof window.matchMedia === 'function') {
            if (thumbnailContainers.length > 0) {
                calculateThumbnailLayout();
                window.addEventListener('resize', calculateThumbnailLayout);
            }
            document.documentElement.classList.add('enhanced-thumbnails');
        }

        // call appropriate functions and plugins
        $('textarea.expanding').autosize();

        // mobile nav
        $('#nav-toggle').on('click', function (ev) {
            ev.preventDefault();
            $('#header-nav, #nav-toggle').toggleClass('open');
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
        function closeLogin() {
            $('body').removeClass('modal-login');
            $(document).off('keyup', closeLoginIfEscape);
        }

        function closeLoginIfEscape(e) {
            if (e.key === 'Escape' && !hasModifierKeys(e)) {
                e.preventDefault();
                closeLogin();
            }
        }

        $('#hg-login').on('click', function (ev) {
            if (hasModifierKeys(ev)) {
                return;
            }

            ev.preventDefault();

            if (!$('body').hasClass('modal-login')) {
                $('body').addClass('modal-login');
                $(document).on('keyup', closeLoginIfEscape);
            }

            $('#login-user').focus();
        });

        $('#lb-close').on('click', function (ev) {
            ev.preventDefault();
            closeLogin();
        });

        // submission notifs buttons
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

        var staffNoteArea = $('#note-compose-staff-note #staff-note-area').hide();

        $('#note-compose-staff-note #mod-copy').change(function () {
            staffNoteArea.slideToggle(400);
        });
    });

    var newSocialGroup = document.getElementById('new-social-group');

    function addNewSocialGroupIfNeeded() {
        if (this.children[0].value || this.children[1].value) {
            newSocialGroup = this.cloneNode(true);
            newSocialGroup.children[0].value = newSocialGroup.children[1].value = '';
            this.insertAdjacentElement('afterend', newSocialGroup);
            this.removeEventListener('input', addNewSocialGroupIfNeeded);
            newSocialGroup.addEventListener('input', addNewSocialGroupIfNeeded);
        }
    }

    if (newSocialGroup) {
        newSocialGroup.removeAttribute('id');
        newSocialGroup.addEventListener('input', addNewSocialGroupIfNeeded);
        addNewSocialGroupIfNeeded.call(newSocialGroup);
    }

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

        function defang(node, isBody) {
            var i;

            for (i = node.childNodes.length; i--;) {
                var child = node.childNodes[i];

                if (child.nodeType === 1) {
                    defang(child, false);
                }
            }

            if (!isBody && allowedTags.indexOf(node.nodeName.toLowerCase()) === -1) {
                while (node.hasChildNodes()) {
                    node.parentNode.insertBefore(node.firstChild, node);
                }

                node.parentNode.removeChild(node);
            } else {
                for (i = node.attributes.length; i--;) {
                    var attribute = node.attributes[i];
                    var scheme = attribute.value && attribute.value.substring(0, attribute.value.indexOf(':'));

                    if (node.nodeName === 'A' && attribute.name === 'href' && allowedSchemes.indexOf(scheme) !== -1) {
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

    var markedLoadState = 0;

    function loadMarked() {
        if (markedLoadState !== 0) {
            return;
        }

        markedLoadState = 1;

        var markedScript = document.createElement('script');

        markedScript.onload = function () {
            markedLoadState = 2;

            forEach(document.getElementsByClassName('markdown'), updateMarkdownPreview);
        };

        markedScript.src = document.getElementById('scripts').getAttribute('data-marked-src');

        document.body.appendChild(markedScript);
    }

    function renderMarkdown(content, container) {
        var markdown = marked(content, markdownOptions);
        var sanitizeDocument = new DOMParser().parseFromString(markdown, 'text/html');
        var fragment = sanitizeDocument.body;

        weasylMarkdown(fragment);
        defang(fragment, true);

        while (fragment.hasChildNodes()) {
            container.appendChild(fragment.firstChild);
        }
    }

    function updateMarkdownPreview(input) {
        if (markedLoadState === 2) {
            var preview = input.nextSibling;
            empty(preview);
            renderMarkdown(input.value, preview);
        } else {
            loadMarked();
        }
    }

    function updateMarkdownPreviewListener() {
        updateMarkdownPreview(this);
    }

    function addMarkdownPreview(input) {
        var preview = document.createElement('div');
        preview.className = 'markdown-preview formatted-content';

        input.parentNode.insertBefore(preview, input.nextSibling);

        input.addEventListener('input', updateMarkdownPreviewListener);

        if (input.value === '') {
            input.addEventListener('focus', loadMarked);
        } else {
            updateMarkdownPreview(input);
        }
    }

    forEach(document.getElementsByClassName('markdown'), addMarkdownPreview);

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
        var formattedDate = date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hourCycle: 'h23',
        });

        var formattedTime = date.toLocaleString('en-US', {
            hour: 'numeric',
            minute: 'numeric',
            second: 'numeric',
            hourCycle: 'h23',
            timeZoneName: 'short',
        });

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

            if (confirm('Delete this comment and any replies?')) {
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
                        target.textContent = 'Failed to delete comment';

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

            // Remove the original form’s non-functional Markdown preview element
            contentField.parentNode.removeChild(contentField.nextSibling);
            contentField.value = '';

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
                target.removeEventListener('click', cancelReply);

                children.removeChild(newListItem);
                if (!children.hasChildNodes()) {
                    children.parentNode.removeChild(children);
                }

                target.focus();
            };

            var handleShortcuts = function handleShortcuts(e) {
                if (e.key === 'Escape' && !contentField.value) {
                    contentField.removeEventListener('keydown', handleShortcuts);
                    cancelReply(e);
                } else if (e.key === 'Enter' && e.ctrlKey) {
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
                    hideLink.textContent = 'Delete';

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

                    if (markedLoadState === 2) {
                        renderMarkdown(contentField.value, commentBody);
                    } else {
                        var pre = document.createElement('span');
                        pre.style.whiteSpace = 'pre-wrap';
                        pre.textContent = contentField.value;
                        commentBody.appendChild(pre);
                    }

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

                                    commentBody.innerHTML = result.html;

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
                        '&' + targetIdField.name + '=' + targetId +
                        '&parentid=' + commentInfo.id +
                        '&content=' + encodeURIComponent(contentField.value)
                    );

                    target.textContent = 'Reply';
                    target.removeEventListener('click', cancelReply);
                    contentField.removeEventListener('keydown', handleShortcuts);

                    newForm.style.display = 'none';
                    newForm.parentNode.insertBefore(newComment, newForm);

                    if (newFormError) {
                        newFormContent.removeChild(newFormError);
                        newFormError = null;
                    }
                }
            };

            target.textContent = 'Cancel (esc)';
            target.addEventListener('click', cancelReply);
            contentField.addEventListener('keydown', handleShortcuts);

            newForm.addEventListener('submit', function (e) {
                submitComment();
                e.preventDefault();
            });

            e.preventDefault();

            addMarkdownPreview(contentField);

            $(contentField).autosize();
            contentField.focus();
        }
    });

    var canTriggerShortcut = e =>
        ['INPUT', 'SELECT', 'TEXTAREA'].indexOf(e.target.nodeName) === -1;

    function addShortcut(key, action) {
        document.addEventListener('keydown', function (e) {
            if (e.key === key && !hasModifierKeys(e) && canTriggerShortcut(e)) {
                e.preventDefault();
                action();
            }
        });
    }

    var clickShortcut = element => element.click.bind(element);
    var focusShortcut = element => element.focus.bind(element);

    (function () {
        var folderNavPrev, folderNavNext;
        if ((folderNavPrev = document.getElementById('folder-nav-prev'))) {
            addShortcut('ArrowLeft', clickShortcut(folderNavPrev));
        }
        if ((folderNavNext = document.getElementById('folder-nav-next'))) {
            addShortcut('ArrowRight', clickShortcut(folderNavNext));
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
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                rootCommentForm.submit();
            }
        });

        // 'c' to focus comment box
        addShortcut('c', focusShortcut(rootCommentBox));

        // 'f' to favorite
        var faveButton = document.querySelector('#submission-favorite-form button');
        if (faveButton) {
            addShortcut('f', () => {
                faveButton.focus();
                faveButton.click();
            });
        }

    })();

    function disableWithLabel(inputElement, disable) {
        inputElement.disabled = disable;
        inputElement.parentNode.classList.toggle('disabled', disable);
    }

    function handleCheckState(target) {
        var disableId = target.dataset.disables;

        if (disableId) {
            var disables = document.getElementById(disableId);
            var disable = target.checked;

            disableWithLabel(disables, disable);
        }

        var showId = target.dataset.shows;

        if (showId) {
            var shows = document.getElementById(showId);

            shows.style.display = target.checked ? '' : 'none';
        }
    }

    document.addEventListener('change', function (e) {
        handleCheckState(e.target);
    });

    forEach(document.querySelectorAll('[data-disables]'), handleCheckState);
    forEach(document.querySelectorAll('[data-shows]'), handleCheckState);

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
            if (
                favoriteButton.classList.contains('pending')
                || (favoriteAction.value === 'unfavorite' && !confirm('Are you sure you wish to remove this submission from your favorites?'))
            ) {
                e.preventDefault();
                return;
            }

            favoriteButton.classList.add('pending');

            fetch(favoriteActionBase + favoriteAction.value, { method: 'POST' })
                .then(response =>
                    response.ok
                        ? response.json()
                        : Promise.reject()
                )
                .then(data => {
                    if (!data.success) {
                        return Promise.reject();
                    }

                    favoriteButton.classList.remove('pending');

                    var newState = favoriteButton.classList.toggle('active');
                    favoriteButton.replaceChild(document.createTextNode(newState ? ' Favorited' : ' Favorite'), favoriteButton.lastChild);
                    favoriteAction.value = newState ? 'unfavorite' : 'favorite';
                })
                // If there was any error, resubmit the form so the user can see it in full.
                .catch(error => {
                    favoriteForm.submit();
                });

            e.preventDefault();
        });
    })();

    // Home tabs
    (function () {
        function logStorageError(error) {
            try {
                console.warn(error);
            } catch (consoleError) {}
        }

        var homeTabs = document.getElementById('home-tabs');
        var homePanes = document.getElementById('home-panes');

        if (!homePanes) {
            return;
        }

        var currentTab = homeTabs.getElementsByClassName('current')[0];
        var currentPane = homePanes.getElementsByClassName('current')[0];

        $(homeTabs).on('click', '.home-pane-link', function (e) {
            e.preventDefault();

            var paneId = this.getAttribute('href').substring(1);
            var pane = document.getElementById(paneId);

            if (pane === currentPane) {
                return;
            }

            if (currentPane) {
                currentTab.classList.remove('current');
                currentPane.classList.remove('current');
            }

            currentTab = this;
            currentPane = pane;
            this.classList.add('current');
            pane.classList.add('current');

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

        var savedTab = savedTabId && homeTabs.querySelector('.home-pane-link[href="#' + savedTabId + '"]');

        if (savedTab) {
            savedTab.click();
        }
    })();
})();
