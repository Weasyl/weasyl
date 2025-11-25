/* global marked */
import autosize_ from 'autosize';
import defang from './defang.js';
import {byClass} from './dom.js';
import initEmbed from './embed.js';
import {forEach, some} from './util/array-like.js';
import hasModifierKeys from './util/has-modifier-keys.js';
import loginName from './util/login-name.js';
import {tryGetLocal, trySetLocal} from './util/storage.js';
import weasylMarkdown from './weasyl-markdown.js';

const autosize =
    CSS.supports('field-sizing', 'content')
        ? Object.assign(() => {}, {destroy: () => {}})
        : autosize_;

$(document).ready(() => {
    // autosizing textareas
    autosize($('textarea.expanding'));

    // mobile nav
    $('#nav-toggle').on('click', ev => {
        ev.preventDefault();
        $('#header-nav, #nav-toggle').toggleClass('open');
    });

    // report
    $('#detail-report-button').on('click', function (ev) {
        ev.preventDefault();
        $(this).addClass('active');
        $('#detail-report').slideDown(250);
    });

    $('#report-cancel').on('click', ev => {
        ev.preventDefault();
        $('#detail-report-button').removeClass('active');
        $('#detail-report').slideUp(250);
    });

    $('#detail_report_violation').on('change', () => {
        const reminder = document.getElementById('detail_report_reminder');
        const comment = document.getElementById('detail_report_content');
        const required = this.options[this.selectedIndex].getAttribute('data-comment-required').toLowerCase() === 'true';

        comment.required = required;
        reminder.style.visibility = required ? 'visible' : 'hidden';
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
    $('.marketplace-desc-fade button').on('click', function () {
        const fadebox = $(this).parent();
        fadebox.parent().removeClass('marketplace-desc-preview');
        fadebox.remove();
    });

    // Commishinfo prices "autopopulate" dropdown
    $('#commish-edit-select').on('change', function () {
        const selectedID = $(this).val();
        forEach(document.getElementsByClassName('select-priceid'), field => {
            const myID = field.getAttribute('data-priceid');
            const visible = selectedID == myID;
            field.style.display = visible ? '' : 'none';
        });
    });

    // checkbox containers
    $('.input-checkbox input[type=checkbox]').each(function () {
        const $this = $(this);
        const container = $this.closest('.input-checkbox');

        const updateChecked = () => {
            container.toggleClass('checked', this.checked);
        };

        $this.change(updateChecked);
        updateChecked();
    });

    const staffNoteArea = $('#note-compose-staff-note #staff-note-area').hide();

    $('#note-compose-staff-note #mod-copy').change(() => {
        staffNoteArea.slideToggle(400);
    });
});

let newSocialGroup = document.getElementById('new-social-group');

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

const reportButtons = $('#report_buttons .enableable');
const reportClosureWarning = $('#report-closure-warning');
const noteTitle = $('#note-title');
const noteTitleBox = $('#note-title-box');
const closureExplanation = $('#closure-explanation');
const closureExplanationBox = $('#closure-explanation-box');
const userNote = $('#user-note');
const userNoteBox = $('#user-note-box');

// This is required because expanding textareas don't work right if they
// start out hidden. So, only hide them after they've been autosized.
$(document).ready(() => {
    closureExplanationBox.hide();
    userNoteBox.hide();
});

const reportInputChanged = () => {
    const action = reportClosureAction.val();
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
};

const reportClosureAction = $('#report-closure-action').change(() => {
    setTimeout(reportInputChanged);
});

$('#closure-explanation, #user-note').keydown(() => {
    setTimeout(reportInputChanged);
});

$(document).on('submit', 'form[data-confirm]', function (e) {
    if (confirm(this.getAttribute('data-confirm'))) {
        const field = document.createElement('input');
        field.type = 'hidden';
        field.name = 'confirmed';
        this.appendChild(field);
    } else {
        e.preventDefault();
    }
});

$(document).on('click', 'button[data-confirm]', function (e) {
    if (confirm(this.getAttribute('data-confirm'))) {
        const field = document.createElement('input');
        field.type = 'hidden';
        field.name = 'confirmed';
        this.parentNode.appendChild(field);
    } else {
        e.preventDefault();
    }
});

const markdownOptions = {
    breaks: true,
    smartLists: true,
    noIndentedCode: true,
};

let markedLoadState = 0;

const loadMarked = () => {
    if (markedLoadState !== 0) {
        return;
    }

    markedLoadState = 1;

    const markedScript = document.createElement('script');

    markedScript.onload = function () {
        markedLoadState = 2;

        forEach(document.getElementsByClassName('markdown'), updateMarkdownPreview);
    };

    markedScript.src = MARKED_SRC;

    document.body.appendChild(markedScript);
};

const renderMarkdown = (content, container) => {
    const markdown = marked(content, markdownOptions);
    const sanitizeDocument = new DOMParser().parseFromString(markdown, 'text/html');
    const fragment = sanitizeDocument.body;

    weasylMarkdown(fragment);
    defang(fragment, true);

    while (fragment.hasChildNodes()) {
        container.appendChild(fragment.firstChild);
    }
};

const updateMarkdownPreview = input => {
    if (markedLoadState === 2) {
        const preview = input.nextSibling;
        preview.textContent = '';
        renderMarkdown(input.value, preview);
    } else {
        loadMarked();
    }
};

function updateMarkdownPreviewListener() {
    updateMarkdownPreview(this);
}

const addMarkdownPreview = input => {
    const preview = document.createElement('div');
    preview.className = 'markdown-preview formatted-content';

    input.parentNode.insertBefore(preview, input.nextSibling);

    input.addEventListener('input', updateMarkdownPreviewListener);

    if (input.value === '') {
        input.addEventListener('focus', loadMarked);
    } else {
        updateMarkdownPreview(input);
    }
};

forEach(document.getElementsByClassName('markdown'), addMarkdownPreview);

const getCommentInfo = commentActionLink => {
    let comment = commentActionLink;

    do {
        comment = comment.parentNode;
    } while (!comment.classList.contains('comment'));

    let comments = comment;

    do {
        comments = comments.parentNode;
    } while (!comments.classList.contains('comments'));

    return {
        m_comment: comment,
        m_comments: comments,
        m_id: parseInt(comment.dataset.id, 10),
        m_feature: comments.dataset.feature,
        m_removalPrivileges: comments.dataset.removalPrivileges,
    };
};

const formatDate = date => {
    const formattedDate = date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hourCycle: 'h23',
    });

    const formattedTime = date.toLocaleString('en-US', {
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
        hourCycle: 'h23',
        timeZoneName: 'short',
    });

    const timeElement = document.createElement('time');
    timeElement.dateTime = date.toISOString();

    const emphAt = document.createElement('i');
    emphAt.textContent = 'at';

    const datePart = document.createElement('b');
    datePart.textContent = formattedDate;

    timeElement.appendChild(datePart);
    timeElement.appendChild(document.createTextNode(' '));
    timeElement.appendChild(emphAt);
    timeElement.appendChild(document.createTextNode(' ' + formattedTime));

    return timeElement;
};

document.addEventListener('click', e => {
    const target = e.target;

    if (target.classList.contains('comment-hide-link')) {
        const commentInfo = getCommentInfo(target);
        const comment = commentInfo.m_comment;
        let children = comment.nextElementSibling;

        if (children && children.nodeName !== 'UL') {
            children = null;
        }

        if (confirm('Delete this comment and any replies?')) {
            const rq = new XMLHttpRequest();

            rq.open('POST', '/remove/comment', true);
            rq.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

            rq.onreadystatechange = function () {
                if (rq.readyState === 4) {
                    let result = null;

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
                'format=json&feature=' + commentInfo.m_feature +
                '&commentid=' + commentInfo.m_id);

            comment.classList.add('removing');

            if (children) {
                forEach(children.getElementsByClassName('comment'), function (descendant) {
                    descendant.classList.add('removing');
                });
            }
        }

        e.preventDefault();
    } else if (target.classList.contains('comment-reply-link')) {
        const commentInfo = getCommentInfo(target);
        const comment = commentInfo.m_comment;
        let children = comment.nextElementSibling;

        const newForm = commentInfo.m_comments.parentNode.getElementsByClassName('comment-form')[0].cloneNode(true);
        const newFormContent = newForm.getElementsByClassName('comment-content')[0];
        let newFormError = null;
        const targetIdField = newForm.getElementsByClassName('form-target-id')[0];
        const targetId = parseInt(targetIdField.value, 10);
        const contentField = newFormContent.getElementsByClassName('form-content')[0];

        // Remove the original form’s non-functional Markdown preview element
        contentField.parentNode.removeChild(contentField.nextSibling);
        contentField.value = '';

        if (!children || children.nodeName !== 'UL') {
            children = document.createElement('ul');
            comment.parentNode.insertBefore(children, comment.nextElementSibling);
        }

        const newListItem = document.createElement('li');

        newListItem.appendChild(newForm);
        children.insertBefore(newListItem, children.firstChild);

        const cancelReply = e => {
            e.preventDefault();
            e.stopPropagation();

            target.textContent = 'Reply';
            target.removeEventListener('click', cancelReply);

            children.removeChild(newListItem);
            if (!children.hasChildNodes()) {
                children.parentNode.removeChild(children);
            }

            autosize.destroy(contentField);

            target.focus();
        };

        const handleShortcuts = e => {
            if (e.key === 'Escape' && !contentField.value) {
                contentField.removeEventListener('keydown', handleShortcuts);
                cancelReply(e);
            } else if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                submitComment();
            }
        };

        const submitComment = () => {
            if (newForm.checkValidity()) {
                const posterUsername = document.getElementById('username').textContent;

                const newComment = document.createElement('div');
                newComment.className = 'comment';

                const commentAvatar = document.createElement('a');
                commentAvatar.className = 'avatar';
                commentAvatar.href = '/~' + loginName(posterUsername);

                const commentAvatarImage = document.createElement('img');
                commentAvatarImage.alt = 'Your avatar';
                commentAvatarImage.src = document.getElementById('avatar').src;

                commentAvatar.appendChild(commentAvatarImage);

                const commentContent = document.createElement('div');
                commentContent.className = 'comment-content';

                const commentActions = document.createElement('p');
                commentActions.className = 'actions';

                const replyLink = document.createElement('a');
                replyLink.href = '#';
                replyLink.className = 'comment-reply-link';
                replyLink.textContent = 'Reply';

                const hideLink = document.createElement('a');
                hideLink.href = '#';
                hideLink.className = 'comment-hide-link';
                hideLink.textContent = 'Delete';

                commentActions.appendChild(replyLink);
                commentActions.appendChild(document.createTextNode(' '));
                commentActions.appendChild(hideLink);

                const commentByline = document.createElement('p');
                commentByline.className = 'byline';

                const commentUserLink = document.createElement('a');
                commentUserLink.href = '/~' + loginName(posterUsername);
                commentUserLink.className = 'username';
                commentUserLink.textContent = posterUsername;

                commentByline.appendChild(commentUserLink);

                const userType = document.getElementById('header-user').dataset.userType;

                if (userType) {
                    const typeBadge = document.createElement('strong');
                    typeBadge.className = 'user-type-' + userType;
                    typeBadge.textContent = '(' + userType + ')';

                    commentByline.appendChild(document.createTextNode(' '));
                    commentByline.appendChild(typeBadge);
                }

                // TODO: Update this on response. API. Again.
                const posted = new Date();

                const emphOn = document.createElement('i');
                emphOn.textContent = 'on';

                commentByline.appendChild(document.createTextNode(' '));
                commentByline.appendChild(emphOn);
                commentByline.appendChild(document.createTextNode(' '));
                commentByline.appendChild(formatDate(posted));

                const commentBody = document.createElement('div');
                commentBody.className = 'formatted-content';

                if (markedLoadState === 2) {
                    renderMarkdown(contentField.value, commentBody);
                } else {
                    const pre = document.createElement('span');
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

                const rq = new XMLHttpRequest();

                rq.open('POST', newForm.action, true);
                rq.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

                rq.onreadystatechange = function () {
                    if (rq.readyState === 4) {
                        let result = null;

                        if (rq.status === 200) {
                            try {
                                result = JSON.parse(rq.responseText);
                            } catch (ex) {}

                            if (result && result.id) {
                                newComment.dataset.id = result.id;
                                newComment.id = 'cid' + result.id;
                                newComment.classList.remove('submitting');
                                newForm.parentNode.removeChild(newForm);

                                autosize.destroy(contentField);

                                if (commentInfo.m_removalPrivileges !== 'all') {
                                    const parentComment = newComment.parentNode.parentNode.previousElementSibling;
                                    const parentHideLink = parentComment && parentComment.getElementsByClassName('comment-hide-link')[0];

                                    if (parentHideLink) {
                                        parentHideLink.parentNode.removeChild(parentHideLink);
                                    }
                                }

                                const linkLink = document.createElement('a');
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
                    '&parentid=' + commentInfo.m_id +
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

        newForm.addEventListener('submit', e => {
            submitComment();
            e.preventDefault();
        });

        e.preventDefault();

        addMarkdownPreview(contentField);

        autosize(contentField);
        contentField.focus();
    }
});

const canTriggerShortcut = e =>
    !['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.nodeName);

const addShortcut = (key, action) => {
    document.addEventListener('keydown', e => {
        if (e.key === key && !hasModifierKeys(e) && canTriggerShortcut(e)) {
            e.preventDefault();
            action();
        }
    });
};

const clickShortcut = element => element.click.bind(element);
const focusShortcut = element => element.focus.bind(element);

(() => {
    const folderNavPrev = document.getElementById('folder-nav-prev');
    const folderNavNext = document.getElementById('folder-nav-next');
    if (folderNavPrev) {
        addShortcut('ArrowLeft', clickShortcut(folderNavPrev));
    }
    if (folderNavNext) {
        addShortcut('ArrowRight', clickShortcut(folderNavNext));
    }

    if (!document.getElementsByClassName) {
        return;
    }

    const rootCommentForm = byClass('comment-form');

    if (!rootCommentForm) {
        return;
    }

    const rootCommentBox = byClass('form-content');

    // ctrl+enter comment submit
    rootCommentBox.addEventListener('keydown', e => {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            rootCommentForm.submit();
        }
    });

    // 'c' to focus comment box
    addShortcut('c', focusShortcut(rootCommentBox));

    // 'f' to favorite
    const faveButton = document.querySelector('#submission-favorite-form button');
    if (faveButton) {
        addShortcut('f', () => {
            faveButton.focus();
            faveButton.click();
        });
    }

})();

const disableWithLabel = (inputElement, disable) => {
    inputElement.disabled = disable;
    inputElement.parentNode.classList.toggle('disabled', disable);
};

const handleCheckState = target => {
    const disableId = target.dataset.disables;

    if (disableId) {
        const disables = document.getElementById(disableId);
        const disable = target.checked;

        disableWithLabel(disables, disable);
    }

    const showId = target.dataset.shows;

    if (showId) {
        const shows = document.getElementById(showId);

        shows.style.display = target.checked ? '' : 'none';
    }
};

document.addEventListener('change', e => {
    handleCheckState(e.target);
});

forEach(document.querySelectorAll('[data-disables]'), handleCheckState);
forEach(document.querySelectorAll('[data-shows]'), handleCheckState);

{
    const isOtherOption = option =>
        option.hasAttribute('data-select-other');

    forEach(document.getElementsByClassName('data-select-other'), field => {
        const select = document.getElementById(field.getAttribute('data-select'));

        function updateVisibility() {
            const visible = some(this.selectedOptions, isOtherOption);

            field.style.display = visible ? '' : 'none';
        }

        updateVisibility.call(select);
        select.addEventListener('change', updateVisibility, {passive: true});
    });
}

// Ajax favorites
(() => {
    const favoriteForm = document.getElementById('submission-favorite-form');

    if (!favoriteForm) {
        return;
    }

    const favoriteButton = favoriteForm.getElementsByTagName('button')[0];
    const favoriteActionBase = favoriteForm.getAttribute('data-action-base');
    const favoriteAction = favoriteForm.querySelector('input[name="action"]');

    favoriteForm.addEventListener('submit', e => {
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

                const newState = favoriteButton.classList.toggle('active');
                favoriteButton.replaceChild(document.createTextNode(newState ? ' Favorited' : ' Favorite'), favoriteButton.lastChild);
                favoriteAction.value = newState ? 'unfavorite' : 'favorite';
            })
            // If there was any error, resubmit the form so the user can see it in full.
            .catch(() => {
                favoriteForm.submit();
            });

        e.preventDefault();
    });
})();

// Embeds
initEmbed();

// Home tabs
(() => {
    const homeTabs = document.getElementById('home-tabs');
    const homePanes = document.getElementById('home-panes');

    if (!homePanes) {
        return;
    }

    let currentTab = byClass('current', homeTabs);
    let currentPane = byClass('current', homePanes);

    $(homeTabs).on('click', '.home-pane-link', function (e) {
        e.preventDefault();

        const paneId = this.getAttribute('href').substring(1);
        const pane = document.getElementById(paneId);

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

        trySetLocal('home-tab', paneId);
    });

    const savedTabId = tryGetLocal('home-tab');

    const savedTab = savedTabId && homeTabs.querySelector('.home-pane-link[href="#' + savedTabId + '"]');

    if (savedTab) {
        savedTab.click();
    }
})();
